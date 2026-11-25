"""Run the publisher's Hy4 language and vision graph with row-streamed weights."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F
from transformers import AutoConfig, AutoProcessor, AutoTokenizer
from transformers.conversion_mapping import get_checkpoint_conversion_mapping
from transformers.core_model_loading import rename_source_key
from transformers.models.hy_v4_flash.modeling_hy_v4_flash import (
    HYV4FlashEngramEmbedding,
    HYV4FlashEngramLayer,
    HYV4FlashForConditionalGeneration,
    HYV4FlashRotaryEmbedding,
)

from source_archive import atomic_bytes
from stream_routed import check_resources
from weight_store import Original, Packed


class Engine:
    def __init__(
        self, store, output, device, cache_gib=4, workers=4, vision_only=False
    ):
        self.store, self.output, self.device = store, output, device
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.workers = workers
        self.cap = int(cache_gib * 2**30)
        self.kept = 0
        self.times = []
        config = AutoConfig.from_pretrained(store.assets, local_files_only=True)
        config._attn_implementation = "eager"
        with torch.device("meta"):
            self.model = (
                HYV4FlashForConditionalGeneration(config)
                .to(dtype=torch.bfloat16)
                .eval()
            )
        state = self.model.state_dict()
        mapping = get_checkpoint_conversion_mapping("hy_v4_flash")
        self.names = {
            rename_source_key(n, mapping, [], meta_state_dict=state)[0]: n
            for n in store.fields
            if not n.startswith("model.dfly_layers.")
        }
        if set(self.names) != set(state) or any(
            list(state[k].shape) != store.fields[n]["shape"]
            for k, n in self.names.items()
        ):
            raise ValueError(
                "Official model state and input tensor names or shapes disagree"
            )
        self._constants(vision_only)
        self.groups = {}
        for dst, src in self.names.items():
            if vision_only and not dst.startswith("model.vision_tower."):
                continue
            if (
                ".mlp.experts." in src
                or src.endswith(".multi_head_embedding.embedding.weight")
                or src == "model.embed_tokens.weight"
            ):
                continue
            if dst.startswith("model.language_model.layers."):
                group = dst.split(".")
                group = ".".join(group[:4])
            elif dst.startswith("model.vision_tower."):
                group = "model.vision_tower"
            else:
                group = dst.rsplit(".", 1)[0]
            modpath, attr = dst.rsplit(".", 1)
            mod = self.model.get_submodule(modpath)
            strict = any(
                term in dst for term in self.model._keep_in_fp32_modules_strict
            )
            dtype = (
                torch.float32
                if strict and state[dst].is_floating_point()
                else state[dst].dtype
            )
            if dtype != state[dst].dtype:
                # The HF head inspects weight.dtype before its own pre-hook runs.
                self._set(
                    mod, attr, torch.empty(state[dst].shape, device="meta", dtype=dtype)
                )
            self.groups.setdefault(group, []).append((mod, attr, src, dtype))
        for name in self.groups:
            module = self.model.get_submodule(name)
            module.register_forward_pre_hook(lambda mod, inp, grp=name: self._load(grp))
            module.register_forward_hook(
                lambda mod, inp, result, grp=name: self._release(grp)
            )
        self.resident = set()
        self.ephemeral = set()
        if not vision_only:
            self._streamed_modules()
        self.last_hidden = None
        self.model.model.language_model.norm.register_forward_hook(self._capture_hidden)

    def _capture_hidden(self, mod, args, output):
        self.last_hidden = output[:, -1, :].detach()

    def _constants(self, vision_only):
        model = self.model.model.vision_tower if vision_only else self.model
        for module in model.modules():
            if isinstance(module, HYV4FlashRotaryEmbedding):
                for lt, fn in module.rope_init_fns.items():
                    freq, scaling = fn(
                        module.config.per_layer_config[lt],
                        device=self.device,
                        layer_type=lt,
                    )
                    setattr(module, f"{lt}_inv_freq", freq)
                    setattr(module, f"{lt}_original_inv_freq", freq.clone())
                    setattr(module, f"{lt}_attention_scaling", scaling)
            elif isinstance(module, HYV4FlashEngramLayer):
                src = f"model.layers.{module.layer_id - 1}.engram_layer.lookup_table"
                token_map = self.store.get(src, "cpu", torch.int32)
                module.head_vocab_sizes = torch.tensor(
                    module.config_head_vocab_sizes, device=self.device
                )
                module.hash_multipliers = module.draw_hash_multipliers(
                    int(token_map.max()) + 1
                ).to(self.device)
            elif isinstance(module, HYV4FlashEngramEmbedding):
                module.offsets = module.head_offsets().to(self.device)
        persistent = set(model.state_dict())
        unknown = [
            n for n, b in model.named_buffers() if n not in persistent and b.is_meta
        ]
        if unknown:
            raise ValueError(f"Missing derived buffers: {unknown}")

    @staticmethod
    def _set(m, attr, value):
        if attr in m._parameters:
            setattr(m, attr, nn.Parameter(value, requires_grad=False))
        else:
            setattr(m, attr, value)

    def _load(self, name):
        if name in self.resident:
            return
        check_resources(self.output, 0)
        if (
            self.device.startswith("cuda")
            and torch.cuda.mem_get_info()[0] < 1536 * 2**20
        ):
            raise MemoryError("CUDA free-memory reserve reached before layer transfer")
        total = 0
        for m, attr, src, dtype in self.groups[name]:
            value = self.store.get(src, self.device, dtype)
            total += value.numel() * value.element_size()
            self._set(m, attr, value)
        if self.kept + total <= self.cap:
            self.kept += total
            self.resident.add(name)
        else:
            self.ephemeral.add(name)
        if re.fullmatch(r"model\.language_model\.layers\.\d+", name):
            print(f"Loaded {name}", flush=True)

    def _release(self, name):
        if name not in self.ephemeral:
            return
        for m, attr, src, dtype in self.groups[name]:
            self._set(
                m,
                attr,
                torch.empty(
                    self.store.fields[src]["shape"], device="meta", dtype=dtype
                ),
            )
        self.ephemeral.remove(name)

    def _streamed_modules(self):
        text = self.model.model.language_model

        def embedding(key):
            def lookup(module, ids):
                idx, inverse = torch.unique(ids, sorted=True, return_inverse=True)
                rows = list(
                    self.pool.map(lambda i: self.store.row(key, i), idx.tolist())
                )
                values = [
                    self.store.decode(row, self.device, torch.bfloat16).reshape(-1)
                    for row in rows
                ]
                return torch.stack(values)[inverse]

            return lookup

        text.embed_tokens.forward = types.MethodType(
            embedding("model.embed_tokens.weight"), text.embed_tokens
        )
        for lid, layer in enumerate(text.layers):
            eng = layer.engram_layer
            if eng is not None:
                key = f"model.layers.{lid}.engram_layer.multi_head_embedding.embedding.weight"
                mod = eng.multi_head_embedding.embedding
                mod.forward = types.MethodType(embedding(key), mod)
            if lid:
                mod = layer.mlp.experts

                def experts(module, x, top_k_index, top_k_weights, layer_no=lid):
                    result = torch.zeros_like(x)
                    active = torch.unique(top_k_index, sorted=True).tolist()
                    for off in range(0, len(active), self.workers):
                        ids = active[off : off + self.workers]
                        weights = self.pool.map(
                            lambda i: self.store.expert(layer_no, i), ids
                        )
                        for expert, (pair, down) in zip(ids, weights, strict=True):
                            token, slot = torch.where(top_k_index == expert)
                            if isinstance(self.store, Packed):
                                both = torch.cat(
                                    [
                                        self.store.decode(t, self.device, x.dtype)
                                        for t in pair
                                    ]
                                )
                            else:
                                both = self.store.decode(pair, self.device, x.dtype)
                            current = module._apply_gate(F.linear(x[token], both))
                            current = F.linear(
                                current, self.store.decode(down, self.device, x.dtype)
                            )
                            result.index_add_(
                                0,
                                token,
                                (current * top_k_weights[token, slot, None]).to(
                                    x.dtype
                                ),
                            )
                    return result

                mod.forward = types.MethodType(experts, mod)

    def close(self):
        self.pool.shutdown()


def image_case(colour):
    rgb = {"red": (240, 16, 16), "blue": (16, 16, 240)}[colour]
    return Image.new("RGB", (64, 64), rgb)


def sync(device):
    if device.startswith("cuda"):
        torch.cuda.synchronize()


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output / "run.json").exists():
        raise FileExistsError("Use a new directory for each evaluation")
    if args.gguf:
        sys.path.insert(0, str(args.gguf_python.resolve(strict=True)))
        import gguf

        store = Packed(
            args.gguf,
            gguf,
            args.prism_bin,
            args.assets,
            partial=args.component_partial,
            cuda_codec=args.cuda_codec,
        )
    else:
        store = Original(
            args.source, args.sample_cache, args.offline_bf16, args.sample_cache_gib
        )
    engine = Engine(
        store,
        args.output,
        args.device,
        args.gpu_cache_gib,
        args.workers,
        args.vision_only,
    )
    try:
        evaluate(args, store, engine)
    finally:
        engine.close()


@torch.inference_mode()
def evaluate(args, store, engine):
    model = engine.model
    tokenizer = AutoTokenizer.from_pretrained(store.assets, local_files_only=True)
    if args.device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    init = dict(
        format="PQ2_0 GGUF" if args.gguf else "original BF16 source",
        device=args.device,
        prompt=args.prompt,
        image=args.image,
        source_tensor_count=len(store.fields),
        model_state_tensors=len(engine.names),
        offline_bf16=args.offline_bf16,
        torch_version=str(torch.__version__),
        gpu=torch.cuda.get_device_name() if args.device == "cuda" else None,
        gpu_cache_gib=args.gpu_cache_gib,
        workers=args.workers,
        cuda_codec=bool(args.cuda_codec),
    )

    def save():
        if args.device == "cuda":
            init["peak_torch_gpu_bytes"] = torch.cuda.max_memory_allocated()
            init["peak_torch_reserved_bytes"] = torch.cuda.max_memory_reserved()
        atomic_bytes(
            args.output / "run.json",
            json.dumps(init, ensure_ascii=False, indent=2).encode(),
        )

    if args.image:
        processor = AutoProcessor.from_pretrained(store.assets, local_files_only=True)
        image = image_case(args.image)
        if args.vision_only:
            vi = processor.image_processor(images=[image], return_tensors="pt")
            vi = vi.to(args.device)
            sync(args.device)
            start = time.perf_counter()
            vision = model.model.get_image_features(**vi, return_dict=True)
            sync(args.device)
            features = vision.pooler_output
            if isinstance(features, (tuple, list)):
                features = torch.cat(features)
            array = features.float().cpu().numpy()
            if not np.isfinite(array).all():
                raise ValueError("Non-finite vision features")
            np.save(args.output / "vision.npy", array)
            init.update(
                vision_shape=list(array.shape),
                elapsed_seconds=time.perf_counter() - start,
                reads=dict(store.stats),
            )
            save()
            print(f"Vision output {array.shape}", flush=True)
            return
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": args.prompt},
                ],
            }
        ]
        inputs = processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            reasoning_effort="no_think",
        ).to(args.device)
    elif args.chat:
        inputs = tokenizer.apply_chat_template(
            [{"role": "user", "content": args.prompt}],
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
            reasoning_effort="no_think",
        ).to(args.device)
    else:
        inputs = tokenizer(
            args.prompt, return_tensors="pt", add_special_tokens=False
        ).to(args.device)
    seq = inputs["input_ids"]
    ids = seq[0].tolist()
    if args.dfly2:
        from draft_decode import speculative

        generated, scores, receipt = speculative(engine, inputs, args.tokens)
        np.save(args.output / "logits.npy", np.stack(scores))
        init.update(
            input_ids=ids,
            generated_ids=generated,
            trajectory_ids=generated,
            teacher_forced=False,
            text=tokenizer.decode(generated),
            dfly2=receipt,
            reads=dict(store.stats),
        )
        save()
        print(f"Verified {len(generated)} target tokens with DFly2", flush=True)
        return
    generated, used, logits, latencies = [], [], [], []
    forced = (
        json.loads(args.teacher.read_bytes())["generated_ids"] if args.teacher else []
    )
    if forced and len(forced) < args.tokens - 1:
        raise ValueError("Teacher trajectory is shorter than this evaluation")
    cache = None
    for i in range(args.tokens):
        if i == 0:
            feed = dict(inputs)
        else:
            ng, mask = model.model.build_engram_inputs(seq, None)
            feed = dict(
                input_ids=seq[:, -1:],
                attention_mask=torch.ones_like(seq),
                cache=cache,
                ngram_tokens=ng[:, -1:],
                engram_mask=mask[:, -1:] if mask is not None else None,
            )
        sync(args.device)
        start = time.perf_counter()
        out = model(**feed, use_cache=True, logits_to_keep=1)
        sync(args.device)
        latencies.append(time.perf_counter() - start)
        scores = out.logits[0, -1].float().cpu().numpy().copy()
        if not np.isfinite(scores).all():
            raise ValueError("Non-finite model logits")
        logits.append(scores)
        token = int(scores.argmax())
        generated.append(token)
        selected = forced[i] if i < len(forced) else token
        used.append(selected)
        seq = torch.cat((seq, torch.tensor([[selected]], device=args.device)), dim=1)
        cache = out.cache
        print(f"Step {i + 1}: token {token} in {latencies[-1]:.3f}s", flush=True)
    np.save(args.output / "logits.npy", np.stack(logits))
    init.update(
        input_ids=ids,
        generated_ids=generated,
        trajectory_ids=used,
        teacher_forced=bool(forced),
        text=tokenizer.decode(generated),
        step_seconds=latencies,
        reads=dict(store.stats),
    )
    save()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--gguf", type=Path)
    source.add_argument("--source", type=Path)
    for k in (
        "output",
        "assets",
        "gguf-python",
        "prism-bin",
        "sample-cache",
        "teacher",
        "cuda-codec",
    ):
        p.add_argument("--" + k, type=Path, required=(k == "output"))
    p.add_argument("--offline-bf16", action="store_true")
    p.add_argument("--component-partial", action="store_true")
    p.add_argument("--sample-cache-gib", type=float, default=24)
    p.add_argument("--gpu-cache-gib", type=float, default=4)
    p.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    p.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    p.add_argument("--prompt", default="Tokyo")
    p.add_argument("--tokens", type=int, default=2)
    p.add_argument("--image", choices=("red", "blue"))
    p.add_argument("--vision-only", action="store_true")
    p.add_argument("--chat", action="store_true")
    p.add_argument("--dfly2", action="store_true")
    args = p.parse_args()
    if (
        args.tokens < 1
        or (args.vision_only and not args.image)
        or (args.component_partial and not args.vision_only)
    ):
        p.error("Invalid evaluation scope")
    if args.dfly2 and (args.teacher or args.vision_only or args.tokens < 2):
        p.error("DFly2 verifies a free-running target sequence of at least two tokens")
    if (args.gguf and not (args.gguf_python and args.prism_bin and args.assets)) or (
        args.source and not args.sample_cache
    ):
        p.error("Missing model-specific inputs")
    with torch.inference_mode():
        run(args)
