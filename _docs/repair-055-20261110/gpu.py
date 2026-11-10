"""Serial synthetic numerical checks; final-build mode requires fresh source binding."""
from __future__ import annotations

import hashlib
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = Path("H:/Strata/releases/repair-055-20261110-opencode")
BUILD = BASE / "native-build"
OLD = Path("H:/Strata/releases/upstream-0213-20261109-opencode/native-build")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', required=True)
    parser.add_argument('--final-source-commit', help='Require completed final build/source binding')
    args = parser.parse_args()
    attempt = args.attempt
    if not re.fullmatch(r'[a-z0-9-]+', attempt):
        parser.error('Safe fresh attempt label required')
    spec = importlib.util.spec_from_file_location("gpu_repair_guard", ROOT / "_docs/local-053-20261109/native/common.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE = BASE
    guard.require_current_job(ROOT)
    results = []
    final = args.final_source_commit is not None
    identity = {}
    report_path = BASE / f"gpu-{'final' if final else 'diagnostic'}-results-{attempt}.json"
    guard.require(not report_path.exists(), 'Retain earlier GPU results')

    def build_files() -> dict:
        paths = sorted((BUILD / 'Release').glob('*.lib'))
        paths += [BUILD / 'Release' / name for name in (
            'strata.exe', 'strata-q36.exe', 'native-build.json', 'expdec_bench.exe',
            'native_grouped_parity.exe', 'dflash2_q4_parity.exe', 'qsa_topk_parity.exe',
            'qsa_topk_active_parity.exe', 'prefill_iq4_w4a8_test.exe')]
        values = {}
        for path in paths:
            with path.open('rb') as stream:
                values[path.relative_to(BUILD).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
        return values

    if final:
        guard.require(re.fullmatch('[0-9a-f]{40}', args.final_source_commit), 'Full source commit required')
        evidence = BASE / 'native-evidence'
        freeze = json.loads((evidence / 'freeze.json').read_text(encoding='utf-8'))
        bound = json.loads((evidence / 'receipts/bind-phase.json').read_text(encoding='utf-8'))
        guard.require(freeze['sourceCommit'] == args.final_source_commit and bound.get('passed') is True
                      and bound.get('frozenIdentity') == freeze and guard.passed_run(bound.get('run', {})),
                      'Final native build not successfully bound/drained')
        row = guard.owned(ROOT, 'gpu-final-binding-' + attempt, [str(guard.NODE),
            str(BASE / 'adapters/native/binding.mjs'), freeze['sourceRoot'], str(BUILD / 'Release')], 120)
        guard.require(row['passed'], 'Final source/binary binding failed')
        binding = json.loads(guard.text('gpu-final-binding-' + attempt))
        guard.require(binding == json.loads((evidence / 'results/build.json').read_text(encoding='utf-8')),
                      'Final build identity changed')
        identity = {'sourceCommit': args.final_source_commit, 'binding': binding, 'testedBuildFiles': build_files()}

    def case(name: str, args: list[str], *, settings: dict | None = None, seconds: int = 300) -> str:
        free = int(subprocess.check_output(["C:/Windows/System32/nvidia-smi.exe", "--query-gpu=memory.free", "--format=csv,noheader,nounits"], timeout=15).splitlines()[0])
        guard.require(free >= 12000, "Serial GPU admission needs the user model unloaded")
        env = guard.environment()
        env.update(CARGO_BUILD_JOBS="5", CMAKE_BUILD_PARALLEL_LEVEL="5", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
        env["PATH"] = str(Path(args[0]).parent) + ";" + env["PATH"]
        env.update(settings or {})
        row = guard.owned(ROOT, "gpu-" + name + '-' + attempt, args, seconds, env=env)
        text = guard.text("gpu-" + name + '-' + attempt)
        results.append({"case": name, "passed": row["passed"]})
        guard.save(report_path, {"diagnosticOnly": not final, **identity, "cases": results, "passed": False})
        # Bench headers describe the possible DIFFERENT verdict. Judge actual
        # data/diagnostics, not a comment naming that verdict.
        data = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#'))
        guard.require(row["passed"] and not re.search(r"\b(?:Skipped|MISMATCH|DIFFERENCES|DIFFERENT|FAIL)\b", data), "GPU numerical check failed: " + name)
        return text

    case("libraries", [str(guard.CTEST), "--test-dir", str(BUILD), "-C", "Release", "--parallel", "1", "--no-tests=error", "--output-on-failure", "--timeout", "120", "-R", "^cuda_spill_guard$"])
    expdec = case("expdec", [str(BUILD / "Release/expdec_bench.exe"), "1", "0", "10", "21/20", "def,dec:d4:w1:x1:h256", "real"], seconds=180)
    guard.require('down type 20: expdec_down_kernel R 4' in expdec and '0 choice comparisons differ' in expdec, 'Repaired EXPDEC route coverage missing')
    case("grouped", [str(BUILD / "Release/native_grouped_parity.exe")])
    reference = None
    for variant in (17, 18, 21):
        target = BASE / f"dflash-{variant}-{attempt}-outputs.bin"
        guard.require(not target.exists(), "Retain prior parity outputs")
        case(f"dflash-{variant}", [str(BUILD / "Release/dflash2_q4_parity.exe"), "--output", str(target)], settings={"STRATA_DF2_GEMM4": str(variant)}, seconds=600)
        with target.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        guard.require(target.stat().st_size > 0, "Empty DFlash byte comparison")
        if reference is None:
            reference = digest
        guard.require(digest == reference, "DFlash repaired schedules differ bitwise from unchanged17")
    settings = {"STRATA_QSA_CLUSTER": "0", "STRATA_TOPK_STREAM": "0"}
    case("qsa-selftest", [str(BUILD / "Release/qsa_topk_parity.exe"), "--selftest"], settings=settings)
    case("qsa-boundary", [str(BUILD / "Release/qsa_topk_parity.exe"), "135160", "64", "3", "135160", "1"], settings=settings)
    case("qsa-active", [str(BUILD / "Release/qsa_topk_active_parity.exe")], settings=settings)
    for cfg in range(4):
        for label, folder in (("old", OLD), ("new", BUILD)):
            text = case(f"w4a8-{cfg}-{label}", [str(folder / "Release/prefill_iq4_w4a8_test.exe"), "--bench"], settings={"STRATA_W4A8_CFG": str(cfg)}, seconds=600)
            counts = re.findall(r"kernel (\d+) \+ (\d+) products", text)
            guard.require(counts and sum(int(a) for a, _ in counts) > 0 and sum(int(b) for _, b in counts) > 0, "Both W4A8 formats need actual kernel coverage")
        case(f"w4a8-{cfg}-wide", [str(BUILD / "Release/prefill_iq4_w4a8_test.exe"), "--wide", "--tokens", "2049"], settings={"STRATA_W4A8_CFG": str(cfg)}, seconds=600)
    if final:
        guard.require(build_files() == identity['testedBuildFiles'], 'Final tested build changed during GPU checks')
    guard.save(report_path, {"diagnosticOnly": not final, **identity, "passed": True, "cases": results,
                            "dflashBitwiseSHA256": reference, "releaseQualified": False})
    print(json.dumps({"diagnosticOnly": not final, "passed": True, "cases": len(results)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
