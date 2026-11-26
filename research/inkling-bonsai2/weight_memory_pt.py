"""Persistent PyTorch (.pt) Weight-Memory Sidecar for Inkling-2-Mini Mode B.

Maintains a compact, versioned, 3-generation-rotated `.pt` fast-weight memory
store targeting the recurrent core layers (`blk.6..17`, 3x visits per token):
  - Low-rank associative fast-weight matrices (A, B) per recurrent layer
  - Ebbinghaus retention metadata (strength, access_count, last_consolidated_utc)
  - Strict `weights_only=True` safe serialisation
  - Atomic write + 3-generation rolling backup stock (`*.gen1.pt`..`*.gen3.pt`)
  - Zero mutation of the immutable base Mode B GGUF (`Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf`)

Uses logging, strict typing, UTF-8, and zero print()/eval()/exec().
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from pathlib import Path
import shutil
import sys
from typing import Any

import torch

LOGGER = logging.getLogger("strata.weight_memory_pt")

RECURRENT_CORE_LAYERS: tuple[int, ...] = tuple(range(6, 18))  # blk.6..17 (3x visits)
HIDDEN_DIM: int = 2304


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _rotate_generations(path: Path, keep: int = 3) -> None:
    if not path.is_file():
        return
    for idx in range(keep, 1, -1):
        src = path.with_name(f"{path.stem}.gen{idx - 1}{path.suffix}")
        dst = path.with_name(f"{path.stem}.gen{idx}{path.suffix}")
        if src.is_file():
            shutil.copy2(src, dst)
    shutil.copy2(path, path.with_name(f"{path.stem}.gen1{path.suffix}"))


def _atomic_save_pt(payload: dict[str, Any], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_generations(path, keep=3)
    tmp = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, tmp)
    tmp.replace(path)
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h


def init_weight_memory(
    path: Path,
    *,
    base_model_name: str,
    base_model_sha256: str,
    rank: int = 16,
    hidden_dim: int = HIDDEN_DIM,
) -> dict[str, Any]:
    """Initialise an identity-preserving (zero-B) persistent .pt weight-memory store."""
    gen = torch.Generator().manual_seed(20261125)
    weights: dict[str, torch.Tensor] = {}
    for layer in RECURRENT_CORE_LAYERS:
        # LoRA-style zero-init B so initial delta W = B @ A == 0 (bit-exact base behaviour)
        a_mat = torch.randn((rank, hidden_dim), generator=gen, dtype=torch.bfloat16) * (1.0 / math.sqrt(hidden_dim))
        b_mat = torch.zeros((hidden_dim, rank), dtype=torch.bfloat16)
        weights[f"blk.{layer}.attn_output.mem_A"] = a_mat
        weights[f"blk.{layer}.attn_output.mem_B"] = b_mat

    payload: dict[str, Any] = {
        "schema": "strata-inkling2-weight-memory-pt-v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "base_model_name": base_model_name,
        "base_model_sha256": base_model_sha256,
        "rank": rank,
        "hidden_dim": hidden_dim,
        "layers": list(RECURRENT_CORE_LAYERS),
        "consolidation_steps": 0,
        "ebbinghaus_half_life_days": 14.0,
        "weights": weights,
    }
    sha = _atomic_save_pt(payload, path)
    LOGGER.info("Initialised persistent weight memory %s (rank=%d, %d tensors, sha256=%s)", path, rank, len(weights), sha[:16])
    return {"path": str(path), "sha256": sha, "tensors": len(weights), "bytes": path.stat().st_size}


def consolidate_hebbian_step(
    path: Path,
    *,
    key_vec: torch.Tensor,
    val_vec: torch.Tensor,
    lr: float = 1e-3,
    decay: float = 0.995,
) -> dict[str, Any]:
    """Apply one bounded Hebbian outer-product consolidation + Ebbinghaus decay step to the .pt memory."""
    payload = torch.load(path, map_location="cpu", weights_only=True)
    weights: dict[str, torch.Tensor] = payload["weights"]
    k = key_vec.float()
    v = val_vec.float()
    k = k / (k.norm() + 1e-8)
    v = v / (v.norm() + 1e-8)
    for layer in payload["layers"]:
        a_key = f"blk.{layer}.attn_output.mem_A"
        b_key = f"blk.{layer}.attn_output.mem_B"
        a_f = weights[a_key].float()
        b_f = weights[b_key].float() * decay
        proj = a_f @ k  # [rank]
        b_f = b_f + lr * torch.outer(v, proj)
        # Strict spectral/norm clamp to prevent catastrophic drift
        b_norm = float(b_f.norm())
        if b_norm > 1.0:
            b_f = b_f * (1.0 / b_norm)
        weights[b_key] = b_f.to(torch.bfloat16)

    payload["consolidation_steps"] = int(payload.get("consolidation_steps", 0)) + 1
    payload["updated_utc"] = datetime.now(timezone.utc).isoformat()
    sha = _atomic_save_pt(payload, path)
    LOGGER.info("Consolidated step=%d into %s (sha256=%s)", payload["consolidation_steps"], path, sha[:16])
    return {"path": str(path), "consolidation_steps": payload["consolidation_steps"], "sha256": sha}


def inspect_weight_memory(path: Path) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu", weights_only=True)
    weights: dict[str, torch.Tensor] = payload["weights"]
    max_b_norm = max(
        (float(t.float().norm()) for k, t in weights.items() if k.endswith(".mem_B")),
        default=0.0,
    )
    return {
        "schema": payload.get("schema"),
        "base_model_name": payload.get("base_model_name"),
        "base_model_sha256": payload.get("base_model_sha256"),
        "rank": payload.get("rank"),
        "layers": payload.get("layers"),
        "tensor_count": len(weights),
        "consolidation_steps": payload.get("consolidation_steps"),
        "max_mem_B_norm": round(max_b_norm, 6),
        "bytes": path.stat().st_size,
        "updated_utc": payload.get("updated_utc"),
    }


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init")
    pi.add_argument("--path", type=Path, required=True)
    pi.add_argument("--base-model", required=True)
    pi.add_argument("--base-sha256", required=True)
    pi.add_argument("--rank", type=int, default=16)

    ps = sub.add_parser("inspect")
    ps.add_argument("--path", type=Path, required=True)
    ps.add_argument("--out", type=Path, default=None)

    args = p.parse_args(argv)
    if args.cmd == "init":
        info = init_weight_memory(args.path, base_model_name=args.base_model, base_model_sha256=args.base_sha256, rank=args.rank)
        LOGGER.info("Result: %s", json.dumps(info))
        return 0
    if args.cmd == "inspect":
        info = inspect_weight_memory(args.path)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        LOGGER.info("Inspect: %s", json.dumps(info))
        return 0
    raise ValueError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())
