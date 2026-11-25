"""Paired, zero-shot MMLU elementary mathematics evaluation on identical token IDs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

import numpy as np

from source import atomic_bytes, await_capacity, download


def save(path, data):
    atomic_bytes(path, json.dumps(data, indent=2, allow_nan=False).encode())


def prepare(args):
    import pyarrow.parquet as pq
    from transformers import AutoTokenizer
    import requests

    folder = args.output.parent
    folder.mkdir(parents=True, exist_ok=True)
    dataset = "cais/mmlu"
    table_path = "elementary_mathematics/test-00000-of-00001.parquet"
    revision = args.revision
    if not revision:
        response = requests.get(f"https://huggingface.co/api/datasets/{dataset}", timeout=30)
        response.raise_for_status()
        revision = response.json()["sha"]
    source = f"https://huggingface.co/datasets/{dataset}/resolve/{revision}/{table_path}"
    raw = download(source)
    dataset_path = folder / "elementary_mathematics-test.parquet"
    atomic_bytes(dataset_path, raw)
    table = pq.read_table(dataset_path).to_pylist()
    indices = np.random.default_rng(args.seed).choice(len(table), args.count, replace=False)
    tok = AutoTokenizer.from_pretrained(args.source, local_files_only=True)
    letters = "ABCD"
    label_ids = [tok.encode(" " + x, add_special_tokens=False) for x in letters]
    if any(len(x) != 1 for x in label_ids):
        raise ValueError("The four answer labels must each occupy one token")
    cases = []
    for index in indices:
        row = table[int(index)]
        prompt = ("The following are multiple choice questions (with answers) about elementary mathematics.\n\n"
                  + row["question"] + "\n" + "\n".join(f"{l}. {v}" for l, v in zip(letters, row["choices"], strict=True))
                  + "\nAnswer:")
        tokens = tok.encode(prompt, add_special_tokens=False)
        for label, ids in zip(letters, label_ids):
            if tok.encode(prompt + " " + label, add_special_tokens=False) != tokens + ids:
                raise ValueError("Answer tokenisation depends on the label boundary")
        cases.append(dict(row=int(index), tokens=tokens, answer=int(row["answer"])))
    save(args.output, dict(dataset=dataset, subject="elementary_mathematics", split="test",
         revision=revision, parquet_sha256=hashlib.sha256(raw).hexdigest(), seed=args.seed,
         population=len(table), shots=0, label_token_ids=[x[0] for x in label_ids], items=cases))


def read_logits(path, row):
    with path.open("rb") as f:
        shape=np.fromfile(f, dtype="<i4", count=2)
        if len(shape)!=2 or shape[0]!=1 or shape[1]<=0:
            raise ValueError(f"Wrong native logit dimensions for item {row}")
        data=np.fromfile(f, dtype="<f4")
    if len(data)!=shape[1] or not np.isfinite(data).all():
        raise ValueError(f"Incomplete or non-finite native logits for item {row}")
    return data


def evaluate(args):
    spec=json.loads(args.selection.read_bytes())
    folder=args.output.parent
    folder.mkdir(parents=True,exist_ok=True)
    items=spec["items"]
    label_ids=spec["label_token_ids"]
    rows={}
    def record(row, values):
        values=np.asarray(values,dtype=np.float64)
        if values.shape!=(4,) or not np.isfinite(values).all():
            raise ValueError("Four finite answer logits are required")
        choice=int(values.argmax())
        rows[str(row["row"])]=dict(prediction=choice,answer=row["answer"],
            correct=choice==row["answer"],choice_logits=values.tolist(),tokens=len(row["tokens"]))
    if args.model:
        ext=".exe" if os.name=="nt" else ""
        cmd=[str(args.bin/("inkling-logits"+ext)),"--last","--gpu-layers",str(args.gpu_layers),str(args.model)]
        for row in items:
            case=str(row["row"])
            inp=folder/(case+".i32")
            np.asarray(row["tokens"],dtype="<i4").tofile(inp)
            cmd.extend((str(inp),str(folder/(case+".f32"))))
        if os.name=="nt":
            from sm120_native import run
            run(folder/"native-run",cmd,args.admit_mib,900,7200)
        else:
            with (folder/"native.log").open("w", encoding="utf8") as log:
                subprocess.run(cmd,check=True,stdout=log,stderr=log)
        for row in items:
            logits=read_logits(folder/(str(row["row"])+".f32"),row["row"])
            record(row,logits[label_ids])
        backend="native GGUF CUDA"
        source=str(args.model)
    else:
        import torch
        from infer import Experts, OfficialSafetensors, Safetensors, load_graph

        if not args.source:
            raise ValueError("Provide --model and --bin, or a source checkpoint")
        identity=dict(revision=json.loads((args.source/"source.json").read_bytes())["revision"],
                      selection=hashlib.sha256(args.selection.read_bytes()).hexdigest(),
                      batch_size=args.batch,original=args.original)
        progress=folder/"reference-progress.json"
        if progress.exists():
            saved=json.loads(progress.read_bytes())
            if saved["identity"]!=identity:
                raise ValueError("The existing mathematics results have a different source or selection")
            rows.update(saved["rows"])
        store=(OfficialSafetensors if args.original else Safetensors)(args.source)
        model=load_graph(store,"cuda",False)
        experts=Experts(store,args.cache_gib,"cuda")
        experts.install(model)
        backend="Transformers reconstructed BF16" if args.original else "Transformers BF16"
        source=store.assets.as_posix()
        ordered=sorted(items,key=lambda x:len(x["tokens"]))
        with torch.inference_mode():
            complete=args.heldout_reference_dir/"source.json" if args.heldout_reference_dir else None
            text_identity = dict(identity, texts=hashlib.sha256(args.texts.read_bytes()).hexdigest())
            if complete and complete.is_file() and json.loads(complete.read_bytes())!=text_identity:
                raise ValueError("Existing held-out source identity differs")
            if complete and not complete.is_file():
                from transformers import AutoTokenizer
                from source import atomic_bytes
                from io import BytesIO

                texts=json.loads(args.texts.read_bytes())
                if not texts["holdout"] or set(texts["holdout"]) & set(texts["calibration"]):
                    raise ValueError("The evaluation texts must be independent of calibration")
                tokenizer=AutoTokenizer.from_pretrained(store.assets,local_files_only=True)
                seq=[tokenizer.encode(t,add_special_tokens=False) for t in texts["holdout"]]
                args.heldout_reference_dir.mkdir(parents=True,exist_ok=True)
                pending=[]
                for i,ids in enumerate(seq):
                    path=args.heldout_reference_dir/f"holdout-{i}.npz"
                    if path.is_file():
                        with np.load(path) as archive:
                            if not np.array_equal(archive["input_ids"][0],ids):
                                raise ValueError("Saved reference token sequence differs")
                    else:
                        pending.append(i)
                for start in range(0,len(pending),args.text_batch):
                    group=pending[start:start+args.text_batch]
                    limit=max(len(seq[i]) for i in group)
                    inputs=torch.tensor([seq[i]+[0]*(limit-len(seq[i])) for i in group],device="cuda")
                    values=model(input_ids=inputs,attention_mask=torch.ones_like(inputs),use_cache=False).logits
                    for row,i in enumerate(group):
                        ids=seq[i]
                        logits=values[row,:len(ids)].float().cpu().numpy()
                        if not np.isfinite(logits).all():
                            raise ArithmeticError("Non-finite held-out reference logits")
                        buffer=BytesIO()
                        np.savez(buffer,input_ids=np.array([ids],np.int64),logits=logits)
                        atomic_bytes(args.heldout_reference_dir/f"holdout-{i}.npz",buffer.getvalue())
                        del buffer, logits
                    del values
                    print(f"Saved held-out sequences {group} from the matching source model",flush=True)
                save(complete,text_identity)
            starts=list(range(0,len(ordered),args.batch))
            starts.sort(key=lambda start: not any(r["row"]==180 for r in ordered[start:start+args.batch]))
            for start in starts:
                await_capacity(folder,0)
                group=ordered[start:start+args.batch]
                if all(str(row["row"]) in rows for row in group):
                    continue
                positions=[len(row["tokens"])-1 for row in group]
                end=max(positions)+1
                # Padding follows the scored position of every causal prefix.
                ids=[r["tokens"]+[0]*(end-len(r["tokens"])) for r in group]
                inputs=torch.tensor(ids,device="cuda",dtype=torch.long)
                kept=sorted(set(positions))
                logits=model(input_ids=inputs,attention_mask=torch.ones_like(inputs),
                    use_cache=False,logits_to_keep=torch.tensor(kept,device="cuda")).logits
                for j,row in enumerate(group):
                    record(row,logits[j,kept.index(positions[j]),label_ids].float().cpu().numpy())
                save(progress,dict(identity=identity,rows=rows))
                print(f"Scored {len(rows)}/{len(items)} source questions",flush=True)
    correct=sum(x["correct"] for x in rows.values())
    save(args.output,dict(dataset=spec["dataset"],subject=spec["subject"],split=spec["split"],
        seed=spec["seed"],count=len(rows),correct=correct,accuracy=correct/len(rows),backend=backend,
        source=source,shots=0,selection_sha256=hashlib.sha256(args.selection.read_bytes()).hexdigest(),
        score="argmax over the next-token logits for space-prefixed A/B/C/D",items=rows))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare","score"))
    for key in ("source","model","bin","selection","output"):
        parser.add_argument("--"+key,type=Path,required=key=="output")
    parser.add_argument("--count",type=int,default=32)
    parser.add_argument("--seed",type=int,default=20261125)
    parser.add_argument("--revision")
    parser.add_argument("--batch",type=int,default=8)
    parser.add_argument("--text-batch",type=int,default=3)
    parser.add_argument("--cache-gib",type=float,default=1.5)
    parser.add_argument("--gpu-layers",type=int,default=99)
    parser.add_argument("--admit-mib",type=int,default=11300)
    parser.add_argument("--heldout-reference-dir",type=Path)
    parser.add_argument("--texts",type=Path,default=Path(__file__).with_name("calibration_text.json"))
    parser.add_argument("--original",action="store_true")
    args=parser.parse_args()
    (prepare if args.action=="prepare" else evaluate)(args)
