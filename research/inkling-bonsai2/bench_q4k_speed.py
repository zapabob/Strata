from __future__ import annotations
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
from phase13_acceptance_eval import chat_completion, launch_llama_server, stop_server, wait_health
MODEL=Path(r"H:\Strata\models\inkling2-heretic-q4k\Inkling-2-Mini-Heretic-ModeB-NVFP4-DenseQ4_K.gguf")
SERVER=Path(r"H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\llama-server.exe")
OUT=Path(r"H:\Strata\evidence\phase13-agentic-hybrid\q4k-benchmark\speed_q4k.json")
PORT=8096
OT=[r"blk\.(0|1|2|3|4|5|22|23)\.ffn_.*_exps=CPU"]
def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    proc,fh=launch_llama_server(SERVER,MODEL,ctx=4096,ub=32,port=PORT,log_path=OUT.with_suffix('.server.log'),extra_ot=OT)
    try:
        load=wait_health(f"http://127.0.0.1:{PORT}",proc,timeout_s=600.0)
        body,lat=chat_completion(f"http://127.0.0.1:{PORT}",[{"role":"user","content":"Explain in two sentences why Q4_K dense weights can preserve logits better than ternary PQ2_0."}],max_tokens=64,temperature=0.0,reasoning_effort="none",timeout_s=600.0)
    finally:
        stop_server(proc,fh)
    result={"model":str(MODEL),"load_seconds":load,"latency_s":lat,"timings":body.get("timings"),"usage":body.get("usage"),"content":(body["choices"][0]["message"].get("content") or "")[:200]}
    OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="content"},indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__": raise SystemExit(main())
