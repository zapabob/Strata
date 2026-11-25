"""Run the Inkling looped language and image graph on BF16 safetensors or one local PQ2_0 GGUF."""

import argparse
import json
import math
import os
import sys
import time
import types
from collections import Counter, OrderedDict
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.nn import functional as F
from transformers import (
    AutoConfig,
    AutoProcessor,
    AutoTokenizer,
    Inkling2LoopForConditionalGeneration,
)
from transformers.conversion_mapping import get_model_conversion_mapping
from transformers.core_model_loading import convert_and_load_state_dict_in_model
from transformers.modeling_utils import LoadStateDictConfig
from transformers.models.inkling2.modeling_inkling2 import Inkling2VisionRotaryEmbedding

from source import atomic_bytes, await_capacity
DTYPES={"BF16":torch.bfloat16,"F32":torch.float32,"F16":torch.float16,"I32":torch.int32}
ITEMSIZE={key:torch.empty((),dtype=typ).element_size() for key,typ in DTYPES.items()}


class Safetensors:
    def __init__(self, root, inventory=False):
        self.assets = root
        headers=json.loads((root/"headers.json").read_bytes())
        self.physical={}
        for shard,descriptor in headers.items():
            if not shard.startswith("model-"):continue
            for key,d in descriptor["tensors"].items():
                self.physical[key]=dict(origin=d["shape"],dtype=d["dtype"],shard=shard,
                    role="expert" if key.endswith((".w2_weight",".w13_weight")) else "vision" if key.startswith("model.visual.") else "text",
                    input_offset=descriptor["base"]+d["data_offsets"][0])
        self.stats = Counter()
        if not inventory:
            for name in {t["shard"] for t in self.physical.values()}:
                if (
                    not (root / (name + ".verified.json")).is_file()
                    or not (root / name).is_file()
                ):
                    raise ValueError(f"Missing verified safetensors file {name}")

    def read(self, key, device, start=0, count=None):
        t = self.physical[key]
        shape = t["origin"]
        count = shape[0] - start if count is None else count
        size = math.prod(shape[1:]) * ITEMSIZE[t["dtype"]]
        with (self.assets / t["shard"]).open("rb") as f:
            f.seek(t["input_offset"] + size * start)
            values = bytearray(count * size)
            if f.readinto(values) != len(values):
                raise OSError(f"Truncated safetensors input for {key}")
        self.stats["local_safetensors_bytes"] += len(values)
        return (
            torch.frombuffer(values, dtype=DTYPES[t["dtype"]])
            .reshape(count, *shape[1:])
            .to(device)
        )


class Weights:
    def __init__(self, store, key, device, inventory):
        self.store, self.key, self.device, self.inventory = (
            store,
            key,
            device,
            inventory,
        )

    def __getitem__(self, index):
        if index is not Ellipsis:
            raise ValueError("Whole non-expert tensor expected")
        t = self.store.physical[self.key]
        if self.inventory:
            return torch.empty(t["origin"], device="meta", dtype=DTYPES[t["dtype"]])
        if isinstance(self.store, Safetensors):
            return self.store.read(self.key, self.device)
        return self.store.get(self.key, self.device, DTYPES[t["dtype"]])


class OfficialSafetensors(Safetensors):
    """The published mixed-precision expert weights, reconstructed at the BF16 reference boundary."""

    def __init__(self, root, inventory=False):
        from official_weights import Original
        self.original = Original(root)
        self.original.cache_limit=int(float(os.environ.get("INKLING_SOURCE_CACHE_GIB","1.25"))*2**30)
        self.source_kernels=None
        if os.environ.get("INKLING_SOURCE_CUDA"):
            from spin8_cuda import Kernels
            self.source_kernels=Kernels(os.environ["INKLING_SOURCE_CUDA"])
        if not inventory and not self.original.published.is_file():
            raise ValueError("The verified official safetensors are required for full-graph inference")
        self.assets, self.stats, self.physical = root, Counter(), {}
        for name, descriptor in self.original.header.items():
            if name.endswith(("_weight_scale", "_weight_amax", "_weight_outer_scale_denominator")):
                continue
            geom = list(descriptor["shape"])
            role = "expert" if name in self.original.schemes else "vision" if name.startswith("model.visual.") else "text"
            storage = descriptor["dtype"]
            if role == "expert":
                if self.original.schemes[name]["weight_transform"] == "nvfp4_nearest":
                    geom[-1] *= 2
                storage = "BF16"
            self.physical[name] = dict(origin=geom, dtype=storage, role=role)

    def read(self, key, device, start=0, count=None):
        from official_weights import reconstruct
        descriptor = self.physical[key]
        geom = descriptor["origin"]
        count = geom[0] - start if count is None else count
        if descriptor["role"] == "expert":
            values=[]
            for e in range(start,start+count):
                parts=self.original.parts(key,e)
                value=(self.source_kernels.original(parts) if self.source_kernels and str(device).startswith("cuda")
                       else torch.from_numpy(reconstruct(parts)).to(torch.bfloat16))
                values.append(value)
            out=values[0].unsqueeze(0) if count==1 else torch.stack(values)
        else:
            stride = math.prod(geom[1:])
            arr = self.original.read(key, start*stride, count*stride).copy()
            out = torch.from_numpy(arr).view(DTYPES[descriptor["dtype"]]).reshape(count,*geom[1:])
        self.stats["working_values"] += out.numel()
        return out.to(device)


