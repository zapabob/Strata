"""Recover recorded trajectories, audit saved KV continuation and score nested AIME budgets."""
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

from agentic_quality import lease
from benchmark_apex import visible_and_reasoning
from benchmark_generation import digest, read, save
from phase7_controls import immutable
from sm120_native import run
from termination_survival import BUDGETS, parse_integer, summarise


def reconstruct(a):
    source=a.root/"evaluation/aime2025"
    dest=a.root/"evaluation/phase11"
    spec,gold=read(source/"protocol.json"),read(source/"gold.json")
    tok=Tokenizer.from_file(str(a.root/"official/tokenizer.json"))
    roles={i:w.content for i,w in tok.get_added_tokens_decoder().items() if w.special}
    for variant in a.variants:
        model=a.root/(variant+"-models")/"Inkling-2-Mini-PQ2_0-Balanced.gguf"
        for key in a.items or spec["full"]:
            prompt=spec["items"][key]["tokens"]
            history=dest/"original-aime"/variant/"answers"/(key+".json")
            old=read(history) if history.exists() else {}
            valid_ids=old.get("output_ids")
            valid_ids=valid_ids if isinstance(valid_ids,list) and len(valid_ids)==old["output_tokens"] else []
            folder=dest/"greedy"/variant/key
            folder.mkdir(parents=True,exist_ok=True)
            immutable(folder/"identity.json",dict(official_protocol=digest(source/"protocol.json"),model=str(model),
                engine=digest(a.binary),context=17408,prompt=prompt,reasoning_effort=spec["reasoning_effort"],
                original=digest(history) if history.exists() else None,
                origin="recorded IDs and rebuilt KV" if valid_ids else "frozen prompt regenerated",
                sampling="argmax, repeat penalty 1, historical stop tokens, no logit bias"))
            ids=list(valid_ids)
            prev=None
            for budget in BUDGETS:
                result_file=folder/f"at-{budget}.json"
                if prev is not None and prev["outcome"]!="censored":
                    if not result_file.exists():
                        save(result_file,dict(prev,budget=budget,carried_from=prev["budget"]))
                    prev=read(result_file)
                    continue
                if result_file.exists():
                    prev=read(result_file)
                    ids=np.fromfile(prev["raw_ids"],dtype="<i4").tolist()
                    continue
                stage=folder/(str(budget)+"-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
                stage.mkdir()
                np.asarray(prompt,dtype="<i4").tofile(stage/"prompt.i32")
                np.asarray(ids,dtype="<i4").tofile(stage/"prefix.i32")
                if prev:
                    os.link(prev["kv"],stage/"previous.state")
                with lease().acquire(poll_interval=.022):
                    receipt=run(stage,[str(a.binary),str(model),str(stage),str(budget),"17408","legacy"],
                                11000,7200,3600)
                raw_ids=np.fromfile(stage/"ids.i32",dtype="<i4").tolist()
                if raw_ids[:len(ids)]!=ids:raise ValueError("Resumed IDs diverged")
                line=next(l for l in (stage/"stdout.txt").read_text().splitlines() if l.startswith("TERMINATION "))
                n,terminal,vocab,restoring=map(int,line.split()[1:])
                if n!=len(raw_ids) or n>budget or bool(restoring)!=bool(prev) or not(terminal or n==budget):
                    raise ValueError("Incomplete trajectory receipt")
                reason="eos" if terminal else "limit"
                channels=visible_and_reasoning(raw_ids,tok,reason)
                value=parse_integer(channels["content"])
                state="censored" if not terminal else ("terminal_without_final" if value is None else "final")
                with (stage/"steps.tsv").open(newline="") as f:
                    steps=list(csv.DictReader(f,delimiter="\t"))
                forced=[r for r in steps if int(r["forced"])]
                tail=list(zip(raw_ids[-256:],raw_ids[-255:],raw_ids[-254:],raw_ids[-253:])) if len(raw_ids)>=256 else list(zip(raw_ids,raw_ids[1:],raw_ids[2:],raw_ids[3:]))
                counts=Counter(tail)
                prev=dict(id=key,budget=budget,time=n,outcome=state,correct=state=="final" and value==gold[key],parsed=value,
                          terminal=bool(terminal),raw_ids=str(stage/"ids.i32"),kv=str(stage/"next.state") if (stage/"next.state").exists() else None,
                          logits_and_steps=str(stage),peak_device_bytes=receipt["peak_device_used_bytes"],
                          restored_saved_kv=bool(restoring),replayed_tokens=len(forced),
                          replay_argmax_mismatches=sum(int(r["id"])!=int(r["greedy"]) for r in forced),
                          visible_text=channels["content"],reasoning_characters=len(channels["reasoning"]),
                          markers=[(i+1,roles[t]) for i,t in enumerate(raw_ids) if t in roles],
                          repeated_fourgram_fraction=sum(c-1 for c in counts.values())/len(tail) if tail else None)
                save(result_file,prev)
                ids=raw_ids
                print(variant,key,budget,state,value,flush=True)
                if budget==a.stop_after:break


def report(root):
    folder=root/"evaluation/phase11/greedy"
    result={}
    for variant in ("official","ablated"):
        result[variant]={}
        for b in BUDGETS:
            records=[read(p) for p in sorted((folder/variant).glob(f"*/at-{b}.json"))]
            if records: result[variant][b]=dict(expected=30,**summarise(records,b))
    save(folder.parent/"greedy-survival.json",result)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("action",choices=("run","report"))
    p.add_argument("--root",type=Path,required=True);p.add_argument("--binary",type=Path)
    p.add_argument("--variants",nargs="+",choices=("official","ablated"),default=["official","ablated"])
    p.add_argument("--items",nargs="+");p.add_argument("--stop-after",type=int,choices=BUDGETS,default=16384)
    a=p.parse_args()
    if a.action=="run":reconstruct(a)
    report(a.root)
