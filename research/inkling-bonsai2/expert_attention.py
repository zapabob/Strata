"""Paired interventions on official Inkling weights in the same Transformers graph."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import tempfile
import time

from filelock import FileLock
import numpy as np

from benchmark_generation import digest, read, save
from phase7_controls import immutable


HERE=Path(__file__).resolve().parent
ARMS={"A":"source", "B":"experts", "C":"attention", "D":"experts-attention",
      "F":"full", "R_E":"restore-experts", "R_A":"restore-attention",
      "R_EA":"restore-experts-attention"}
ARMS.update({k:k for k in ("embedding","head","gate","up","down","gate-up",
                         "restore-gate","restore-up","restore-down","restore-gate-up","restore-embedding")})


def protocol(root):
    e=root/"evaluation"
    loc=e/"phase10"
    loc.mkdir(exist_ok=True)
    frozen=read(e/"phase7/protocol.json")
    items={x["id"]:x for x in frozen["entries"]}
    rows=[items[k] for k in frozen["core"]]
    if [len(x["ids"])-1 for x in rows]!=[54,16,28,23,45,46,48]:
        raise ValueError("The original or additional Japanese prediction positions differ")
    weights=root/"official-models/Inkling-2-Mini-PQ2_0-Baseline.gguf"
    manifest=weights.parent/"Inkling-2-Mini-PQ2_0-Balanced.manifest.json"
    receipts=dict(corpus=digest(e/"phase7/protocol.json"),manifest=digest(manifest),conditions=ARMS,
        source=read(root/"official/source.json")["revision"],heldout=[x["id"] for x in rows],
        paired_positions="All next-token targets. Within each document the final input has no target.",
        fixed="Embedding, router, output head and all other weights retain source precision in A/B/C/D.",
        nonexpert="All lossy non-expert tensors comprise attention, input embeddings and output head.",
        reverse="F is the fully decoded deployment. R_E, R_A and R_EA restore experts, attention or both in F.",
        parity=dict(top1_agreement=1.,max_abs_mean_delta_nll=.001,max_mean_kl=.00001),
        interval="Percentile bootstrap resamples paired whole documents, then divides by their total prediction count.",
        source_replay="The independently reconstructed final readout must pass on the added 139 positions.",
        rationale="Estimate and report attribution before selecting any new rotation or precision.")
    immutable(loc/"protocol.json",receipts)
    return loc,rows,weights,manifest


def record_case(a,label,frozen=False):
    from sm120_native import run
    loc,rows,weights,manifest=protocol(a.root)
    out=loc/("frozen" if frozen else "dynamic")/label
    out.mkdir(exist_ok=True,parents=True)
    if a.kernels:
        os.environ["INKLING_SOURCE_CUDA"]=str(a.kernels.resolve(strict=True))
    lock=FileLock(str(Path(tempfile.gettempdir())/"strata-inkling-benchmark-gpu0.lock"))
    run_id=dict(protocol=digest(loc/"protocol.json"),condition=ARMS[label],sequence_batch=7,
                routing="source IDs and weights" if frozen else "dynamic",dtype="BF16",attention="eager")
    immutable(out/"identity.json",run_id)
    with FileLock(str(out/"case.lock")):
        if (out/"splits.json").is_file():
            for i,r in enumerate(rows):
                with np.load(out/f"holdout-{i}.npz") as z:
                    if not np.array_equal(z["input_ids"][0],r["ids"]) or "l23.v0.expert_mixture" not in z:
                        raise ValueError("Incomplete intervention trace")
            return
        cmd=[sys.executable,"-B",str(HERE/"calibrate_inkling2.py"),"--original","--source",str(a.root/"official"),
             "--output",str(out),"--texts",str(a.root/"evaluation/phase7/core-texts.json"),
             "--sequence-batch","7","--compact-traces","--cache-gib","1.25","--split","holdout"]
        if label!="A":
            cmd.extend(["--gguf",str(weights),"--llama",str(a.llama),"--manifest",str(manifest),"--weights-mode",ARMS[label]])
        if frozen:
            if not (loc/"dynamic/A/splits.json").exists(): raise ValueError("Frozen routing requires the source traces")
            cmd.extend(["--frozen",str(loc/"dynamic/A")])
        for trial in range(12):
            attempt=out/("run-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
            try:
                with lock: run(attempt,cmd,12000,3600,21600)
                print("Measured",label,"frozen" if frozen else "dynamic",flush=True)
                return
            except RuntimeError:
                receipt=attempt/"measurement.json"
                if trial==11 or not receipt.is_file() or read(receipt)["reason"] not in {
                      "physical_memory_pressure","commit_pressure","device_memory_pressure","disk_space_pressure"}: raise
                time.sleep(10)


def effects(values):
    a,b,c,d=(values[k] for k in "ABCD")
    return dict(expert_alone=b-a,attention_alone=c-a,interaction=(d-c)-(b-a),
                joint=d-a,expert_given_attention=d-c,attention_given_expert=d-b,
                average_expert=.5*((b-a)+(d-c)),average_attention=.5*((c-a)+(d-b)))


def paired_effects(documents,counts,draws=8000):
    values=np.asarray([[d[k] for k in "ABCD"] for d in documents],dtype=float)
    sizes=np.asarray(counts,dtype=np.int64)
    if sizes.shape!=(len(values),) or not len(sizes) or np.any(sizes<=0) or not np.isfinite(values).all():
        raise ValueError("Four finite paired NLL sums per document and positive document lengths are required")
    def calculate(sums,denominator):
        return effects(dict(zip("ABCD",(sums/denominator).T,strict=True)))
    means=values.sum(0)/sizes.sum()
    out=dict(tokens=int(sizes.sum()),documents=len(sizes),mean_nll=dict(zip("ABCD",means.tolist(),strict=True)),
             effects=calculate(values.sum(0),sizes.sum()),document_cluster_95=None)
    if len(sizes)>1:
        samples=np.random.default_rng(20261125).integers(len(sizes),size=(draws,len(sizes)))
        delta=calculate(values[samples].sum(1),sizes[samples].sum(1)[:,None])
        out["document_cluster_95"]={k:np.quantile(v,[.025,.975]).tolist() for k,v in delta.items()}
    return out


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("run","summarise"))
    for key in ("root","llama","kernels"):p.add_argument("--"+key,type=Path,required=key=="root")
    p.add_argument("--arms",nargs="+",choices=ARMS,default=list("ABCD")+["F","R_E","R_A","R_EA"])
    p.add_argument("--frozen",action="store_true")
    p.add_argument("--profile",choices=("matched","serial","single"),default="matched")
    a=p.parse_args()
    if a.action=="run":
        if not a.llama: p.error("Supply the matching GGUF implementation")
        for label in a.arms: record_case(a,label,a.frozen)
    else:
        from factorial_report import report
        report(a.root,a.profile)
