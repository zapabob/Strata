"""Evaluate the twelve public MathArena Apex 2025 problems using its non-strict grader."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime,timezone
from pathlib import Path
import subprocess
import sys
import time

import requests

from benchmark_generation import digest,local_server,read,save
from phase7_controls import immutable
from source import atomic_bytes,download


REPO="MathArena/apex_2025"
LIMIT=8192
SEED=20261125
HERE=Path(__file__).resolve().parent


def prepare(a):
    import pyarrow.parquet as pq
    import yaml
    from transformers import AutoTokenizer
    loc=a.root/"evaluation/apex2025"
    loc.mkdir(parents=True,exist_ok=True)
    data=loc/"questions.parquet"
    frozen=loc/"protocol.json"
    rev=read(frozen)["revision"] if frozen.exists() else requests.get("https://huggingface.co/api/datasets/"+REPO,timeout=20).json()["sha"]
    if not data.exists():atomic_bytes(data,download(f"https://huggingface.co/datasets/{REPO}/resolve/{rev}/data/train-00000-of-00001.parquet"))
    cfg_file=a.matharena/"configs/competitions/apex/apex_2025.yaml"
    cfg=yaml.safe_load(cfg_file.read_text(encoding="utf8"))
    data_rows=sorted(pq.read_table(data).to_pylist(),key=lambda r:r["problem_idx"])
    if [r["problem_idx"] for r in data_rows]!=list(range(1,13)) or cfg["strict_parsing"] is not False or cfg["dataset_path"]!=REPO or cfg["n_problems"]!=12:
        raise ValueError("The competition configuration or the question set differs")
    tok=AutoTokenizer.from_pretrained(a.root/"official",local_files_only=True)
    items={};gold={}
    for r in data_rows:
        i=str(r["problem_idx"])
        user=(cfg["instruction"]+"\n\n{problem}").format(problem=r["problem"])
        ids=tok.apply_chat_template([dict(role="user",content=user)],add_generation_prompt=True,reasoning_effort="high",
                                    tokenize=True,return_dict=False)
        if list(ids)!=tok.encode(tok.apply_chat_template([dict(role="user",content=user)],tokenize=False,
                    add_generation_prompt=True,reasoning_effort="high"),add_special_tokens=False):
            raise ValueError("Inconsistent assistant prompt boundary")
        items[i]=list(ids);gold[i]=str(r["answer"])
    immutable(loc/"gold.json",gold)
    immutable(frozen,dict(dataset=REPO,config="default",split="train",revision=rev,data_digest=digest(data),
              competition=digest(cfg_file),grader_revision=subprocess.check_output(["git","-C",str(a.matharena),"rev-parse","HEAD"],text=True).strip(),
              strict_parsing=False,reasoning_effort="high",temperature=0.,repeat_penalty=1.,seed=SEED,samples_per_problem=1,
              output_budget=LIMIT,stop="Natural end of assistant sampling, including the transition from reasoning to visible text",
              generation_template=digest(a.root/"official/chat_template.jinja"),items=items,
              published_percentage=34.4,published_settings="The model card reports a percentage. Its Apex-specific sampling parameters and repetition count were not established."))
    print("Frozen official competition inputs 1–12",flush=True)


def visible_and_reasoning(tokens,tokenizer,reason):
    sys.path.insert(0,str(HERE.parents[1]/"terminal/serve"))
    from inkling_dialect import InklingDialect
    dialect=InklingDialect()
    special={k:v.content for k,v in tokenizer.get_added_tokens_decoder().items() if v.special}
    out=[];start=0
    for i,tid in enumerate(tokens):
        if tid not in special:continue
        if i>start:out.extend(dialect.feed_token(tokenizer.decode(tokens[start:i],skip_special_tokens=False),is_special=False))
        out.extend(dialect.feed_token(special[tid],is_special=True));start=i+1
    if start<len(tokens):
        out.extend(dialect.feed_token(tokenizer.decode(tokens[start:],skip_special_tokens=False),is_special=False))
    out.extend(dialect.feed_channels(final=True,reason=reason))
    return {k:"".join(v for c,v in out if c==k) for k in ("content","reasoning")}


def generate(a):
    from tokenizers import Tokenizer
    loc=a.root/"evaluation/apex2025"
    spec=read(loc/"protocol.json")
    if spec["output_budget"]!=LIMIT:raise ValueError("Frozen budget differs")
    tok=Tokenizer.from_file(str(a.root/"official/tokenizer.json"))
    max_len=max(map(len,spec["items"].values()))
    capacity=((max_len+LIMIT+255)//256)*256
    for variant in ("official","ablated"):
        model=a.root/(variant+"-models")/("Inkling-2-Mini-PQ2_0-Baseline.gguf" if variant=="official" else "Inkling-2-Mini-PQ2_0-Balanced.gguf")
        work=loc/variant
        answers=work/"answers";answers.mkdir(parents=True,exist_ok=True)
        immutable(work/"identity.json",dict(protocol=digest(loc/"protocol.json"),engine=digest(a.binary),
                  manifest=digest(model.parent/"Inkling-2-Mini-PQ2_0-Balanced.manifest.json"),slots=a.slots,context_per_slot=capacity))
        pending=[k for k in spec["items"] if not (answers/(k+".json")).exists()]
        for start in range(0,len(pending),a.slots):
            group=pending[start:start+a.slots]
            for retry in range(8):
                dest=work/("server-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"))
                try:
                    with local_server(a.binary,model,dest,a.slots,a.slots*capacity) as base:
                        def one(k):
                            if (answers/(k+".json")).is_file():return
                            prompt=spec["items"][k]
                            resp=requests.post(base+"/completion",json=dict(prompt=prompt,temperature=0,seed=SEED,
                                n_predict=LIMIT,return_tokens=True,special=True,repeat_penalty=1.0,
                                cache_prompt=False,stream=False),timeout=(15,2700))
                            resp.raise_for_status();r=resp.json();ids=r["tokens"]
                            if r["truncated"] or r["tokens_evaluated"]!=len(prompt) or r["stop_type"] not in ("eos","limit") or not isinstance(ids,list):
                                raise ValueError("Prompt, token trajectory or natural stopping differs")
                            save(answers/(k+".json"),dict(problem_idx=int(k),output_ids=ids,
                                    **visible_and_reasoning(ids,tok,r["stop_type"]),stop=r["stop_type"],
                                    output_tokens=r["tokens_predicted"],input_tokens=len(prompt),timings=r["timings"]))
                        with ThreadPoolExecutor(a.slots) as pool:
                            for done in as_completed([pool.submit(one,k) for k in group]):done.result()
                    break
                except (RuntimeError,requests.RequestException):
                    receipt=dest/"measurement.json"
                    if retry==7 or not receipt.exists() or not read(receipt).get("protection_events"):raise
                    time.sleep(15)
            print(variant,"saved",len(list(answers.glob("*.json"))),"of 12",flush=True)
        grade(a)


def grade(a):
    from matharena.grader import extract_and_grade
    loc=a.root/"evaluation/apex2025"
    cfg=dict(strict_parsing=False)
    spec,gold=read(loc/"protocol.json"),read(loc/"gold.json")
    current=subprocess.check_output(["git","-C",str(a.matharena),"rev-parse","HEAD"],text=True).strip()
    if spec["grader_revision"]!=current:raise ValueError("Grader revision differs")
    import matharena.grader
    if not Path(matharena.grader.__file__).resolve().is_relative_to(a.matharena.resolve()):raise ValueError("Different MathArena source")
    for content,g,expected in ((r"\boxed{2}","2",True),(r"\boxed{3}","2",False),("","2",False)):
        if bool(extract_and_grade([dict(role="assistant",content=content)],20,g,cfg)[1])!=expected:raise ValueError("Apex grading control failed")
    models={}
    for variant in ("official","ablated"):
        scores={}
        for k in spec["items"]:
            f=loc/variant/"answers"/(k+".json")
            if not f.is_file():continue
            r=read(f)
            if r["problem_idx"]!=int(k) or r["input_tokens"]!=len(spec["items"][k]):raise ValueError("Apex item mismatch")
            ans,correct,w=extract_and_grade([dict(role="assistant",content=r["content"])],r["output_tokens"],gold[k],cfg,debug_info=k)
            scores[k]=dict(correct=bool(correct),extracted=None if ans is None else str(ans),warning=int(w),
                          truncated=r["stop"]=="limit",visible=bool(r["content"].strip()),tokens=r["output_tokens"])
        count=len(scores);n=sum(r["correct"] for r in scores.values())
        models[variant]=dict(generated=count,scored=count,correct=n,expected=12,truncated=sum(r["truncated"] for r in scores.values()),
                              unparseable=sum(r["extracted"] is None for r in scores.values()),items=scores,
                              observed_minus_publisher_pp=100*n/count-34.4 if count==12 else None)
    common=sorted(set(models["official"]["items"]) & set(models["ablated"]["items"]),key=int)
    deltas=[int(models["ablated"]["items"][k]["correct"])-int(models["official"]["items"][k]["correct"]) for k in common]
    save(loc/"scores.json",dict(programme="Independent matched local benchmark, one greedy attempt per model and problem",
         models=models,paired_items=common,heretic_minus_official_paired_pp=100*sum(deltas)/len(common) if common else None))


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("prepare","generate","grade"))
    for k in ("root","matharena","binary"):p.add_argument("--"+k,type=Path,required=k!="binary")
    p.add_argument("--slots",type=int,choices=range(1,9),default=4)
    a=p.parse_args()
    if a.action=="generate" and not a.binary:p.error("Provide the patched llama.cpp server")
    {"prepare":prepare,"generate":generate,"grade":grade}[a.action](a)
