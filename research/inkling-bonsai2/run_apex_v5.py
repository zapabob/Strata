from __future__ import annotations
import json
from pathlib import Path
import sys
from typing import Any
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from heretic_model_card_eval import run_apex_subset
from phase13_acceptance_eval import launch_llama_server, stop_server, wait_health
MODEL = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf")
SERVER = Path(r"H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\llama-server.exe")
APEX = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\apex2025")
OUT_DIR = Path(r"H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3")
PORT = 8095
OT = [r"blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps=CPU"]

def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base_url = f"http://127.0.0.1:{PORT}"
    proc, fh = launch_llama_server(SERVER, MODEL, ctx=4096, ub=32, port=PORT, log_path=OUT_DIR / "apex_v5_server.log", extra_ot=OT)
    try:
        load_s = wait_health(base_url, proc, timeout_s=300.0)
        apex = run_apex_subset(base_url, APEX, 6)
    finally:
        stop_server(proc, fh)
    payload: dict[str, Any] = {"schema": "modeb-apex-v5", "model": str(MODEL), "load_seconds": load_s, "context": 4096, "extra_ot": OT, "apex2025": apex}
    out = OUT_DIR / "apex_v5.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"saved": str(out), "apex": {k: v for k, v in apex.items() if k != "records"}}, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
