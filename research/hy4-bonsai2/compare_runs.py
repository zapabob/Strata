"""Compare visual embeddings or next-token distributions on identical Hy4 inputs."""

import argparse
import json
from pathlib import Path

import numpy as np


def normalise_logits(logits):
    centred = logits - logits.max(axis=-1, keepdims=True)
    return centred - np.log(np.exp(centred).sum(axis=-1, keepdims=True))


def measure_speed(receipt):
    times = receipt.get("step_seconds", [])
    if not times:
        return None
    return {
        "prompt_tokens": len(receipt["input_ids"]),
        "time_to_first_token_seconds": times[0],
        "decode_steps": len(times) - 1,
        "mean_decode_seconds_per_token": float(np.mean(times[1:]))
        if len(times) > 1
        else None,
        "decode_tokens_per_second": (len(times) - 1) / sum(times[1:])
        if len(times) > 1
        else None,
    }


def compare(ref_dir, test_dir):
    ref, test = (json.loads((p / "run.json").read_bytes()) for p in (ref_dir, test_dir))
    for key in ("prompt", "image"):
        if ref[key] != test[key]:
            raise ValueError(f"Different inputs for {key}")
    local = [r["reads"].get("remote_bytes", 0) == 0 for r in (ref, test)]
    result = dict(
        reference=str(ref_dir.resolve()),
        candidate=str(test_dir.resolve()),
        prompt=ref["prompt"],
        image=ref["image"],
        all_weight_reads_local=all(local),
    )
    vision = "vision_shape" in ref and "vision_shape" in test
    array_name = "vision.npy" if vision else "logits.npy"
    a, b = (
        np.load(p / array_name, allow_pickle=False).astype(np.float64)
        for p in (ref_dir, test_dir)
    )
    if a.shape != b.shape or not all(np.isfinite(v).all() for v in (a, b)):
        raise ValueError("Different shapes or non-finite values")
    if vision:
        norms = np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1)
        if np.any(norms == 0):
            raise ValueError("Cosine similarity is undefined for a zero embedding")
        return {
            **result,
            "feature_shape": list(a.shape),
            "relative_l2": float(np.linalg.norm(a - b) / np.linalg.norm(a)),
            "cosine_per_image_token": (np.sum(a * b, axis=-1) / norms).tolist(),
        }
    if ref["input_ids"] != test["input_ids"]:
        raise ValueError("Different initial token sequences")
    if len(a) != len(ref["trajectory_ids"]) or len(b) != len(test["trajectory_ids"]):
        raise ValueError("Trajectory and logits lengths disagree")
    aligned = 1
    for ref_id, test_id in zip(
        ref["trajectory_ids"][:-1], test["trajectory_ids"][:-1], strict=True
    ):
        if ref_id != test_id:
            break
        aligned += 1
    a, b = a[:aligned], b[:aligned]
    p, q = normalise_logits(a), normalise_logits(b)
    teacher = a.argmax(axis=-1)
    positions = np.arange(aligned)
    kl = np.maximum(0, (np.exp(p) * (p - q)).sum(axis=-1))
    top = min(5, a.shape[1])
    ta, tb = (np.argpartition(v, -top, axis=-1)[:, -top:] for v in (a, b))
    overlap = [len(set(x).intersection(y)) / top for x, y in zip(ta, tb, strict=True)]
    result.update(
        reference_text=ref["text"],
        candidate_text=test["text"],
        reference_token_ids=ref["generated_ids"],
        candidate_token_ids=test["generated_ids"],
        candidate_teacher_forced=test["teacher_forced"],
        matched_prefix_positions=aligned,
        total_positions=len(test["trajectory_ids"]),
        vocabulary_size=a.shape[-1],
        mean_forward_kl_nats=float(kl.mean()),
        forward_kl_nats=kl.tolist(),
        mean_top1_agreement=float(np.mean(teacher == b.argmax(axis=-1))),
        mean_top5_overlap=float(np.mean(overlap)),
        mean_extra_nll_on_reference_argmax_nats=float(
            (p[positions, teacher] - q[positions, teacher]).mean()
        ),
        reference_speed=measure_speed(ref),
        candidate_speed=measure_speed(test),
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("reference", "candidate", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    metrics = compare(args.reference, args.candidate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(metrics, ensure_ascii=False, indent=2, allow_nan=False)
    args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
