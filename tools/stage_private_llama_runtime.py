"""Stage a new private Prism 0.4.1 payload and selection plan; never activate."""

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
BASE_COMMIT = "73bfe6cc485554822f80c473a3c0c4f25e80f41b"
REPOSITORY = "https://github.com/PrismML-Eng/llama.cpp.git"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def copy_verified(source: Path, target: Path, expected_sha256: str) -> None:
    """A same-sized copied file is not evidence that its bytes were preserved."""
    if target.exists() or target.is_symlink():
        raise FileExistsError("Runtime payload destinations must be fresh")
    if sha(source) != expected_sha256:
        raise ValueError("Source payload changed before copy")
    shutil.copy2(source, target)
    if sha(target) != expected_sha256:
        raise ValueError("Copied payload differs from the source receipt")


def member(root: Path, name: str) -> Path:
    """Flat payload membership, without links or alternate Windows paths."""
    if (
        not isinstance(name, str)
        or not re.fullmatch(r"[A-Za-z0-9_.+-]+", name)
        or name in (".", "..")
    ):
        raise ValueError("Unsafe runtime payload path")
    path = root / name
    if path.is_symlink() or path.is_junction() or not path.is_file():
        raise ValueError("Invalid runtime payload member: " + name)
    return path


def verify_package(root: Path, expected_manifest_sha256: str) -> dict:
    """Check the parent's recorded manifest digest and every payload member."""
    if root.is_symlink() or root.is_junction() or not root.is_dir():
        raise ValueError("Invalid runtime package root")
    manifest_path = member(root, "runtime.json")
    if (
        not re.fullmatch(r"[a-f0-9]{64}", expected_manifest_sha256)
        or sha(manifest_path) != expected_manifest_sha256
    ):
        raise ValueError("Runtime manifest SHA-256 differs")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("schema") != 1
        or manifest.get("backend") != "prism"
        or manifest.get("version") != "0.4.1"
        or manifest.get("privateCandidate") is not True
    ):
        raise ValueError("Unexpected private runtime manifest")
    seen = set()
    for item in manifest["files"]:
        name = item["path"]
        if (
            not isinstance(name, str)
            or name.lower() in seen
            or name.lower() == "runtime.json"
        ):
            raise ValueError("Duplicate payload membership")
        seen.add(name.lower())
        path = member(root, name)
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise ValueError("Runtime payload differs: " + name)
    actual = {
        path.name.lower() for path in root.iterdir() if path.name != "runtime.json"
    }
    if (
        actual != seen
        or "llama-server.exe" not in seen
        or any(
            not p.is_file() or p.is_symlink() or p.is_junction() for p in root.iterdir()
        )
    ):
        raise ValueError("Unexpected runtime payload membership")
    return manifest


def selection_plan(folder: str, previous_pointer: bytes, environment: dict) -> dict:
    """Describe parent-only activation, preserving explicit environment selection."""
    if not re.fullmatch(r"[A-Za-z0-9_.+-]+", folder) or folder in (".", ".."):
        raise ValueError("Invalid candidate folder")
    previous = (
        json.loads(previous_pointer.decode("utf-8-sig")) if previous_pointer else {}
    )
    return {
        "activated": False,
        "recommendedBackend": "PrismML",
        "runtimeVersion": "0.4.1",
        "parentReviewRequired": True,
        "automaticEnvironment": dict(environment),
        "pointerWouldSelectCandidate": not any(environment.values()),
        "previousPointerSHA256": hashlib.sha256(previous_pointer).hexdigest(),
        "previousPointer": previous,
        "proposedPointer": {"folder": folder, "previous": previous.get("folder")},
        "action": (
            "After review, include the new payload and its exact source/patch "
            "identity in the private distribution; select PrismML only for "
            "this model through the existing profile API."
        ),
    }


def environment_selection() -> dict:
    """Read only the runtime selector, never credentials or the whole registry."""
    values = {
        "Process": os.environ.get("STRATA_LLAMA_SERVER"),
        "User": None,
        "Machine": None,
    }
    if os.name == "nt":
        import winreg

        for label, hive, path in [
            ("User", winreg.HKEY_CURRENT_USER, "Environment"),
            (
                "Machine",
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            ),
        ]:
            try:
                with winreg.OpenKey(hive, path) as key:
                    values[label] = winreg.QueryValueEx(key, "STRATA_LLAMA_SERVER")[0]
            except FileNotFoundError:
                pass
    return values


