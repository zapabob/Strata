"""Score every matched next token and bootstrap paired documents in the factorial study."""
import numpy as np
from scipy.special import logsumexp

from benchmark_generation import read,save
from benchmark_inkling2 import aggregate,score,trace
from expert_attention import ARMS,paired_effects,protocol


def per_token(a,b,ids):
    if a.ndim!=2 or a.shape[0]!=len(ids) or b.shape!=a.shape:
        raise ValueError("Factorial logits must cover the identical token positions and vocabulary")
    result=[]
    for i,y in enumerate(ids[1:]):
        ar=a[i].astype(np.float64)
        br=b[i].astype(np.float64)
        if not np.isfinite(ar).all() or not np.isfinite(br).all(): raise ArithmeticError("Non-finite logits")
        ap,bp=ar-logsumexp(ar),br-logsumexp(br)
        result.append(dict(position=i,target=int(y),source_nll=float(-ap[y]),nll=float(-bp[y]),
                           kl=float(np.dot(np.exp(ap),ap-bp)),source_argmax=int(np.argmax(ar)),
                           candidate_argmax=int(np.argmax(br))))
    return result


def scopes(rows):
    groups={"all":list(range(len(rows))),"legacy":list(range(4)),"added_japanese":[4,5,6]}
    for i,r in enumerate(rows): groups.setdefault(r["domain"],[]).append(i)
    return groups


def pool_visits(docs):
    result=[]
    for index in range(48):
        visits=[(d["tokens"],d["visits"][index]) for d in docs.values()]
        n=sum(w for w,_ in visits)
        layer,visit=visits[0][1]["layer"],visits[0][1]["visit"]
        if any((r["layer"],r["visit"])!=(layer,visit) for _,r in visits):raise ValueError("Incompatible visit order")
        row=dict(layer=layer,visit=visit,prediction_positions=n,
                 dynamic_router_overlap=sum(w*r["dynamic_router_overlap"] for w,r in visits)/n,
                 applied_top8_overlap=sum(w*r["applied_top8_overlap"] for w,r in visits)/n)
        for field in ("hidden","attention_output","expert_mixture"):
            s=[v if field=="hidden" else v[field] for _,v in visits]
            sa,sb,err,dot,values=(sum(x[k] for x in s) for k in
                 ("reference_sum_squares","candidate_sum_squares","sum_squared_error","dot","values"))
            row[field]=dict(relative_l2=float(np.sqrt(err/max(sa,1e-60))),
                      cosine=dot/max(float(np.sqrt(sa*sb)),1e-30),mse=err/values)
        for field in ("routing_margin","router_logit_margin"):
            row[field]={k:sum(w*r[field][k] for w,r in visits)/n for k in ("reference_mean","candidate_mean")}
        result.append(row)
    return result


def summarise_arms(loc,items,routing):
    directory=loc/routing
    source=loc/"dynamic/A"
    groups=scopes(items)
    records={}
    complete={}
    for label in ARMS:
        folder=directory/label
        if not (folder/"splits.json").is_file():continue
        dest=folder/"paired-scores.json"
        visit_file=folder/"visits-pooled.json"
        if not dest.is_file() or not visit_file.is_file():
            docs={}
            for i,r in enumerate(items):
                ref=source/f"holdout-{i}.npz"
                cand=folder/ref.name
                with np.load(ref) as a,np.load(cand) as b:
                    if not all(np.array_equal(z["input_ids"][0],r["ids"]) for z in (a,b)):
                        raise ValueError("The factorial token trajectory was altered")
                    tokens=per_token(a["logits"],b["logits"],r["ids"])
                values=trace(ref,cand,scored_only=True)
                if len(values["visits"])!=48 or any(not {"expert_mixture","attention_output","router_logit_margin","routing_margin"}<=v.keys() for v in values["visits"]):
                    raise ValueError("A physical layer visit or component observation is missing")
                values["positions"]=tokens
                docs[r["id"]]=values
            save(dest,docs)
            save(visit_file,pool_visits(docs))
        data=read(dest)
        records[label]={key:{k:v for k,v in row.items() if k not in ("visits","positions")} for key,row in data.items()}
        complete[label]={}
        for group,idx in groups.items():
            summary=aggregate({items[i]["id"]:records[label][items[i]["id"]] for i in idx})
            del summary["sequences"]
            complete[label][group]=summary
    outcome=dict(conditions=complete)
    if all(k in records for k in "ABCD"):
        outcome["factorial"]={}
        rows=[{k:records[k][r["id"]]["sum_candidate_nll"] for k in "ABCD"} for r in items]
        for name,idx in groups.items():
            outcome["factorial"][name]=paired_effects([rows[i] for i in idx],[len(items[i]["ids"])-1 for i in idx])
    if {"F","R_A","R_E","R_EA"}<=records.keys():
        outcome["reverse_restoration"]={}
        for name,idx in groups.items():
            ordered=("R_EA","R_A","R_E","F")
            rows=[{k:records[arm][items[i]["id"]]["sum_candidate_nll"] for k,arm in zip("ABCD",ordered,strict=True)} for i in idx]
            measured=paired_effects(rows,[len(items[i]["ids"])-1 for i in idx])
            measured["nll_recovered_restoring_experts_in_full"]=measured["effects"]["expert_given_attention"]
            measured["nll_recovered_restoring_attention_in_full"]=measured["effects"]["attention_given_expert"]
            outcome["reverse_restoration"][name]=measured
    return outcome


