"""Probe how the Mode B chat template splits thinking vs. answer content."""

from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from phase13_acceptance_eval import chat_completion, launch_llama_server, stop_server, wait_health  # noqa: E402

from heretic_model_card_eval import load_mmlu_tokenizer  # noqa: E402

MODEL = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf")
SERVER = Path(r"H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\llama-server.exe")
SELECTION = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\mmlu-sm120\selection.json")
TOKENIZER = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\source\tokenizer.json")
OUT = Path(r"H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3\reasoning_probe.json")
PORT = 8095
OT = [r"blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps=CPU"]


def main() -> int:
    spec = json.loads(SELECTION.read_text(encoding="utf-8"))
    item = next(i for i in spec["items"] if i["row"] == 187)
    prompt = load_mmlu_tokenizer(TOKENIZER).decode(item["tokens"], skip_special_tokens=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    proc, fh = launch_llama_server(SERVER, MODEL, ctx=4096, ub=32, port=PORT, log_path=OUT.with_suffix(".server.log"), extra_ot=OT)
    try:
        wait_health(f"http://127.0.0.1:{PORT}", proc, timeout_s=300.0)
        probes = []
        for effort, max_tokens in (("none", 16), ("none", 128), ("high", 128)):
            body, lat = chat_completion(
                f"http://127.0.0.1:{PORT}",
                [{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.0,
                reasoning_effort=effort,
                timeout_s=300.0,
            )
            probes.append({"effort": effort, "max_tokens": max_tokens, "latency_s": lat, "body": body})
    finally:
        stop_server(proc, fh)
    OUT.write_text(json.dumps({"prompt": prompt, "gold": item["answer"], "probes": probes}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for p in probes:
        msg = p["body"]["choices"][0]["message"]
        print(json.dumps({"effort": p["effort"], "max_tokens": p["max_tokens"],
                          "content": (msg.get("content") or "")[:120],
                          "reasoning_content": (msg.get("reasoning_content") or "")[:120],
                          "finish_reason": p["body"]["choices"][0].get("finish_reason")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
