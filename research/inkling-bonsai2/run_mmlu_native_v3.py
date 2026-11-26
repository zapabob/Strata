"""Measure MMLU with the pinned next-token-letter logits protocol used by the upstream model card."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

DEFAULT_MODEL = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf")
DEFAULT_BIN = Path(r"H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\inkling-logits.exe")
DEFAULT_SELECTION = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\mmlu-sm120\selection.json")
DEFAULT_OUT = Path(r"H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3\mmlu_native_v3.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--bin", type=Path, default=DEFAULT_BIN)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--gpu-layers", type=int, default=24)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args(argv)

    spec = json.loads(args.selection.read_text(encoding="utf-8"))
    label_ids = spec["label_token_ids"]
    items = spec["items"][: args.limit]
    folder = args.out.parent / "native"
    folder.mkdir(parents=True, exist_ok=True)
    pairs: list[tuple[Path, Path, dict[str, Any]]] = []
    for item in items:
        stem = f"row{int(item['row'])}"
        inp = folder / f"{stem}.i32"
        out = folder / f"{stem}.f32"
        np.asarray(item["tokens"], dtype="<i4").tofile(inp)
        pairs.append((inp, out, item))

    cmd = [str(args.bin), "--last", "--gpu-layers", str(args.gpu_layers), str(args.model)]
    for inp, out, _ in pairs:
        cmd.extend((str(inp), str(out)))
    run_log = folder / "inkling-logits.log"
    with run_log.open("w", encoding="utf-8") as fh:
        result = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=args.timeout, check=False)

    records: list[dict[str, Any]] = []
    for inp, out, item in pairs:
        with out.open("rb") as fh:
            shape = np.fromfile(fh, dtype="<i4", count=2)
            values = np.fromfile(fh, dtype="<f4")
        if len(shape) != 2 or shape[0] != 1 or len(values) != shape[1] or not np.isfinite(values).all():
            raise ValueError(f"Incomplete or non-finite logits for row {item['row']}")
        choice_logits = [float(values[i]) for i in label_ids]
        prediction = int(np.argmax(choice_logits))
        answer = int(item["answer"])
        records.append(
            {
                "row": item["row"],
                "prediction": prediction,
                "answer": answer,
                "correct": prediction == answer,
                "choice_logits": choice_logits,
                "tokens": len(item["tokens"]),
            }
        )
    correct = sum(int(r["correct"]) for r in records)
    payload: dict[str, Any] = {
        "schema": "modeb-mmlu-native-v3",
        "model": str(args.model),
        "selection": str(args.selection),
        "label_token_ids": label_ids,
        "gpu_layers": args.gpu_layers,
        "tool_rc": result.returncode,
        "tool_log": str(run_log),
        "evaluated": len(records),
        "correct": correct,
        "accuracy_pct": round(100.0 * correct / max(1, len(records)), 2),
        "score": "argmax over the next-token logits for space-prefixed A/B/C/D",
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "records"}, indent=2, ensure_ascii=False))
    return 0 if result.returncode == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
