"""Freeze matched Inkling inputs, replay the four conditions and retain item-level evidence."""
import argparse
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import sys
import tempfile
import time

import numpy as np
from filelock import FileLock

from benchmark_generation import digest, read, save
from benchmark_inkling2 import aggregate, score
from source import atomic_bytes


HERE = Path(__file__).resolve().parent
VARIANTS = ("official", "ablated")
CARD_NAMES = ("Inkling-2-Mini-PQ2_0-GGUF", "Inkling-2-Mini-Heretic-PQ2_0-GGUF")


def immutable(path, value):
    if path.exists():
        if read(path) != value:
            raise ValueError(f"Existing frozen record differs: {path}")
        return
    save(path, value)


def matrix(path, tokens):
    with path.open("rb") as handle:
        n, v = map(int, np.fromfile(handle, dtype="<i4", count=2))
    if n != len(tokens) or v < 1 or path.stat().st_size != 8+4*n*v:
        raise ValueError(f"Logit extent differs: {path}")
    return np.memmap(path, mode="r", dtype="<f4", offset=8, shape=(n,v))


def freeze(root):
    from tokenizers import Tokenizer
    e=root/"evaluation"
    work=e/"phase7"
    work.mkdir(exist_ok=True)
    history=work/"baseline-20261125-1024-jst"
    history.mkdir(exist_ok=True)
    for slug in CARD_NAMES:
        path=history/(slug+".md")
        if not path.exists():
            atomic_bytes(path,(root/"huggingface"/slug/"README.md").read_bytes())
    sources=e/"official-dynamic"
    old=e/"sm120-official"/"heldout-native-r1"
    if not (history/"corrected-official.json").exists():
        rows={}
        for path in sorted(sources.glob("holdout-*.npz")):
            with np.load(path) as z:
                ids=z["input_ids"][0]
                if not np.array_equal(ids,np.fromfile(old/(path.stem+".i32"),dtype="<i4")):
                    raise ValueError("Historical token trajectories differ")
                rows[path.stem]=score(z["logits"],matrix(old/(path.stem+".logits"),ids),ids)
        corrected=aggregate(rows)
        original=read(old/"scores.json")
        for key in ("candidate_ppl","reference_ppl","top1_agreement","mean_kl"):
            if not math.isclose(corrected[key],original[key],rel_tol=1e-7):
                raise AssertionError(f"Historical raw values differ for {key}")
        corrected.update(reference="Published NVFP4/MXFP8 reconstructed for BF16 Transformers calculation",
                         candidate="Patched llama.cpp, CUDA",original_file_digest=digest(old/"scores.json"))
        save(history/"corrected-official.json",corrected)
        pilot=read(e/"generative-maths"/"pilot-summary.json")["models"]["ablated"]
        ctx=read(e/"hermes-long-context"/"ablated"/"accepted-98304.json")
        stopped=read(e/"hermes-long-context"/"ablated"/"server-20261125T004834"/"measurement.json")
        speeds={}
        for variant in VARIANTS:
            trials=read(e/f"sm120-{variant}"/"throughput-compact-r1"/"stdout.txt")
            speeds[variant]=next(t["avg_ts"] for t in trials if t["n_gen"]==128 and not t["n_prompt"])
        pilot_keys=("correct","n","at_limit","missing_final","wilson95")
        save(history/"baseline.json",dict(as_of="2026-11-25T10:24:00+09:00",candidate_engine="patched llama.cpp",
             hardware="RTX 5060 Ti 16 GiB",decode128_tokens_s=speeds,official_tokens=corrected["total_tokens"],
             reference_ppl=corrected["reference_ppl"],official_pq2_ppl=corrected["candidate_ppl"],
             top1=corrected["top1_agreement"],kl=corrected["mean_kl"],
             heretic_pilot={s:{k:pilot[s][k] for k in pilot_keys} for s in ("gsm8k","math500")},
             hermes_98304=dict(input=ctx["observed_prompt_tokens"],prefill=ctx["timings"]["prompt_per_second"],
                              recalled=len(ctx["correct_labels"]),expected=3),
             hermes_131072=stopped["protection_events"]))
    corp=read(HERE/"phase7_corpus.json")
    prev=read(HERE/"calibration_text.json")
    tok=Tokenizer.from_file(str(root/"official"/"tokenizer.json"))
    if digest(root/"official"/"tokenizer.json")!=digest(root/"source"/"tokenizer.json"):
        raise ValueError("Compare vocabulary and segmentation before pooling these checkpoints")
    dataset=set()
    entries=[]
    for i,t in enumerate(prev["holdout"]):
        domain=("mixed-prose","english-technical","japanese-prose","english-mathematics")[i]
        entries.append(dict(id=f"legacy-{i}",domain=domain,split="holdout",text=t))
    for domain,splits in corp.items():
        for split,texts in splits.items():
            for i,t in enumerate(texts):
                if t in dataset or t in prev["calibration"]+prev["holdout"]:
                    raise ValueError("Duplicated calibration, validation or held-out text")
                dataset.add(t)
                entries.append(dict(id=f"{domain}-{split}-{i}",domain=domain,split=split,text=t))
    for r in entries:
        r["ids"]=tok.encode(r["text"],add_special_tokens=False).ids
        r["scored_positions"]=[0,len(r["ids"])-2]
    for i in range(4):
        with np.load(sources/f"holdout-{i}.npz") as z:
            if not np.array_equal(entries[i]["ids"],z["input_ids"][0]):
                raise ValueError("Historical holdout differs from frozen tokenizer inputs")
    sels=e/"mmlu-sm120"/"selection.json"
    allheld=[r for r in entries if r["split"]=="holdout"]
    core=allheld[:4]+[r for r in allheld[4:] if r["domain"]=="japanese-prose"]
    remaining=[r for r in allheld if r not in core]
    for subset,items in (("core",core),("extended",remaining)):
        immutable(work/(subset+"-texts.json"),dict(calibration=prev["calibration"]+
                  [r["text"] for r in entries if r["split"]=="calibration"],holdout=[r["text"] for r in items]))
    immutable(work/"protocol.json",dict(version=1,seed=20261125,tokenizer=digest(root/"official"/"tokenizer.json"),
              selection=digest(sels),conditions={"A":"official reconstructed BF16 Transformers","B":"official PQ2_0 patched llama.cpp",
              "C":"Heretic source BF16 Transformers","D":"Heretic PQ2_0 patched llama.cpp"},
              scoring="Every next token from position 1 onwards, no BOS, no padding included in scores",
              core=[r["id"] for r in core],extended=[r["id"] for r in remaining],entries=entries))
    print("Frozen",len(allheld),"holdouts,",sum(len(r["ids"])-1 for r in allheld),"scored next tokens",flush=True)


