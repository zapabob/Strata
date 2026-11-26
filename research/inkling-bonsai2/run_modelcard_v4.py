"""Re-run AIME and refusal behaviour with the corrected model-card evaluator."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from heretic_model_card_eval import run_aime_subset, run_refusal_eval  # noqa: E402
from phase13_acceptance_eval import launch_llama_server, stop_server, wait_health  # noqa: E402

MODEL = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf")
SERVER = Path(r"H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\llama-server.exe")
AIME = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\aime2025")
OUT_DIR = Path(r"H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3")
PORT = 8095
OT = [r"blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps=CPU"]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base_url = f"http://127.0.0.1:{PORT}"
    proc, fh = launch_llama_server(SERVER, MODEL, ctx=4096, ub=32, port=PORT, log_path=OUT_DIR / "modelcard_v4_server.log", extra_ot=OT)
    try:
        load_s = wait_health(base_url, proc, timeout_s=300.0)
        aime = run_aime_subset(base_url, AIME, 6)
        refusal = run_refusal_eval(base_url)
    finally:
        stop_server(proc, fh)
    payload: dict[str, Any] = {
        "schema": "modeb-modelcard-v4",
        "model": str(MODEL),
        "load_seconds": load_s,
        "context": 4096,
        "extra_ot": OT,
        "aime2025": aime,
        "refusal_behaviour": refusal,
    }
    out = OUT_DIR / "modelcard_v4.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"saved": str(out), "aime": {k: v for k, v in aime.items() if k != "records"},
                      "refusal": {k: v for k, v in refusal.items() if k != "records"}}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
