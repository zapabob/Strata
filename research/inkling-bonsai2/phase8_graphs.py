"""Run controlled dense/expert interventions in one graph, then quantify their interaction."""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import sys
import tempfile
import time

import numpy as np
from filelock import FileLock

from benchmark_generation import digest,read,save
from benchmark_inkling2 import aggregate,score,trace
from phase7_controls import immutable,matrix


HERE=Path(__file__).resolve().parent
MODES=("experts","full","nonexperts","embedding-head","attention")


def plan(root):
    e=root/"evaluation"
    folder=e/"phase8"
    folder.mkdir(exist_ok=True)
    counts=np.zeros((24,128),dtype=np.int64)
    for path in sorted((e/"official-dynamic").glob("calibration-*.npz"))[:2]:
        with np.load(path) as z:
            for name in z.files:
                if name.endswith(".counts"):
                    layer=int(name.split(".")[0][1:])
                    counts[layer]+=z[name]
    specs=read(root/"official-models"/"Inkling-2-Mini-PQ2_0-Balanced.manifest.json")["tensors"]
    choices=[]
    # Cover the input stem, two recurrent bands, and the published MXFP8 tail.
    for lo,hi in ((0,6),(6,12),(12,18),(20,24)):
        layer,expert=np.unravel_index(counts[lo:hi].argmax(),counts[lo:hi].shape)
        layer,expert=int(lo+layer),int(expert)
        selected=[t for t in specs if t["type"]=="PQ2_0" and t["name"].startswith(f"blk.{layer}.")]
        if len(selected)!=2 or counts[layer,expert]<=0: raise ValueError("Invalid calibration intervention")
        cost=sum((2*int(np.prod(t["shape"]))-t["bytes"])//128 for t in selected)
        choices.append(dict(layer=layer,expert=expert,calibration_routes=int(counts[layer,expert]),
                    incremental_bf16_expert_bytes=cost))
    immutable(folder/"restoration-plan.json",dict(choices=choices,fit_documents=["calibration-0","calibration-1"],
         validation_documents=["calibration-2","calibration-3"],selection="Highest number of observed routes per band. Frequency screens candidates; restoration measures sensitivity.",
         score="Reduction in mean validation NLL per extra BF16 byte; tie-break by physical layer then expert",
         control="Full decoded mixed GGUF in the Transformers graph",weights_mode="full"))


def run_case(a,name,mode,restore,split,frozen=False):
    from sm120_native import run
    e=a.root/"evaluation"
    sub=e/"phase8"/("frozen" if frozen else "dynamic")/name/split
    sub.mkdir(parents=True,exist_ok=True)
    weights=a.root/"official-models"/"Inkling-2-Mini-PQ2_0-Baseline.gguf"
    manifest=weights.parent/"Inkling-2-Mini-PQ2_0-Balanced.manifest.json"
    identity=dict(graph="official Transformers eager BF16",weights_mode=mode,restore=restore,split=split,
          manifest=digest(manifest),texts=digest(HERE/"calibration_text.json"),frozen=frozen)
    immutable(sub/"identity.json",identity)
    if (sub/"splits.json").exists(): return
    cmd=[sys.executable,"-B",str(HERE/"calibrate_inkling2.py"),"--source",str(a.root/"official"),"--original",
         "--gguf",str(weights),"--manifest",str(manifest),"--llama",str(a.llama),"--weights-mode",mode,
         "--output",str(sub),"--sequence-batch","3","--split",split,"--compact-traces","--cache-gib","1.75"]
    if frozen: cmd.extend(["--frozen",str(e/"official-dynamic")])
    if restore: cmd.extend(["--restore",restore])
    lock=FileLock(str(Path(tempfile.gettempdir())/"strata-inkling-benchmark-gpu0.lock"))
    for attempt in range(12):
        dest=sub/("run-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
        try:
            with lock: run(dest,cmd,12000,3600,21600)
            return
        except RuntimeError:
            receipt=dest/"measurement.json"
            if attempt==11 or not receipt.exists() or read(receipt)["reason"] not in {
                  "device_memory_pressure","physical_memory_pressure","commit_pressure","disk_space_pressure"}: raise
            time.sleep(15)


def summarise(root,split):
    e=root/"evaluation"
    work=e/"phase8"
    result={}
    refs=sorted((e/"official-dynamic").glob(split+"-*.npz"))
    for condition in sorted((work/"dynamic").glob("*")):
        folder=condition/split
        rows={}
        for ref in refs:
            candidate=folder/ref.name
            if candidate.is_file():
                rows[ref.stem]=trace(ref,candidate)
        if rows: result[condition.name]=aggregate(rows)
    summary=dict(split=split,conditions=result)
    if split=="holdout" and set(("experts","nonexperts","full"))<=set(result) and all(
            set(result[k]["sequences"])=={f.stem for f in refs} for k in ("experts","nonexperts","full")):
        exact=read(e/"phase7/baseline-20261125-1024-jst/corrected-official.json")
        src=exact["reference_nll"]
        exp,other,both=[result[k]["candidate_nll"] for k in ("experts","nonexperts","full")]
        rt={}
        for ref in refs:
            with np.load(work/"dynamic/full/holdout"/ref.name) as z:
                ids=z["input_ids"][0]
                ll=e/"sm120-official"/"heldout-native-r1"/(ref.stem+".logits")
                rt[ref.stem]=score(z["logits"],matrix(ll,ids),ids)
        summary["same_gguf_runtime"]=aggregate(rt)
        summary["attribution_nats_per_token"]=dict(
            expert_shapley=.5*((exp-src)+(both-other)),nonexpert_shapley=.5*((other-src)+(both-exp)),
            dense_expert_interaction=both-exp-other+src,reference_graph_to_patched_llama=exact["candidate_nll"]-both,
            total=exact["delta_nll"],tokens=exact["total_tokens"])
    save(work/(split+"-graphs.json"),summary)
    return result


def run_all(a):
    e=a.root/"evaluation/phase8"
    plan(a.root)
    for mode in MODES:
        run_case(a,mode,mode,None,"holdout")
        summarise(a.root,"holdout")
    run_case(a,"full","full",None,"calibration")
    choices=read(e/"restoration-plan.json")["choices"]
    for c in choices:
        key=f"{c['layer']}:{c['expert']}"
        run_case(a,"restore-"+key.replace(":","-"),"full",key,"calibration")
    rows=summarise(a.root,"calibration")
    def validation_nll(record):
        two=[record["sequences"][k] for k in ("calibration-2","calibration-3")]
        return sum(r["sum_candidate_nll"] for r in two)/sum(r["tokens"] for r in two)
    origin=validation_nll(rows["full"])
    for c in choices:
        name=f"restore-{c['layer']}-{c['expert']}"
        gain=origin-validation_nll(rows[name])
        c.update(validation_nll_recovered=gain,recovery_per_byte=gain/c["incremental_bf16_expert_bytes"])
    best=max(choices,key=lambda c:(c["recovery_per_byte"],-c["layer"],-c["expert"]))
    selection=dict(candidates=choices,selected=best if best["validation_nll_recovered"]>0 else None)
    immutable(e/"restoration-selection.json",selection)
    if selection["selected"]:
        key=f"{best['layer']}:{best['expert']}"
        run_case(a,"restore-"+key.replace(":","-"),"full",key,"holdout")
        summarise(a.root,"holdout")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("plan","run","summarise"))
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--llama",type=Path)
    args=parser.parse_args()
    if args.action=="plan": plan(args.root)
    elif args.action=="summarise": summarise(args.root,"holdout")
    elif args.llama: run_all(args)
    else: parser.error("Supply the llama.cpp tree containing the matching GGUF codec")