def receipts(root,variant):
    return root/"evaluation"/"phase7"/variant


def reference(root,variant,scope):
    e=root/"evaluation"
    folder=receipts(root,variant)
    target=folder/scope/"reference"
    target.mkdir(parents=True,exist_ok=True)
    (folder/"maths").mkdir(exist_ok=True)
    src=root/("official" if variant=="official" else "source")
    identity=dict(revision=read(src/"source.json")["revision"],protocol=digest(e/"phase7"/"protocol.json"),scope=scope)
    immutable(target/"identity.json",identity)
    if scope=="core" and variant=="official":
        for i in range(4):
            dst=target/f"holdout-{i}.npz"
            if not dst.exists():
                os.link(e/"official-dynamic"/dst.name,dst)
    cmd=[sys.executable,"-B",str(HERE/"benchmark_maths.py"),"score","--source",str(src),"--selection",
            str(e/"mmlu-sm120"/"selection.json"),"--output",str(folder/"maths"/"score.json"),
            "--heldout-reference-dir",str(target),"--texts",str(e/"phase7"/(scope+"-texts.json")),
            "--cache-gib","1.5","--batch","8","--text-batch","3"]
    if variant=="official":
        cmd.append("--original")
    return cmd


def quantised(root,variant,scope,binary,output):
    e=root/"evaluation"
    protocol=read(e/"phase7"/"protocol.json")
    entries={r["id"]:r for r in protocol["entries"]}
    model=root/(variant+"-models")/("Inkling-2-Mini-PQ2_0-Baseline.gguf" if variant=="official" else "Inkling-2-Mini-PQ2_0-Balanced.gguf")
    cmd=[str(binary),"--gpu-layers","99",str(model)]
    output.mkdir(parents=True,exist_ok=True)
    for i,key in enumerate(protocol[scope]):
        ids=entries[key]["ids"]
        path=output/f"holdout-{i}.logits"
        inputs=path.with_suffix(".i32")
        old=e/"sm120-official"/"heldout-native-r1"
        if variant=="official" and scope=="core" and i<4 and not path.exists():
            if not np.array_equal(np.fromfile(old/inputs.name,dtype="<i4"),ids):
                raise ValueError("Saved candidate token trajectory differs")
            os.link(old/path.name,path)
        if path.exists():
            matrix(path,ids)
            continue
        np.asarray(ids,dtype="<i4").tofile(inputs)
        cmd.extend([str(inputs),str(path.with_suffix(".part"))])
    return cmd if len(cmd)>4 else []


