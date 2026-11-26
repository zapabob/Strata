"""Paired PQ2_0 vs Q6_K LM-head (`output.weight`) ablation on identical hidden states.

Measures exact KL divergence, NLL delta, Top-1 agreement, and marginal quality
recovery per additional MiB between:
  - Pre-quantisation Heretic BF16 `output.weight` (reference)
  - `Q6_K` `output.weight` (210 B / 256 elems)
  - `PQ2_0` `output.weight` (34 B / 128 elems, H128 folded)

Uses logging, strict typing, UTF-8, and zero print()/eval()/exec().
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any
import urllib.request

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from heretic_hybrid_upgrade import GgmlCodec, H128_NORM, encode_pq2_0_matrix  # noqa: E402
from phase13_acceptance_eval import launch_llama_server, stop_server, wait_health  # noqa: E402
from quantize_inkling2_pq2 import Checkpoint, upstream  # noqa: E402

LOGGER = logging.getLogger("phase13.lm_head_ablation")


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _log_softmax(logits: np.ndarray) -> np.ndarray:
    m = np.max(logits, axis=-1, keepdims=True)
    shifted = logits - m
    return shifted - np.log(np.sum(np.exp(shifted), axis=-1, keepdims=True))


def compare_heads(
    source_dir: Path,
    llama_dir: Path,
    ggml_base: Path,
    hidden_states: np.ndarray,
    *,
    vocab_chunk: int = 8192,
) -> dict[str, Any]:
    """Evaluate exact logits of BF16 ref, Q6_K, and PQ2_0 output heads on identical hidden states [N, D]."""
    cp = Checkpoint(source_dir)
    g, _ = upstream(llama_dir)
    codec = GgmlCodec(ggml_base.resolve(strict=True), g)

    # Locate lm_head raw key in Heretic BF16 safetensors
    lm_key = next(
        k for k in cp.header
        if k.endswith("lm_head.weight") or k.endswith("output.weight") or k.endswith("unembed.weight")
    )
    w_full = cp.raw(lm_key)  # [V, D] memmap-backed BF16 tensor
    vocab, hidden = int(w_full.shape[0]), int(w_full.shape[1])
    h = np.ascontiguousarray(hidden_states, dtype=np.float32)
    if h.ndim != 2 or h.shape[1] != hidden:
        raise ValueError(f"Expected hidden states [N, {hidden}], got {h.shape}")
    n_tok = int(h.shape[0])

    logits_ref = np.empty((n_tok, vocab), dtype=np.float32)
    logits_q6 = np.empty((n_tok, vocab), dtype=np.float32)
    logits_pq2 = np.empty((n_tok, vocab), dtype=np.float32)

    for start in range(0, vocab, vocab_chunk):
        end = min(vocab, start + vocab_chunk)
        w_blk = w_full[start:end].float().numpy()

        # Reference BF16
        logits_ref[:, start:end] = h @ w_blk.T

        # Q6_K decoded
        q6_raw = codec.encode_np(w_blk, "Q6_K")
        w_q6 = codec.dequant_np(q6_raw, "Q6_K", w_blk.shape)
        logits_q6[:, start:end] = h @ w_q6.T

        # PQ2_0 (H128 folded) decoded (codec.dequant_np already applies inverse H128_NORM)
        pq2_raw = encode_pq2_0_matrix(w_blk)
        w_pq2 = codec.dequant_np(pq2_raw, "PQ2_0", w_blk.shape)
        logits_pq2[:, start:end] = h @ w_pq2.T

    lp_ref = _log_softmax(logits_ref.astype(np.float64))
    p_ref = np.exp(lp_ref)
    top1_ref = np.argmax(logits_ref, axis=-1)

    def _metrics(cand_logits: np.ndarray) -> dict[str, float]:
        lp_c = _log_softmax(cand_logits.astype(np.float64))
        kl = float(np.mean(np.sum(p_ref * (lp_ref - lp_c), axis=-1)))
        top1 = float(np.mean(np.argmax(cand_logits, axis=-1) == top1_ref))
        max_abs = float(np.max(np.abs(cand_logits - logits_ref)))
        return {"mean_forward_kl_nats": round(kl, 6), "top1_agreement": round(top1, 6), "max_abs_logit_diff": round(max_abs, 4)}

    m_q6 = _metrics(logits_q6)
    m_pq2 = _metrics(logits_pq2)
    q6_bytes = (vocab * hidden // 256) * 210
    pq2_bytes = (vocab * hidden // 128) * 34
    delta_mib = (q6_bytes - pq2_bytes) / (1024.0 ** 2)
    kl_gain = m_pq2["mean_forward_kl_nats"] - m_q6["mean_forward_kl_nats"]

    return {
        "schema": "phase13-lm-head-ablation-v1",
        "lm_head_key": lm_key,
        "vocab": vocab,
        "hidden": hidden,
        "num_positions": n_tok,
        "q6_k_bytes": q6_bytes,
        "pq2_0_bytes": pq2_bytes,
        "delta_mib_q6k_minus_pq2": round(delta_mib, 2),
        "q6_k": m_q6,
        "pq2_0": m_pq2,
        "kl_recovery_nats_q6k_over_pq2": round(kl_gain, 6),
        "kl_recovery_nats_per_mib": round(kl_gain / max(delta_mib, 1e-9), 8),
        "top1_recovery_pct_points": round((m_q6["top1_agreement"] - m_pq2["top1_agreement"]) * 100.0, 3),
    }


def extract_hybrid_hidden_states(
    server_exe: Path,
    model_path: Path,
    texts: list[str],
    out_npy: Path,
    *,
    port: int = 8096,
    ngl: int = 0,
    ot_rules: list[str] | None = None,
) -> np.ndarray:
    """Extract raw unnormalised post-norm hidden states [N, D] from the hybrid GGUF via llama-server --embeddings --pooling none."""
    import subprocess

    log_path = out_npy.parent / "lm_head_hidden_server.log"
    cmd = [
        str(server_exe),
        "-m", str(model_path),
        "-ngl", str(ngl),
        "-fit", "off",
        "-fa", "on",
        "-c", "4096",
        "-ub", "256",
        "-b", "256",
        "-np", "1",
        "-t", "6",
        "--embeddings",
        "--pooling", "none",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]
    for ot in (ot_rules or []):
        cmd.extend(["-ot", ot])
    base_url = f"http://127.0.0.1:{port}"
    log_fh = log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT, text=True)
    rows: list[np.ndarray] = []
    try:
        wait_health(base_url, proc, timeout_s=360.0)
        for text in texts:
            req = urllib.request.Request(
                f"{base_url}/embedding",
                data=json.dumps({"content": text, "embd_normalize": -1}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120.0) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            # llama-server /embedding with --pooling none returns [{"index":0,"embedding":[[...], ...]}]
            if isinstance(body, list) and body:
                emb = body[0].get("embedding", [])
            elif isinstance(body, dict):
                emb = body.get("embedding", [])
            else:
                emb = []
            arr = np.asarray(emb, dtype=np.float32)
            if arr.ndim == 1:
                arr = arr[None, :]
            if arr.ndim == 2 and arr.shape[0] > 0:
                rows.append(arr)
    finally:
        stop_server(proc, log_fh)
    if not rows:
        raise RuntimeError("No hidden states returned from llama-server /embedding")
    hidden = np.concatenate(rows, axis=0)
    out_npy.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_npy, hidden)
    LOGGER.info("Extracted %d hybrid hidden-state positions (shape=%s, mean_norm=%.3f) -> %s", hidden.shape[0], hidden.shape, float(np.mean(np.linalg.norm(hidden, axis=-1))), out_npy)
    return hidden


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--llama", type=Path, required=True)
    p.add_argument("--ggml-base", type=Path, required=True)
    p.add_argument("--hidden-npy", type=Path, required=True, help="Saved hybrid hidden states [N, 2304] float32 .npy")
    p.add_argument("--server", type=Path, default=None, help="If set and --hidden-npy does not exist, extract from --model via llama-server")
    p.add_argument("--model", type=Path, default=None)
    p.add_argument("--core-texts", type=Path, default=None, help="Optional core-texts.json whose holdout prompts are used for hidden extraction")
    p.add_argument("--ngl", type=int, default=0, help="GPU layers for hidden-state extraction")
    p.add_argument("--ot", action="append", default=[], help="Extra -ot offload rules")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)

    if args.hidden_npy.is_file():
        hidden = np.load(args.hidden_npy)
    elif args.server and args.model:
        texts = [
            "Seven boats carry two lanterns apiece. The total number of lanterns is fourteen. 夕方の駅で友人を待ちました。",
            "def normalise_path(p: str) -> str:\n    parts = []\n    for seg in p.split('/'):\n",
            "{\"name\":\"search_files\",\"arguments\":{\"path\":\"src/main.rs\",\"pattern\":\"nvfp4\"}}",
            "山道に沿って白い花が咲いています。朝の雨が上がり、遠くの峰が見えました。",
        ]
        if args.core_texts and args.core_texts.is_file():
            ct = json.loads(args.core_texts.read_text(encoding="utf-8"))
            if isinstance(ct, dict) and ct.get("holdout"):
                texts = list(ct["holdout"]) + texts[1:3]
        hidden = extract_hybrid_hidden_states(args.server, args.model, texts, args.hidden_npy, ngl=args.ngl, ot_rules=args.ot)
    else:
        raise FileNotFoundError(f"Missing {args.hidden_npy} and --server/--model not provided")
    res = compare_heads(args.source, args.llama, args.ggml_base, hidden)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    LOGGER.info(
        "LM-head ablation complete: PQ2_0 KL=%.5f (top1=%.2f%%) vs Q6_K KL=%.5f (top1=%.2f%%) | delta=+%.1f MiB (%.6f nats/MiB)",
        res["pq2_0"]["mean_forward_kl_nats"],
        res["pq2_0"]["top1_agreement"] * 100.0,
        res["q6_k"]["mean_forward_kl_nats"],
        res["q6_k"]["top1_agreement"] * 100.0,
        res["delta_mib_q6k_minus_pq2"],
        res["kl_recovery_nats_per_mib"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
