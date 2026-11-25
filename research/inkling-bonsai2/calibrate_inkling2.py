"""Capture actual per-expert route, activation and loop traces from disjoint text splits."""

import argparse
import hashlib
import json
from contextlib import ExitStack
from collections import Counter
from pathlib import Path

import numpy as np
import torch

from infer import Experts, OfficialSafetensors, Safetensors, load_graph
from source import atomic_bytes, await_capacity


def bits(x):
    return x.detach().to(torch.bfloat16).contiguous().view(torch.uint16).cpu().numpy().copy()


def floats(u):
    return (u.astype(np.uint32) << 16).view(np.float32)

def frozen_batch(traces, width):
    merged={}
    for key in traces[0].files:
        if key.endswith((".ids",".weights")):
            arrays=[trace[key] for trace in traces]
            merged[key]=np.concatenate([np.pad(a,((0,width-len(a)),(0,0)),mode="edge") for a in arrays])
    return merged


def split_observations(data,index,width,length):
    start=index*width
    stop=start+length
    result={}
    for key,values in data.items():
        if key.endswith((".hidden",".attention_output",".expert_mixture")):
            result[key]=values[index:index+1,:length]
        elif key.endswith((".router_logit_margin",".routing_margin")):
            result[key]=values.reshape(-1)[start:stop]
        elif key.endswith(".counts"):
            ids=data[key.removesuffix(".counts")+".ids"][start:stop]
            result[key]=np.bincount(ids.ravel(),minlength=128)
        elif key.endswith(".down_input"):
            prefix,expert=key.removesuffix(".down_input").rsplit(".e",1)
            routed=np.where(data[prefix+".ids"]==int(expert))[0]
            rows=(routed>=start)&(routed<stop)
            if len(rows)!=len(values):
                raise ValueError("Routed activations differ from the original slot order")
            if rows.any():
                result[key]=values[rows]
        elif key.endswith((".gate_input",".ids",".dynamic_ids",".weights",".router_logits")):
            result[key]=values.reshape(-1,values.shape[-1])[start:stop]
        else:
            raise ValueError("Unexpected activation field "+key)
    return result


def capture_batch(model,experts,group,args,expected):
    names, ids_list=zip(*group)
    width=max(map(len,ids_list))
    # The causal model cannot use a right-hand filler token to predict earlier positions.
    inputs=torch.as_tensor(np.stack([np.pad(ids,(0,width-len(ids))) for ids in ids_list]),device="cuda")
    with ExitStack() as cleanup:
        frozen=None
        if args.frozen:
            traces=[cleanup.enter_context(np.load(args.frozen/(name+".npz"))) for name in names]
            for ids,tr in zip(ids_list,traces):
                if not np.array_equal(ids,tr["input_ids"][0]):
                    raise ValueError("Frozen routes have a different token sequence")
            frozen=frozen_batch(traces,width)
        obs=Observer(frozen,compact=getattr(args,"compact_traces",False))
        experts.install(model,obs)
        for j,layer in enumerate(model.model.language_model.layers):
            cleanup.callback(layer.register_forward_hook(obs.layer_hook(j)).remove)
            cleanup.callback(layer.mlp.gate.register_forward_hook(obs.router_hook(j)).remove)
            cleanup.callback(layer.self_attn.register_forward_hook(obs.output_hook(j,True)).remove)
            cleanup.callback(layer.mlp.register_forward_hook(obs.output_hook(j,False)).remove)
        print("Evaluating "+", ".join(f"{n} ({len(i)} tokens)" for n,i in group),flush=True)
        result=model(input_ids=inputs,attention_mask=torch.ones_like(inputs),use_cache=False)
    if [obs.visits[j] for j in range(len(expected))]!=expected:
        raise ValueError(f"Unexpected physical visits {obs.visits}")
    for i,(name,ids) in enumerate(group):
        data=split_observations(obs.data,i,width,len(ids))
        logits=result.logits[i,:len(ids)].detach().float().cpu().numpy()
        if not np.isfinite(logits).all():
            raise ArithmeticError("Non-finite capture logits")
        data.update(input_ids=ids[None,:],logits=logits)
        dest=args.output/(name+".npz")
        tmp=dest.with_suffix(".partial")
        with tmp.open("wb") as f:
            np.savez(f,**data)
        tmp.replace(dest)
        print(f"Committed {name} with {sum(expected)} layer visits",flush=True)


class Observer:
    def __init__(self, frozen=None, compact=False):
        self.frozen, self.visits, self.data = frozen, Counter(), {}
        self.compact=compact

    def begin(self, layer, x, ids, weights):
        visit = self.visits[layer]
        self.visits[layer] += 1
        prefix = f"l{layer}.v{visit}"
        if not self.compact: self.data[prefix+".gate_input"] = bits(x)
        self.data[prefix+".dynamic_ids"] = ids.to(torch.int16).cpu().numpy()
        if self.frozen is not None:
            ids = torch.as_tensor(self.frozen[prefix+".ids"].astype(np.int64), device=x.device)
            weights = torch.as_tensor(self.frozen[prefix+".weights"], device=x.device, dtype=weights.dtype)
        self.data[prefix+".ids"] = ids.to(torch.int16).cpu().numpy()
        self.data[prefix+".weights"] = weights.float().cpu().numpy()
        self.data[prefix+".counts"] = np.bincount(self.data[prefix+".ids"].ravel(), minlength=128)
        return ids, weights

    def down(self, layer, expert, tokens, slots, x):
        if self.compact: return
        prefix = f"l{layer}.v{self.visits[layer]-1}.e{expert}"
        self.data[prefix+".down_input"] = bits(x)

    def layer_hook(self, layer):
        def capture(module, args, output):
            self.data[f"l{layer}.v{self.visits[layer]-1}.hidden"] = bits(output)
            if self.compact and layer in (5,11,17,23):
                print(f"Captured physical layer {layer}, visit {self.visits[layer]}",flush=True)
        return capture

    def router_hook(self,layer):
        def capture(module,args,output):
            prefix=f"l{layer}.v{self.visits[layer]}"
            logits=output[0].detach().float()
            self.data[prefix+".router_logits"]=logits.cpu().numpy()
            for key,values in (("router_logit_margin",logits),
                               ("routing_margin",module.score_fn(logits)+module.e_score_correction_bias)):
                ranked=values.topk(module.top_k+1,sorted=True).values
                self.data[prefix+"."+key]=(ranked[...,-2]-ranked[...,-1]).cpu().numpy()
        return capture

    def output_hook(self,layer,attention):
        def capture(module,args,output):
            visit=self.visits[layer] if attention else self.visits[layer]-1
            key="attention_output" if attention else "expert_mixture"
            self.data[f"l{layer}.v{visit}.{key}"]=bits(output[0] if attention else output)
        return capture


