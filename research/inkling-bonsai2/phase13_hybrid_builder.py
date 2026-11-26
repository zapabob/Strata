"""Phase XIII — Constrained precision allocator and official-checkpoint hybrid GGUF builder.

Produces both Phase XIII deliverables from the official Thinking Machines Lab
Inkling-2-Mini checkpoint while preserving all existing official and Heretic
PQ2_0 artefacts:
  1. Inkling-2-Mini-Agentic-128K-Hybrid.gguf        (lossless NVFP4 + MXFP4/IQ* mixed experts)
  2. Inkling-2-Mini-Agentic-128K-Spin8-Hybrid.gguf  (adds Spin(8)/Hadamard PQ2_0 only where
                                                     validation degradation is within tolerance,
                                                     reinvesting freed bytes into NVFP4/MXFP4)

Uses logging + tqdm, strict typing, resumable SQLite journalling, and zero print()/eval()/exec().
"""

from __future__ import annotations

import argparse
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

from check_hybrid_scales import pack_nv  # noqa: E402
from gguf_stream import directory  # noqa: E402
from official_weights import Original, reconstruct  # noqa: E402
from quantize_inkling2_pq2 import Checkpoint, mapped, upstream  # noqa: E402
from source import atomic_bytes, await_capacity  # noqa: E402

LOGGER = logging.getLogger("phase13.hybrid_builder")

# Bits per weight for each candidate expert encoding (block_elements, block_bytes).
EXPERT_GEOMETRY: dict[str, tuple[int, int]] = {
    "NVFP4": (64, 36),     # 4.500 bpw (lossless original on layers 0..19)
    "IQ4_NL": (32, 18),    # 4.500 bpw
    "MXFP4": (32, 17),     # 4.250 bpw (native CUDA kernel + SM120)
    "IQ4_XS": (256, 136),  # 4.250 bpw
    "IQ3_S": (256, 110),   # 3.4375 bpw
    "IQ3_XXS": (256, 98),  # 3.0625 bpw
    "IQ2_S": (256, 82),    # 2.5625 bpw
    "PQ2_0": (128, 34),    # 2.125 bpw (ternary {-1, 0, +1} Hadamard/Spin8)
}