def load_graph(store, device, inventory):
    config = AutoConfig.from_pretrained(store.assets, local_files_only=True)
    config._attn_implementation = "eager"
    original_dtype = torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.bfloat16)
        with torch.device("meta"):
            model = Inkling2LoopForConditionalGeneration(config).eval()
    finally:
        torch.set_default_dtype(original_dtype)
    others = {
        k: Weights(store, k, device, inventory)
        for k, t in store.physical.items()
        if t["role"] not in ("expert", "draft")
    }
    os.environ["HF_DEACTIVATE_ASYNC_LOAD"] = "1"
    cfg = LoadStateDictConfig(
        device_map={"": device},
        dtype=torch.bfloat16,
        dtype_plan=model._get_dtype_plan(torch.bfloat16),
        weight_mapping=get_model_conversion_mapping(model),
    )
    info, _ = convert_and_load_state_dict_in_model(model, others, cfg)
    expected = {
        f"model.language_model.layers.{i}.mlp.experts.{p}"
        for i in range(config.text_config.num_hidden_layers)
        for p in ("gate_up_proj", "down_proj")
    }
    if (
        info.missing_keys != expected
        or info.unexpected_keys
        or info.conversion_errors
        or info.mismatched_keys
        or info.error_msgs
    ):
        raise ValueError(
            f"Official weight-loading mismatch: missing {info.missing_keys ^ expected}, unexpected {info.unexpected_keys}, errors {info.conversion_errors}, shapes {info.mismatched_keys}, messages {info.error_msgs}"
        )
    for i, layer in enumerate(model.model.language_model.layers):
        experts = layer.mlp.experts
        for raw, param in [("w13_weight", "gate_up_proj"), ("w2_weight", "down_proj")]:
            key = f"model.llm.layers.{i}.mlp.experts.{raw}"
            if store.physical[key]["origin"] != list(getattr(experts, param).shape):
                raise ValueError(f"Expert geometry differs for {key}")
    if not inventory:
        for module in model.modules():
            if isinstance(module, Inkling2VisionRotaryEmbedding):
                freq, scale = module.compute_axial_rope_parameters(
                    module.config, device=device
                )
                module.inv_freq = freq
                module.original_inv_freq = freq.clone()
                module.attention_scaling = scale
        unknown = [k for k, x in model.named_buffers() if x.is_meta]
        if unknown:
            raise ValueError(f"Uninitialised model buffers: {unknown}")
    return model


