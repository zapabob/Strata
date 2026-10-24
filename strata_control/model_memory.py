"""strata_control/model_memory.py - Strict hardware memory budgeting and preflight launch rejection for RAM32."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from strata_control.bundle_identity import VerifiedBundle
from strata_control.backend_contracts import BackendCapabilities


@dataclass(frozen=True)
class HardwareSnapshot:
    total_physical_ram_bytes: int
    available_physical_ram_bytes: int
    commit_limit_bytes: int
    available_commit_bytes: int
    total_vram_bytes: int
    free_vram_bytes: int


@dataclass(frozen=True)
class ResourcePolicy:
    max_host_budget_bytes: int = 24 * 1024 * 1024 * 1024  # 24 GiB cap
    min_os_ram_headroom_bytes: int = 4 * 1024 * 1024 * 1024  # 4 GiB OS reserve
    min_commit_headroom_bytes: int = 4 * 1024 * 1024 * 1024  # 4 GiB commit reserve
    vram_reserve_bytes: int = 2 * 1024 * 1024 * 1024  # 2 GiB VRAM reserve


@dataclass(frozen=True)
class MemoryPlan:
    is_launchable: bool
    planned_host_bytes: int
    planned_vram_bytes: int
    headroom_bytes: int
    rejection_reason: str | None = None


def plan_memory(
    bundle: VerifiedBundle,
    caps: BackendCapabilities | None,
    hardware: HardwareSnapshot,
    policy: ResourcePolicy | None = None,
    dense_bytes: int = 6 * 1024 * 1024 * 1024,
    expert_resident_bytes: int = 4 * 1024 * 1024 * 1024,
    scratch_bytes: int = 1 * 1024 * 1024 * 1024,
) -> MemoryPlan:
    """Compute strict separate host RAM and GPU VRAM budget; reject launch if headroom violated."""
    policy = policy or ResourcePolicy()

    # Rule 1: Host and VRAM are NEVER unified into a single pool
    planned_host = dense_bytes + expert_resident_bytes + scratch_bytes
    planned_vram = 2 * 1024 * 1024 * 1024  # KV cache + base staging in VRAM

    # Check host budget cap
    if planned_host > policy.max_host_budget_bytes:
        return MemoryPlan(
            is_launchable=False,
            planned_host_bytes=planned_host,
            planned_vram_bytes=planned_vram,
            headroom_bytes=0,
            rejection_reason=f"Planned host RAM {planned_host / 1e9:.2f}GB exceeds budget cap {policy.max_host_budget_bytes / 1e9:.2f}GB",
        )

    # Check available physical RAM headroom
    if hardware.available_physical_ram_bytes < (planned_host + policy.min_os_ram_headroom_bytes):
        return MemoryPlan(
            is_launchable=False,
            planned_host_bytes=planned_host,
            planned_vram_bytes=planned_vram,
            headroom_bytes=0,
            rejection_reason=(
                f"Insufficient available RAM: requires {planned_host / 1e9:.2f}GB + "
                f"{policy.min_os_ram_headroom_bytes / 1e9:.2f}GB OS reserve, but only "
                f"{hardware.available_physical_ram_bytes / 1e9:.2f}GB available"
            ),
        )

    # Check VRAM headroom
    if hardware.free_vram_bytes < (planned_vram + policy.vram_reserve_bytes):
        return MemoryPlan(
            is_launchable=False,
            planned_host_bytes=planned_host,
            planned_vram_bytes=planned_vram,
            headroom_bytes=0,
            rejection_reason=f"Insufficient free VRAM: requires {planned_vram / 1e9:.2f}GB + {policy.vram_reserve_bytes / 1e9:.2f}GB reserve",
        )

    headroom = hardware.available_physical_ram_bytes - planned_host
    return MemoryPlan(
        is_launchable=True,
        planned_host_bytes=planned_host,
        planned_vram_bytes=planned_vram,
        headroom_bytes=headroom,
    )