GATE_UP_ELEMS = 128 * 2304 * 2304  # 679,477,248
DOWN_ELEMS = 128 * 2304 * 1152     # 339,738,624


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
    grp, nb = EXPERT_GEOMETRY[fmt]
    extra_scale = 128 * 4 if fmt == "NVFP4" else 0
    return (elems // grp) * nb + extra_scale


def non_expert_type(g: Any, model: Any, name: str, raw_key: str, shape: list[int], layer: int | None, storage: str) -> str:
    """High-fidelity non-expert precision matching P2 priorities (attention, router, controllers)."""
    q = g.GGMLQuantizationType
    if len(shape) <= 1 or "_norm." in name or name.endswith("norm.weight"):
        return "F32"
    forced = model.tensor_force_quant(raw_key, name, layer, len(shape))
    if isinstance(forced, q) and forced == q.F32:
        return "F32"
    if any(s in name for s in ("ffn_gate_inp", "loop_", "_ctrl_", "_conv", "_sconv", "sink", "_bias", "_res_query", "_clip", "k_conv_proj", "v_conv_proj")):
        return "F32" if storage == "F32" else "BF16"
    if name in ("token_embd.weight", "output.weight"):
        return "Q6_K"
    if any(name.endswith(f".{a}.weight") for a in ("attn_q", "attn_k", "attn_v", "attn_output", "attn_gate", "attn_rel")):
        return "Q6_K"
    if len(shape) == 2 and shape[-1] % 256 == 0:
        return "Q6_K"
    if len(shape) == 2 and shape[-1] % 32 == 0:
        return "Q8_0"
    return "F32" if storage == "F32" else "BF16"


def _candidate_error(bank_entry: dict[str, Any], fmt: str, source_precision: str) -> float | None:
    """Return measured validation relative output MSE for a candidate format on this bank."""
    val = bank_entry.get("validation", {})
    if fmt == "NVFP4":
        if source_precision != "NVFP4":
            return None
        if "source_NVFP4" in val:
            return float(val["source_NVFP4"]["relative_output_mse"])
        if "published_NVFP4" in val:
            return float(val["published_NVFP4"]["relative_output_mse"])
        return 0.0
    if fmt == "PQ2_0":
        if "PQ2_0_Spin8" in val:
            return float(val["PQ2_0_Spin8"]["relative_output_mse"])
        if "PQ2_0_H128" in val:
            return float(val["PQ2_0_H128"]["relative_output_mse"])
        return None
    for key in (fmt, f"published_{fmt}"):
        if key in val and val[key].get("relative_output_mse") is not None:
            return float(val[key]["relative_output_mse"])
    return None


def solve_constrained_allocation(
    sensitivity: dict[str, Any],
    *,
    target_total_gib: float,
    non_expert_bytes: int,
    allow_pq2: bool,
    pq2_mse_ceiling: float = 0.015,
) -> dict[str, Any]:
    """Greedy marginal quality-recovery-per-byte precision allocator for all 48 expert banks.

    Starts from the lowest-footprint admissible format per bank, prioritising:
      - Original NVFP4 retention on down projections & looped core layers (blk.6..17)
      - MXFP4 / IQ4_NL on original MXFP8 layers (blk.20..23)
      - PQ2_0 allowed ONLY when `allow_pq2=True` and measured validation relative MSE <= ceiling.
    """
    budget_bytes = int(target_total_gib * (1024 ** 3)) - non_expert_bytes
    if budget_bytes <= 0:
        raise ValueError(f"Non-expert bytes ({non_expert_bytes}) exceed target {target_total_gib} GiB")

    banks = sensitivity["banks"]
    choices: dict[str, str] = {}
    options: dict[str, list[tuple[str, int, float]]] = {}

    for layer in range(24):
        for proj in ("gate_up", "down"):
            name = f"blk.{layer}.ffn_{proj}_exps.weight"
            entry = banks[name]
            src_prec = entry["source_precision"]
            # Weight looped core layers (6..17, executed 3x/token) and down projections higher.
            visit_mult = 3.0 if 6 <= layer <= 17 else 1.0
            proj_mult = 1.35 if proj == "down" else 1.0
            weight = visit_mult * proj_mult

            cands: list[tuple[str, int, float]] = []
            allowed_fmts = ["IQ2_S", "IQ3_XXS", "IQ3_S", "IQ4_XS", "MXFP4", "IQ4_NL"]
            if src_prec == "NVFP4":
                allowed_fmts.append("NVFP4")
            if allow_pq2 and proj == "gate_up":
                pq_err = _candidate_error(entry, "PQ2_0", src_prec)
                if pq_err is not None and pq_err <= pq2_mse_ceiling:
                    allowed_fmts.insert(0, "PQ2_0")

            for fmt in allowed_fmts:
                err = _candidate_error(entry, fmt, src_prec)
                if err is None:
                    continue
                cands.append((fmt, bank_bytes(proj, fmt), err * weight))

            # Sort ascending by byte size, keeping Pareto-undominated (strictly lower error for larger size)
            cands.sort(key=lambda t: (t[1], t[2]))
            pareto: list[tuple[str, int, float]] = []
            for fmt, nbytes, werr in cands:
                if not pareto or werr < pareto[-1][2] - 1e-12:
                    pareto.append((fmt, nbytes, werr))
                elif fmt == "NVFP4" and src_prec == "NVFP4":
                    # Always preserve lossless NVFP4 as the top tier on native NVFP4 banks
                    pareto.append((fmt, nbytes, min(werr, pareto[-1][2] - 1e-9)))
            options[name] = pareto
            choices[name] = pareto[0][0]

    # Mandatory P2 floor: keep all 20 original NVFP4 down projections at lossless NVFP4 if budget allows
    def current_bytes() -> int:
        total = 0
        for layer in range(24):
            for proj in ("gate_up", "down"):
                nm = f"blk.{layer}.ffn_{proj}_exps.weight"
                total += bank_bytes(proj, choices[nm])
        return total

    for layer in range(20):
        nm = f"blk.{layer}.ffn_down_exps.weight"
        if any(f == "NVFP4" for f, _, _ in options[nm]):
            prev = choices[nm]
            choices[nm] = "NVFP4"
            if current_bytes() > budget_bytes:
                choices[nm] = prev
                break

    # Greedy marginal-gain-per-byte promotions until budget is saturated
    promotions: list[dict[str, Any]] = []
    while True:
        best_gain = -1.0
        best_move: tuple[str, str, int, float] | None = None
        used = current_bytes()
        for nm, pareto in options.items():
            cur_fmt = choices[nm]
            cur_idx = next(i for i, (f, _, _) in enumerate(pareto) if f == cur_fmt)
            cur_b, cur_e = pareto[cur_idx][1], pareto[cur_idx][2]
            for nxt_fmt, nxt_b, nxt_e in pareto[cur_idx + 1 :]:
                delta_b = nxt_b - cur_b
                if delta_b <= 0 or used + delta_b > budget_bytes:
                    continue
                gain = (cur_e - nxt_e) / float(delta_b)
                if gain > best_gain:
                    best_gain = gain
                    best_move = (nm, nxt_fmt, delta_b, cur_e - nxt_e)
        if best_move is None:
            break
        nm, nxt_fmt, delta_b, delta_e = best_move
        old_fmt = choices[nm]
        choices[nm] = nxt_fmt
        promotions.append(
            {
                "tensor": nm,
                "from": old_fmt,
                "to": nxt_fmt,
                "delta_bytes": delta_b,
                "weighted_mse_reduction": round(delta_e, 8),
                "recovery_per_mib": round(delta_e / (delta_b / (1024 ** 2)), 8),
            }
        )

    expert_total = current_bytes()
    total_bytes = non_expert_bytes + expert_total
    counts: dict[str, int] = {}
    for fmt in choices.values():
        counts[fmt] = counts.get(fmt, 0) + 1

    return {
        "target_total_gib": target_total_gib,
        "allow_pq2": allow_pq2,
        "pq2_mse_ceiling": pq2_mse_ceiling if allow_pq2 else None,
        "non_expert_bytes": non_expert_bytes,
        "expert_bytes": expert_total,
        "estimated_total_bytes": total_bytes,
        "estimated_total_gib": round(total_bytes / (1024 ** 3), 4),
        "expert_format_counts": dict(sorted(counts.items())),
        "bank_types": choices,
        "promotion_trace": promotions,
    }


class NativePacker:
    """GGML native quantiser wrapper (MXFP4, IQ2_S, IQ3_XXS, IQ3_S, IQ4_XS, IQ4_NL, Q4_K, Q6_K, Q8_0)."""

    def __init__(self, library: Path, gguf_mod: Any) -> None:
        self._dll_dir = os.add_dll_directory(str(library.parent)) if os.name == "nt" else None
        self.lib = ct.CDLL(str(library))
        self.pack = self.lib.ggml_quantize_chunk
        self.pack.argtypes = [ct.c_int, ct.c_void_p, ct.c_void_p, ct.c_int64, ct.c_int64, ct.c_int64, ct.c_void_p]
        self.pack.restype = ct.c_size_t
        self.gguf = gguf_mod

    def encode(self, w: torch.Tensor, fmt: str, importance: np.ndarray | None = None) -> bytes:
        if fmt in ("F32", "BF16", "F16"):
            dt = {"F32": torch.float32, "BF16": torch.bfloat16, "F16": torch.float16}[fmt]
            return w.to(dt).contiguous().view(torch.uint8).numpy().tobytes()
        typ = self.gguf.GGMLQuantizationType[fmt]
        grp, nb = self.gguf.GGML_QUANT_SIZES[typ]
        arr = np.ascontiguousarray(w.float().numpy(), dtype=np.float32)
        rows = math.prod(arr.shape[:-1])
        cols = arr.shape[-1]
        expected = (arr.size // grp) * nb
        out = np.empty(expected, dtype=np.uint8)
        imp_ptr = None
        imp_arr: np.ndarray | None = None
        if importance is not None:
            imp_arr = np.ascontiguousarray(importance, dtype=np.float32)
            imp_ptr = imp_arr.ctypes.data
        written = self.pack(int(typ), arr.ctypes.data, out.ctypes.data, 0, rows, cols, imp_ptr)
        if written != expected:
            raise ArithmeticError(f"Unexpected GGML packed size for {fmt}: got {written}, expected {expected}")
        return out.tobytes()


def cmd_allocate(args: argparse.Namespace) -> int:
    sens = json.loads(args.sensitivity.read_text(encoding="utf-8"))
    cp = Checkpoint(args.source)
    g, klass = upstream(args.llama)
    model = klass(cp.path, g.LlamaFileType.MOSTLY_Q4_K_M, args.out.with_suffix(".tmp.gguf"), model_name="Inkling-2-Mini-Phase13")

    non_expert_bytes = 0
    non_expert_map: dict[str, str] = {}
    for raw, name, shape, _, layer in mapped(model, cp, meta=True):
        if raw.endswith((".w13_weight", ".w2_weight")):
            continue
        fmt = non_expert_type(g, model, name, raw, shape, layer, cp.header[raw]["dtype"])
        typ = g.GGMLQuantizationType[fmt]
        grp, nb = g.GGML_QUANT_SIZES[typ]
        nbytes = (math.prod(shape) // grp) * nb
        non_expert_bytes += nbytes
        non_expert_map[name] = fmt

    hybrid = solve_constrained_allocation(
        sens,
        target_total_gib=args.target_gib,
        non_expert_bytes=non_expert_bytes,
        allow_pq2=False,
    )
    spin8_hybrid = solve_constrained_allocation(
        sens,
        target_total_gib=args.target_gib,
        non_expert_bytes=non_expert_bytes,
        allow_pq2=True,
        pq2_mse_ceiling=args.pq2_ceiling,
    )
    recipe = {
        "schema": "strata-phase13-recipe-v1",
        "source_repository": cp.repo,
        "source_revision": cp.revision,
        "target_resident_gib": args.target_gib,
        "non_expert_bytes": non_expert_bytes,
        "non_expert_types": non_expert_map,
        "variants": {
            "Inkling-2-Mini-Agentic-128K-Hybrid.gguf": hybrid,
            "Inkling-2-Mini-Agentic-128K-Spin8-Hybrid.gguf": spin8_hybrid,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    atomic_bytes(args.out, (json.dumps(recipe, indent=2) + "\n").encode("utf-8"))
    LOGGER.info(
        "Wrote quantisation recipe to %s | Hybrid=%.3f GiB %s | Spin8-Hybrid=%.3f GiB %s",
        args.out,
        hybrid["estimated_total_gib"],
        hybrid["expert_format_counts"],
        spin8_hybrid["estimated_total_gib"],
        spin8_hybrid["expert_format_counts"],
    )
    return 0


def _load_importance_map(moments_dir: Path | None) -> dict[tuple[int, str, int], np.ndarray]:
    """Load optional per-expert calibration activation-squared importance vectors."""
    out: dict[tuple[int, str, int], np.ndarray] = {}
    if moments_dir is None or not moments_dir.is_dir():
        return out
    for npz_path in sorted(moments_dir.glob("calibration-*.npz")):
        # Traces are loaded on demand per layer during build; placeholder for precomputed moments
        _ = npz_path
    return out


def cmd_build(args: argparse.Namespace) -> int:
    recipe = json.loads(args.recipe.read_text(encoding="utf-8"))
    variant_name = args.output.name
    if variant_name not in recipe["variants"]:
        raise KeyError(f"Variant {variant_name} not found in recipe {list(recipe['variants'].keys())}")
    variant = recipe["variants"][variant_name]
    bank_types: dict[str, str] = variant["bank_types"]
    non_expert_types: dict[str, str] = recipe["non_expert_types"]

    cp = Checkpoint(args.source)
    g, klass = upstream(args.llama)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    header_path = args.output.with_suffix(".gguf.header")
    model = klass(cp.path, g.LlamaFileType.MOSTLY_Q4_K_M, args.output, model_name=variant_name.removesuffix(".gguf"))

    entries: list[dict[str, Any]] = []
    nvfp4_scales: list[tuple[str, str, int]] = []  # (scale_tensor_name, raw_weight_key, layer)
    pq2_names: list[str] = []

    for raw, name, shape, _, layer in mapped(model, cp, meta=True):
        if raw.endswith((".w13_weight", ".w2_weight")):
            fmt = bank_types[name]
            if fmt == "PQ2_0":
                pq2_names.append(name)
            typ = g.GGMLQuantizationType[fmt]
            grp, nb = g.GGML_QUANT_SIZES[typ]
            entries.append(dict(raw=raw, name=name, shape=shape, type=fmt, bytes=(math.prod(shape) // grp) * nb, is_expert=True, layer=layer))
            if fmt == "NVFP4":
                scale_name = name.removesuffix("weight") + "scale"
                entries.append(dict(raw=raw, name=scale_name, shape=[128], type="F32", bytes=128 * 4, is_scale=True, layer=layer))
                nvfp4_scales.append((scale_name, raw, layer))
        else:
            fmt = non_expert_types[name]
            typ = g.GGMLQuantizationType[fmt]
            grp, nb = g.GGML_QUANT_SIZES[typ]
            entries.append(dict(raw=raw, name=name, shape=shape, type=fmt, bytes=(math.prod(shape) // grp) * nb, is_expert=False, layer=layer))

    # Write GGUF header
    w = model.gguf_writer
    for d in entries:
        w.add_tensor_info(d["name"], d["shape"], np.dtype("float32"), d["bytes"], raw_dtype=g.GGMLQuantizationType[d["type"]])
    model.prepare_metadata(vocab_only=False)
    w.add_string("inkling_quant.source", cp.repo)
    w.add_string("inkling_quant.revision", cp.revision)
    w.add_string("inkling_quant.profile", variant_name.removesuffix(".gguf"))
    if pq2_names:
        w.add_uint32("prism.hadamard.version", 1)
        w.add_uint32("prism.hadamard.block_size", 128)
        w.add_string("prism.hadamard.transform", "normalized-sylvester-walsh-hadamard")
        w.add_string("prism.hadamard.axis", "input-last-dimension")
        w.add_string("prism.hadamard.sign_mode", "identity")
        w.add_array("prism.hadamard.weight_names", pq2_names)
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
    LOGGER.info("Prepared header for %s: %d tensors, %d bytes (%.3f GiB)", variant_name, len(entries), total_size, total_size / (1024 ** 3))
    if args.layout_only:
        return 0

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
        raise ValueError("Existing journal header mismatch")
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

    packer = NativePacker(args.ggml_base.resolve(strict=True), g)
    orig = Original(args.source)
    pq2_reuse_map: dict[str, Any] = {}
    pq2_fh = None
    if pq2_names and args.pq2_source and args.pq2_source.is_file():
        _, pq_entries = directory(args.pq2_source, g.GGML_QUANT_SIZES)
        pq2_reuse_map = {t.name: t for t in pq_entries}
        pq2_fh = args.pq2_source.open("rb")

    # Build a quick lookup for calibration activation importance per (layer, proj, expert)
    from phase3_study import Traces  # noqa: E402

    cal_paths = sorted(args.cal_dir.glob("calibration-*.npz")) if args.cal_dir and args.cal_dir.is_dir() else []

    index = {d["name"]: d for d in entries}
    t_last_ckpt = time.monotonic()

    try:
        with partial.open("r+b") as f:
            def write_chunk(d: dict[str, Any], part: int, offset_in_tensor: int, payload: bytes) -> None:
                nonlocal t_last_ckpt
                if db.execute("select 1 from done where name=? and part=?", (d["name"], part)).fetchone():
                    return
                pos_w = d["offset"] + offset_in_tensor
                end_w = f.seek(0, os.SEEK_END)
                if pos_w > end_w:
                    f.write(bytes(pos_w - end_w))
                else:
                    f.seek(pos_w)
                f.write(payload)
                db.execute(
                    "insert into done values(?,?,?,?)",
                    (d["name"], part, len(payload), hashlib.sha256(payload).hexdigest()),
                )
                if time.monotonic() - t_last_ckpt >= 30.0:
                    f.flush()
                    os.fsync(f.fileno())
                    db.commit()
                    t_last_ckpt = time.monotonic()

            # 1. Write non-expert tensors + NVFP4 scales + expert banks in canonical header order
            layer_traces_cache: dict[int, Any] = {}
            for raw, name, shape, value, layer in tqdm(list(mapped(model, cp, meta=False)), desc=variant_name, unit="tensor"):
                d = index[name]
                if not d.get("is_expert"):
                    done_b = db.execute("select coalesce(sum(n),0) from done where name=?", (name,)).fetchone()[0]
                    if done_b < d["bytes"]:
                        payload = packer.encode(value, d["type"])
                        write_chunk(d, 0, 0, payload)
                        f.flush()
                        db.commit()
                    continue

                fmt = d["type"]
                # Write NVFP4 scale tensor right after weight tensor if present
                scale_name = name.removesuffix("weight") + "scale"
                if fmt == "NVFP4":
                    done_b = db.execute("select coalesce(sum(n),0) from done where name=?", (name,)).fetchone()[0]
                    if done_b < d["bytes"]:
                        expert_stride = d["bytes"] // 128
                        for e in range(128):
                            if db.execute("select 1 from done where name=? and part=?", (name, e)).fetchone():
                                continue
                            parts = orig.parts(raw, e)
                            packed = pack_nv(parts)
                            if ".w13_" in raw:
                                # De-interleave even=gate, odd=up to match GGUF ffn_gate_up_exps layout
                                packed = np.concatenate((packed[::2], packed[1::2]), axis=0)
                            write_chunk(d, e, e * expert_stride, packed.tobytes())
                        f.flush()
                        db.commit()
                    sd = index[scale_name]
                    if db.execute("select coalesce(sum(n),0) from done where name=?", (scale_name,)).fetchone()[0] < sd["bytes"]:
                        outer = (orig.read(raw + "_amax") / orig.read(raw + "_outer_scale_denominator")[0]).astype("<f4")
                        write_chunk(sd, 0, 0, outer.tobytes())
                        f.flush()
                        db.commit()
                elif fmt == "PQ2_0":
                    if pq2_fh is None or name not in pq2_reuse_map:
                        raise FileNotFoundError(f"Missing verified PQ2_0 source bank for {name}")
                    done_b = db.execute("select coalesce(sum(n),0) from done where name=?", (name,)).fetchone()[0]
                    if done_b < d["bytes"]:
                        src_t = pq2_reuse_map[name]
                        if src_t.n_bytes != d["bytes"]:
                            raise ValueError(f"PQ2_0 byte mismatch for {name}: {src_t.n_bytes} vs {d['bytes']}")
                        expert_stride = d["bytes"] // 128
                        for e in range(128):
                            if db.execute("select 1 from done where name=? and part=?", (name, e)).fetchone():
                                continue
                            pq2_fh.seek(src_t.data_offset + e * expert_stride)
                            chunk = pq2_fh.read(expert_stride)
                            if len(chunk) != expert_stride:
                                raise EOFError(f"Short read on PQ2_0 source for {name}[{e}]")
                            write_chunk(d, e, e * expert_stride, chunk)
                        f.flush()
                        db.commit()
                else:
                    # Quantise expert-by-expert using native GGML quantiser with calibration importance
                    done_b = db.execute("select coalesce(sum(n),0) from done where name=?", (name,)).fetchone()[0]
                    if done_b < d["bytes"]:
                        tr = None
                        if cal_paths and layer is not None:
                            if layer not in layer_traces_cache:
                                for old_l in list(layer_traces_cache.keys()):
                                    layer_traces_cache.pop(old_l).close()
                                layer_traces_cache[layer] = Traces(cal_paths, layer)
                            tr = layer_traces_cache[layer]
                        proj_key = "w13" if ".w13_" in raw else "w2"
                        expert_stride = d["bytes"] // 128
                        for e in range(128):
                            if db.execute("select 1 from done where name=? and part=?", (name, e)).fetchone():
                                continue
                            w_exp = torch.from_numpy(reconstruct(orig.parts(raw, e)))
                            if ".w13_" in raw:
                                w_exp = torch.cat((w_exp[::2], w_exp[1::2]), dim=0)
                            imp = None
                            if tr is not None:
                                fit = tr.expert(e, proj_key)
                                if fit:
                                    x_mat = np.concatenate([z for _, _, z in fit])
                                    imp = np.maximum(np.mean(np.square(x_mat, dtype=np.float64), axis=0), 1e-8).astype(np.float32)
                            payload = packer.encode(w_exp, fmt, importance=imp)
                            if len(payload) != expert_stride:
                                raise ArithmeticError(f"{name}[{e}] {fmt}: {len(payload)} != {expert_stride}")
                            write_chunk(d, e, e * expert_stride, payload)
                        f.flush()
                        db.commit()

            for tr in layer_traces_cache.values():
                tr.close()

            end_pos = f.seek(0, os.SEEK_END)
            if not 0 <= total_size - end_pos < 32:
                raise IOError(f"Invalid final GGUF extent: end={end_pos}, expected={total_size}")
            if total_size > end_pos:
                f.write(bytes(total_size - end_pos))
            f.flush()
            os.fsync(f.fileno())
            db.commit()
    finally:
        if pq2_fh is not None:
            pq2_fh.close()
        db.close()

    partial.rename(args.output)
    sha = hashlib.sha256()
    with args.output.open("rb") as fh:
        for block in iter(lambda: fh.read(16 * 1024 * 1024), b""):
            sha.update(block)
    manifest = {
        "file": str(args.output),
        "bytes": args.output.stat().st_size,
        "gib": round(args.output.stat().st_size / (1024 ** 3), 4),
        "sha256": sha.hexdigest(),
        "variant": variant,
    }
    atomic_bytes(args.output.with_suffix(".manifest.json"), (json.dumps(manifest, indent=2) + "\n").encode("utf-8"))
    LOGGER.info("Built %s (%.3f GiB, sha256=%s)", args.output.name, manifest["gib"], manifest["sha256"][:16])
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_alloc = sub.add_parser("allocate", help="Solve constrained 11.0-11.3 GiB precision allocation")
    p_alloc.add_argument("--sensitivity", type=Path, required=True)
    p_alloc.add_argument("--source", type=Path, required=True)
    p_alloc.add_argument("--llama", type=Path, required=True)
    p_alloc.add_argument("--target-gib", type=float, default=11.2)
    p_alloc.add_argument("--pq2-ceiling", type=float, default=0.015)
    p_alloc.add_argument("--out", type=Path, required=True)

    p_build = sub.add_parser("build", help="Build a hybrid GGUF from quantisation_recipe.json")
    p_build.add_argument("--recipe", type=Path, required=True)
    p_build.add_argument("--source", type=Path, required=True)
    p_build.add_argument("--llama", type=Path, required=True)
    p_build.add_argument("--ggml-base", type=Path, required=True)
    p_build.add_argument("--output", type=Path, required=True)
    p_build.add_argument("--pq2-source", type=Path, default=None)
    p_build.add_argument("--cal-dir", type=Path, default=None)
    p_build.add_argument("--layout-only", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    args = build_parser().parse_args(argv)
    with torch.inference_mode():
        if args.cmd == "allocate":
            return cmd_allocate(args)
        if args.cmd == "build":
            return cmd_build(args)
    raise ValueError(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
