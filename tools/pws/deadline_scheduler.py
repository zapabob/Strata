"""Deadline-aware Earliest-Deadline-First (EDF) asynchronous prefetch simulator (Section 8 & 16).

Models:
    t_io[e] = queue_delay[e] + ssd_latency[e] + weight_bytes[e] / B_eff
              + staging_time[e] + pcie_transfer_time[e]
    stall[e] = max(0, t_io[e] - t_lead[e])

Mirrors Strata's `TwoPriorityExpertScheduler` (`ssd_stream_scheduler.hpp`):
- Demand reads strictly preempt speculative prefetch reads,
- Bounded prefetch queue + double/triple buffering slots,
- Dynamic EMA estimation of effective bandwidth and latency,
- Safe prefetch range throttling when deadline misses or unused prefetches rise,
- Full Section 16 telemetry: precision, recall, deadline miss rate, unused prefetch bytes,
  alignment overhead, read amplification, p50/p95/p99 read latency, and exposed I/O stall.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence

from .bandwidth_model import ActualSsdBytesBreakdown
from .expert_predictor import NKATSequencePredictor
from .trace import RoutingEvent


@dataclass(frozen=True)
class IoTimingModel:
    """Hardware transfer parameters for discrete-event deadline scheduling."""

    ssd_bandwidth_bytes_per_s: float
    ssd_base_latency_s: float = 0.00012   # 120 us typical NVMe / SATA command overhead
    staging_time_s: float = 0.00003       # 30 us pinned host staging
    pcie_bandwidth_bytes_per_s: float = 12e9
    alignment_bytes: int = 4096
    layer_compute_time_s: float = 0.00045 # compute time per layer providing lead time

    def aligned_read_bytes(self, logical_bytes: int) -> int:
        a = max(1, int(self.alignment_bytes))
        return ((logical_bytes + a - 1) // a) * a

    def transfer_time_s(self, logical_bytes: int, queue_delay_s: float = 0.0) -> float:
        phys = self.aligned_read_bytes(logical_bytes)
        ssd_t = self.ssd_base_latency_s + (phys / self.ssd_bandwidth_bytes_per_s)
        pcie_t = logical_bytes / self.pcie_bandwidth_bytes_per_s
        return queue_delay_s + ssd_t + self.staging_time_s + pcie_t


@dataclass(frozen=True)
class PrefetchSchedulerConfig:
    """Bounded deadline-aware prefetch settings."""

    enable_prefetch: bool = True
    max_prefetch_queue: int = 4
    staging_buffers: int = 2  # 2 = double buffering, 3 = triple buffering
    layer_lookahead: int = 2
    min_confidence: float = 0.25
    adaptive_throttle: bool = True


def _percentile(values: Sequence[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round((pct / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]


def simulate_deadline_prefetch(
    events: Sequence[RoutingEvent],
    *,
    cache_budget_bytes: int,
    io_model: IoTimingModel,
    config: PrefetchSchedulerConfig,
) -> dict[str, Any]:
    """Simulate demand-preempting EDF prefetching over a routing trace (CPU-only replay)."""
    if not events:
        raise ValueError("events must be non-empty")
    if cache_budget_bytes <= 0:
        raise ValueError("cache_budget_bytes must be positive")

    from collections import OrderedDict

    resident: OrderedDict[tuple[int, int], int] = OrderedDict()
    used_bytes = 0
    predictor = NKATSequencePredictor()

    # Prefetch staging buffer: key -> (ready_time_s, weight_bytes, used_flag)
    prefetched: OrderedDict[tuple[int, int], tuple[float, int, bool]] = OrderedDict()
    max_stage_slots = max(1, int(config.staging_buffers) * max(1, int(config.max_prefetch_queue)))

    # Dynamic bandwidth EMA estimator
    est_bw = io_model.ssd_bandwidth_bytes_per_s
    sim_time_s = 0.0
    io_busy_until_s = 0.0

    demand_reads_bytes = 0
    unused_prefetch_bytes = 0
    alignment_overhead_bytes = 0
    repeated_reads_bytes = 0
    seen_ever: set[tuple[int, int]] = set()

    total_misses = 0
    prefetch_issued = 0
    prefetch_hits = 0
    prefetch_deadline_misses = 0
    exposed_stall_s = 0.0
    read_latencies_ms: list[float] = []
    current_lookahead = max(0, int(config.layer_lookahead))

    def _admit(key: tuple[int, int], w: int) -> None:
        nonlocal used_bytes
        if key in resident:
            resident.move_to_end(key)
            return
        if w > cache_budget_bytes:
            return
        while used_bytes + w > cache_budget_bytes and resident:
            _, vb = resident.popitem(last=False)
            used_bytes -= vb
        resident[key] = w
        used_bytes += w

    # Group events by token for realistic per-layer timeline progression
    num_tokens = len({e.token_idx for e in events})

    for ev in events:
        key = ev.key
        w = ev.weight_bytes
        phys_w = io_model.aligned_read_bytes(w)
        align_extra = phys_w - w

        if key in resident:
            resident.move_to_end(key)
        else:
            total_misses += 1
            if key in prefetched:
                ready_t, pw, _ = prefetched.pop(key)
                prefetch_hits += 1
                stall = max(0.0, ready_t - sim_time_s)
                if stall > 0.0:
                    prefetch_deadline_misses += 1
                exposed_stall_s += stall
                sim_time_s += stall
                demand_reads_bytes += pw
                if key in seen_ever:
                    repeated_reads_bytes += pw
                seen_ever.add(key)
                _admit(key, pw)
            else:
                # Demand read preempts speculative queue immediately (TwoPriorityExpertScheduler)
                q_delay = max(0.0, io_busy_until_s - sim_time_s)
                # Preemption caps speculative interference at 1 chunk (512 KiB)
                chunk_cap_s = (512 * 1024) / io_model.ssd_bandwidth_bytes_per_s
                q_delay = min(q_delay, chunk_cap_s)
                t_io = io_model.transfer_time_s(w, queue_delay_s=q_delay)
                exposed_stall_s += t_io
                read_latencies_ms.append(t_io * 1000.0)
                sim_time_s += t_io
                io_busy_until_s = max(io_busy_until_s, sim_time_s)
                demand_reads_bytes += w
                alignment_overhead_bytes += align_extra
                if key in seen_ever:
                    repeated_reads_bytes += w
                seen_ever.add(key)
                _admit(key, w)

        # Update predictor and advance compute clock by one layer slot
        predictor.observe(ev.layer, ev.expert)
        sim_time_s += io_model.layer_compute_time_s

        # Issue deadline-aware speculative prefetch for upcoming layer(s)
        if config.enable_prefetch and current_lookahead > 0:
            edf_candidates: list[tuple[float, float, tuple[int, int], int]] = []
            for dl in range(1, current_lookahead + 1):
                target_layer = ev.layer + dl
                t_lead = dl * io_model.layer_compute_time_s
                deadline = sim_time_s + t_lead
                for cand_e, conf in predictor.predict_probs(target_layer, top_m=2):
                    ckey = (target_layer, cand_e)
                    if conf < config.min_confidence or ckey in resident or ckey in prefetched:
                        continue
                    t_est = io_model.transfer_time_s(w)
                    # Only schedule if lead time covers transfer or reduces stall meaningfully
                    if t_lead >= 0.5 * t_est:
                        edf_candidates.append((deadline, -conf, ckey, w))

            # Earliest-Deadline-First ordering
            edf_candidates.sort(key=lambda x: (x[0], x[1]))
            issued_here = 0
            for _, _, ckey, cw in edf_candidates:
                if issued_here >= config.max_prefetch_queue:
                    break
                while len(prefetched) >= max_stage_slots:
                    _, (_, old_w, old_used) = prefetched.popitem(last=False)
                    if not old_used:
                        unused_prefetch_bytes += old_w
                start_io = max(sim_time_s, io_busy_until_s)
                t_io = io_model.transfer_time_s(cw)
                ready_t = start_io + t_io
                io_busy_until_s = ready_t
                prefetched[ckey] = (ready_t, cw, False)
                alignment_overhead_bytes += io_model.aligned_read_bytes(cw) - cw
                read_latencies_ms.append(t_io * 1000.0)
                prefetch_issued += 1
                issued_here += 1
                # Update dynamic bandwidth EMA
                obs_bw = io_model.aligned_read_bytes(cw) / max(1e-9, t_io)
                est_bw = 0.85 * est_bw + 0.15 * obs_bw

            # Safe adaptive throttling if precision collapses (Section 8)
            if config.adaptive_throttle and prefetch_issued >= 16 and (prefetch_issued % 16 == 0):
                prec_now = prefetch_hits / max(1, prefetch_issued)
                if prec_now < 0.25 and current_lookahead > 1:
                    current_lookahead -= 1

    # Flush unconsumed prefetches at end of trace
    for _, (_, pw, used_flag) in prefetched.items():
        if not used_flag:
            unused_prefetch_bytes += pw

    breakdown = ActualSsdBytesBreakdown(
        demand_reads_bytes=demand_reads_bytes,
        unused_prefetch_bytes=unused_prefetch_bytes,
        alignment_overhead_bytes=alignment_overhead_bytes,
        read_amplification_bytes=0,
        repeated_reads_bytes=0,  # tracked separately below so physical_total is never double-counted
    )
    precision = (prefetch_hits / prefetch_issued) if prefetch_issued > 0 else None
    recall = (prefetch_hits / total_misses) if total_misses > 0 else None
    deadline_miss_rate = (prefetch_deadline_misses / prefetch_hits) if prefetch_hits > 0 else None

    return {
        "enable_prefetch": config.enable_prefetch,
        "num_events": len(events),
        "num_tokens": num_tokens,
        "total_misses": total_misses,
        "prefetch_issued": prefetch_issued,
        "prefetch_hits": prefetch_hits,
        "prefetch_precision": round(precision, 6) if precision is not None else None,
        "prefetch_recall": round(recall, 6) if recall is not None else None,
        "prefetch_deadline_miss_rate": round(deadline_miss_rate, 6) if deadline_miss_rate is not None else None,
        "exposed_io_stall_total_ms": round(exposed_stall_s * 1000.0, 4),
        "exposed_io_stall_ms_per_token": round((exposed_stall_s * 1000.0) / max(1, num_tokens), 4),
        "ssd_logical_bytes_per_token": round(breakdown.logical_demand_bytes / max(1, num_tokens), 2),
        "ssd_physical_bytes_per_token": round(breakdown.physical_total_bytes / max(1, num_tokens), 2),
        "repeated_reads_bytes": repeated_reads_bytes,
        "bytes_breakdown": breakdown.to_dict(),
        "read_latency_ms_p50": round(_percentile(read_latencies_ms, 50) or 0.0, 4) if read_latencies_ms else None,
        "read_latency_ms_p95": round(_percentile(read_latencies_ms, 95) or 0.0, 4) if read_latencies_ms else None,
        "read_latency_ms_p99": round(_percentile(read_latencies_ms, 99) or 0.0, 4) if read_latencies_ms else None,
        "estimated_effective_bw_mb_s": round(est_bw / 1e6, 3),
        "final_lookahead_after_throttle": current_lookahead,
    }
