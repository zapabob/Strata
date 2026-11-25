"""Hy4 DFly2 draft with target KV sharing and batched greedy verification."""

from __future__ import annotations

import copy
import math
import time

import torch
from torch.nn import functional as F
from transformers.models.hy_v4_flash.modeling_hy_v4_flash import apply_rotary_pos_emb

LAYERS = (25, 29, 33, 37, 41)
MASK_ID = 120009


class DFly2:
    def __init__(self, engine):
        self.engine = engine
        self.text = engine.model.model.language_model
        self.weights = {}
        self.selected = {}
        self.used = set()
        self.hooks = []
        for il in LAYERS:
            indexer = self.text.layers[il].self_attn.compressed_indexer
            if indexer is not None:
                self.hooks.append(
                    indexer.register_forward_hook(
                        lambda mod, inp, out, i=il: self._indices(i, out)
                    )
                )

    def _indices(self, il, mask):
        if mask is not None:
            last = mask[0, 0, -1]
            allowed = last if last.dtype == torch.bool else last > -1e4
            self.selected[il] = torch.where(allowed)[0].detach()

    def w(self, name):
        if name not in self.weights:
            key = "model.dfly_layers." + name
            self.weights[name] = self.engine.store.get(
                key, self.engine.device, torch.bfloat16
            )
        self.used.add(name)
        return self.weights[name]

    def norm(self, x, name):
        return (
            x.float()
            * torch.rsqrt(
                x.float().square().mean(-1, keepdim=True)
                + self.text.config.rms_norm_eps
            )
            * self.w(name + ".weight").float()
        ).to(torch.bfloat16)

    def linear(self, x, name):
        return F.linear(x.to(torch.bfloat16), self.w(name + ".weight"))

    def step(self, seq, anchor, cache, target_hidden):
        ids = torch.tensor([[anchor, MASK_ID]], device=self.engine.device)
        hidden = self.text.embed_tokens(ids)[0].float()
        embed = self.norm(hidden[:1], "mtp_fusion.enorm")
        target = self.norm(target_hidden, "mtp_fusion.hnorm")
        fusion = self.linear(torch.cat((embed, target), dim=-1), "mtp_fusion.eh_proj")
        hidden[:1] += self.w("mtp_fusion.gate").float() * fusion.float()
        a = seq.shape[1]
        delta = self.engine.model.model.rope_deltas
        positions = torch.arange(a, a + 2, device=self.engine.device)
        if delta is not None:
            positions = positions + int(delta.flatten()[0])
        positions = positions.view(1, 1, 2).expand(3, 1, 2)
        cos, sin = self.text.rotary_emb(
            hidden.to(torch.bfloat16), positions, layer_type="indexed_attention"
        )
        for d, il in enumerate(LAYERS):
            lp = str(d)
            sp = lp + ".self_attn."
            h = self.norm(hidden, lp + ".input_layernorm")
            q = self.norm(self.linear(h, sp + "q_a_proj"), sp + "q_a_layernorm")
            q = self.linear(q, sp + "q_b_proj").reshape(1, 2, 32, 256).transpose(1, 2)
            q0, qr = q.split((192, 64), dim=-1)
            raw = self.linear(h, sp + "kv_a_proj_with_mqa")
            kp, kr = raw.split((512, 64), dim=-1)
            own = self.norm(kp, sp + "kv_a_layernorm")
            qr, kr = apply_rotary_pos_emb(qr, kr.reshape(1, 1, 2, 64), cos, sin)
            prior = cache.layers[il]
            if prior.keys.shape[-2] != a or prior.values.shape[-2] != a:
                raise ValueError(
                    f"Target cache at layer {il} does not cover the anchor prefix"
                )
            ids_old = self.selected.get(il)
            if ids_old is None:
                if a > self.text.config.index_topk:
                    raise ValueError(
                        "Missing target sparse-index selection for the draft"
                    )
                ids_old = torch.arange(a, device=self.engine.device)
            hist = prior.keys[0, 0].index_select(0, ids_old)
            rot = prior.values[0, 0].index_select(0, ids_old)
            kv = (
                self.linear(torch.cat((hist, own)), sp + "kv_b_proj")
                .reshape(-1, 32, 448)
                .transpose(0, 1)
            )
            k, v = kv.split((192, 256), dim=-1)
            krot = torch.cat((rot, kr[0, 0])).unsqueeze(0).expand(32, -1, -1)
            k = torch.cat((k, krot), dim=-1)
            scores = torch.matmul(
                torch.cat((q0, qr), dim=-1)[0].float(), k.float().transpose(1, 2)
            ) / math.sqrt(256)
            scores[:, 0, -1] = float("-inf")
            sink = (
                self.w(sp + "learnable_sink_param")
                .float()
                .reshape(32, 1, 1)
                .expand(-1, 2, -1)
            )
            probs = torch.softmax(torch.cat((scores, sink), dim=-1), dim=-1)[
                ..., :-1
            ].to(v.dtype)
            attn = torch.matmul(probs, v).transpose(0, 1).reshape(2, -1)
            attn *= torch.sigmoid(self.linear(h, sp + "linear_gate"))
            hidden += self.norm(
                self.linear(attn, sp + "o_proj"), sp + "post_proj_norm"
            ).float()
            h = self.norm(hidden, lp + ".post_attention_layernorm")
            mp = lp + ".mlp."
            hidden += self.linear(
                F.silu(self.linear(h, mp + "gate_proj"))
                * self.linear(h, mp + "up_proj"),
                mp + "down_proj",
            ).float()
        final = self.norm(hidden, "final_norm")[1:]
        hc = torch.cat(
            (
                self.norm(final, "hidden_correction.hidden_norm"),
                self.norm(
                    self.text.embed_tokens(ids[:, :1])[0],
                    "hidden_correction.embed_norm",
                ),
            ),
            dim=-1,
        )
        residual = self.linear(
            F.silu(self.linear(hc, "hidden_correction.gate_proj"))
            * self.linear(hc, "hidden_correction.up_proj"),
            "hidden_correction.down_proj",
        )
        corrected = final.float() + residual.float()
        conf = torch.sigmoid(
            F.linear(
                corrected,
                self.w("confidence_head.proj.weight").float(),
                self.w("confidence_head.proj.bias").float(),
            )
        ).item()
        logits = self.engine.model.lm_head(
            corrected.to(self.engine.model.lm_head.weight.dtype)
        )
        return int(logits.argmax(-1).item()), conf

    def close(self):
        for hook in self.hooks:
            hook.remove()


