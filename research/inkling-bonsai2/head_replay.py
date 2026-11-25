"""Isolate Q6_K output-head error using saved recurrent states and verify the source readout."""
import argparse
from pathlib import Path
import sys
import time

import numpy as np
from scipy.special import softmax

from benchmark_generation import read,save
from benchmark_inkling2 import aggregate,score
from official_weights import Original


def from_bfloat(bits):
    return (bits.astype(np.uint32)<<16).view(np.float32)


def bfloat(x):
    u=np.asarray(x,dtype=np.float32).view(np.uint32)
    return from_bfloat(((u+0x7fff+((u>>16)&1))>>16).astype(np.uint16))


def rms(x,eps):
    return x/np.sqrt(np.mean(x*x,axis=-1,keepdims=True,dtype=np.float32)+eps)


def evaluate(root,llama,traces=None,output=None):
    sys.path.insert(0,str(llama/"gguf-py"))
    import gguf
    started=time.monotonic()
    e=root/"evaluation"
    o=Original(root/"official")
    model=root/"official-models/Inkling-2-Mini-PQ2_0-Baseline.gguf"
    spec=read(model.parent/"Inkling-2-Mini-PQ2_0-Balanced.manifest.json")
    layers=read(root/"official/config.json")["text_config"]
    width=layers["hidden_size"]
    eps=layers["rms_norm_eps"]
    vocab=layers["unpadded_vocab_size"]
    cap=layers["final_logit_softcapping"]
    def raw(key,begin=0,count=None):
        x=o.read(key,begin,count)
        return from_bfloat(x) if o.header[key]["dtype"]=="BF16" else x.astype(np.float32)
    embed_norm=raw("model.llm.embed_norm.weight")
    out_norm=raw("model.llm.norm.weight")
    query=raw("model.llm.attn_res.output_query")
    control={}
    offsets={}
    ids={}
    all_hidden=[]
    refs=sorted((traces or e/"official-dynamic").glob("holdout-*.npz"))
    protocol=None
    if traces is not None:
        protocol=read(e/"phase7/protocol.json")
        members={r["id"]:r for r in protocol["entries"]}
        expected=[f"holdout-{i}" for i in range(len(protocol["core"]))]
        if [f.stem for f in refs]!=expected: raise ValueError("Incomplete source-parity corpus")
    loop=layers["loop_config"]
    stride=layers["n_layers_per_attn_res_block"]
    for f in refs:
        with np.load(f) as z:
            tokens=z["input_ids"][0]
            if protocol and not np.array_equal(tokens,members[protocol["core"][int(f.stem.split("-")[-1])]]["ids"]):
                raise ValueError("Source parity input or positions differ")
            ids[f.stem]=tokens
            embeds=np.stack([raw("model.llm.embed.weight",int(t)*width,width) for t in tokens])
            states=[bfloat(rms(embeds,eps)*embed_norm)]
            for boundary in range(stride,layers["num_hidden_layers"]+1,stride):
                prev=boundary-1
                visit=loop["num_passes"]-1 if loop["core_start"]<=prev<loop["core_end"] else 0
                states.append(from_bfloat(z[f"l{prev}.v{visit}.hidden"][0]))
            block=rms(np.stack(states,axis=1),1e-6)
            mixture=softmax((block@query)/np.sqrt(np.float32(width)),axis=1)
            h=bfloat(rms((mixture[:,:,None]*block).sum(axis=1),eps)*out_norm)
            offsets[f.stem]=sum(len(x) for x in all_hidden)
            all_hidden.append(h)
    h=np.concatenate(all_hidden)
    shape=(len(h),vocab)
    oracle=np.empty(shape,dtype=np.float32)
    changed=np.empty_like(oracle)
    t=next(t for t in spec["tensors"] if t["name"]=="output.weight")
    if t["type"]!="Q6_K" or t["shape"][1]!=width: raise ValueError("Unexpected head layout")
    row_bytes=t["bytes"]//t["shape"][0]
    with model.open("rb") as handle:
        handle.seek(t["offset"])
        for i in range(0,vocab,512):
            n=min(512,vocab-i)
            ref=raw(t["raw"],i*width,n*width).reshape(n,width)
            data=np.fromfile(handle,dtype=np.uint8,count=n*row_bytes).reshape(n,row_bytes)
            candidate=bfloat(gguf.quants.dequantize(data,gguf.GGMLQuantizationType.Q6_K))
            for w,target in ((ref,oracle),(candidate,changed)):
                target[:,i:i+n]=np.tanh(bfloat(h@w.T)/cap)*cap
    quant={}
    attribution={}
    for f in refs:
        k=f.stem
        sl=slice(offsets[k],offsets[k]+len(ids[k]))
        with np.load(f) as z:
            expected=z["logits"]
            control[k]=score(expected,oracle[sl],ids[k])
            control[k]["max_abs_logit"]=float(np.abs(expected-oracle[sl]).max())
            quant[k]=score(expected,changed[sl],ids[k])
            attribution[k]=score(oracle[sl],changed[sl],ids[k])
    def accepted(check):
        return check["top1_agreement"]==1. and abs(check["delta_nll"])<.001 and check["mean_kl"]<1e-5
    check=aggregate(control)
    passed=accepted(check)
    result=dict(engine="CPU float32 streamed replay of the saved RTX BF16 residual states; linear products rounded to BF16",
                condition="Source graph with only the Q6_K output head substituted",
                source_reproduction=check,source_reproduction_accepted=passed,exact_paired_head_effect=aggregate(attribution),
                from_recorded_source=aggregate(quant),seconds=time.monotonic()-started,
                source_parameter_bytes=2*int(np.prod(t["shape"])),quantised_parameter_bytes=t["bytes"])
    if protocol:
        ixs=[f"holdout-{i}" for i in (4,5,6)]
        extra=aggregate({k:control[k] for k in ixs})
        individually=all(accepted(aggregate({k:control[k]})) for k in ixs)
        if extra["total_tokens"]!=139 or check["total_tokens"]!=260:
            raise ValueError("The expanded parity denominator is incomplete")
        result.update(added_japanese=extra,added_japanese_parity_accepted=accepted(extra) and individually,
                      source_reproduction_accepted=passed and accepted(extra) and individually)
    save(output or e/"phase8/output-head-only.json",result)
    print("Source replay accepted",passed,"KL",check["mean_kl"],"delta NLL",check["delta_nll"],
          "top1",check["top1_agreement"],"head-only delta NLL",result["exact_paired_head_effect"]["delta_nll"])


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("root","llama","traces","output"):p.add_argument("--"+key,type=Path,required=key in ("root","llama"))
    args=p.parse_args()
    evaluate(args.root,args.llama,args.traces,args.output)
