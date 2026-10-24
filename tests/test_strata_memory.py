"""tests/test_strata_memory.py - Test suite for Strata Unified Long-Term Memory.

Tests:
1. Status retrieval of SOUL.md, MEMORY.md, Hermes SQLite, and hakua CompositeMemory.
2. Reading SOUL.md and MEMORY.md.
3. Adding and recalling memory items across subsystems.
4. CLI execution.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from strata_memory_mcp import StrataUnifiedMemory, run_cli


def test_strata_memory_status() -> None:
    mem = StrataUnifiedMemory()
    status = mem.status()
    assert status["status"] == "healthy"
    assert "soul" in status
    assert "memory_md" in status
    assert "hermes_ebbinghaus" in status
    assert "hakua_composite" in status
    assert status["soul"]["exists"] is True


def test_strata_memory_read_soul() -> None:
    mem = StrataUnifiedMemory()
    soul_data = mem.read_soul()
    assert soul_data["exists"] is True
    assert "content" in soul_data
    assert len(soul_data["content"]) > 0
    assert "sha256" in soul_data


def test_strata_memory_read_memory_md() -> None:
    mem = StrataUnifiedMemory()
    mem_data = mem.read_memory_md(limit=10)
    assert mem_data["exists"] is True
    assert isinstance(mem_data["sections"], list)
    if mem_data["sections"]:
        first = mem_data["sections"][0]
        assert "header" in first
        assert "body" in first


def test_strata_memory_remember_and_recall() -> None:
    mem = StrataUnifiedMemory()
    test_tag = "pytest-test-marker"
    test_content = "Antigravity and Strata pair-programming verification checkpoint."

    save_res = mem.remember(content=test_content, importance=0.85, tags=[test_tag])
    assert save_res["saved"] is True

    recall_res = mem.recall(query=test_tag, top_k=5)
    assert recall_res["count"] >= 1
    found = any(test_tag in str(r.get("metadata", {})) or test_tag in r.get("content", "") for r in recall_res["results"])
    assert found is True


def test_strata_memory_cli_status() -> None:
    cmd = ["py", "-3", str(REPO_ROOT / "tools" / "strata_memory_mcp.py"), "--cli", "status"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    out_json = json.loads(proc.stdout)
    assert out_json["status"] == "healthy"
    assert out_json["soul"]["exists"] is True


if __name__ == "__main__":
    print("Running test_strata_memory_status()...")
    test_strata_memory_status()
    print("Running test_strata_memory_read_soul()...")
    test_strata_memory_read_soul()
    print("Running test_strata_memory_read_memory_md()...")
    test_strata_memory_read_memory_md()
    print("Running test_strata_memory_remember_and_recall()...")
    test_strata_memory_remember_and_recall()
    print("Running test_strata_memory_cli_status()...")
    test_strata_memory_cli_status()
    print("ALL TESTS PASSED!")
