"""Routing trace reader (compatible with Strata `--dump-routing`) and synthetic workloads.

Reads the exact binary format written by Strata's `--dump-routing` flag and consumed by
`tools/bench_eviction.py`:
    int32 layer, int32 k, k * int32 expert_ids, k * float32 weights

Also generates deterministic synthetic traces for reproducible CPU-only policy comparison
and Section 18 negative-control experiments (uniform random routing with zero locality).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import struct
from typing import Sequence


@dataclass(frozen=True)
class RoutingEvent:
    """Single routed expert lookup at a given (token_idx, layer, expert)."""

    token_idx: int
    layer: int
    expert: int
    weight_bytes: int
    task_category: str = "general"

    @property
    def key(self) -> tuple[int, int]:
        return (self.layer, self.expert)


def load_strata_routing_trace(
    path: Path,
    *,
    n_layers: int = 48,
    n_experts: int = 512,
    expert_bytes: int = 1_310_720,
    max_events: int = 0,
) -> list[RoutingEvent]:
    """Read a native Strata `--dump-routing` binary file into ordered `RoutingEvent`s."""
    blob = path.read_bytes()
    events: list[RoutingEvent] = []
    off = 0
    token_idx = 0
    last_layer = -1

    while off + 8 <= len(blob):
        layer, k = struct.unpack_from("<ii", blob, off)
        off += 8
        need = 8 * k
        if k <= 0 or off + need > len(blob):
            break
        if layer <= last_layer:
            token_idx += 1
        last_layer = layer
        eids = struct.unpack_from(f"<{k}i", blob, off)
        off += need
        for eid in eids:
            if 0 <= layer < n_layers and 0 <= eid < n_experts:
                events.append(
                    RoutingEvent(
                        token_idx=token_idx,
                        layer=layer,
                        expert=eid,
                        weight_bytes=expert_bytes,
                    )
                )
                if max_events > 0 and len(events) >= max_events:
                    return events
    return events


def generate_structured_moe_trace(
    *,
    num_tokens: int = 60,
    num_layers: int = 8,
    num_experts: int = 64,
    top_k: int = 2,
    expert_bytes: int = 1_048_576,
    seed: int = 42,
) -> list[RoutingEvent]:
    """Generate a deterministic non-commutative multi-phase MoE trace (math -> code -> shift).

    Contains explicit non-commutative order-dependent motifs:
    - Phase A (`math` tasks): deterministic motif (e0 -> e1 -> e2) vs reverse (e1 -> e0 -> e3)
    - Phase B (`code` tasks): shifted hot expert subset to test adaptation after topic change.
    """
    rng = random.Random(seed)
    events: list[RoutingEvent] = []
    half = num_tokens // 2
    for tok in range(num_tokens):
        cat = "math" if tok < half else "code"
        base = 0 if cat == "math" else 16
        for layer in range(num_layers):
            # Deterministic non-commutative motif across consecutive tokens
            phase = tok % 4
            if phase == 0:
                e_primary = (base + (layer % 4)) % num_experts
            elif phase == 1:
                e_primary = (base + ((layer + 1) % 4)) % num_experts
            elif phase == 2:
                # Follows (0 -> 1) with expert base+6
                e_primary = (base + 6 + (layer % 2)) % num_experts
            else:
                # Reverse order motif lands on a different expert base+10
                e_primary = (base + 10 + (layer % 2)) % num_experts

            chosen = [e_primary]
            while len(chosen) < top_k:
                # Heavy-tailed secondary expert within the active task cluster
                if rng.random() < 0.78:
                    cand = (base + rng.randint(0, 11)) % num_experts
                else:
                    cand = rng.randint(0, num_experts - 1)
                if cand not in chosen:
                    chosen.append(cand)

            # Vary expert bytes slightly by layer to exercise byte-weighted priority p*t/w
            layer_bytes = expert_bytes + (layer % 3) * (128 * 1024)
            for eid in chosen:
                events.append(
                    RoutingEvent(
                        token_idx=tok,
                        layer=layer,
                        expert=eid,
                        weight_bytes=layer_bytes,
                        task_category=cat,
                    )
                )
    return events


def generate_random_negative_control_trace(
    *,
    num_tokens: int = 60,
    num_layers: int = 8,
    num_experts: int = 64,
    top_k: int = 2,
    expert_bytes: int = 1_048_576,
    seed: int = 1337,
) -> list[RoutingEvent]:
    """Section 18 negative control: i.i.d. uniform random expert selection with zero locality."""
    rng = random.Random(seed)
    events: list[RoutingEvent] = []
    for tok in range(num_tokens):
        for layer in range(num_layers):
            chosen = rng.sample(range(num_experts), k=min(top_k, num_experts))
            for eid in chosen:
                events.append(
                    RoutingEvent(
                        token_idx=tok,
                        layer=layer,
                        expert=eid,
                        weight_bytes=expert_bytes,
                        task_category="random_negative_control",
                    )
                )
    return events


def trace_summary(events: Sequence[RoutingEvent]) -> dict[str, int]:
    distinct = len({e.key for e in events})
    tokens = len({e.token_idx for e in events})
    total_bytes = sum(e.weight_bytes for e in events)
    return {
        "total_lookups": len(events),
        "distinct_experts": distinct,
        "num_tokens": tokens,
        "total_logical_bytes": total_bytes,
    }
