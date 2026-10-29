"""Stage a pinned, freshly built llama-server and its complete Windows DLL closure."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packaging"))
import package_engine as pe

PINS = {
    "prism": ("https://github.com/PrismML-Eng/llama.cpp.git", "73bfe6cc485554822f80c473a3c0c4f25e80f41b"),
    "turboquant": ("https://github.com/TheTom/llama-cpp-turboquant.git", "643956891dfdf51aecdbd05ca508dd21e21e8195"),
}

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--backend", required=True, choices=PINS)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--search", action="append", type=Path, default=[])
    args = parser.parse_args()
    build = args.build.resolve()
    report = json.loads((build / "bonsai-runtime.json").read_text(encoding="utf-8-sig"))
    repository, commit = PINS[args.backend]
    source = report.get("source", {})
    if report.get("backend") != args.backend or source.get("repository") != repository or source.get("commit") != commit or report.get("build", {}).get("status") != "success":
        raise SystemExit("The build does not identify a successful pinned runtime")
    def member(value):
        path = (build / value).resolve()
        if not path.is_relative_to(build) or not path.is_file():
            raise SystemExit("Unsafe or missing build receipt member")
        return path
    binary = member(report["binary"]["path"])
    if not any(member(item["path"]) == binary for item in report["files"]):
        raise SystemExit("The executable is absent from the build inventory")
    if sha(binary) != report["binary"]["sha256"]:
        raise SystemExit("The built binary changed after its build receipt")
    for item in report["files"]:
        if sha(member(item["path"])) != item["sha256"]:
            raise SystemExit("A build input changed: " + item["path"])
    out = args.out.resolve()
    if out.exists():
        raise SystemExit("Runtime packages are immutable; use a fresh output folder")
    out.mkdir(parents=True)
    for file in binary.parent.iterdir():
        if file.is_file() and (file == binary or file.suffix.lower() == ".dll"):
            shutil.copy2(file, out / file.name)
    source_dir = Path(source["path"])
    for name, source_file in [("LICENSE.txt", source_dir / "LICENSE"), ("LICENSE-ggml.txt", source_dir / "ggml/LICENSE")]:
        if source_file.is_file():
            shutil.copy2(source_file, out / name)
    if source.get("patches"):
        shutil.copy2(build / "source-patch.diff", out / "source-patch.diff")
    pe._bundle_missing_libraries(out, "windows-x86_64", [file.name for file in out.iterdir()], args.search, [])
    env = {k: v for k, v in os.environ.items() if k.upper() not in {"LLAMA_ARG_CACHE_TYPE_K", "LLAMA_ARG_CACHE_TYPE_V", "TURBO_AUTO_ASYMMETRIC", "TURBO_LAYER_ADAPTIVE"}}
    env.update(PATH=str(Path(env.get("SystemRoot", r"C:\Windows")) / "System32"), TURBO_AUTO_ASYMMETRIC="0", TURBO_LAYER_ADAPTIVE="0")
    executable = out / binary.name
    version = subprocess.run([str(executable), "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30, check=True)
    version_text = version.stdout + version.stderr
    # Upstream uses git --short (normally seven characters); the receipt retains the full pin.
    if not any(commit.startswith(value.lower()) for value in re.findall(r"\b[0-9a-f]{7,40}\b", version_text, re.I)):
        raise SystemExit("The actual executable does not report the pinned source commit")
    help_result = subprocess.run([str(executable), "--help"], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30, check=True)
    help_text = help_result.stdout + help_result.stderr
    cache_types = [name for name in ("f16", "bf16", "q8_0", "q4_0", "turbo2", "turbo3", "turbo4") if re.search(r"(?<![\w])" + name + r"(?![\w])", help_text)]
    if args.backend == "turboquant" and not all(name in cache_types for name in ("turbo2", "turbo3", "turbo4")):
        raise SystemExit("The TurboQuant executable does not offer the required cache types")
    # Real-model tests failed with turbo K, while FP16 K + turbo2/3/4 V passed.
    # Parsing support is insufficient: record independently qualified K/V capabilities.
    cache_k = [name for name in cache_types if not name.startswith("turbo")]
    cache_v = list(cache_types)
    manifest = {
        "schema": 1, "backend": args.backend, "version": re.search(r"project\(strata VERSION ([\d.]+)", (ROOT / "CMakeLists.txt").read_text(encoding="utf-8"))[1],
        "source": {key: source[key] for key in ("repository", "commit", "dirty", "patches")},
        "cacheTypes": cache_types, "cacheTypesK": cache_k, "cacheTypesV": cache_v, "executableVersion": version_text.strip(),
        "build": {key: report["build"].get(key) for key in ("device", "cudaArchitecture", "cudaCubins")},
        "files": [{"path": file.name, "bytes": file.stat().st_size, "sha256": sha(file)} for file in sorted(out.iterdir()) if file.is_file()],
    }
    (out / "runtime.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"staged": str(out), "backend": args.backend, "cacheTypes": cache_types}))

if __name__ == "__main__":
    main()