def run_condition(args):
    from sm120_native import run
    work=receipts(args.root,args.variant)/args.scope
    output=work/"candidate"
    lease=FileLock(str(Path(tempfile.gettempdir())/"strata-inkling-benchmark-gpu0.lock"))
    with lease.acquire(poll_interval=.008 if args.kind=="reference" else .05):
        if args.kind=="reference":
            cmd=reference(args.root,args.variant,args.scope)
            if args.kernels and args.variant=="official":
                os.environ["INKLING_SOURCE_CUDA"]=str(args.kernels.resolve(strict=True))
            if (work/"reference"/"source.json").is_file() and (work.parent/"maths"/"score.json").is_file():
                cmd=[]
        else:
            cmd=quantised(args.root,args.variant,args.scope,args.binary,output)
        if cmd:
            for attempt in range(4):
                dest=work/"runs"/(args.kind+"-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
                try:
                    run(dest,cmd,12000,3600,43200)
                    break
                except RuntimeError:
                    receipt=dest/"measurement.json"
                    if attempt==3 or not receipt.exists() or read(receipt).get("reason") not in {
                        "device_memory_pressure","physical_memory_pressure","commit_pressure","disk_space_pressure"}:
                        raise
                    time.sleep(15)
        if args.kind=="candidate":
            for p in output.glob("*.part"):
                ids=np.fromfile(p.with_suffix(".i32"),dtype="<i4")
                matrix(p,ids)
                p.replace(p.with_suffix(".logits"))


def summarise(root):
    e=root/"evaluation"
    work=e/"phase7"
    protocol=read(work/"protocol.json")
    selection=read(e/"mmlu-sm120"/"selection.json")
    gold={str(x["row"]):x["answer"] for x in selection["items"]}
    records={key:{"gold":v} for key,v in gold.items()}
    entries={r["id"]:r for r in protocol["entries"]}
    paired={}
    summary={"protocol":digest(work/"protocol.json"),"mathematics":{},"partial_mathematics":{},"ppl":{}}
    for variant,(ref,quant) in zip(VARIANTS,(("A","B"),("C","D")),strict=True):
        source=receipts(root,variant)
        progress=source/"maths"/"reference-progress.json"
        if progress.is_file() and not (source/"maths"/"score.json").is_file():
            tmp=read(progress)
            if tmp["identity"]["selection"]!=protocol["selection"]:
                raise ValueError("Partial reference uses a different mathematics selection")
            for k,item in tmp["rows"].items():
                if k not in gold or item["answer"]!=gold[k] or item["correct"]!=(item["prediction"]==gold[k]):
                    raise ValueError("Invalid partial mathematics answer")
                records[k][ref]=item["prediction"]
            summary["partial_mathematics"][ref]=dict(scored=len(tmp["rows"]),expected=len(gold),
                  correct=sum(r["correct"] for r in tmp["rows"].values()),engine=protocol["conditions"][ref])
        for condition,path in ((ref,source/"maths"/"score.json"),(quant,e/f"sm120-{variant}"/"maths-native-r1"/"score.json")):
            if not path.is_file():
                continue
            data=read(path)
            if data["selection_sha256"]!=protocol["selection"] or set(data["items"])!=set(gold):
                raise ValueError("Different MMLU selection or incomplete items")
            for k,r in data["items"].items():
                if r["answer"]!=gold[k] or r["correct"]!=(gold[k]==r["prediction"]):
                    raise ValueError("Mismatched MMLU answer key")
                records[k][condition]=r["prediction"]
            summary["mathematics"][condition]=dict(n=len(gold),correct=data["correct"],engine=protocol["conditions"][condition])
        rows={}
        for scope in ("core","extended"):
            for i,key in enumerate(protocol[scope]):
                d=source/scope
                cand=d/"candidate"/f"holdout-{i}.logits"
                archive=d/"reference"/f"holdout-{i}.npz"
                if not archive.exists() or not cand.exists():
                    continue
                ids=entries[key]["ids"]
                with np.load(archive) as z:
                    if not np.array_equal(z["input_ids"][0],ids):
                        raise ValueError("Source token trajectory differs")
                    rows[key]=score(z["logits"],matrix(cand,ids),ids)
        paired[variant]=rows
        if rows:
            summary["ppl"][variant]=dict(overall=aggregate(rows),domains={domain:aggregate({k:r for k,r in rows.items() if entries[k]["domain"]==domain})
                                          for domain in sorted({entries[k]["domain"] for k in rows})})
    changes={}
    for left,right in (("A","B"),("C","D"),("A","C"),("B","D")):
        if left not in summary["mathematics"] or right not in summary["mathematics"]:
            continue
        bins={"both_correct":[],"both_wrong":[],"lost":[],"gained":[]}
        for k,r in records.items():
            a,b=r[left]==r["gold"],r[right]==r["gold"]
            bins[("both_correct" if b else "lost") if a else ("gained" if b else "both_wrong")].append(k)
        changes[left+right]=bins
    common=set(paired["official"]) & set(paired["ablated"])
    if common:
        o,h=[aggregate({k:paired[v][k] for k in sorted(common)}) for v in VARIANTS]
        summary["factorial"]=dict(sequence_ids=sorted(common),tokens=o["total_tokens"],quant_official=o["delta_nll"],
              quant_heretic=h["delta_nll"],editing_at_reference=h["reference_nll"]-o["reference_nll"],
              editing_at_pq2=h["candidate_nll"]-o["candidate_nll"],interaction=h["delta_nll"]-o["delta_nll"])
    summary.update(items=records,transitions=changes)
    save(work/"four-conditions.json",summary)
    print("Measured conditions:",list(summary["mathematics"]),"; paired text rows:",{k:len(v) for k,v in paired.items()})


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("freeze","run","summarise"))
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--variant",choices=VARIANTS)
    p.add_argument("--kind",choices=("reference","candidate"))
    p.add_argument("--scope",choices=("core","extended"),default="core")
    p.add_argument("--binary",type=Path)
    p.add_argument("--kernels",type=Path,help="Audited CUDA reconstruction for the published source experts")
    args=p.parse_args()
    if args.action=="freeze": freeze(args.root)
    elif args.action=="summarise": summarise(args.root)
    elif not args.variant or not args.kind or (args.kind=="candidate" and not args.binary):
        p.error("Run requires a variant, a kind and a candidate binary for candidate scoring")
    else: run_condition(args)