class Experts:
    def __init__(self, store, cache_gib, device):
        self.store, self.device = store, device
        self.cap = int(cache_gib * 2**30)
        self.cache = OrderedDict()
        self.bytes = 0
        self.stats = Counter()

    def get(self, layer, expert):
        key = (layer, expert)
        if key in self.cache:
            self.stats["cache_hits"] += 1
            self.cache.move_to_end(key)
            return self.cache[key][0]
        self.stats["cache_misses"] += 1
        pair = []
        for suffix in ("w13_weight", "w2_weight"):
            name = f"model.llm.layers.{layer}.mlp.experts.{suffix}"
            if isinstance(self.store, Safetensors):
                value = self.store.read(name, self.device, expert, 1)[0]
            else:
                rows = self.store.physical[name]["origin"][1]
                item = self.store.raw(name, expert * rows, rows)
                value = self.store.decode(item, self.device, torch.bfloat16)
            pair.append(value)
        size = sum(x.numel() * x.element_size() for x in pair)
        if size <= self.cap:
            while self.bytes + size > self.cap:
                _, (_, old) = self.cache.popitem(last=False)
                self.bytes -= old
            self.cache[key] = (pair, size)
            self.bytes += size
        return pair

    def install(self, model, observer=None):
        for i, layer in enumerate(model.model.language_model.layers):

            def forward(module, hidden_states, top_k_index, top_k_weights, layer_idx=i):
                if observer is not None:
                    top_k_index, top_k_weights = observer.begin(layer_idx, hidden_states, top_k_index, top_k_weights)
                out = torch.zeros_like(hidden_states, dtype=torch.float32)
                for expert in torch.unique(top_k_index, sorted=True).tolist():
                    tokens, slots = torch.where(top_k_index == expert)
                    w13, w2 = self.get(layer_idx, expert)
                    gate_up = F.linear(hidden_states[tokens], w13)
                    # The safetensors interleave the gate and up rows. HF deinterleaves them on load.
                    activ = module.act_fn(gate_up[..., ::2], gate_up[..., 1::2])
                    if observer is not None:
                        observer.down(layer_idx, expert, tokens, slots, activ)
                    current = F.linear(activ, w2) * top_k_weights[tokens, slots, None]
                    out.index_add_(0, tokens, current.float())
                return out.to(hidden_states.dtype)

            layer.mlp.experts.forward = types.MethodType(forward, layer.mlp.experts)


def inputs_for(store, prompt, chat, image):
    tokenizer = AutoTokenizer.from_pretrained(store.assets, local_files_only=True)
    if image:
        processor = AutoProcessor.from_pretrained(store.assets, local_files_only=True)
        colour = {"red": (240, 16, 16), "blue": (16, 16, 240)}
        pixels = (
            Image.new("RGB", (64, 64), colour[image])
            if image in colour
            else Image.open(image).convert("RGB")
        )
        parts = [dict(type="image", image=pixels), dict(type="text", text=prompt)]
        inputs = processor.apply_chat_template(
            [dict(role="user", content=parts)],
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            reasoning_effort="low",
        )
    elif chat:
        inputs = tokenizer.apply_chat_template(
            [dict(role="user", content=prompt)],
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
            reasoning_effort="low",
        )
    else:
        inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
    return tokenizer, inputs.to("cuda")


def evaluate(model, store, experts, case, out):
    prompt = case["prompt"]
    tokenizer, inputs = inputs_for(store, prompt, case.get("chat"), case.get("image"))
    ids = inputs["input_ids"][0].tolist()
    steps = case.get("tokens", 0)
    gold = []
    if case.get("suffix"):
        if case.get("image") or case.get("chat") or case.get("teacher"):
            raise ValueError("A reference-text continuation requires a raw text prompt")
        entire = tokenizer(prompt + case["suffix"], add_special_tokens=False)[
            "input_ids"
        ]
        if entire[: len(ids)] != ids or len(entire) <= len(ids):
            raise ValueError("Reference continuation changes the prompt tokenisation")
        gold = entire[len(ids) :]
        steps = len(gold)
    forced = (
        json.loads(Path(case["teacher"]).read_bytes()) if case.get("teacher") else None
    )
    if forced and (forced["input_ids"] != ids or len(forced["generated_ids"]) < steps):
        raise ValueError("Teacher does not cover the identical prompt")
    seen = []
    used = []
    logits = []
    times = []
    mask = inputs["attention_mask"]
    cache = None
    initial = Counter(store.stats)
    expert_initial = Counter(experts.stats)
    torch.cuda.reset_peak_memory_stats()
    for i in range(1 if gold else steps):
        if gold:
            full_ids = torch.tensor([ids + gold[:-1]], device="cuda")
            inputs = dict(input_ids=full_ids, attention_mask=torch.ones_like(full_ids))
        if i:
            mask = torch.cat((mask, torch.ones_like(mask[:, :1])), dim=1)
            inputs = dict(
                input_ids=torch.tensor([[used[-1]]], device="cuda"),
                attention_mask=mask,
                cache=cache,
            )
        torch.cuda.synchronize()
        start = time.perf_counter()
        result = model(**inputs, use_cache=True, logits_to_keep=steps if gold else 1)
        torch.cuda.synchronize()
        times.append(time.perf_counter() - start)
        cache = result.cache
        scores = result.logits[0].float().cpu().numpy().copy()
        if not np.isfinite(scores).all():
            raise ValueError("Non-finite token logits")
        if gold:
            logits.extend(scores)
            seen.extend(scores.argmax(axis=1).tolist())
            used.extend(gold)
            break
        scores = scores[-1]
        token = int(scores.argmax())
        seen.append(token)
        used.append(forced["generated_ids"][i] if forced else token)
        logits.append(scores)
        print(
            f"{out.name} {i + 1}/{steps}: token {token}, {times[-1]:.3f}s", flush=True
        )
    np.save(out / "logits.npy", np.stack(logits))
    metrics = dict(
        format="reconstructed original BF16" if isinstance(store, OfficialSafetensors) else
               "BF16 safetensors" if isinstance(store, Safetensors) else "PQ2_0 GGUF",
        repository="thinkingmachines/Inkling-2-Mini" if isinstance(store, OfficialSafetensors) else "yanauto/Inkling-2-Mini-heretic-full",
        prompt=prompt,
        chat=bool(case.get("chat")),
        image=case.get("image"),
        input_ids=ids,
        generated_ids=seen,
        trajectory_ids=used,
        teacher_forced=bool(forced or gold),
        text=tokenizer.decode(seen),
        step_seconds=[] if gold else times,
        reads=dict(store.stats - initial),
        expert_cache=dict(experts.stats - expert_initial),
        peak_torch_gpu_bytes=torch.cuda.max_memory_allocated(),
        gpu=torch.cuda.get_device_name(),
        torch_version=str(torch.__version__),
    )
    if gold:
        values = torch.from_numpy(np.stack(logits)).double().log_softmax(-1)
        loss = -values[torch.arange(steps), torch.tensor(gold)].mean().item()
        metrics.update(
            reference_suffix=case["suffix"],
            gold_ids=gold,
            gold_nll_nats=loss,
            gold_perplexity=math.exp(loss),
            batch_forced_seconds=times[0],
        )
    atomic_bytes(
        out / "run.json", json.dumps(metrics, ensure_ascii=False, indent=2).encode()
    )
    print(
        json.dumps({"output": str(out), "text": metrics["text"]}, ensure_ascii=True),
        flush=True,
    )


