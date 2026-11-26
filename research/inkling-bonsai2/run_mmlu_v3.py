"""Re-run the corrected Mode B MMLU evaluation on a dedicated short-context llama-server."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from heretic_model_card_eval import run_mmlu_subset  # noqa: E402
from phase13_acceptance_eval import (  # noqa: E402
    launch_llama_server,
    query_gpu_and_ram,
    query_process_shared_gpu_mib,
    stop_server,
    wait_health,
)

MODEL = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf")
SERVER = Path(r"H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\llama-server.exe")
SELECTION = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\mmlu-sm120\selection.json")
TOKENIZER = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\source\tokenizer.json")
OUT_DIR = Path(r"H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3")
PORT = 8095
EXTRA_OT = [r"blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps=CPU"]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base_url = f"http://127.0.0.1:{PORT}"
    log_path = OUT_DIR / "mmlu_v3_server.log"
    pre = query_gpu_and_ram()
    proc, fh = launch_llama_server(SERVER, MODEL, ctx=4096, ub=32, port=PORT, log_path=log_path, extra_ot=EXTRA_OT)
    try:
        load_s = wait_health(base_url, proc, timeout_s=300.0)
        t0 = time.monotonic()
        mmlu = run_mmlu_subset(base_url, SELECTION, 30, tokenizer_path=TOKENIZER)
        elapsed = round(time.monotonic() - t0, 2)
        shared = query_process_shared_gpu_mib(proc.pid)
    finally:
        stop_server(proc, fh)
    post = query_gpu_and_ram()
    payload: dict[str, Any] = {
        "schema": "modeb-mmlu-rerun-v3",
        "model": str(MODEL),
        "selection": str(SELECTION),
        "tokenizer": str(TOKENIZER),
        "server_log": str(log_path),
        "load_seconds": load_s,
        "eval_seconds": elapsed,
        "context": 4096,
        "extra_ot": EXTRA_OT,
        "mmlu": mmlu,
        "pre_hw": pre,
        "post_hw": post,
        "process_shared_gpu_mib": shared,
    }
    out = OUT_DIR / "mmlu_v3.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {k: v for k, v in mmlu.items() if k != "records"}
    print(json.dumps({"saved": str(out), "summary": summary}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
