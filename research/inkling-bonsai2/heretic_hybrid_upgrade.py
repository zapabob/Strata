"""Upgrade the ablated (Heretic) Inkling-2-Mini model from all-PQ2_0 (7.24 GiB) to a
16 GB VRAM / 131K-147K context Agentic Hybrid GGUF (~11.15 GiB) directly from the
full BF16 checkpoint (`yanauto/Inkling-2-Mini-heretic-full`) using per-expert
activation-squared importance (`layer-00..23.npz`).

Features:
  - 6-core / 12-thread parallel CPU quantisation (`ggml_quantize_chunk`) — zero GPU lock contention
  - Preserves all existing official and Heretic PQ2_0 artefacts untouched
  - Resumable SQLite journal + periodic fsync checkpoints + SHA-256 verification
  - Strict typing, UTF-8, logging + tqdm, zero print()/eval()/exec()
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import ctypes as ct
import hashlib
import json
import logging
import math
import os
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any

import numpy as np
import torch
from tqdm import tqdm

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from gguf_stream import directory  # noqa: E402
from quantize_inkling2_pq2 import Checkpoint, mapped, upstream  # noqa: E402
from source import atomic_bytes, await_capacity  # noqa: E402
from spin8_quantizer import decode as pq2_decode  # noqa: E402

LOGGER = logging.getLogger("phase13.heretic_upgrade")

EXPERT_FORMATS: dict[str, tuple[int, int]] = {
    "NVFP4": (64, 36),     # 4.500 bpw (+ 128*4B per-expert F32 outer scale; Blackwell SM120 FP4 TC!)
    "IQ4_NL": (32, 18),    # 4.500 bpw
    "MXFP4": (32, 17),     # 4.250 bpw (native CUDA kernel + SM120)
    "IQ4_XS": (256, 136),  # 4.250 bpw
    "IQ3_S": (256, 110),   # 3.4375 bpw
    "IQ3_XXS": (256, 98),  # 3.0625 bpw
    "IQ2_S": (256, 82),    # 2.5625 bpw
    "PQ2_0": (128, 34),    # 2.125 bpw (baseline reference)
}

E2M1_POS = np.array([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0], dtype=np.float32)
E2M1_MIDS = np.array([0.25, 0.75, 1.25, 1.75, 2.5, 3.5, 5.0], dtype=np.float32)


def _build_ue4m3_table() -> np.ndarray:
    ue = np.zeros(127, dtype=np.float32)
    for b in range(1, 127):
        exp = (b >> 3) & 0xF
        man = b & 0x7
        ue[b] = (man / 8.0) * (2.0 ** -6) if exp == 0 else (1.0 + man / 8.0) * (2.0 ** (exp - 7))
    return ue


UE4M3_TABLE = _build_ue4m3_table()


def encode_nvfp4_matrix(w: np.ndarray) -> tuple[np.ndarray, float]:
    """Encode a 2D FP32 matrix (width % 64 == 0) into bit-exact GGML block_nvfp4 + F32 outer scale."""
    x = np.ascontiguousarray(w, dtype=np.float32)
    rows, cols = x.shape
    if cols % 64 != 0:
        raise ValueError(f"NVFP4 requires cols % 64 == 0, got {cols}")
    amax = float(np.max(np.abs(x)))
    outer_scale = amax / (6.0 * 448.0) if amax > 0.0 else 1.0
    x_scaled = x / outer_scale  # range [-6*448, +6*448]

    # Reshape into [rows, n_blk64, 4, 16] sub-blocks of 16 values
    n_blk64 = cols // 64
    sb = x_scaled.reshape(rows, n_blk64, 4, 16)
    sb_amax = np.max(np.abs(sb), axis=-1)  # [rows, n_blk64, 4]
    target_scale = sb_amax / 6.0

    # Nearest valid UE4M3 code in 0..126 (never 127 NaN, never sign bit 0x80)
    idx = np.searchsorted(UE4M3_TABLE, target_scale, side="left")
    idx = np.clip(idx, 0, 126)
    prev_idx = np.maximum(idx - 1, 0)
    choose_prev = np.abs(UE4M3_TABLE[prev_idx] - target_scale) <= np.abs(UE4M3_TABLE[idx] - target_scale)
    sc_u8 = np.where(choose_prev, prev_idx, idx).astype(np.uint8)
    sc_f32 = UE4M3_TABLE[sc_u8]  # [rows, n_blk64, 4]

    inv_sc = np.where(sc_f32 > 0.0, 1.0 / np.maximum(sc_f32, 1e-38), 0.0)
    norm = sb * inv_sc[..., None]
    signs = (norm < 0.0).astype(np.uint8) << 3
    mag = np.abs(norm)
    q_mag = np.searchsorted(E2M1_MIDS, mag, side="right").astype(np.uint8)
    codes = signs | q_mag  # [rows, n_blk64, 4, 16], values in 0..15

    # Split-half GGML layout: sq[0..7] low nibble = elem 0..7, high nibble = elem 8..15
    packed_qs = (codes[..., :8] | (codes[..., 8:] << 4)).reshape(rows, n_blk64, 32)
    out = np.concatenate((sc_u8, packed_qs), axis=-1).reshape(-1)
    return np.ascontiguousarray(out, dtype=np.uint8), float(outer_scale)


def encode_nvfp4_dense_matrix(w: np.ndarray) -> np.ndarray:
    """Encode a dense 2D FP32 matrix as self-contained GGML block_nvfp4 (UE4M3 scales folded, no outer scale)."""
    x = np.ascontiguousarray(w, dtype=np.float32)
    rows, cols = x.shape
    if cols % 64 != 0:
        raise ValueError(f"NVFP4 requires cols % 64 == 0, got {cols}")
    n_blk64 = cols // 64
    sb = x.reshape(rows, n_blk64, 4, 16)
    target_scale = np.max(np.abs(sb), axis=-1) / 6.0
    idx = np.clip(np.searchsorted(UE4M3_TABLE, target_scale, side="left"), 0, 126)
    prev_idx = np.maximum(idx - 1, 0)
    choose_prev = np.abs(UE4M3_TABLE[prev_idx] - target_scale) <= np.abs(UE4M3_TABLE[idx] - target_scale)
    sc_u8 = np.where(choose_prev, prev_idx, idx).astype(np.uint8)
    sc_f32 = UE4M3_TABLE[sc_u8]
    inv_sc = np.where(sc_f32 > 0.0, 1.0 / np.maximum(sc_f32, 1e-38), 0.0)
    norm = sb * inv_sc[..., None]
    signs = (norm < 0.0).astype(np.uint8) << 3
    q_mag = np.searchsorted(E2M1_MIDS, np.abs(norm), side="right").astype(np.uint8)
    codes = signs | q_mag
    packed_qs = (codes[..., :8] | (codes[..., 8:] << 4)).reshape(rows, n_blk64, 32)
    out = np.concatenate((sc_u8, packed_qs), axis=-1).reshape(-1)
    return np.ascontiguousarray(out, dtype=np.uint8)

def _sylvester_h128_norm() -> np.ndarray:
    h = np.array([[1.0]], dtype=np.float32)
    for _ in range(7):
        h = np.block([[h, h], [h, -h]])
    return (h / np.sqrt(np.float32(128.0))).astype(np.float32)


H128_NORM = _sylvester_h128_norm()


def encode_pq2_0_matrix(w: np.ndarray) -> np.ndarray:
    """Encode a 2D FP32 matrix (cols % 128 == 0) into bit-exact PrismML PQ2_0 ({-1, 0, +1}, H128 folded)."""
    x = np.ascontiguousarray(w, dtype=np.float32)
    rows, cols = x.shape
    if cols % 128 != 0:
        raise ValueError(f"PQ2_0 requires cols % 128 == 0, got {cols}")
    rot = x.reshape(-1, 128) @ H128_NORM  # [n_blk, 128]
    abs_r = np.abs(rot)
    # 4-step Lloyd-Max optimal ternary scale per 128-element block
    d = np.mean(abs_r, axis=-1, keepdims=True) * 1.5
    for _ in range(4):
        active = abs_r > (0.5 * d)
        cnt = np.sum(active, axis=-1, keepdims=True)
        d = np.where(cnt > 0, np.sum(abs_r * active, axis=-1, keepdims=True) / np.maximum(cnt, 1), 0.0)
    d_fp16 = d.squeeze(-1).astype(np.float16)
    d_f32 = d_fp16.astype(np.float32)[:, None]
    thresh = 0.5 * d_f32
    # Ternary codes: 0 -> -1, 1 -> 0, 2 -> +1 (matches ops.cu: (code - 1) * d)
    codes = np.ones_like(rot, dtype=np.uint8)
    codes = np.where(rot > thresh, np.uint8(2), codes)
    codes = np.where(rot < -thresh, np.uint8(0), codes)
    codes = np.where(d_f32 == 0.0, np.uint8(1), codes)
    c4 = codes.reshape(-1, 32, 4)
    packed = (c4[..., 0] | (c4[..., 1] << 2) | (c4[..., 2] << 4) | (c4[..., 3] << 6)).astype(np.uint8)
    d_bytes = d_fp16.view(np.uint8).reshape(-1, 2)
    return np.ascontiguousarray(np.concatenate((d_bytes, packed), axis=-1).reshape(-1), dtype=np.uint8)

GATE_UP_ELEMS = 128 * 2304 * 2304
DOWN_ELEMS = 128 * 2304 * 1152


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def bank_bytes(projection: str, fmt: str) -> int:
    elems = GATE_UP_ELEMS if projection == "gate_up" else DOWN_ELEMS
    grp, nb = EXPERT_FORMATS[fmt]
    extra_scale = 128 * 4 if fmt == "NVFP4" else 0
    return (elems // grp) * nb + extra_scale


def non_expert_fmt(
    g: Any,
    model: Any,
    name: str,
    raw_key: str,
    shape: list[int],
    layer: int | None,
    storage: str,
    *,
    dense_pq2: bool = False,
    keep_lm_head_q6k: bool = False,
    keep_embed_q6k: bool = False,
) -> str:
    """Non-expert precision: supports ternary PQ2_0 ({-1, 0, +1}) on foldable dense weights when dense_pq2=True."""
    q = g.GGMLQuantizationType
    if len(shape) <= 1 or "_norm." in name or name.endswith("norm.weight"):
        return "F32"
    forced = model.tensor_force_quant(raw_key, name, layer, len(shape))
    if isinstance(forced, q) and forced == q.F32:
        return "F32"
    if any(s in name for s in ("ffn_gate_inp", "loop_", "_ctrl_", "_conv", "_sconv", "sink", "_bias", "_res_query", "_clip", "k_conv_proj", "v_conv_proj")):
        return "F32" if storage == "F32" else "BF16"
    if dense_pq2 and len(shape) == 2 and shape[-1] % 128 == 0:
        if name == "output.weight" and not keep_lm_head_q6k:
            return "PQ2_0"
        if name == "token_embd.weight" and not keep_embed_q6k:
            return "PQ2_0"
        if any(name.endswith(f".{a}.weight") for a in ("attn_q", "attn_k", "attn_v", "attn_output", "attn_gate")):
            return "PQ2_0"
    if name in ("token_embd.weight", "output.weight"):
        return "Q6_K"
    if any(name.endswith(f".{a}.weight") for a in ("attn_q", "attn_k", "attn_v", "attn_output", "attn_gate", "attn_rel")):
        return "Q6_K"
    if len(shape) == 2 and shape[-1] % 256 == 0:
        return "Q6_K"
    if len(shape) == 2 and shape[-1] % 32 == 0:
        return "Q8_0"
    return "F32" if storage == "F32" else "BF16"


class GgmlCodec:
    """Thread-safe wrapper around ggml-base.dll quantise & dequantise routines."""

    def __init__(self, library: Path, gguf_mod: Any) -> None:
        self._dll_dir = os.add_dll_directory(str(library.parent)) if os.name == "nt" else None
        self.lib = ct.CDLL(str(library))
        self.pack = self.lib.ggml_quantize_chunk
        self.pack.argtypes = [ct.c_int, ct.c_void_p, ct.c_void_p, ct.c_int64, ct.c_int64, ct.c_int64, ct.c_void_p]
        self.pack.restype = ct.c_size_t
        self.gguf = gguf_mod
        self._deq_cache: dict[str, Any] = {}

    def encode_np(self, arr: np.ndarray, fmt: str, importance: np.ndarray | None = None) -> np.ndarray:
        if fmt == "F32":
            return np.ascontiguousarray(arr, dtype=np.float32).view(np.uint8).ravel()
        if fmt == "BF16":
            t = torch.from_numpy(np.ascontiguousarray(arr, dtype=np.float32)).to(torch.bfloat16).contiguous()
            return t.view(torch.uint8).numpy().ravel()
        if fmt == "F16":
            return np.ascontiguousarray(arr, dtype=np.float16).view(np.uint8).ravel()
        typ = self.gguf.GGMLQuantizationType[fmt]
        grp, nb = self.gguf.GGML_QUANT_SIZES[typ]
        x = np.ascontiguousarray(arr, dtype=np.float32)
        rows = math.prod(x.shape[:-1])
        cols = x.shape[-1]
        out = np.empty((x.size // grp) * nb, dtype=np.uint8)
        imp_ptr = None
        imp_c: np.ndarray | None = None
        if importance is not None:
            imp_c = np.ascontiguousarray(importance, dtype=np.float32)
            imp_ptr = imp_c.ctypes.data
        written = self.pack(int(typ), x.ctypes.data, out.ctypes.data, 0, rows, cols, imp_ptr)
        if written != out.size:
            raise ArithmeticError(f"{fmt}: written {written} != expected {out.size}")
        return out

    def dequant_np(self, raw: np.ndarray, fmt: str, shape: tuple[int, ...]) -> np.ndarray:
        if fmt == "PQ2_0":
            from scipy.linalg import hadamard
            x = pq2_decode(raw.reshape(-1, 34), shape).reshape(-1, 128)
            return ((x @ hadamard(128, dtype=np.float32)) / np.sqrt(np.float32(128))).reshape(shape)
        if fmt not in self._deq_cache:
            deq_name = "dequantize_row_" + (fmt.lower() if fmt not in ("Q4_K", "Q6_K") else fmt.replace("Q", "q"))
            fn = getattr(self.lib, deq_name)
            fn.argtypes = [ct.c_void_p, ct.c_void_p, ct.c_int64]
            fn.restype = None
            self._deq_cache[fmt] = fn
        fn = self._deq_cache[fmt]
        raw_c = np.ascontiguousarray(raw, dtype=np.uint8)
        out = np.empty(shape, dtype=np.float32)
        fn(raw_c.ctypes.data, out.ctypes.data, out.size)
        return out


def _layer_importance(moments_dir: Path, layer: int, proj_key: str, expert: int, width: int) -> np.ndarray:
    """Load per-expert activation-squared diagonal importance from saved 24-layer calibration npz."""
    npz_path = moments_dir / f"layer-{layer:02d}.npz"
    if not npz_path.is_file():
        return np.ones(width, dtype=np.float32)
    with np.load(npz_path) as z:
        k = f"{proj_key}.{expert}"
        if k in z.files:
            v = np.asarray(z[k], dtype=np.float32)
            if v.shape == (width,) and np.all(np.isfinite(v)):
                return np.maximum(v, 1e-8)
        # Fallback: mean importance across observed experts in this layer+projection
        matching = [np.asarray(z[fk], dtype=np.float32) for fk in z.files if fk.startswith(proj_key + ".")]
        if matching:
            return np.maximum(np.mean(matching, axis=0), 1e-8).astype(np.float32)
    return np.ones(width, dtype=np.float32)


def cmd_sensitivity(args: argparse.Namespace) -> int:
    """Measure activation-weighted relative error across all 48 Heretic BF16 banks on CPU."""
    cp = Checkpoint(args.source)
    g, _ = upstream(args.llama)
    codec = GgmlCodec(args.ggml_base.resolve(strict=True), g)

    pq2_fh = args.pq2_ablated.open("rb") if args.pq2_ablated and args.pq2_ablated.is_file() else None
    pq2_map: dict[str, Any] = {}
    if pq2_fh is not None:
        _, entries = directory(args.pq2_ablated, g.GGML_QUANT_SIZES)
        pq2_map = {t.name: t for t in entries}

    all_cand_fmts = ["IQ2_S", "IQ3_XXS", "IQ3_S", "IQ4_XS", "MXFP4", "NVFP4", "IQ4_NL"]
    banks_out: dict[str, Any] = {}

    try:
        for layer in tqdm(range(24), desc="heretic-sensitivity", unit="layer"):
            npz_path = args.moments / f"layer-{layer:02d}.npz"
            with np.load(npz_path) as z:
                layer_moments = {k: np.asarray(z[k], dtype=np.float32) for k in z.files if not k.startswith("cov.")}

            for proj_idx, (proj_name, proj_key) in enumerate((("gate_up", "w13"), ("down", "w2"))):
                raw_key = f"model.llm.layers.{layer}.mlp.experts.{proj_key}_weight"
                canon = f"blk.{layer}.ffn_{proj_name}_exps.weight"
                shape = cp.size(raw_key)  # [128, height, width]
                height, width = shape[1], shape[2]
                cand_fmts = [f for f in all_cand_fmts if width % EXPERT_FORMATS[f][0] == 0]

                # Pick up to 4 representative experts with saved calibration importance
                avail_e = sorted(int(k.split(".")[1]) for k in layer_moments if k.startswith(proj_key + "."))
                if len(avail_e) >= 4:
                    pick = [avail_e[i] for i in np.linspace(0, len(avail_e) - 1, 4).astype(int)]
                else:
                    pick = [0, 42, 85, 127]

                rng = np.random.default_rng(20261125 + 2 * layer + proj_idx)
                rows = np.sort(rng.choice(height, size=args.rows, replace=False))
                src_rows = (2 * (rows % (height // 2)) + rows // (height // 2)) if proj_name == "gate_up" else rows

                fmt_rel_errs: dict[str, list[float]] = {f: [] for f in cand_fmts}
                if pq2_fh is not None and canon in pq2_map:
                    fmt_rel_errs["PQ2_0"] = []

                for e in pick:
                    imp = layer_moments.get(f"{proj_key}.{e}")
                    if imp is None or imp.shape != (width,):
                        imp = np.ones(width, dtype=np.float32)
                    imp = np.maximum(imp, 1e-8).astype(np.float32)

                    w_full = cp.raw(raw_key, e).float().numpy()
                    w = np.ascontiguousarray(w_full[src_rows], dtype=np.float32)
                    denom = float(np.sum((w.astype(np.float64) ** 2) * imp.astype(np.float64)[None, :]))
                    denom = max(denom, 1e-30)

                    for fmt in cand_fmts:
                        if fmt == "NVFP4":
                            packed, outer_s = encode_nvfp4_matrix(w)
                            recon = codec.dequant_np(packed, "NVFP4", w.shape) * outer_s
                        else:
                            packed = codec.encode_np(w, fmt, importance=imp)
                            recon = codec.dequant_np(packed, fmt, w.shape)
                        num = float(np.sum(((recon - w).astype(np.float64) ** 2) * imp.astype(np.float64)[None, :]))
                        fmt_rel_errs[fmt].append(num / denom)

                    if "PQ2_0" in fmt_rel_errs:
                        t_pq = pq2_map[canon]
                        row_stride = t_pq.n_bytes // (128 * height)
                        pq_chunks = []
                        for r in rows:
                            pq2_fh.seek(t_pq.data_offset + (e * height + int(r)) * row_stride)
                            pq_chunks.append(np.frombuffer(pq2_fh.read(row_stride), dtype=np.uint8))
                        pq_raw = np.stack(pq_chunks)
                        recon_pq = codec.dequant_np(pq_raw, "PQ2_0", w.shape)
                        num_pq = float(np.sum(((recon_pq - w).astype(np.float64) ** 2) * imp.astype(np.float64)[None, :]))
                        fmt_rel_errs["PQ2_0"].append(num_pq / denom)

                banks_out[canon] = {
                    "layer": layer,
                    "projection": proj_name,
                    "source_precision": "BF16",
                    "visit_weight": 3.0 if 6 <= layer <= 17 else 1.0,
                    "sampled_experts": pick,
                    "rows_per_expert": args.rows,
                    "activation_weighted_rel_mse": {
                        fmt: round(float(np.mean(vals)), 8) for fmt, vals in fmt_rel_errs.items()
                    },
                }
    finally:
        if pq2_fh is not None:
            pq2_fh.close()

    report = {
        "schema": "phase13-heretic-sensitivity-v1",
        "source_repository": cp.repo,
        "source_revision": cp.revision,
        "moments_dir": str(args.moments),
        "banks": banks_out,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    atomic_bytes(args.out, (json.dumps(report, indent=2) + "\n").encode("utf-8"))
    LOGGER.info("Saved 48-bank Heretic activation-weighted sensitivity to %s", args.out)
    return 0


def cmd_allocate(args: argparse.Namespace) -> int:
    """Solve constrained 11.0-11.3 GiB optimal allocation for Heretic Hybrid (ctx131K-147K in 16GB VRAM)."""
    sens = json.loads(args.sensitivity.read_text(encoding="utf-8"))
    cp = Checkpoint(args.source)
    g, klass = upstream(args.llama)
    model = klass(cp.path, g.LlamaFileType.MOSTLY_Q4_K_M, args.out.with_suffix(".tmp.gguf"), model_name="Inkling-2-Mini-Heretic-Agentic-128K-Hybrid")

    non_expert_bytes = 0
    non_expert_map: dict[str, str] = {}
    for raw, name, shape, _, layer in mapped(model, cp, meta=True):
        if raw.endswith((".w13_weight", ".w2_weight")):
            continue
        fmt = non_expert_fmt(
            g,
            model,
            name,
            raw,
            shape,
            layer,
            cp.header[raw]["dtype"],
            dense_pq2=args.dense_pq2,
            keep_lm_head_q6k=args.keep_lm_head_q6k,
            keep_embed_q6k=args.keep_embed_q6k,
        )
        typ = g.GGMLQuantizationType[fmt]
        grp, nb = g.GGML_QUANT_SIZES[typ]
        non_expert_bytes += (math.prod(shape) // grp) * nb
        non_expert_map[name] = fmt

    budget_bytes = int(args.target_gib * (1024 ** 3)) - non_expert_bytes
    banks = sens["banks"]

    # Build Pareto-optimal ladder per bank (including Blackwell native NVFP4 + MXFP4 + IQ*)
    allowed = ["NVFP4"] if args.all_nvfp4_experts else ["IQ2_S", "IQ3_XXS", "IQ3_S", "IQ4_XS", "MXFP4", "NVFP4", "IQ4_NL"]
    options: dict[str, list[tuple[str, int, float]]] = {}
    choices: dict[str, str] = {}

    for layer in range(24):
        for proj in ("gate_up", "down"):
            nm = f"blk.{layer}.ffn_{proj}_exps.weight"
            entry = banks[nm]
            visit_mult = 3.0 if 6 <= layer <= 17 else 1.0
            proj_mult = 1.4 if proj == "down" else 1.0
            w = visit_mult * proj_mult
            errs = entry["activation_weighted_rel_mse"]

            cands = [(fmt, bank_bytes(proj, fmt), float(errs[fmt]) * w) for fmt in allowed if fmt in errs]
            cands.sort(key=lambda t: (t[1], t[2]))
            pareto: list[tuple[str, int, float]] = []
            for fmt, nb, we in cands:
                if not pareto or we < pareto[-1][2] - 1e-12:
                    pareto.append((fmt, nb, we))
            options[nm] = pareto
            choices[nm] = pareto[0][0]

    def used_bytes() -> int:
        return sum(bank_bytes("gate_up" if "gate_up" in nm else "down", fmt) for nm, fmt in choices.items())

    # Guarantee all 24 down projections at >= 4-bit (best of NVFP4/MXFP4/IQ4_NL) before spending on gate_up
    for layer in range(24):
        nm = f"blk.{layer}.ffn_down_exps.weight"
        four_bit = [p for p in options[nm] if p[0] in ("NVFP4", "MXFP4", "IQ4_XS", "IQ4_NL")]
        if four_bit:
            best_4b = min(four_bit, key=lambda t: t[2])
            prev = choices[nm]
            choices[nm] = best_4b[0]
            if used_bytes() > budget_bytes:
                choices[nm] = prev

    # Greedy marginal-error-reduction-per-byte promotions across all 48 banks
    promotions: list[dict[str, Any]] = []
    while True:
        best_gain = -1.0
        best_move: tuple[str, str, int, float] | None = None
        cur_used = used_bytes()
        for nm, pareto in options.items():
            ci = next(i for i, (f, _, _) in enumerate(pareto) if f == choices[nm])
            cb, ce = pareto[ci][1], pareto[ci][2]
            for nf, nb, ne in pareto[ci + 1 :]:
                db = nb - cb
                if db <= 0 or cur_used + db > budget_bytes:
                    continue
                gain = (ce - ne) / float(db)
                if gain > best_gain:
                    best_gain = gain
                    best_move = (nm, nf, db, ce - ne)
        if best_move is None:
            break
        nm, nf, db, de = best_move
        old = choices[nm]
        choices[nm] = nf
        promotions.append({"tensor": nm, "from": old, "to": nf, "delta_mib": round(db / (1024 ** 2), 2), "weighted_mse_drop": round(de, 8)})

    # Compare total weighted MSE: all-PQ2_0 baseline vs our 11.15 GiB Heretic Hybrid!
    pq2_total_werr = 0.0
    hyb_total_werr = 0.0
    for nm, fmt in choices.items():
        e = banks[nm]
        mult = (3.0 if 6 <= e["layer"] <= 17 else 1.0) * (1.4 if e["projection"] == "down" else 1.0)
        hyb_total_werr += float(e["activation_weighted_rel_mse"][fmt]) * mult
        if "PQ2_0" in e["activation_weighted_rel_mse"]:
            pq2_total_werr += float(e["activation_weighted_rel_mse"]["PQ2_0"]) * mult

    counts: dict[str, int] = {}
    for fmt in choices.values():
        counts[fmt] = counts.get(fmt, 0) + 1

    exp_b = used_bytes()
    tot_b = non_expert_bytes + exp_b
    recipe = {
        "schema": "phase13-heretic-recipe-v1",
        "source_repository": cp.repo,
        "source_revision": cp.revision,
        "target_gib": args.target_gib,
        "non_expert_bytes": non_expert_bytes,
        "expert_bytes": exp_b,
        "estimated_total_bytes": tot_b,
        "estimated_total_gib": round(tot_b / (1024 ** 3), 4),
        "expert_format_counts": dict(sorted(counts.items())),
        "weighted_rel_mse_vs_pq2_baseline": {
            "pq2_0_balanced_weighted_rel_mse": round(pq2_total_werr, 6),
            "heretic_hybrid_weighted_rel_mse": round(hyb_total_werr, 6),
            "error_reduction_factor": round(pq2_total_werr / max(hyb_total_werr, 1e-12), 2) if pq2_total_werr > 0 else None,
            "error_reduction_pct": round((1.0 - hyb_total_werr / pq2_total_werr) * 100.0, 2) if pq2_total_werr > 0 else None,
        },
        "non_expert_types": non_expert_map,
        "bank_types": choices,
        "promotions": promotions,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    atomic_bytes(args.out, (json.dumps(recipe, indent=2) + "\n").encode("utf-8"))
    LOGGER.info(
        "Heretic Hybrid recipe: %.3f GiB | counts=%s | weighted MSE drop=%.2f%% (%.2fx lower error than PQ2_0!)",
        recipe["estimated_total_gib"],
        counts,
        recipe["weighted_rel_mse_vs_pq2_baseline"]["error_reduction_pct"] or 0.0,
        recipe["weighted_rel_mse_vs_pq2_baseline"]["error_reduction_factor"] or 0.0,
    )
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Build Inkling-2-Mini-Heretic-Agentic-128K-Hybrid.gguf using 6C/12T CPU parallelism."""
    recipe = json.loads(args.recipe.read_text(encoding="utf-8"))
    bank_types: dict[str, str] = recipe["bank_types"]
    non_expert_types: dict[str, str] = recipe["non_expert_types"]

    cp = Checkpoint(args.source)
    g, klass = upstream(args.llama)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    header_path = args.output.with_suffix(".gguf.header")
    model = klass(cp.path, g.LlamaFileType.MOSTLY_Q4_K_M, args.output, model_name="Inkling-2-Mini-Heretic-Agentic-128K-Hybrid")

    entries: list[dict[str, Any]] = []
    for raw, name, shape, _, layer in mapped(model, cp, meta=True):
        is_exp = raw.endswith((".w13_weight", ".w2_weight"))
        fmt = bank_types[name] if is_exp else non_expert_types[name]
        typ = g.GGMLQuantizationType[fmt]
        grp, nb = g.GGML_QUANT_SIZES[typ]
        entries.append(dict(raw=raw, name=name, shape=shape, type=fmt, bytes=(math.prod(shape) // grp) * nb, is_expert=is_exp, layer=layer))
        if is_exp and fmt == "NVFP4":
            scale_name = name.removesuffix("weight") + "scale"
            entries.append(dict(raw=raw, name=scale_name, shape=[128], type="F32", bytes=128 * 4, is_expert=False, is_scale=True, layer=layer))

    w = model.gguf_writer
    for d in entries:
        w.add_tensor_info(d["name"], d["shape"], np.dtype("float32"), d["bytes"], raw_dtype=g.GGMLQuantizationType[d["type"]])
    model.prepare_metadata(vocab_only=False)
    w.add_string("inkling_quant.source", cp.repo)
    w.add_string("inkling_quant.revision", cp.revision)
    w.add_string("inkling_quant.profile", "heretic-agentic-128k-hybrid")
    pq2_forward = [d["name"] for d in entries if d["type"] == "PQ2_0" and d["name"] != "token_embd.weight"]
    pq2_inverse = [d["name"] for d in entries if d["type"] == "PQ2_0" and d["name"] == "token_embd.weight"]
    if pq2_forward or pq2_inverse:
        w.add_uint32("prism.hadamard.version", 1)
        w.add_uint32("prism.hadamard.block_size", 128)
        w.add_string("prism.hadamard.transform", "normalized-sylvester-walsh-hadamard")
        w.add_string("prism.hadamard.axis", "input-last-dimension")
        w.add_string("prism.hadamard.sign_mode", "identity")
        if pq2_forward:
            w.add_array("prism.hadamard.weight_names", pq2_forward)
        if pq2_inverse:
            w.add_array("prism.hadamard.inverse_weight_names", pq2_inverse)
    w.write_header_to_file(header_path)
    w.write_kv_data_to_file()
    w.write_ti_data_to_file()
    w.close()

    align = lambda n: (n + 31) // 32 * 32
    pos = align(header_path.stat().st_size)
    for d in entries:
        d["offset"] = pos
        pos += align(d["bytes"])
    total_size = pos
    LOGGER.info("Header prepared: %d tensors, %.3f GiB (%d bytes)", len(entries), total_size / (1024 ** 3), total_size)

    if args.output.exists():
        raise FileExistsError(args.output)
    partial = Path(str(args.output) + ".partial")
    ledger = args.output.with_suffix(".sqlite")
    sig = hashlib.sha256(header_path.read_bytes()).hexdigest()
    db = sqlite3.connect(ledger)
    db.execute("create table if not exists identity(h text primary key)")
    db.execute("create table if not exists done(name text, part integer, n integer, hash text, primary key(name, part))")
    ids = db.execute("select h from identity").fetchall()
    if ids and ids != [(sig,)]:
        raise ValueError("Journal header mismatch")
    if not ids:
        await_capacity(args.output.parent, total_size)
        db.execute("insert into identity values(?)", (sig,))
        db.commit()
        with partial.open("wb") as f:
            hb = header_path.read_bytes()
            f.write(hb)
            f.write(bytes((-len(hb)) % 32))
            f.flush()
            os.fsync(f.fileno())

    codec = GgmlCodec(args.ggml_base.resolve(strict=True), g)
    index = {d["name"]: d for d in entries}
    t_ckpt = time.monotonic()

    try:
        with partial.open("r+b") as f, ThreadPoolExecutor(max_workers=args.workers) as pool:
            def write_part(d: dict[str, Any], part: int, rel_off: int, payload: bytes) -> None:
                nonlocal t_ckpt
                pos_w = d["offset"] + rel_off
                end_w = f.seek(0, os.SEEK_END)
                if pos_w > end_w:
                    f.write(bytes(pos_w - end_w))
                else:
                    f.seek(pos_w)
                f.write(payload)
                db.execute("insert into done values(?,?,?,?)", (d["name"], part, len(payload), hashlib.sha256(payload).hexdigest()))
                if time.monotonic() - t_ckpt >= 30.0:
                    f.flush()
                    os.fsync(f.fileno())
                    db.commit()
                    t_ckpt = time.monotonic()

            model._queries.clear()
            for raw, name, shape, value, layer in tqdm(mapped(model, cp, meta=False), total=len(entries), desc="build-heretic-hybrid", unit="tensor"):
                d = index[name]
                done_b = db.execute("select coalesce(sum(n),0) from done where name=?", (name,)).fetchone()[0]
                if done_b >= d["bytes"]:
                    continue
                fmt = d["type"]
                if not d["is_expert"]:
                    if fmt == "PQ2_0":
                        payload = encode_pq2_0_matrix(value.float().numpy()).tobytes()
                    elif fmt == "NVFP4":
                        payload = encode_nvfp4_dense_matrix(value.float().numpy()).tobytes()
                    else:
                        payload = codec.encode_np(value.float().numpy(), fmt).tobytes()
                    write_part(d, 0, 0, payload)
                    f.flush()
                    db.commit()
                    continue

                # Expert bank: parallelise across 6C/12T in batches of 12 experts to keep RAM < 2 GiB
                proj_key = "w13" if ".w13_" in raw else "w2"
                width = shape[-1]
                expert_stride = d["bytes"] // 128
                npz_path = args.moments / f"layer-{layer:02d}.npz"
                layer_moments: dict[str, np.ndarray] = {}
                if npz_path.is_file():
                    with np.load(npz_path) as z:
                        layer_moments = {k: np.asarray(z[k], dtype=np.float32) for k in z.files if k.startswith(proj_key + ".")}
                fallback_imp = (
                    np.maximum(np.mean(list(layer_moments.values()), axis=0), 1e-8).astype(np.float32)
                    if layer_moments
                    else np.ones(width, dtype=np.float32)
                )

                done_parts = {row[0] for row in db.execute("select part from done where name=?", (name,)).fetchall()}
                todo_experts = [e for e in range(128) if e not in done_parts]
                nvfp4_scales = np.ones(128, dtype="<f4")

                def _quant_one(e: int) -> tuple[int, bytes, float]:
                    w_t = cp.raw(raw, e).float()
                    if ".w13_" in raw:
                        w_t = torch.cat((w_t[::2], w_t[1::2]), dim=0)
                    if fmt == "NVFP4":
                        raw_arr, outer_s = encode_nvfp4_matrix(w_t.numpy())
                        raw_b = raw_arr.tobytes()
                        if len(raw_b) != expert_stride:
                            raise ArithmeticError(f"{name}[{e}] NVFP4: {len(raw_b)} != {expert_stride}")
                        return e, raw_b, outer_s
                    imp = layer_moments.get(f"{proj_key}.{e}", fallback_imp)
                    imp = np.maximum(imp, 1e-8).astype(np.float32)
                    raw_b = codec.encode_np(w_t.numpy(), fmt, importance=imp).tobytes()
                    if len(raw_b) != expert_stride:
                        raise ArithmeticError(f"{name}[{e}] {fmt}: {len(raw_b)} != {expert_stride}")
                    return e, raw_b, 1.0

                batch_sz = max(args.workers * 2, 8)
                for i in range(0, len(todo_experts), batch_sz):
                    batch = todo_experts[i : i + batch_sz]
                    for e, payload, outer_s in pool.map(_quant_one, batch):
                        write_part(d, e, e * expert_stride, payload)
                        if fmt == "NVFP4":
                            nvfp4_scales[e] = outer_s
                if fmt == "NVFP4":
                    scale_name = name.removesuffix("weight") + "scale"
                    sd = index[scale_name]
                    if db.execute("select coalesce(sum(n),0) from done where name=?", (scale_name,)).fetchone()[0] < sd["bytes"]:
                        # Recompute outer scale for any experts that were already done in a prior resumed run
                        for e in done_parts:
                            w_t = cp.raw(raw, e).float().numpy()
                            amax = float(np.max(np.abs(w_t)))
                            nvfp4_scales[e] = amax / (6.0 * 448.0) if amax > 0.0 else 1.0
                        write_part(sd, 0, 0, nvfp4_scales.tobytes())
                f.flush()
                os.fsync(f.fileno())
                db.commit()

            end_pos = f.seek(0, os.SEEK_END)
            if not 0 <= total_size - end_pos < 32:
                raise IOError(f"Invalid final GGUF extent: {end_pos} vs {total_size}")
            if total_size > end_pos:
                f.write(bytes(total_size - end_pos))
            f.flush()
            os.fsync(f.fileno())
            db.commit()
    finally:
        db.close()

    partial.rename(args.output)
    sha = hashlib.sha256()
    with args.output.open("rb") as fh:
        for blk in iter(lambda: fh.read(16 * 1024 * 1024), b""):
            sha.update(blk)
    manifest = {
        "file": str(args.output),
        "bytes": args.output.stat().st_size,
        "gib": round(args.output.stat().st_size / (1024 ** 3), 4),
        "sha256": sha.hexdigest(),
        "recipe": str(args.recipe),
        "expert_format_counts": recipe["expert_format_counts"],
    }
    atomic_bytes(args.output.with_suffix(".manifest.json"), (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    LOGGER.info("COMPLETED %s (%.3f GiB, sha256=%s)", args.output.name, manifest["gib"], manifest["sha256"][:16])
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("sensitivity")
    ps.add_argument("--source", type=Path, required=True)
    ps.add_argument("--llama", type=Path, required=True)
    ps.add_argument("--ggml-base", type=Path, required=True)
    ps.add_argument("--moments", type=Path, required=True)
    ps.add_argument("--pq2-ablated", type=Path, default=None)
    ps.add_argument("--rows", type=int, default=32)
    ps.add_argument("--out", type=Path, required=True)

    pa = sub.add_parser("allocate")
    pa.add_argument("--sensitivity", type=Path, required=True)
    pa.add_argument("--source", type=Path, required=True)
    pa.add_argument("--llama", type=Path, required=True)
    pa.add_argument("--target-gib", type=float, default=11.15)
    pa.add_argument("--dense-pq2", action="store_true", help="Quantise foldable dense matrices (attn_*, token_embd, output) to ternary PQ2_0 ({-1,0,+1})")
    pa.add_argument("--keep-lm-head-q6k", action="store_true", help="Keep output.weight (LM head) at Q6_K even when --dense-pq2 is set")
    pa.add_argument("--keep-embed-q6k", action="store_true", help="Keep token_embd.weight at Q6_K even when --dense-pq2 is set")
    pa.add_argument("--all-nvfp4-experts", action="store_true", help="Force all 48 MoE expert banks to NVFP4 (Mode B: RAM/NVMe cold-MoE offload)")
    pa.add_argument("--out", type=Path, required=True)

    pb = sub.add_parser("build")
    pb.add_argument("--recipe", type=Path, required=True)
    pb.add_argument("--source", type=Path, required=True)
    pb.add_argument("--llama", type=Path, required=True)
    pb.add_argument("--ggml-base", type=Path, required=True)
    pb.add_argument("--moments", type=Path, required=True)
    pb.add_argument("--output", type=Path, required=True)
    pb.add_argument("--workers", type=int, default=6)
    return p


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    with torch.inference_mode():
        if args.cmd == "sensitivity":
            return cmd_sensitivity(args)
        if args.cmd == "allocate":
            return cmd_allocate(args)
        if args.cmd == "build":
            return cmd_build(args)
    raise ValueError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
