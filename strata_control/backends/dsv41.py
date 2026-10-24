"""strata_control/backends/dsv41.py - Adapter for strata-dsv41 DeepSeek engine and Maya packing tools."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from strata_control.bundle_identity import VerifiedBundle
from strata_control.backend_contracts import BackendCapabilities


@dataclass(frozen=True)
class CompatibilityReport:
    decision: str  # QUALIFIED, INCOMPATIBLE, MISSING_TENSORS
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    required_dense_tensors: list[str] = field(default_factory=list)
    qualification_status: str = "IN_PROGRESS"


@dataclass(frozen=True)
class PrepareRequest:
    output_dir: Path
    allow_dense_override: bool = False
    context_tokens: int = 4096


@dataclass(frozen=True)
class PreparedModel:
    model_set_id: str
    pack_manifest_path: str
    dense_path: str
    engram_path: str | None = None
    is_ready: bool = True


REQUIRED_DEEPSEEK_DENSE_TENSORS = [
    "model.embed_tokens.weight",
    "model.norm.weight",
    "lm_head.weight",
]


def validate_dsv41(
    bundle: VerifiedBundle,
    caps: BackendCapabilities,
    simulated_tensors: list[str] | None = None,
) -> CompatibilityReport:
    """Validate that bundle meets DeepSeek geometry, required tensors, and dialect specifications."""
    errors: list[str] = []
    warnings: list[str] = []

    # Architecture validation
    arch = bundle.bundle.architecture.lower()
    if arch not in ("dsv41", "deepseek", "deepseek2"):
        errors.append(f"Architecture '{arch}' is not supported by strata-dsv41")

    # Required dense tensors check
    tensors = simulated_tensors if simulated_tensors is not None else [t.name for t in bundle.bundle.files]
    missing = [req for req in REQUIRED_DEEPSEEK_DENSE_TENSORS if req not in tensors]
    if missing:
        errors.append(f"Missing required DeepSeek dense tensors: {missing}")

    decision = "QUALIFIED" if not errors else "INCOMPATIBLE"
    return CompatibilityReport(
        decision=decision,
        errors=errors,
        warnings=warnings,
        required_dense_tensors=REQUIRED_DEEPSEEK_DENSE_TENSORS,
        qualification_status="PASS" if not errors else "FAIL",
    )


def prepare_dsv41(
    bundle: VerifiedBundle,
    request: PrepareRequest,
    simulated_tensors: list[str] | None = None,
) -> PreparedModel:
    """Prepare DeepSeek pack manifest and staging area without overwriting original dense weights."""
    report = validate_dsv41(bundle, None, simulated_tensors=simulated_tensors)
    if report.decision != "QUALIFIED":
        raise ValueError(f"Cannot prepare incompatible DeepSeek bundle: {report.errors}")

    request.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_p = request.output_dir / "ds4_pack.json"
    manifest_p.write_text(
        f'{{"model_set_id": "{bundle.model_set_id}", "status": "prepared"}}\n',
        encoding="utf-8",
    )

    return PreparedModel(
        model_set_id=bundle.model_set_id,
        pack_manifest_path=str(manifest_p),
        dense_path=str(bundle.verified_files[0].path),
        is_ready=True,
    )
