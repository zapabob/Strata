"""Unit tests for tools/full_machine_infer.py hardware tier planning and guardrails."""

from __future__ import annotations

from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import full_machine_infer as fmi


def _ryzen4500_rtx5060ti_hw(
    *,
    ram_avail_gib: float = 16.0,
    commit_avail_gib: float = 35.0,
    vram_free_gib: float = 14.8,
    c_free_gib: float = 11.0,
    h_free_gib: float = 220.0,
) -> fmi.HardwareProfile:
    return fmi.HardwareProfile(
        gpu_name="NVIDIA GeForce RTX 5060 Ti",
        vram_total_gib=15.93,
        vram_free_gib=vram_free_gib,
        compute_cap="12.0",
        pcie_gen=3,
        pcie_width=8,
        power_limit_w=180.0,
        physical_cores=6,
        logical_threads=12,
        primary_cpus=(0, 2, 4, 6, 8, 10),
        smt_secondary_cpus=(1, 3, 5, 7, 9, 11),
        ram_total_gib=31.87,
        ram_avail_gib=ram_avail_gib,
        commit_total_gib=63.87,
        commit_avail_gib=commit_avail_gib,
        disks=(
            fmi.DiskStatus(mount="C:/", total_gib=929.7, free_gib=c_free_gib),
            fmi.DiskStatus(mount="H:/", total_gib=953.9, free_gib=h_free_gib),
        ),
    )


def test_resource_floor_enforcement() -> None:
    ok_hw = _ryzen4500_rtx5060ti_hw()
    ok, warns = fmi.check_resource_floors(ok_hw)
    assert ok is True
    assert warns == ()

    low_hw = _ryzen4500_rtx5060ti_hw(ram_avail_gib=2.4, commit_avail_gib=3.2, c_free_gib=4.1, h_free_gib=8.5)
    ok_low, warns_low = fmi.check_resource_floors(low_hw)
    assert ok_low is False
    assert len(warns_low) == 4


def test_gpu_resident_plan_q38() -> None:
    hw = _ryzen4500_rtx5060ti_hw()
    model = fmi.ModelSpec(
        path=Path("H:/Strata/models/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf"),
        name="qwen3.8-27b-abliterated-3.69bpw-12GB-MTP",
        file_format="gguf",
        size_gib=11.73,
        architecture="qwen35",
        family="qwen38_dense",
        recommended_engine="strata-q38.exe",
    )
    plan = fmi.plan_full_machine(hw, model)
    assert plan.floors_ok is True
    assert plan.release_qualified is False
    assert "GPU-resident" in plan.tier_mode
    assert plan.cpu_compute_threads == 6
    assert plan.cpu_io_smt_threads == 6
    assert plan.env["STRATA_AUX_CPUS"] == "off"
    assert plan.env["STRATA_AUX_IO_SMT"] == "1"
    assert plan.env["STRATA_IO_THREADS"] == "6"
    assert "--kv" in plan.args


def test_hybrid_ram_and_3tier_ssd_plan_inkling2() -> None:
    hw_tight = _ryzen4500_rtx5060ti_hw(ram_avail_gib=10.0, commit_avail_gib=12.0, vram_free_gib=14.0)
    model_big = fmi.ModelSpec(
        path=Path("H:/Strata/models/qsa-nvfp4-header-only.gguf"),
        name="qsa-nvfp4-header-only",
        file_format="gguf",
        size_gib=18.53,
        architecture="inkling2",
        family="inkling2_gguf",
        recommended_engine="strata-inkling2.exe",
    )
    plan = fmi.plan_full_machine(hw_tight, model_big, context=131072)
    assert plan.floors_ok is True
    assert "3-Tier" in plan.tier_mode
    assert plan.gpu_budget_gib > 0.0
    assert plan.ram_pinned_budget_gib > 0.0
    assert plan.ssd_stream_gib > 0.0
    assert plan.env["STRATA_SSD_PREFETCH"] == "1"
    assert plan.env["STRATA_RH_3TIER"] == "1"
    assert plan.env["STRATA_SATA_PF_THREADS"] == "1"
    assert plan.env["STRATA_SATA_COALESCE_GAP_KB"] == "14336"
    assert plan.env["STRATA_AUX_IO_SMT"] == "1"
    assert plan.env["STRATA_VRAM_RESERVE_MB"] == "1536"
    assert plan.env["STRATA_RAM_SQUEEZE"] == "on"


def test_model_routing_hikari_and_tq2_0() -> None:
    fam_h, exe_h = fmi._classify_model(Path("H:/Strata/models/hikari-pq20/Hikari-LoRA-fixed-scale-PQ2_0.gguf"), "qwen35")
    assert fam_h == "qwen38_dense"
    assert exe_h == "strata-q38.exe"

    fam_tq, exe_tq = fmi._classify_model(
        Path("H:/Strata/models/freakyskittle/Inkling-2-Mini-Derisked-GGUF/Inkling-2-Mini-Derisked-TQ2_0.gguf"),
        "inkling2_loop",
    )
    assert fam_tq == "inkling2_strata"
    assert exe_tq == "strata-inkling.exe"


def test_gguf_architecture_header_scanner(tmp_path: Path) -> None:
    gguf_file = tmp_path / "mini_inkling2.gguf"
    key = b"general.architecture"
    val = b"inkling2"
    payload = bytearray()
    payload += b"GGUF"
    payload += struct.pack("<IQQ", 3, 0, 1)
    payload += struct.pack("<Q", len(key)) + key
    payload += struct.pack("<I", 8)
    payload += struct.pack("<Q", len(val)) + val
    gguf_file.write_bytes(bytes(payload))

    spec = fmi.inspect_model(gguf_file)
    assert spec.architecture == "inkling2"
    assert spec.family == "inkling2_gguf"
    assert spec.recommended_engine == "strata-inkling2.exe"


def test_no_print_calls_in_full_machine_infer() -> None:
    import ast

    tree = ast.parse((ROOT / "tools" / "full_machine_infer.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "print", "print() is forbidden; use logging"
