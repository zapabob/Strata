"""tests/backends/test_dsv41_adapter.py - Tests for strata-dsv41 adapter contracts."""
from __future__ import annotations

from pathlib import Path
import pytest

from strata_control.bundle_resolver import ImportSelection, resolve_bundle
from strata_control.bundle_identity import verify_bundle
from strata_control.backends.dsv41 import (
    validate_dsv41,
    prepare_dsv41,
    PrepareRequest,
    REQUIRED_DEEPSEEK_DENSE_TENSORS,
)


def test_renamed_dsv41_variant(tmp_path: Path) -> None:
    """A DeepSeek variant with any filename passes if required tensors and geometry match."""
    f = tmp_path / "custom_uncensored_maya_s.gguf"
    f.write_bytes(b"gguf-data")

    bundle = resolve_bundle(
        ImportSelection(primary_path=f, architecture="dsv41", dialect="standard")
    )
    verified = verify_bundle(bundle)

    # Valid with all required dense tensors
    report = validate_dsv41(
        verified,
        caps=None,
        simulated_tensors=REQUIRED_DEEPSEEK_DENSE_TENSORS,
    )
    assert report.decision == "QUALIFIED"
    assert len(report.errors) == 0


def test_dense_required_tensor_missing(tmp_path: Path) -> None:
    """Missing embed_tokens or norm weights is reported as incompatible."""
    f = tmp_path / "incomplete.gguf"
    f.write_bytes(b"data")

    bundle = resolve_bundle(
        ImportSelection(primary_path=f, architecture="dsv41", dialect="standard")
    )
    verified = verify_bundle(bundle)

    # Missing model.norm.weight
    partial_tensors = ["model.embed_tokens.weight", "lm_head.weight"]
    report = validate_dsv41(verified, caps=None, simulated_tensors=partial_tensors)
    assert report.decision == "INCOMPATIBLE"
    assert any("model.norm.weight" in e for e in report.errors)


def test_unsupported_arch_rejected(tmp_path: Path) -> None:
    """A llama or qwen model is rejected by the dsv41 adapter."""
    f = tmp_path / "qwen.gguf"
    f.write_bytes(b"data")

    bundle = resolve_bundle(
        ImportSelection(primary_path=f, architecture="qwen2", dialect="standard")
    )
    verified = verify_bundle(bundle)

    report = validate_dsv41(verified, caps=None, simulated_tensors=REQUIRED_DEEPSEEK_DENSE_TENSORS)
    assert report.decision == "INCOMPATIBLE"
    assert any("Architecture 'qwen2' is not supported" in e for e in report.errors)


def test_prepare_creates_clean_staging(tmp_path: Path) -> None:
    """Preparation writes isolated staging manifest without mutating original files."""
    f = tmp_path / "ds.gguf"
    f.write_bytes(b"original-dense-content")

    bundle = resolve_bundle(
        ImportSelection(primary_path=f, architecture="dsv41", dialect="standard")
    )
    verified = verify_bundle(bundle)

    out_dir = tmp_path / "staging_ds4"
    prepared = prepare_dsv41(
        verified,
        PrepareRequest(output_dir=out_dir),
        simulated_tensors=REQUIRED_DEEPSEEK_DENSE_TENSORS,
    )
    assert prepared.is_ready is True
    assert Path(prepared.pack_manifest_path).exists()
    assert f.read_bytes() == b"original-dense-content"
