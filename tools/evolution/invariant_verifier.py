"""Immutable invariant, resource-safety, and reward-hacking verifier boundary (Sections 5, 18, 26).

Candidate-generating agents must never modify these bounds, resource floors, or
numerical acceptance gates. Any candidate failing a hard constraint is rejected
regardless of measured speed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .genome import DEFAULT_OPERATOR_SEQUENCE, InferenceGenome, VALID_CACHE_POLICIES


@dataclass(frozen=True)
class ResourceGuardLimits:
    """Immutable Hakua / Strata hardware safety floors (Section 26)."""

    min_free_ram_bytes: int = 3 * 1024 * 1024 * 1024       # 3 GiB RAM floor
    min_free_commit_bytes: int = 4 * 1024 * 1024 * 1024    # 4 GiB Windows commit floor
    min_vram_reserve_bytes: int = 768 * 1024 * 1024        # 768 MiB VRAM floor
    min_free_disk_c_bytes: int = 5 * 1024 * 1024 * 1024    # 5 GiB C: floor
    min_free_disk_h_bytes: int = 10 * 1024 * 1024 * 1024   # 10 GiB H: floor
    max_gpu_cache_bytes: int = 12 * 1024 * 1024 * 1024     # Conservative cap for 16 GB RTX 5060 Ti
    max_ram_cache_bytes: int = 20 * 1024 * 1024 * 1024     # Conservative cap for 32 GB RAM
    max_build_jobs: int = 5


@dataclass(frozen=True)
class InvariantCheckReport:
    """Structured Level-0 invariant verification outcome."""

    passed: bool
    violations: tuple[str, ...]
    checked_constraints: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "violations": list(self.violations),
            "checked_constraints": list(self.checked_constraints),
        }


def verify_genome_invariants(
    genome: InferenceGenome,
    *,
    limits: ResourceGuardLimits = ResourceGuardLimits(),
) -> InvariantCheckReport:
    """Level-0 static invariant & hardware safety verification (cannot be bypassed by speed)."""
    violations: list[str] = []
    checked = (
        "cache_budget_bounds",
        "cache_decay_and_hysteresis",
        "prefetch_bounds",
        "io_alignment_4k",
        "staging_buffer_bounds",
        "cache_policy_valid",
        "operator_sequence_permutation",
    )

    if not (1024 * 1024 <= genome.gpu_cache_budget_bytes <= limits.max_gpu_cache_bytes):
        violations.append(
            f"gpu_cache_budget_bytes={genome.gpu_cache_budget_bytes} outside [1MiB, {limits.max_gpu_cache_bytes}]"
        )
    if not (0 <= genome.ram_cache_budget_bytes <= limits.max_ram_cache_bytes):
        violations.append(
            f"ram_cache_budget_bytes={genome.ram_cache_budget_bytes} outside [0, {limits.max_ram_cache_bytes}]"
        )
    if not (0.50 <= genome.cache_decay <= 0.9999):
        violations.append(f"cache_decay={genome.cache_decay} outside [0.50, 0.9999]")
    if not (0.0 <= genome.eviction_hysteresis <= 4.0):
        violations.append(f"eviction_hysteresis={genome.eviction_hysteresis} outside [0.0, 4.0]")
    if not (0 <= genome.prefetch_depth <= 8):
        violations.append(f"prefetch_depth={genome.prefetch_depth} outside [0, 8]")
    if not (0.0 <= genome.prefetch_threshold <= 1.0):
        violations.append(f"prefetch_threshold={genome.prefetch_threshold} outside [0.0, 1.0]")
    if not (1 <= genome.prefetch_queue_size <= 16):
        violations.append(f"prefetch_queue_size={genome.prefetch_queue_size} outside [1, 16]")
    if genome.io_chunk_bytes < 4096 or (genome.io_chunk_bytes % 4096) != 0 or genome.io_chunk_bytes > 16 * 1024 * 1024:
        violations.append(f"io_chunk_bytes={genome.io_chunk_bytes} must be a 4096-byte multiple in [4KiB, 16MiB]")
    if not (1 <= genome.staging_buffers <= 4):
        violations.append(f"staging_buffers={genome.staging_buffers} outside [1, 4]")
    if genome.cache_policy not in VALID_CACHE_POLICIES:
        violations.append(f"cache_policy={genome.cache_policy!r} not in {VALID_CACHE_POLICIES}")
    if set(genome.operator_sequence) != set(DEFAULT_OPERATOR_SEQUENCE) or len(genome.operator_sequence) != len(DEFAULT_OPERATOR_SEQUENCE):
        violations.append("operator_sequence must be a permutation of A1..A7")

    return InvariantCheckReport(
        passed=len(violations) == 0,
        violations=tuple(violations),
        checked_constraints=checked,
    )


def verify_hard_acceptance_gates(
    *,
    numerical_correctness_pass: bool,
    resource_guards_pass: bool,
    model_integrity_pass: bool,
    required_quality_pass: bool,
    verifier_integrity_pass: bool,
) -> dict[str, Any]:
    """Section 5 hard gate: any failure disqualifies candidate regardless of throughput."""
    gates = {
        "numerical_correctness": bool(numerical_correctness_pass),
        "resource_guards": bool(resource_guards_pass),
        "model_integrity": bool(model_integrity_pass),
        "required_quality": bool(required_quality_pass),
        "verifier_integrity": bool(verifier_integrity_pass),
    }
    failed = [k for k, ok in gates.items() if not ok]
    return {
        "accepted_for_archive": len(failed) == 0,
        "gates": gates,
        "failed_gates": failed,
    }


def build_robust_kbench_cuda_verification_plan(
    *,
    kernel_name: str,
    binary_path: str,
    seeds: Sequence[int] = (7, 42, 1337, 2026),
    unaligned_shapes: Sequence[tuple[int, int, int]] = ((1, 13, 129), (3, 255, 513), (7, 1023, 2049)),
) -> dict[str, Any]:
    """Build an immutable Section 18 robust-kbench-style CUDA verification checklist.

    Documents required checks without claiming they have passed prior to actual execution.
    """
    return {
        "kernel_name": kernel_name,
        "executed": False,
        "sanitizer_commands": [
            ["compute-sanitizer", "--tool", "memcheck", binary_path],
            ["compute-sanitizer", "--tool", "racecheck", binary_path],
            ["compute-sanitizer", "--tool", "synccheck", binary_path],
        ],
        "required_checks": [
            "multi_seed_determinism",
            "unaligned_input_shapes",
            "boundary_and_nan_inf_inputs",
            "real_model_activation_distributions",
            "strict_fp64_reference_tolerance_unchanged",
            "explicit_cudaDeviceSynchronize_before_timing",
        ],
        "seeds": list(seeds),
        "unaligned_shapes": [list(s) for s in unaligned_shapes],
        "reward_hacking_prohibitions": [
            "no_skipped_computation",
            "no_shape_spoofing",
            "no_seed_overfitting",
            "no_precomputed_output_cache",
            "no_unsynchronised_async_timing",
            "no_tolerance_relaxation",
        ],
    }