def main(args):
    device = "meta" if args.inventory else "cuda"
    if args.official:
        store = OfficialSafetensors(args.official, args.inventory)
    elif args.source:
        store = Safetensors(args.source, args.inventory)
    else:
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"hy4-bonsai2"))
        from convert import ARCH,ASSETS,PREFIX
        from weight_store import Packed
        sys.path.insert(0, str(args.gguf_python.resolve(strict=True)))
        import gguf

        store = Packed(
            args.gguf,
            gguf,
            args.prism_bin,
            args.assets,
            cuda_codec=args.cuda_codec,
            architecture=ARCH,
            prefix=PREFIX,
            asset_names=ASSETS,
        )
    if not args.inventory:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        await_capacity(args.output.parent, 0)
    model = load_graph(store, device, args.inventory)
    if args.inventory:
        print(
            "Official graph loaded all non-expert mappings. All 48 expert parameter shapes agree.",
            flush=True,
        )
        return
    if args.direct_pq:
        from routed import TernaryExperts

        if args.source or not args.cuda_codec:
            raise ValueError("Direct PQ2_0 requires the GGUF and its CUDA library")
        experts = TernaryExperts(store, args.cache_gib, device)
    else:
        experts = Experts(store, args.cache_gib, device)
    experts.install(model)
    cases = (
        json.loads(args.cases.read_bytes())
        if args.cases
        else [
            dict(
                prompt=args.prompt,
                tokens=args.tokens,
                chat=args.chat,
                image=args.image,
                teacher=str(args.teacher) if args.teacher else None,
            )
        ]
    )
    for case in cases:
        out = args.output / case["id"] if args.cases else args.output
        out.mkdir(parents=True, exist_ok=True)
        if (out / "run.json").is_file() or (
            not case.get("suffix") and case.get("tokens", 0) < 1
        ):
            raise ValueError(f"Invalid evaluation destination or length: {out}")
        evaluate(model, store, experts, case, out)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--source", type=Path)
    g.add_argument("--official", type=Path)
    g.add_argument("--gguf", type=Path)
    for key in (
        "output",
        "gguf-python",
        "prism-bin",
        "cuda-codec",
        "assets",
        "cases",
        "teacher",
    ):
        p.add_argument("--" + key, type=Path)
    p.add_argument("--cache-gib", type=float, default=3)
    p.add_argument("--inventory", action="store_true")
    p.add_argument("--direct-pq", action="store_true")
    p.add_argument("--prompt", default="The capital of France is")
    p.add_argument("--tokens", type=int, default=8)
    p.add_argument("--chat", action="store_true")
    p.add_argument("--image")
    with torch.inference_mode():
        main(p.parse_args())
