"""Categorical Fisher geometry and termination statistics on matched source and candidate logits."""
import argparse
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from benchmark_generation import save


def fisher_action(p, tangent):
    centred = tangent - np.sum(p*tangent, axis=-1, keepdims=True)
    return p*centred


def row_metrics(ref, cand, event):
    a, b = np.asarray(ref,dtype=np.float64), np.asarray(cand,dtype=np.float64)
    if a.ndim!=1 or b.ndim!=1 or len(b)<len(a) or not (0<=event<len(a)):
        raise ValueError("Incompatible vocabulary or event")
    if not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ArithmeticError("Non-finite logits")
    la,lb=a-logsumexp(a),b-logsumexp(b)
    p=np.exp(la)
    dz=b[:len(a)]-a
    centred=dz-np.dot(p,dz)
    quadratic=float(np.dot(p,centred*centred)/2)
    kl=float(np.dot(p,la-lb[:len(a)]))
    extra=float(-logsumexp(lb[:len(a)]))
    def event_stats(l):
        rest=np.concatenate((l[:event],l[event+1:]))
        return float(np.exp(l[event])),float(l[event]-logsumexp(rest)),float(logsumexp(rest))
    pa,ma,ra=event_stats(la)
    pb,mb,rb=event_stats(lb)
    bernoulli_kl=float(pa*(la[event]-lb[event])+(1-pa)*(ra-rb))
    return dict(kl_nats=kl,quadratic_kl_nats=quadratic,support_penalty_nats=extra,
                approximation_minus_observed_nats=quadratic+extra-kl,reference_event_p=pa,
                candidate_event_p=pb,reference_event_log_odds=ma,candidate_event_log_odds=mb,
                termination_bernoulli_kl_nats=bernoulli_kl)


def gauss_newton_vector(forward, parameters, direction):
    """Return G-transpose F G v for shared physical weights without forming G or F.

    forward must reuse the same parameters at every visit, use fixed token inputs,
    and return one vector of logits or a batch of equally weighted logit vectors.
    """
    import torch
    from torch.func import jvp, vjp
    z,u=jvp(forward,parameters,direction)
    p=z.detach().softmax(dim=-1)
    centred=u-(p*u).sum(dim=-1,keepdim=True)
    cotangent=p*centred/(z.numel()//z.shape[-1])
    _,pullback=vjp(forward,*parameters)
    return pullback(cotangent.detach())


def evaluate(root):
    from phase7_controls import matrix
    from tokenizers import Tokenizer
    source=root/"evaluation"/"official-dynamic"
    candidate=root/"evaluation"/"sm120-official"/"heldout-native-r1"
    tok=Tokenizer.from_file(str(root/"official"/"tokenizer.json"))
    event=tok.token_to_id("<|content_model_end_sampling|>")
    docs={}
    for path in sorted(source.glob("holdout-*.npz")):
        with np.load(path) as z:
            tokens=z["input_ids"][0]
            if not np.array_equal(tokens,np.fromfile(candidate/(path.stem+".i32"),dtype="<i4")):
                raise ValueError("Mismatched token trajectories")
            a=z["logits"]
            b=matrix(candidate/(path.stem+".logits"),tokens)
            docs[path.stem]=[row_metrics(a[i],b[i],event) for i in range(len(tokens)-1)]
    rows=[r for v in docs.values() for r in v]
    means={k:float(np.mean([r[k] for r in rows])) for k in rows[0]}
    save(root/"evaluation"/"phase7"/"fisher-observed-logits.json",dict(
         reference="Official published source reconstructed for BF16 calculation in Transformers",
         candidate="Full mixed PQ2_0 GGUF with patched llama.cpp on SM120",
         scope="Actual output-logit displacement on teacher-forced prose; the weight Jacobian and free-reasoning termination are separate experiments.",
         event_id=event,tokens=len(rows),means=means,sequences=docs))
    print(len(rows),"next-token positions, mean measured KL",means["kl_nats"],"local quadratic",means["quadratic_kl_nats"])


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,required=True)
    evaluate(parser.parse_args().root)
