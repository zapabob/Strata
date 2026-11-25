"""Exact target-specific and distributional attribution for identical teacher-forced tokens."""
import argparse
import math
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from benchmark_generation import save
from phase7_controls import matrix


def at_position(a, b, y):
    a=np.asarray(a,dtype=np.float64)
    b=np.asarray(b,dtype=np.float64)
    if a.ndim!=1 or b.ndim!=1 or len(a)<2 or len(b)<len(a) or not 0<=y<len(a):
        raise ValueError("Invalid target or incompatible vocabularies")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ArithmeticError("Non-finite logits")
    za,zb=logsumexp(a),logsumexp(b)
    lp,lq=a-za,b-zb
    p,q=np.exp(lp),np.exp(lq)
    dz=b[:len(a)]-a
    kl=float(p@(lp-lq[:len(a)]))
    residual=float(p@dz-dz[y])
    delta=float(lp[y]-lq[y])
    if not math.isclose(kl+residual,delta,rel_tol=1e-10,abs_tol=1e-10):
        raise ArithmeticError("KL and centred displacement do not reconstruct observed NLL")
    def metrics(z,l,prob):
        competitor=max(z[:y].max(initial=-np.inf),z[y+1:].max(initial=-np.inf))
        largest=np.partition(z,-2)[-2:]
        return dict(nll=float(-l[y]),rank=int(1+np.count_nonzero(z>z[y])),
                    target_margin=float(z[y]-competitor),argmax=int(np.argmax(z)),
                    winner_margin=float(largest.max()-largest.min()),entropy=float(-prob@l))
    ref,cand=metrics(a,lp,p),metrics(b,lq,q)
    return dict(reference=ref,candidate=cand,kl=kl,target_specific_nll=residual,nll_change=delta,
                raw_target_logit_change=float(dz[y]),mean_reference_logit_change=float(p@dz),
                log_partition_change=float(zb-za),entropy_change=cand["entropy"]-ref["entropy"],
                target_margin_change=cand["target_margin"]-ref["target_margin"],rank_change=cand["rank"]-ref["rank"])


def summarise(rows):
    fields=("kl","target_specific_nll","nll_change","entropy_change","target_margin_change","rank_change")
    return dict(tokens=len(rows),means={k:float(np.mean([r[k] for r in rows])) for k in fields},
                rank_improved=sum(r["rank_change"]<0 for r in rows),rank_worsened=sum(r["rank_change"]>0 for r in rows),
                target_top1_lost=sum(r["reference"]["rank"]==1 and r["candidate"]["rank"]>1 for r in rows),
                target_top1_gained=sum(r["candidate"]["rank"]==1 and r["reference"]["rank"]>1 for r in rows),
                argmax_agreement_count=sum(r["reference"]["argmax"]==r["candidate"]["argmax"] for r in rows))


def evaluate(root):
    from tokenizers import Tokenizer
    e=root/"evaluation"
    tok=Tokenizer.from_file(str(root/"official"/"tokenizer.json"))
    docs={}
    for src in sorted((e/"official-dynamic").glob("holdout-*.npz")):
        folder=e/"sm120-official"/"heldout-native-r1"
        with np.load(src) as z:
            ids=z["input_ids"][0]
            if not np.array_equal(ids,np.fromfile(folder/(src.stem+".i32"),dtype="<i4")):
                raise ValueError("Prediction positions differ")
            a=z["logits"]
            b=matrix(folder/(src.stem+".logits"),ids)
            rows=[]
            for i,y in enumerate(ids[1:]):
                rows.append(dict(position=i,target_id=int(y),token_piece=tok.id_to_token(int(y)),**at_position(a[i],b[i],y)))
        docs[src.stem]=dict(**summarise(rows),rows=rows)
    all_rows=[r for d in docs.values() for r in d["rows"]]
    overall=summarise(all_rows)
    result=dict(source="Published official NVFP4/MXFP8 weights, reconstructed BF16 Transformers forward",
                candidate="Official-source mixed PQ2_0 GGUF in patched llama.cpp, CUDA",
                rank_convention="1 + count of logits strictly larger than target",
                margin_convention="target logit minus highest competing logit",
                decomposition="delta_NLL = KL(p||q) + E_p[delta_z] - delta_z[target]",
                overall=overall,sequences=docs)
    dest=e/"phase8"
    dest.mkdir(exist_ok=True)
    save(dest/"official-token-attribution.json",result)
    print(overall)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    evaluate(parser.parse_args().root)