def independent_source(root,loc,rows):
    result={}
    for i,r in enumerate(rows):
        paths=[root/"evaluation/official-dynamic"/f"holdout-{i}.npz"] if i<4 else []
        paths.extend([root/"evaluation/phase7/official/core/reference"/f"holdout-{i}.npz",
                      root/"evaluation/phase10/dynamic/A"/f"holdout-{i}.npz"])
        candidate=loc/"dynamic/A"/f"holdout-{i}.npz"
        if not candidate.exists():continue
        ref=next((p for p in paths if p.exists() and not p.samefile(candidate)),None)
        if ref is None:continue
        with np.load(ref) as a,np.load(candidate) as b:
            if not all(np.array_equal(z["input_ids"][0],r["ids"]) for z in (a,b)):raise ValueError("Source trajectory differs")
            result[r["id"]]=score(a["logits"],b["logits"],r["ids"])
    if len(result)!=len(rows):
        return dict(compared_documents=len(result),complete=False,observed=aggregate(result) if result else None)
    extra={r["id"]:result[r["id"]] for r in rows[4:]}
    def passes(s):return s["top1_agreement"]==1. and s["mean_kl"]<1e-5 and abs(s["delta_nll"])<.001
    total=aggregate(result);new=aggregate(extra)
    return dict(complete=True,all=total,added_japanese=new,
                accepted=passes(total) and passes(new) and all(passes(aggregate({k:v})) for k,v in extra.items()))


def report(root,profile="serial"):
    loc,rows,_,manifest=protocol(root)
    out={"matched_source":"Published NVFP4/MXFP8 reconstructed for BF16 in Transformers, eager attention",
         "uncertainty":"Intervals resample whole documents. The added Japanese set has three independent documents.",
         "groups":{k:[rows[i]["id"] for i in v] for k,v in scopes(rows).items()}}
    if profile not in ("matched","serial","single"):raise ValueError("Unknown reference-graph profile")
    work=loc/profile if profile!="single" else loc
    for k in ("dynamic","frozen"):
        if (work/"dynamic/A/splits.json").exists():out[k]=summarise_arms(work,rows,k)
    parity=work/"expanded-source-parity.json"
    out["expanded_source_replay_accepted"]=read(parity)["source_reproduction_accepted"] if parity.exists() else None
    out["independent_source"]=independent_source(root,work,rows)
    out["eligible_for_interpretation"]=bool(out["expanded_source_replay_accepted"] and
        out["independent_source"].get("accepted") and "factorial" in out.get("dynamic",{}))
    out["condition_batching"]={"matched":"four conditions on the batch axis","single":"one condition per traversal",
                         "serial":"independent calls at the original minibatch shapes, sharing physical weight reads"}[profile]
    tensors=read(manifest)["tensors"]
    out["diagnostic_restoration_storage"]={}
    for name,typ,effect in (("experts","PQ2_0","expert_given_attention"),("attention","Q4_K","attention_given_expert")):
        ts=[t for t in tensors if t["type"]==typ]
        count=sum(int(np.prod(t["shape"])) for t in ts)
        added=2*count-sum(t["bytes"] for t in ts)
        entry=dict(parameters=count,bf16_extra_payload_bytes=added,extra_bytes_written_to_deployment=0,
                   fitting_steps=0,scope="Hypothetical BF16 payload cost of the full-component diagnostic restoration")
        reverse=out.get("dynamic",{}).get("reverse_restoration",{}).get("all")
        if reverse:
            gain=reverse["effects"][effect]
            entry.update(validation_role="held-out attribution",nll_recovery_per_additional_bf16_byte=gain/added,
                         nll_recovery_per_additional_bf16_gib=gain*2**30/added)
        out["diagnostic_restoration_storage"][name]=entry
    out["execution_receipts"]=[]
    from datetime import datetime
    for receipt in sorted(work.glob("*/**/measurement.json")):
        s=read(receipt)
        if s["status"]=="exited" and s["returncode"]==0:
            elapsed=(datetime.fromisoformat(s["finished_utc"])-datetime.fromisoformat(s["started_utc"])).total_seconds()
            out["execution_receipts"].append(dict(run=str(receipt.parent.relative_to(work)),elapsed_seconds=elapsed,
                  peak_device_bytes=s["peak_device_used_bytes"]))
    work.mkdir(exist_ok=True)
    save(work/"factorial-results.json",out)
    return out
