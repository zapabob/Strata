"""Diagnostic incremental cache and selected CUDA compiles; never a release bind."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path("H:/Strata/releases/repair-055-20261110-opencode")
OLD = Path("H:/Strata/releases/upstream-0213-20261109-opencode/native-build")
BUILD = OUT / "native-build"
MSBUILD = Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/MSBuild/Current/Bin/MSBuild.exe")
FILES = {"expdec": ("strata_kernels", "src/kernels/cuda/iq_kernels.cu"),
         "dflash": ("strata_kernels", "src/kernels/cuda/dflash2.cu"),
         "qsa": ("strata_kernels", "src/kernels/cuda/qsa_select.cu"),
         "w4a8": ("strata_mmq", "src/prefill/moe_iq4_w4a8.cu")}


def require(value: object, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inventory(root: Path) -> dict:
    result = {}
    for path in root.rglob("*"):
        require(not path.is_symlink() and not path.is_junction(), "Linked cache input refused")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = {"bytes": path.stat().st_size, "sha256": sha(path)}
    return result


def run(*command: str, timeout: int = 600) -> None:
    subprocess.run(command, cwd=ROOT, check=True, timeout=timeout)


def seed(guard) -> None:
    require(OLD.is_dir() and not BUILD.exists(), "Fresh diagnostic build root and retained cache required")
    before = inventory(OLD)
    shutil.copytree(OLD, BUILD, copy_function=shutil.copy2)
    require(inventory(BUILD) == before and inventory(OLD) == before, "Cache copy/source readback differs")
    guard.save(OUT / "native-seed.json", {"diagnosticOnly": True, "source": str(OLD), "files": before}, fresh=True)
    (BUILD / "CMakeCache.txt").rename(BUILD / "CMakeCache.pre-055.txt")
    args = guard.configure(ROOT)
    args[args.index("-B") + 1] = str(BUILD)
    run(*args, timeout=600)
    for name in ("strata_kernels", "strata_mmq"):
        text = (BUILD / (name + ".vcxproj")).read_text(encoding="utf-8-sig")
        require(str(OLD).replace("\\", "/") not in text.replace("\\", "/"), "Generated project still writes frozen build")
    guard.save(OUT / "native-diagnostic-configure.json", {"diagnosticOnly": True, "root": str(ROOT), "build": str(BUILD), "configure": args,
        "parallelism": 5, "spillGuardSHA256": sha(ROOT / "tools/check_cuda_spills.py"), "sourceHEAD": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()}, fresh=True)


def compile_one(name: str, attempt: str) -> None:
    target, relative = FILES[name]
    require(re.fullmatch(r"[a-z0-9-]+", attempt), "Explicit safe attempt label required")
    evidence = OUT / "object-attempts" / name / attempt
    require(not evidence.exists(), "Retain earlier object/source attempts")
    evidence.mkdir(parents=True)
    source_hash = sha(ROOT / relative)
    shutil.copy2(ROOT / relative, evidence / Path(relative).name)
    obj = BUILD / (target + ".dir") / "Release" / (Path(relative).stem + ".obj")
    if obj.exists():
        shutil.copy2(obj, evidence / "previous.obj")
    run(str(MSBUILD), str(BUILD / (target + ".vcxproj")), "/t:CudaBuild", "/p:Configuration=Release", "/p:Platform=x64",
        "/p:SelectedFiles=" + str(ROOT / relative), "/p:BuildProjectReferences=false", "/m:5", "/nr:false", timeout=1500)
    require(obj.is_file() and sha(ROOT / relative) == source_hash, "Source changed during compile or expected object missing")
    shutil.copy2(obj, evidence / "result.obj")
    print(json.dumps({"diagnosticOnly": True, "source": relative, "sourceSHA256": sha(ROOT / relative), "objectSHA256": sha(obj)}))
    run(str(guard.PYTHON), "-B", str(ROOT / "tools/check_cuda_spills.py"), "--cuobjdump", str(guard.CUDA / "bin/cuobjdump.exe"), str(obj), timeout=120)


def parity_build() -> None:
    targets = ("strata_kernels", "strata_mmq", "expdec_bench", "dflash2_q4_parity", "qsa_topk_parity",
               "qsa_topk_active_parity", "prefill_iq4_w4a8_test", "native_grouped_parity")
    run(str(guard.CMAKE), "--build", str(BUILD), "--config", "Release", "--parallel", "5", "--target", *targets, timeout=5100)


def final_configure() -> None:
    require((OUT / 'diagnostic-snapshot.json').is_file(), 'Preserve prototype evidence before final configuration')
    require('project(strata VERSION 0.5.5 ' in (ROOT / 'CMakeLists.txt').read_text(encoding='utf-8'), 'Expected new native source version')
    shutil.copy2(BUILD / 'CMakeCache.txt', BUILD / 'CMakeCache.pre-final055.txt')
    args = guard.configure(ROOT)
    args[args.index('-B') + 1] = str(BUILD)
    run(*args, timeout=600)
    guard.save(OUT / 'native-final-configure.json', {'configure': args, 'jobs': 5,
        'cacheSHA256': sha(BUILD / 'CMakeCache.txt'), 'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()}, fresh=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("seed", "all", "parity-build", "final-configure", *FILES))
    parser.add_argument("--attempt", default="initial")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("native_repair_guard", ROOT / "_docs/local-053-20261109/native/common.py")
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE = OUT
    guard.require_current_job(ROOT)
    if args.action == "seed":
        seed(guard)
    elif args.action == "parity-build":
        parity_build()
    elif args.action == "final-configure":
        final_configure()
    elif args.action == "all":
        results = {}
        for name in FILES:
            try:
                compile_one(name, args.attempt)
                results[name] = {"passed": True}
            except subprocess.CalledProcessError as error:
                results[name] = {"passed": False, "exit": error.returncode}
        guard.save(OUT / "native-objects-r1.json", {"diagnosticOnly": True, "cases": results}, fresh=True)
        raise SystemExit(0 if all(row["passed"] for row in results.values()) else 1)
    else:
        compile_one(args.action, args.attempt)
