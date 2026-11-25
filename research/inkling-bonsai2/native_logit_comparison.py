"""Compare Strata CUDA and patched llama.cpp on identical official GGUF tokens with FP16 KV."""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import tempfile

from filelock import FileLock
import numpy as np

from benchmark_generation import digest,read,save
from benchmark_inkling2 import aggregate,score
from expert_attention import protocol
from phase7_controls import immutable,matrix
from sm120_native import run


def load_native(path,ids,vocab):
    with path.open("rb") as f:
        dims=np.fromfile(f,dtype="<i4",count=2)
        if len(dims)!=2 or list(dims)!=[len(ids),vocab]:raise ValueError("Invalid Strata logit extent")
        if not np.array_equal(np.fromfile(f,dtype="<i4",count=len(ids)),ids):raise ValueError("Different Strata prompt")
    offset=8+4*len(ids)
    if path.stat().st_size!=offset+4*len(ids)*vocab:raise ValueError("Truncated Strata logits")
    return np.memmap(path,mode="r",dtype="<f4",offset=offset,shape=(len(ids),vocab))


def evaluate(a):
    loc,rows,model,manifest=protocol(a.root)
    dest=loc/"strata-fp16-kv"
    dest.mkdir(exist_ok=True)
    immutable(dest/"identity.json",dict(engine=digest(a.engine),manifest=digest(manifest),protocol=digest(loc/"protocol.json"),
              command_profile="SM120, FP16 KV, CUDA prefill, 2048 slot capacity, draft off"))
    lock=FileLock(str(Path(tempfile.gettempdir())/"strata-inkling-benchmark-gpu0.lock"))
    comparisons={"llama_cpp_to_strata":{},"source_to_strata":{},"decoded_to_strata":{},"decoded_to_llama_cpp":{}}
    for i,row in enumerate(rows):
        ids=row["ids"];key=row["id"];out=dest/f"holdout-{i}.bin"
        ext=loc.parent/"phase7/official/core/candidate"/f"holdout-{i}.logits"
        gg=matrix(ext,ids)
        if not out.exists():
            now=dest/("run-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
            part=now/(out.name+".partial")
            cmd=[str(a.engine),"--dump-ref",str(part),"--prompt-ids",",".join(map(str,ids)),
                 "--native",str(model),"--gpu","0","--parallel","1","--max-context","2048","--kv","fp16",
                 "--draft","off","--cpu-threads","5","--vram-reserve-mib","1536"]
            with lock:run(now,cmd,12000,3600,1800)
            if "cuda" not in (now/"stdout.txt").read_text().lower():raise ValueError("Missing native CUDA attestation")
            del_guard=load_native(part,ids,gg.shape[1])
            del del_guard
            os.replace(part,out)
        native=load_native(out,ids,gg.shape[1])
        comparisons["llama_cpp_to_strata"][key]=score(gg,native,ids)
        for condition,prefix in (("A","source"),("F","decoded")):
            trace=loc/a.graphs/"dynamic"/condition/f"holdout-{i}.npz"
            if not trace.exists():continue
            with np.load(trace) as z:
                if not np.array_equal(z["input_ids"][0],ids):raise ValueError("Different reference graph prompt")
                ref=z["logits"]
                comparisons[prefix+"_to_strata"][key]=score(ref,native,ids)
                if condition=="F":comparisons["decoded_to_llama_cpp"][key]=score(ref,gg,ids)
        save(dest/"comparisons.json",dict(weight_file=model.name,reference_graphs=a.graphs,
             comparisons={k:aggregate(v) for k,v in comparisons.items() if v}))
        print("Native FP16-KV comparison",i+1,"of",len(rows),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("root","engine"):p.add_argument("--"+k,type=Path,required=True)
    p.add_argument("--graphs",choices=("serial","matched"),default="serial")
    evaluate(p.parse_args())