def target_block(model, seq, block, cache):
    inputs = torch.tensor([block], device=seq.device)
    full = torch.cat([seq, inputs], dim=1)
    ng, mask = model.model.build_engram_inputs(full, None)
    return model(
        input_ids=inputs,
        attention_mask=torch.ones_like(full),
        cache=cache,
        ngram_tokens=ng[:, -len(block) :],
        engram_mask=mask[:, -len(block) :] if mask is not None else None,
        use_cache=True,
        logits_to_keep=len(block),
    )


def speculative(engine, inputs, n):
    draft = DFly2(engine)
    seq = inputs["input_ids"]
    model = engine.model
    start = time.perf_counter()
    trace = []
    scores = []
    answer = []
    try:
        output = model(**inputs, use_cache=True, logits_to_keep=1)
        cache = output.cache
        next_scores = output.logits[0, -1]
        while len(answer) < n:
            anchor = int(next_scores.argmax().item())
            scores.append(next_scores.float().cpu().numpy().copy())
            answer.append(anchor)
            if len(answer) == n:
                break
            proposed, conf = draft.step(seq, anchor, cache, engine.last_hidden)
            trial = copy.deepcopy(cache)
            check = target_block(model, seq, [anchor, proposed], trial)
            verified = int(check.logits[0, 0].argmax().item())
            accepted = proposed == verified
            trace.append(
                dict(
                    anchor=anchor,
                    proposal=proposed,
                    target=verified,
                    accepted=accepted,
                    confidence=conf,
                )
            )
            if accepted or len(answer) + 1 == n:
                scores.append(check.logits[0, 0].float().cpu().numpy().copy())
                answer.append(verified)
                if len(answer) == n:
                    break
                seq = torch.cat(
                    [seq, torch.tensor([[anchor, proposed]], device=seq.device)], dim=1
                )
                cache = trial
                next_scores = check.logits[0, 1]
            else:
                # The unverified branch wrote its own cache. Rebuild only the true anchor.
                output = target_block(model, seq, [anchor], cache)
                cache = output.cache
                next_scores = output.logits[0, -1]
                if next_scores.argmax().item() != verified:
                    raise ValueError(
                        "Target disagrees between batched and singleton greedy verification"
                    )
                seq = torch.cat(
                    [seq, torch.tensor([[anchor]], device=seq.device)], dim=1
                )
        if any(not torch.isfinite(torch.tensor(x)).all() for x in scores):
            raise ValueError("Non-finite verified target logits")
        return (
            answer,
            scores,
            dict(
                proposals=trace,
                draft_tensors_used=len(draft.used),
                target_kv_layers=list(LAYERS),
                elapsed_seconds=time.perf_counter() - start,
            ),
        )
    finally:
        draft.close()
