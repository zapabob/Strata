#!/usr/bin/env python3
"""CLI entrypoint for NKAT-URT Predictive Weight Streaming (PWS) audit and replay.

Subcommands:
    math-check  Verify Section 4, 5, 6, 8, 9, 10 mathematical bounds & negative controls
    replay      Replay a Strata `--dump-routing` trace or synthetic trace across all 7 policies
                and deadline-aware EDF prefetching
    factorise   Evaluate NKAT common-basis factorisation, URT bounds, and Spin(8) vs SO(8)
    ssd-probe   Non-destructive unbuffered (FILE_FLAG_NO_BUFFERING) read bandwidth probe on a
                read-only existing file (zero model writes or mutations)
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import logging
import math
from pathlib import Path
import random
import sys
import time
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from pws import PWS_SCHEMA_VERSION  # noqa: E402
from pws.bandwidth_model import dense_full_weight_streaming_bound, moe_cache_hit_requirement  # noqa: E402
from pws.cache_policy import compare_all_cache_policies  # noqa: E402
from pws.certificates import certify_pws_tsi_efficiency  # noqa: E402
from pws.deadline_scheduler import IoTimingModel, PrefetchSchedulerConfig, simulate_deadline_prefetch  # noqa: E402
from pws.factorisation import (  # noqa: E402
    analyse_common_basis_factorisation,
    compare_spin8_vs_so8_quantisation,
    evaluate_common_basis_adoption,
)
from pws.report import render_pws_markdown_report  # noqa: E402
from pws.roofline import MultiTierRooflineInput, evaluate_multitier_roofline  # noqa: E402
from pws.trace import (  # noqa: E402
    generate_random_negative_control_trace,
    generate_structured_moe_trace,
    load_strata_routing_trace,
    trace_summary,
)

LOGGER = logging.getLogger("strata.pws_bench")


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def run_pws_math_checks() -> dict[str, Any]:
    """Verify exact Section 4, 5, 6, 10 mathematical examples and negative controls."""
    dense = dense_full_weight_streaming_bound(
        num_params=27e9, effective_bpw=3.69, ssd_bandwidths_gb_s=(3.5, 7.0, 14.0)
    )
    assert abs(dense["weight_gb_decimal"] - 12.45375) < 1e-5
    assert abs(dense["ceilings"][0]["max_decode_tok_s"] - 0.28104) < 1e-3
    assert abs(dense["ceilings"][1]["max_decode_tok_s"] - 0.56208) < 1e-3
    assert abs(dense["ceilings"][2]["max_decode_tok_s"] - 1.12416) < 1e-3

    moe = moe_cache_hit_requirement(
        active_params=3e9,
        effective_bpw=2.0,
        ssd_bandwidth_gb_s=3.5,
        target_decode_tok_s=30.0,
        probe_hit_rates=(0.90,),
    )
    assert abs(moe["active_weight_mb"] - 750.0) < 1e-6
    assert abs(moe["allowable_ssd_mb_per_token"] - 116.666667) < 1e-3
    assert abs(moe["required_byte_hit_rate"] - 0.844444) < 1e-4
    assert abs(moe["probes"][0]["ideal_ssd_demand_mb_per_token"] - 75.0) < 1e-6
    assert abs(moe["probes"][0]["ssd_bandwidth_only_ceiling_tok_s"] - 46.666667) < 1e-3

    roof = evaluate_multitier_roofline(
        MultiTierRooflineInput(
            flops_per_token=6e9,
            vram_bytes_per_token=800e6,
            ram_bytes_per_token=200e6,
            pcie_bytes_per_token=100e6,
            ssd_bytes_per_token=75e6,
            gpu_flops_per_s=24e12,
            vram_bw_bytes_per_s=448e9,
            ram_bw_bytes_per_s=40e9,
            pcie_bw_bytes_per_s=12e9,
            ssd_bw_bytes_per_s=3.5e9,
            cpu_compute_s_per_token=0.012,
            exposed_io_stall_s_per_token=0.008,
        )
    )
    assert roof["binding_roofline_tier"] == "ssd_bandwidth"
    assert roof["exceeds_roofline_impossible"]

    adopt_good = evaluate_common_basis_adoption(
        m=2048, n=2048, rank=64, orig_bits=4.0, corr_bits=4.0,
        metadata_bytes=4096, effective_ssd_bw_bytes_per_s=3.5e9,
        additional_reconstruction_and_sync_s=0.0001,
    )
    adopt_bad = evaluate_common_basis_adoption(
        m=2048, n=2048, rank=64, orig_bits=4.0, corr_bits=4.0,
        metadata_bytes=4096, effective_ssd_bw_bytes_per_s=3.5e9,
        additional_reconstruction_and_sync_s=0.005,
    )
    assert adopt_good["net_speedup_justified"]
    assert not adopt_bad["net_speedup_justified"]

    tsi_cert = certify_pws_tsi_efficiency(
        optimisation_kind="lossless_cache_placement",
        p_ref=0.5,
        cost_ref_s=2.0,
        p_new=0.5,
        cost_new_s=1.4,
        bit_exact_parity_verified=True,
    )
    assert tsi_cert["improved"]

    return {
        "schema": PWS_SCHEMA_VERSION,
        "pass": True,
        "dense_section4_bound": dense,
        "moe_section5_bound": moe,
        "multitier_roofline": roof,
        "factorisation_adoption_positive": adopt_good,
        "factorisation_adoption_negative_control": adopt_bad,
        "tsi_lossless_cert": tsi_cert,
    }


def _probe_unbuffered_windows_file(
    file_path: Path,
    *,
    seq_mb: int = 128,
    rand_reads: int = 128,
    block_bytes: int = 1048576,
    rand_block_bytes: int = 65536,
) -> dict[str, Any]:
    """Read-only unbuffered (FILE_FLAG_NO_BUFFERING) SSD read benchmark on Windows.

    Bypasses the OS page cache so physical SSD read bandwidth is separated from RAM cache.
    Never modifies or writes to the target file.
    """
    if sys.platform != "win32":
        return {"supported": False, "reason": "Windows FILE_FLAG_NO_BUFFERING probe requires win32"}
    if not file_path.is_file():
        raise FileNotFoundError(f"Probe file not found: {file_path}")

    file_size = file_path.stat().st_size
    if file_size < max(block_bytes, 4 * 1024 * 1024):
        raise ValueError(f"Probe file too small ({file_size} bytes); need >= 4 MiB")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    OPEN_EXISTING = 3
    FILE_FLAG_NO_BUFFERING = 0x20000000
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    MEM_RELEASE = 0x8000
    PAGE_READWRITE = 0x04
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel32.VirtualAlloc.restype = ctypes.c_void_p
    kernel32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
    kernel32.VirtualFree.restype = wintypes.BOOL
    kernel32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD]
    kernel32.ReadFile.restype = wintypes.BOOL
    kernel32.ReadFile.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p,
    ]
    kernel32.SetFilePointerEx.restype = wintypes.BOOL
    kernel32.SetFilePointerEx.argtypes = [
        wintypes.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD,
    ]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    handle = kernel32.CreateFileW(
        str(file_path),
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        FILE_FLAG_NO_BUFFERING,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        raise OSError(f"CreateFileW(FILE_FLAG_NO_BUFFERING) failed: err={ctypes.get_last_error()}")

    buf_size = max(block_bytes, rand_block_bytes)
    buf = kernel32.VirtualAlloc(None, buf_size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
    if not buf:
        kernel32.CloseHandle(handle)
        raise MemoryError("VirtualAlloc failed for page-aligned probe buffer")

    try:
        # 1. Sequential unbuffered read (1 MiB aligned blocks)
        max_seq_bytes = min(seq_mb * 1024 * 1024, (file_size // block_bytes) * block_bytes)
        n_seq_blocks = max(1, max_seq_bytes // block_bytes)
        read_out = wintypes.DWORD(0)
        seq_bytes = 0
        seq_lat_ms: list[float] = []

        t_seq0 = time.perf_counter()
        for _ in range(n_seq_blocks):
            tb0 = time.perf_counter()
            ok = kernel32.ReadFile(handle, buf, block_bytes, ctypes.byref(read_out), None)
            if not ok:
                raise OSError(f"Sequential ReadFile failed: err={ctypes.get_last_error()}")
            seq_lat_ms.append((time.perf_counter() - tb0) * 1000.0)
            seq_bytes += int(read_out.value)
        seq_elapsed = time.perf_counter() - t_seq0

        # 2. Random unbuffered 64 KiB reads across full file span (4096-byte aligned)
        max_off_aligned = ((file_size - rand_block_bytes) // 4096) * 4096
        rng = random.Random(20261125)
        rand_bytes = 0
        rand_lat_ms: list[float] = []
        new_pos = ctypes.c_longlong(0)

        t_rand0 = time.perf_counter()
        for _ in range(rand_reads):
            off = rng.randrange(0, max(4096, max_off_aligned), 4096)
            if not kernel32.SetFilePointerEx(handle, off, ctypes.byref(new_pos), 0):
                raise OSError(f"SetFilePointerEx failed: err={ctypes.get_last_error()}")
            tb0 = time.perf_counter()
            ok = kernel32.ReadFile(handle, buf, rand_block_bytes, ctypes.byref(read_out), None)
            if not ok:
                raise OSError(f"Random ReadFile failed: err={ctypes.get_last_error()}")
            rand_lat_ms.append((time.perf_counter() - tb0) * 1000.0)
            rand_bytes += int(read_out.value)
        rand_elapsed = time.perf_counter() - t_rand0
    finally:
        kernel32.VirtualFree(buf, 0, MEM_RELEASE)
        kernel32.CloseHandle(handle)

    def _pct(vals: list[float], p: float) -> float:
        s = sorted(vals)
        return s[min(len(s) - 1, max(0, int(round((p / 100.0) * (len(s) - 1)))))]

    return {
        "supported": True,
        "unbuffered_bypass_os_page_cache": True,
        "file_size_bytes": file_size,
        "seq_block_bytes": block_bytes,
        "seq_bytes_read": seq_bytes,
        "seq_elapsed_s": round(seq_elapsed, 4),
        "seq_bandwidth_mb_s": round((seq_bytes / 1e6) / max(1e-9, seq_elapsed), 2),
        "seq_latency_ms_p50": round(_pct(seq_lat_ms, 50), 3),
        "seq_latency_ms_p95": round(_pct(seq_lat_ms, 95), 3),
        "seq_latency_ms_p99": round(_pct(seq_lat_ms, 99), 3),
        "rand_block_bytes": rand_block_bytes,
        "rand_reads": rand_reads,
        "rand_bytes_read": rand_bytes,
        "rand_elapsed_s": round(rand_elapsed, 4),
        "rand_bandwidth_mb_s": round((rand_bytes / 1e6) / max(1e-9, rand_elapsed), 2),
        "rand_latency_ms_p50": round(_pct(rand_lat_ms, 50), 3),
        "rand_latency_ms_p95": round(_pct(rand_lat_ms, 95), 3),
        "rand_latency_ms_p99": round(_pct(rand_lat_ms, 99), 3),
    }


def cmd_math_check(args: argparse.Namespace) -> int:
    res = run_pws_math_checks()
    txt = json.dumps(res, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    LOGGER.info("PWS mathematical self-checks PASSED:\n%s", txt)
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    if args.trace is not None:
        events = load_strata_routing_trace(
            args.trace,
            n_layers=args.n_layers,
            n_experts=args.n_experts,
            expert_bytes=args.expert_bytes,
            max_events=args.max_events,
        )
        label = args.trace.name
    elif args.workload == "random":
        events = generate_random_negative_control_trace(num_tokens=args.tokens, expert_bytes=args.expert_bytes)
        label = "synthetic_random_negative_control"
    else:
        events = generate_structured_moe_trace(num_tokens=args.tokens, expert_bytes=args.expert_bytes)
        label = "synthetic_structured_noncommutative_moe"

    budget_bytes = int(args.cache_mb * 1024 * 1024)
    cache_cmp = compare_all_cache_policies(events, memory_budget_bytes=budget_bytes)
    io_model = IoTimingModel(ssd_bandwidth_bytes_per_s=args.ssd_gb_s * 1e9)
    demand_only = simulate_deadline_prefetch(
        events,
        cache_budget_bytes=budget_bytes,
        io_model=io_model,
        config=PrefetchSchedulerConfig(enable_prefetch=False),
    )
    edf_prefetch = simulate_deadline_prefetch(
        events,
        cache_budget_bytes=budget_bytes,
        io_model=io_model,
        config=PrefetchSchedulerConfig(enable_prefetch=True, layer_lookahead=args.lookahead),
    )
    payload = {
        "schema": PWS_SCHEMA_VERSION,
        "releaseQualified": False,
        "trace_label": label,
        "trace_summary": trace_summary(events),
        "cache_policies": cache_cmp,
        "deadline_prefetch": {
            "demand_only": demand_only,
            "edf_predictive_prefetch": edf_prefetch,
        },
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_pws_markdown_report(payload) + "\n", encoding="utf-8")
    LOGGER.info("PWS replay finished (%s):\n%s", label, render_pws_markdown_report(payload))
    return 0


def cmd_factorise(args: argparse.Namespace) -> int:
    rng = random.Random(42)
    m, n = 8, 8
    # Construct correlated low-rank + residual experts and an uncorrelated negative control
    shared = [[math.sin(0.5 * i + 0.3 * j) for j in range(n)] for i in range(m)]
    u_base = [[math.cos(0.4 * i + k) for k in range(2)] for i in range(m)]
    v_base = [[math.sin(0.6 * j - k) for k in range(2)] for j in range(n)]
    experts = []
    for e in range(4):
        scale = 0.25 * (e + 1)
        w = [
            [
                shared[i][j]
                + scale * (u_base[i][0] * v_base[j][0] - 0.5 * u_base[i][1] * v_base[j][1])
                + rng.uniform(-0.02, 0.02)
                for j in range(n)
            ]
            for i in range(m)
        ]
        experts.append(w)

    fact = analyse_common_basis_factorisation(experts, rank=args.rank)
    spin_cmp = compare_spin8_vs_so8_quantisation(experts[0], bits=args.bits)
    out = {"schema": PWS_SCHEMA_VERSION, "factorisation": fact, "spin8_vs_so8": spin_cmp}
    txt = json.dumps(out, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    LOGGER.info("PWS factorisation & Spin(8) audit:\n%s", txt)
    return 0


def cmd_ssd_probe(args: argparse.Namespace) -> int:
    res = _probe_unbuffered_windows_file(
        args.file,
        seq_mb=args.seq_mb,
        rand_reads=args.rand_reads,
    )
    txt = json.dumps(res, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    LOGGER.info("Unbuffered SSD read probe (bypassing OS page cache):\n%s", txt)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NKAT-URT Predictive Weight Streaming (PWS) CLI.")
    p.add_argument("--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    pm = sub.add_parser("math-check", help="Run exact PWS mathematical and negative-control checks.")
    pm.add_argument("--out", type=Path, default=None)
    pm.set_defaults(func=cmd_math_check)

    pr = sub.add_parser("replay", help="Replay a Strata --dump-routing or synthetic MoE trace.")
    pr.add_argument("--trace", type=Path, default=None, help="Optional native --dump-routing binary trace.")
    pr.add_argument("--workload", choices=["structured", "random"], default="structured")
    pr.add_argument("--tokens", type=int, default=60)
    pr.add_argument("--n-layers", type=int, default=48)
    pr.add_argument("--n-experts", type=int, default=512)
    pr.add_argument("--expert-bytes", type=int, default=1_048_576)
    pr.add_argument("--max-events", type=int, default=0)
    pr.add_argument("--cache-mb", type=float, default=64.0)
    pr.add_argument("--ssd-gb-s", type=float, default=0.5)
    pr.add_argument("--lookahead", type=int, default=2)
    pr.add_argument("--out", type=Path, default=None)
    pr.add_argument("--md-out", type=Path, default=None)
    pr.set_defaults(func=cmd_replay)

    pf = sub.add_parser("factorise", help="Run NKAT common-basis SVD & Spin(8) vs SO(8) audit.")
    pf.add_argument("--rank", type=int, default=2)
    pf.add_argument("--bits", type=int, default=4)
    pf.add_argument("--out", type=Path, default=None)
    pf.set_defaults(func=cmd_factorise)

    ps = sub.add_parser("ssd-probe", help="Read-only unbuffered Windows SSD bandwidth probe.")
    ps.add_argument("file", type=Path, help="Existing read-only file on target SSD.")
    ps.add_argument("--seq-mb", type=int, default=128)
    ps.add_argument("--rand-reads", type=int, default=128)
    ps.add_argument("--out", type=Path, default=None)
    ps.set_defaults(func=cmd_ssd_probe)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.verbose)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