def admit_build(report: dict, freeze: dict, guard: dict) -> None:
    """A successful linker cannot erase a resource or containment failure."""
    if (
        report.get("status") != "success"
        or report.get("sourceCommit") != freeze.get("commit")
        or freeze.get("baseCommit") != BASE_COMMIT
    ):
        raise ValueError("Successful matching frozen-source build required")
    if (
        report.get("cudaCubins") != ["sm_120"]
        or report.get("cudaArchitecture") != "120"
        or report.get("jobs") != 1
    ):
        raise ValueError("Serial standard-sm120 build evidence required")
    if (
        guard.get("status") != "passed"
        or guard.get("containedBeforeGo") is not True
        or guard.get("cleanup") is not True
        or guard.get("abort") is not None
        or guard.get("exitCode") != 0
        or any(
            guard.get("floorsGiB", {}).get(key, 0) < floor
            for key, floor in {"ram": 3, "commit": 4, "c": 5, "h": 10}.items()
        )
    ):
        raise ValueError("The completed build resource guard did not pass")


def stage(
    build_receipt: Path,
    freeze_path: Path,
    guard_receipt: Path,
    out: Path,
    search: list[Path],
    components: Path,
) -> dict:
    if not os.environ.get("QWEN35_TEST_OUT"):
        raise ValueError("Stage under the owned resource guard")
    report = json.loads(build_receipt.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    guard = json.loads(guard_receipt.read_text(encoding="utf-8"))
    admit_build(report, freeze, guard)
    build, source = Path(report["build"]), Path(report["source"])
    if (
        not out.is_absolute()
        or out.drive.upper() != "H:"
        or out.exists()
        or not out.parent.is_dir()
        or out.parent.is_symlink()
        or out.parent.is_junction()
    ):
        raise ValueError(
            "Use a fresh private H: package folder under an existing plain parent"
        )
    files = []
    for item in report["files"]:
        if not re.fullmatch(r"bin/[A-Za-z0-9_.+-]+", item["path"]):
            raise ValueError("Unexpected build member path")
        path = member(build / "bin", item["path"][4:])
        if path.stat().st_size != item["bytes"] or sha(path) != item["sha256"]:
            raise ValueError("Build payload changed")
        files.append((path, item["sha256"]))
    if not any(path.name == "llama-server.exe" for path, _ in files):
        raise ValueError("Missing built server")
    patch = freeze_path.parent / "source-patch.diff"
    if sha(patch) != freeze["sourcePatchSHA256"]:
        raise ValueError("Frozen source patch changed")
    for item in freeze["patches"]:
        if sha(member(freeze_path.parent, item["path"])) != item["sha256"]:
            raise ValueError("Reviewed patch changed")
    from verify_frozen_llama_source import verify

    proof = verify(source, freeze["commit"])
    actual_patch = subprocess.check_output(
        [
            "git",
            "diff",
            "--binary",
            "--full-index",
            BASE_COMMIT,
            freeze["commit"],
        ],
        cwd=source,
    )
    if (
        hashlib.sha256(actual_patch).hexdigest() != freeze["sourcePatchSHA256"]
        or proof["sourceTree"] != freeze["tree"]
    ):
        raise ValueError("Source patch/tree does not match the frozen commit")
    out.mkdir()
    for path, expected in files:
        copy_verified(path, out / path.name, expected)
    copy_verified(source / "LICENSE", out / "LICENSE.txt", sha(source / "LICENSE"))
    copy_verified(patch, out / "source-patch.diff", freeze["sourcePatchSHA256"])
    for item in freeze["patches"]:
        copy_verified(
            freeze_path.parent / item["path"], out / item["path"], item["sha256"]
        )
    sys.path.insert(0, str(ROOT / "packaging"))
    import package_engine

    added = package_engine._bundle_missing_libraries(
        out, "windows-x86_64", [p.name for p in out.iterdir()], search, []
    )
    for item in added:
        original = next(
            (
                folder / item["path"]
                for folder in search
                if (folder / item["path"]).is_file()
            ),
            None,
        )
        if original is None or sha(out / item["path"]) != sha(original):
            raise ValueError("Copied payload DLL differs from its search source")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("LLAMA_", "GGML_", "CUDA_", "STRATA_"))
    }
    env["PATH"] = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32")
    executable = out / "llama-server.exe"
    version = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
        check=True,
    )
    version_text = (version.stdout + version.stderr).strip()
    if not any(
        freeze["commit"].startswith(value)
        for value in re.findall(r"\b[a-f0-9]{7,40}\b", version_text)
    ):
        raise ValueError(
            "Executable version does not identify the private source commit"
        )
    help_result = subprocess.run(
        [str(executable), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
        check=True,
    )
    help_text = help_result.stdout + help_result.stderr
    cache_types = ["f16", "bf16", "q8_0", "q4_0"]
    if any(
        not re.search(r"(?<!\w)" + kind + r"(?!\w)", help_text) for kind in cache_types
    ):
        raise ValueError("Existing Prism cache parser types are not all present")
    folder = "prism-qwen35-mtp-0.4.1-" + freeze["commit"][:8] + "-cuda133-sm120"
    patch_ids = {
        "qwen35_absent_mtp.patch": "qwen35-absent-mtp-v1",
        "spin8_backend_sm120.patch": "prism-standard-sm120-v1",
    }
    patches = [dict(item, id=patch_ids[item["path"]]) for item in freeze["patches"]]
    status_probe = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=source,
        capture_output=True,
        check=True,
    )
    manifest = {
        "schema": 1,
        "backend": "prism",
        "version": "0.4.1",
        "id": folder,
        "privateCandidate": True,
        "source": {
            "repository": REPOSITORY,
            "baseCommit": BASE_COMMIT,
            "commit": freeze["commit"],
            "tree": freeze["tree"],
            "dirty": False,
            "byteVerification": proof,
            "gitStatusReportedDirty": bool(status_probe.stdout.strip()),
            "patches": patches,
            "sourcePatchSHA256": freeze["sourcePatchSHA256"],
        },
        "build": {
            "device": "cuda",
            "cudaArchitecture": "120",
            "cudaCubins": ["sm_120"],
            "cudaToolkit": "13.3",
            "jobs": 1,
            "receiptSHA256": sha(build_receipt),
            "guardReceiptSHA256": sha(guard_receipt),
        },
        "cacheTypes": cache_types,
        "cacheTypesK": cache_types,
        "cacheTypesV": cache_types,
        "cacheTypeEvidence": (
            "Existing Prism policy and actual CLI help; "
            "model qualification is separate."
        ),
        "executableVersion": version_text,
        "releaseQualified": False,
        "files": [
            {"path": p.name, "bytes": p.stat().st_size, "sha256": sha(p)}
            for p in sorted(out.iterdir())
        ],
    }
    with (out / "runtime.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
    digest = sha(out / "runtime.json")
    verify_package(out, digest)
    pointer = components / "generic-gguf/active.json"
    previous = pointer.read_bytes() if pointer.exists() else b""
    plan = selection_plan(folder, previous, environment_selection())
    plan.update(
        package=str(out),
        manifestSHA256=digest,
        componentDestination=str(components / "generic-gguf" / folder),
        localBackendPolicyUpdateRequired=True,
    )
    with (out.parent / (out.name + "-selection-plan.json")).open(
        "x", encoding="utf-8"
    ) as stream:
        json.dump(plan, stream, indent=2)
    return {
        "package": str(out),
        "manifestSHA256": digest,
        "sourceCommit": freeze["commit"],
        "addedLibraries": added,
        "activated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-receipt", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--guard-receipt", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--search", type=Path, action="append", required=True)
    parser.add_argument("--components", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            stage(
                args.build_receipt,
                args.freeze,
                args.guard_receipt,
                args.out,
                args.search,
                args.components,
            )
        )
    )


if __name__ == "__main__":
    main()
