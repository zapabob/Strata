"""CUDA routed products with ternary experts resident in their original PQ2_0 packing."""

import ctypes
from collections import Counter, OrderedDict

import torch


class TernaryExperts:
    def __init__(self, store, cache_gib, device):
        self.store, self.device = store, device
        self.dot = store.fused.lib.inkling_pq_matmul
        ptr, num = ctypes.c_void_p, ctypes.c_int
        self.dot.argtypes = [ptr, ptr, ptr, ptr, num, num, num, num, num, ptr, ptr, ptr]
        self.dot.restype = num
        self.cache = OrderedDict()
        self.cap = int(cache_gib * 2**30)
        self.bytes = 0
        self.directions = {}
        self.stats = Counter()

    def bank(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            self.stats["bank_hits"] += 1
            return self.cache[key]
        t = self.store.physical[key]
        if t["type"] != 142 or t["original_width"] != t["shape"][-1]:
            raise ValueError(
                "A routed PQ2_0 bank with its exact input width is required"
            )
        while self.cache and (
            self.bytes + t["bytes"] > self.cap
            or torch.cuda.mem_get_info()[0] < t["bytes"] + 2**30
        ):
            _, old = self.cache.popitem(last=False)
            self.bytes -= old.numel()
            del old
        if torch.cuda.mem_get_info()[0] < t["bytes"] + 2**30:
            raise MemoryError("Insufficient free VRAM for one more expert bank")
        _, data, _ = self.store.raw(key)
        value = torch.frombuffer(bytearray(data), dtype=torch.uint8).to(self.device)
        if t["bytes"] <= self.cap:
            self.cache[key] = value
            self.bytes += value.numel()
        self.stats["bank_loads"] += 1
        return value

    def product(self, key, activation, ids, repeats):
        t = self.store.physical[key]
        _, rows, width = t["shape"]
        act = activation.contiguous()
        if (
            act.dtype != torch.bfloat16
            or act.shape[-1] != width
            or ids.dtype != torch.int64
            or ids.numel() != len(act) * repeats
        ):
            raise ValueError("Invalid expert product geometry or dtype")
        if width not in self.directions:
            self.directions[width] = self.store.directions[width].to(self.device)
        q = self.bank(key)
        rotated = torch.empty_like(act, dtype=torch.float32)
        out = torch.empty((ids.numel(), rows), dtype=torch.bfloat16, device=self.device)
        status = self.dot(
            q.data_ptr(),
            act.data_ptr(),
            self.directions[width].data_ptr(),
            ids.data_ptr(),
            len(act),
            repeats,
            rows,
            width,
            t["block"],
            rotated.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream,
        )
        if status:
            raise RuntimeError(f"Routed ternary CUDA multiply returned {status}")
        self.stats["routed_products"] += 1
        return out

    def install(self, model):
        import types

        for i, layer in enumerate(model.model.language_model.layers):

            def forward(module, hidden_states, top_k_index, top_k_weights, layer_id=i):
                ids = top_k_index.to(torch.int64).contiguous()
                topk = ids.shape[1]
                root = f"model.llm.layers.{layer_id}.mlp.experts."
                gu = self.product(root + "w13_weight", hidden_states, ids, topk)
                h = module.act_fn(gu[..., ::2], gu[..., 1::2])
                down = self.product(root + "w2_weight", h, ids, 1).reshape(
                    len(ids), topk, -1
                )
                weighted = (down * top_k_weights[..., None]).float()
                # Match the reference's ascending expert accumulation order.
                index = ids.argsort(dim=1)[..., None].expand_as(weighted)
                return torch.gather(weighted, 1, index).sum(1).to(hidden_states.dtype)

            layer.mlp.experts.forward = types.MethodType(forward, layer.mlp.experts)
