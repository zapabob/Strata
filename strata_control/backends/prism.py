"""strata_control/backends/prism.py - Prism backend adapter for Bonsai PQ2_0/PTQ1_0 dialects."""
from __future__ import annotations

from dataclasses import dataclass
from strata_control.bundle_identity import VerifiedBundle


@dataclass(frozen=True)
class PrismLaunchPlan:
    backend_id: str = "prism"
    binary_path: str = "prism-server"
    args: list[str] = None
    supports_pq2_0: bool = True


def build_prism_plan(bundle: VerifiedBundle, port: int = 18503) -> PrismLaunchPlan:
    dialect = bundle.bundle.dialect.lower()
    if dialect not in ("pq2_0", "ptq1_0", "standard"):
        raise ValueError(f"Prism backend does not support dialect '{dialect}'")

    args = [
        "--model", bundle.verified_files[0].path,
        "--dialect", dialect,
        "--port", str(port),
        "--host", "127.0.0.1",
    ]
    return PrismLaunchPlan(args=args)