def main(args):
    from transformers import AutoTokenizer
    texts = json.loads(args.texts.read_bytes())
    if set(texts) != {"calibration","holdout"} or not all(texts.values()):
        raise ValueError("Provide separate, non-empty calibration and holdout texts")
    token_sets = {}
    if args.weights_mode:
        from decoded_reference import DecodedOfficial
        if not (args.original and args.gguf and args.manifest and args.llama):
            raise ValueError("A source checkpoint, GGUF, manifest and llama.cpp tree are required for attribution")
        restored=[tuple(map(int,key.split(":"))) for key in args.restore]
        if any(len(pair)!=2 or not 0<=pair[0]<24 or not 0<=pair[1]<128 for pair in restored):
            raise ValueError("Restoration expects physical-layer:expert pairs")
        torch.set_float32_matmul_precision("highest")
        store=DecodedOfficial(args.source,args.gguf,args.manifest,args.llama,args.weights_mode,restored)
    else:
        store = (OfficialSafetensors if args.original else Safetensors)(args.source)
    args.output.mkdir(parents=True, exist_ok=True)
    await_capacity(args.output, 0)
    model = load_graph(store, "cuda", False)
    if args.gguf and not args.weights_mode:
        from packed_replay import PackedReplay
        experts=PackedReplay(args.gguf,args.llama,args.kernels,args.cache_gib)
    else:
        experts = Experts(store,args.cache_gib,"cuda")
    cfg = model.config.text_config
    tok=AutoTokenizer.from_pretrained(store.assets,local_files_only=True)
    expected=[cfg.loop_num_passes if cfg.loop_layer_index_start<=j<cfg.loop_layer_index_end else 1
              for j in range(cfg.num_hidden_layers)]
    with torch.inference_mode():
        for split, examples in texts.items():
            pending=[]
            for i, prompt in enumerate(examples):
                name = f"{split}-{i}"
                dest = args.output / (name+".npz")
                ids=np.asarray(tok.encode(prompt,add_special_tokens=False),dtype=np.int64)[None,:]
                token_key = hashlib.sha256(ids.tobytes()).hexdigest()
                if token_key in token_sets:
                    raise ValueError("Repeated examples across calibration or holdout")
                token_sets[token_key] = split
                if args.split and split!=args.split:continue
                if dest.exists():
                    with np.load(dest) as old:
                        if not np.array_equal(old["input_ids"], ids):
                            raise ValueError("Recorded inputs differ")
                    continue
                pending.append((name,ids[0]))
            for start in range(0,len(pending),args.sequence_batch):
                capture_batch(model,experts,pending[start:start+args.sequence_batch],args,expected)
    atomic_bytes(args.output/"splits.json", json.dumps(dict(split_sha256=token_sets, source=str(args.source),
                 source_family="original" if args.original else "ablated", routing="frozen" if args.frozen else "dynamic",
                 activation_storage="exact BF16 bits", expert_gguf=str(args.gguf) if args.gguf else None,
                 cache_gib=args.cache_gib,sequence_batch=args.sequence_batch,
                decoded_weight_condition=args.weights_mode,restored=args.restore,
                recorded_sequences=sorted(p.stem for p in args.output.glob("*.npz"))),indent=2).encode())


def expert_activations(path, layer, expert, proj, split):
    files=sorted(Path(path).glob(split+"-*.npz"))
    if not files:
        raise ValueError(f"No completed {split} capture")
    visits={}
    for file in files:
        with np.load(file) as trace:
            for v in range(3):
                base=f"l{layer}.v{v}"
                if base+".ids" not in trace:
                    continue
                ids=trace[base+".ids"]
                tokens, _=np.where(ids==expert)
                if len(tokens):
                    acts=(trace[base+".gate_input"][tokens] if proj=="w13" else trace[base+f".e{expert}.down_input"])
                    visits.setdefault(v,[]).append(floats(acts))
    return [np.concatenate(visits[v]) for v in sorted(visits)]


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--texts",type=Path,default=Path(__file__).with_name("calibration_text.json"))
    p.add_argument("--original",action="store_true")
    p.add_argument("--compact-traces",action="store_true")
    p.add_argument("--weights-mode",help="A decoded component set or its restore- complement; see decoded_reference.CONDITIONS")
    p.add_argument("--manifest",type=Path)
    p.add_argument("--restore",action="append",default=[])
    p.add_argument("--frozen",type=Path)
    for key in ("gguf","llama","kernels"):p.add_argument("--"+key,type=Path)
    p.add_argument("--cache-gib",type=float,default=1.5)
    p.add_argument("--sequence-batch",type=int,choices=range(1,9),default=1)
    p.add_argument("--split",choices=("calibration","holdout"))
    main(p.parse_args())
