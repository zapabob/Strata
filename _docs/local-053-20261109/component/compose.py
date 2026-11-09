"""Parent-operated private 0.5.3 compose/sign/stage. Default: read-only plan."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace
from typing import Any
import uuid

from core import (BASE, HERE, MANIFEST, NAME, NATIVE, NATIVE_COMMIT, NATIVE_ROOT, NODE,
                  PRISM, PRISM_EXE, PYTHON, RECEIPT, REFERENCE, RESOURCES, ROOT, TURBO,
                  WORK, STAGING, Blocked, check_archive, check_dependencies, compose, copy_tree,
                  digest, inventory, load, no_links, preserve_bundle_metadata, production_modules,
                  require, sha, write_new)
from quality import finished, validate

GIB = 1024**3


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--execute", action="store_true")
    result.add_argument("--reviewed-commit", help="Full current app HEAD; execute only")
    result.add_argument("--native-source-root", type=Path, help="Explicit reviewed frozen native checkout")
    result.add_argument("--key", type=Path, help="Explicit absolute signing-key path; read only by feed_tool.py")
    result.add_argument("--plan", action="store_true", help="Read-only plan (also the default)")
    result.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    return result


def plan(args: argparse.Namespace) -> dict:
    return {"execution": False, "appRoot": str(ROOT), "nativeSourceRoot": str(args.native_source_root or NATIVE_ROOT),
            "nativeSourceCommit": NATIVE_COMMIT, "reviewedAppCommit": args.reviewed_commit,
            "nativeOnly": str(NATIVE), "retainedReference": str(REFERENCE),
            "unsigned": str(WORK / "unsigned" / NAME), "signed": str(WORK / "signed" / NAME),
             "staged": str(RESOURCES / "engine-bundle" / NAME), "receipt": str(RECEIPT),
             "sameVolumeStaging": str(STAGING), "priorEngineBundle": str(STAGING / "prior-engine-bundle"),
            "key": "explicit path required on execute; not inspected by plan",
            "reportNames": ["package.json", "cpu.json", "gpu.json", "sanitizer.json", "spill.json",
                            "model-bounded.json", "model-legacy7.json", "model-restart.json",
                            "comparison.json", "qualification-summary.json"],
            "floorsGiB": {"RAM": 3, "commit": 4, "C": 5, "H": 10},
            "deadlinesSeconds": {"wholeOwnedJob": 1800, "sign": 60, "zip": 300, "verify": 180, "dependency": 120},
            "releaseQualified": False, "checksRun": False,
            "prerequisites": "Clean reviewed app HEAD, clean frozen native root, completed reports/Jobs, fixed sibling backends and notices, pinned PublicAssets; fresh component-053 and staged-native.json"}


def environment() -> dict[str, str]:
    keep = {"SYSTEMROOT", "WINDIR", "COMSPEC", "SYSTEMDRIVE", "PROGRAMFILES", "PROGRAMFILES(X86)",
            "PROGRAMW6432", "PROGRAMDATA", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "NUMBER_OF_PROCESSORS"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    git = shutil.which("git.exe")
    require(git, "Existing Git required")
    env.update(PATH=";".join(map(str, (NODE.parent, PYTHON.parent, Path(git).parent,
                                     Path("C:/Windows/System32"), Path("C:/Windows")))),
               TEMP=str(WORK / "temp"), TMP=str(WORK / "temp"), TMPDIR=str(WORK / "temp"),
               PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1", PYTHONIOENCODING="utf-8",
               UV_OFFLINE="1", UV_PYTHON_DOWNLOADS="never", PIP_NO_INDEX="1",
               NODE_OPTIONS="--max-old-space-size=1024")
    return env


def command(args: list[str], seconds: int, *, quiet: bool = False) -> str:
    """All executed commands inherit the worker's owned Job. Never emit raw failures."""
    try:
        run = subprocess.run(args, cwd=BASE, env=environment(), stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL if quiet else subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                             timeout=seconds, creationflags=subprocess.CREATE_NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        raise Blocked("Bounded child did not complete; no automatic retry") from None
    require(run.returncode == 0, "Bounded production command failed; raw output suppressed")
    require(quiet or len(run.stdout) <= 2 * 1024**2, "Child output exceeds budget")
    return "" if quiet else run.stdout.strip()


def git(root: Path, *args: str) -> str:
    return command(["git", "-C", str(root), *args], 30)


def freeze(args: argparse.Namespace) -> dict:
    require(os.name == "nt" and Path(sys.executable).resolve() == PYTHON.resolve()
            and sys.version_info[:2] == (3, 12), "Pinned Windows Python 3.12 required")
    require(bool(re.fullmatch("[0-9a-f]{40}", args.reviewed_commit or "")), "Explicit full reviewed app HEAD required")
    require(args.native_source_root is not None and args.native_source_root.is_absolute()
            and args.native_source_root == NATIVE_ROOT, "Explicit frozen native root required")
    require(args.key is not None and args.key.is_absolute(), "Explicit absolute key path required")
    # The key is opaque: no read/stat/hash and no key-derived data in any receipt.
    for root in (ROOT, NATIVE_ROOT, BASE, REFERENCE, RESOURCES, WORK, STAGING):
        no_links(root)
        require(not args.key.is_relative_to(root), "Key must be outside source/release/resource trees")
    require(ROOT == Path("C:/Users/downl/Documents/ChatGPT/Strata"), "Unexpected app checkout")
    for root, commit in ((ROOT, args.reviewed_commit), (NATIVE_ROOT, NATIVE_COMMIT)):
        require(git(root, "rev-parse", "HEAD") == commit, "Reviewed source HEAD changed")
        require(not git(root, "status", "--porcelain", "--untracked-files=all"), "Parent must freeze clean checkouts")
    require((ROOT / "VERSION").read_text().strip() == "0.5.3-local.1"
            and (ROOT / "CONTROL_VERSION").read_text().strip() == "0.5.4", "App/Control version differs")
    require(BASE.is_dir() and RESOURCES.is_dir() and not (BASE / "active.json").exists(),
            "Parent must finish native Jobs first")
    require(not RECEIPT.exists(), "Preserve prior staged receipt")
    return {"reviewedAppCommit": args.reviewed_commit, "nativeSourceCommit": NATIVE_COMMIT,
            "nativeSourceRoot": str(NATIVE_ROOT),
            "helperSHA256": {p.name: sha(p) for p in sorted(HERE.iterdir()) if p.suffix in (".py", ".mjs")}}


def helpers() -> tuple[Any, Any, Any]:
    sys.path[:0] = [str(ROOT / "tools"), str(ROOT)]
    from native_model_resource_guard import available_memory
    from perf131k.windows_job import api, run_owned
    return available_memory, api, run_owned


def resources(_root: Any = None) -> dict:
    memory, _, _ = helpers()
    sample = memory()
    return {"available_ram": sample["available_physical_bytes"], "commit_headroom": sample["available_commit_bytes"],
            "H_free": shutil.disk_usage("H:/").free, "C_free": shutil.disk_usage("C:/").free}


def admit() -> dict:
    sample = resources()
    for key, floor in (("available_ram", 3), ("commit_headroom", 4), ("C_free", 5), ("H_free", 10)):
        require(sample[key] >= floor * GIB, "Resource floor admission refused: " + key)
    return sample


def verify_node(folder: Path, version: str, native: bool) -> dict:
    output = command([str(NODE), str(HERE / "verify.mjs"), str(ROOT), str(folder), version,
                      str(NATIVE_ROOT) if native else "-", NATIVE_COMMIT if native else "-"], 180)
    value = json.loads(output)
    require(value["ok"] is True and value["publicAssetsVerified"] is True, "Production guards did not pass")
    return value


def dependency_worker(folder: Path) -> None:
    # Separate short bounded child; no runtime executable is started for dependency verification.
    command([str(PYTHON), "-B", str(HERE / "deps.py"), str(folder)], 120, quiet=True)


def worker(args: argparse.Namespace, identity: dict) -> None:
    import ctypes
    from ctypes import wintypes
    _, api, _ = helpers()
    present = wintypes.BOOL()
    require(api().IsProcessInJob(wintypes.HANDLE(-1), None, ctypes.byref(present)) and present.value,
            "Worker requires its owned Windows Job")
    require(os.environ.get("COMPONENT_WORKER_TOKEN") == load(WORK / "reservation.json")["token"],
            "Worker ownership mismatch")
    require(identity == load(WORK / "reservation.json")["identity"], "Worker source identity changed")
    admit()
    require(command([str(NODE), "--version"], 15) == "v24.22.2", "Pinned Node version differs")
    require(command([str(PYTHON), "--version"], 15).startswith("Python 3.12."), "Python version differs")
    ec, signing, _ = production_modules()
    # Authenticate the complete old payload BEFORE retaining any file from it.
    from core import verify_payload
    old_manifest, old_tree = verify_payload(REFERENCE, ec, signing, signed=True)
    require(old_manifest["version"] == "0.5.2", "Reference version differs")
    verify_node(REFERENCE, "0.5.2", False)
    native_manifest, native_tree = verify_payload(NATIVE, ec, signing, signed=False)
    require(native_manifest["version"] == "0.5.3" and native_manifest["build_id"] == NATIVE_COMMIT
            and native_manifest["entrypoint"] == "strata.exe" and native_manifest["backend"] == "cuda"
            and native_manifest["platform"] == "windows-x86_64" and native_manifest["variant"] == "cuda13"
            and native_manifest["archs"] == ["sm_120"], "Fresh native identity differs")
    bound = verify_node(NATIVE, "0.5.3", True)
    quality = validate()
    package = load(BASE / "results/package.json")
    require(bound["nativeSourceCount"] == package["nativeSourceCount"], "Dynamic native source count differs")
    # Existing sibling backend resources are used by app builds independently of the bundle.
    sibling_tree = inventory(RESOURCES / "local-backends", admit)
    for backend in ("prism", "turboquant"):
        require(inventory(RESOURCES / "local-backends" / backend, admit)
                == inventory(REFERENCE / "local-backends" / backend, admit), "Sibling runtime bytes differ")
    verify_node(RESOURCES, "siblings", False)
    write_new(WORK / "inputs.json", {"reference": old_tree, "native": native_tree, "quality": quality,
                                    "binding": bound, "siblingBackends": sibling_tree})
    for directory in ("unsigned", "signed", "archive"):
        (WORK / directory).mkdir()
    (STAGING / "pending-engine-bundle").mkdir()
    unsigned, signed = (WORK / name / NAME for name in ("unsigned", "signed"))
    compose(NATIVE, REFERENCE, unsigned, admit)
    verify_payload(unsigned, ec, signing, signed=False)
    verify_node(unsigned, "0.5.3", True)
    dependency_worker(unsigned)
    unsigned_tree = copy_tree(unsigned, signed, admit)
    # Only this production subprocess opens the explicit private key. All output is discarded.
    command([str(PYTHON), "-I", "-B", str(ROOT / "packaging/feed_tool.py"), "sign-package", str(signed),
             "--key", str(args.key)], 60, quiet=True)
    _, signed_tree = verify_payload(signed, ec, signing, signed=True)
    require({k: v for k, v in signed_tree.items() if k != MANIFEST}
            == {k: v for k, v in unsigned_tree.items() if k != MANIFEST}, "Signing altered payload")
    verify_node(signed, "0.5.3", True)
    command([str(PYTHON), "-I", "-B", str(ROOT / "packaging/feed_tool.py"), "pack-engine", str(signed),
             "--out", str(WORK / "archive"), "--format", "zip", "--url-prefix="], 300, quiet=True)
    archive = WORK / "archive" / ("strata-engine-" + NAME + ".zip")
    entry = load(archive.with_name(archive.name + ".entry.json"))
    check_archive(archive, entry, signed_tree)
    pending = STAGING / "pending-engine-bundle" / NAME
    require(copy_tree(signed, pending, admit) == signed_tree, "Fresh staged copy differs")
    verify_payload(pending, ec, signing, signed=True)
    verify_node(pending, "0.5.3", True)
    dependency_worker(pending)
    # Recheck all bound inputs/reports immediately before the one managed replacement.
    require(freeze(args) == identity and validate() == quality
            and inventory(NATIVE, admit) == native_tree and inventory(REFERENCE, admit) == old_tree
            and inventory(RESOURCES / "local-backends", admit) == sibling_tree, "Inputs changed before staging")
    bundle = RESOURCES / "engine-bundle"
    prior = preserve_bundle_metadata(bundle, STAGING / "pending-engine-bundle", admit)
    write_new(WORK / "prior-engine-bundle.json", {"inventory": prior, "inventorySHA256": digest(prior)})
    require(not (STAGING / "prior-engine-bundle").exists(), "Prior backup already exists")
    # Same-volume renames preserve the ENTIRE former managed root. No delete or automatic rollback.
    bundle.rename(STAGING / "prior-engine-bundle")
    require(inventory(STAGING / "prior-engine-bundle", admit) == prior, "Preserved managed root differs")
    (STAGING / "pending-engine-bundle").rename(bundle)
    staged = bundle / NAME
    verify_payload(staged, ec, signing, signed=True)
    verify_node(staged, "0.5.3", True)
    require(inventory(staged, admit) == signed_tree and inventory(unsigned, admit) == unsigned_tree
            and inventory(signed, admit) == signed_tree and validate() == quality
            and freeze(args) == identity, "Final staging/source/evidence changed")
    check_archive(archive, entry, signed_tree)
    receipt = {"ok": True, "signatureVerified": True, "releaseQualified": False,
               "nativeSourceCommit": NATIVE_COMMIT, "engineSHA256": signed_tree["strata.exe"],
               "q36SHA256": signed_tree["strata-q36.exe"], "signedManifestSHA256": signed_tree[MANIFEST],
               "prismVersion": "0.4.1", "prismManifestSHA256": PRISM, "prismExeSHA256": PRISM_EXE,
               "turboquantVersion": "0.4.0", "turboquantManifestSHA256": TURBO,
               "nativeBuildSHA256": signed_tree["native-build.json"], "nativeSourceCount": bound["nativeSourceCount"],
               "archive": str(archive), "archiveSHA256": sha(archive), "archiveBytes": archive.stat().st_size,
               "payloadInventorySHA256": digest(signed_tree), "quality": quality,
               "reviewedAppCommit": args.reviewed_commit, "nativeSourceRoot": str(NATIVE_ROOT),
                "priorEngineBundle": str(STAGING / "prior-engine-bundle"), "installed": False}
    pending_receipt = WORK / "staged-native.pending.json"
    write_new(pending_receipt, receipt)
    write_new(WORK / "completed.json", {"ok": True, "stagedReceiptSHA256": sha(pending_receipt)})


def main() -> int:
    args = parser().parse_args()
    require(not (args.plan and args.execute), "Choose plan or execute")
    if not args.execute:
        require(not args.worker, "Worker requires execute")
        print(json.dumps(plan(args), indent=2))
        return 0
    identity = freeze(args)
    if args.worker:
        worker(args, identity)
        return 0
    admit()
    require(not WORK.exists(), "Prior component attempt exists; retain it for parent disposition")
    require(not STAGING.exists(), "Prior same-volume staging must be retained")
    (BASE / "app").mkdir(exist_ok=True)
    WORK.mkdir()  # Exclusive reservation; failed attempts are never reused.
    STAGING.mkdir(parents=True)
    (WORK / "temp").mkdir()
    token = uuid.uuid4().hex
    write_new(WORK / "reservation.json", {"identity": identity, "token": token})
    _, _, run_owned = helpers()
    budget = SimpleNamespace(job_commit_bytes=None, max_processes=16, min_available_ram=3 * GIB,
                             min_commit_headroom=4 * GIB, min_H_free=10 * GIB, timeout_s=1800, output_bytes=2 * 1024**2)
    env = environment()
    env["COMPONENT_WORKER_TOKEN"] = token
    run = run_owned([str(PYTHON), "-B", str(HERE / "compose.py"), "--worker", "--execute",
                     "--reviewed-commit", args.reviewed_commit, "--native-source-root", str(args.native_source_root),
                     "--key", str(args.key)], BASE, env, WORK / "worker.txt", budget, resources,
                    memory_diagnostics=True,
                    on_tick=lambda: "C_disk_floor" if shutil.disk_usage("C:/").free < 5 * GIB else None)
    write_new(WORK / "owned-job.json", run)
    require(finished(run), "Component worker failed/blocked; inspect sanitized owned-job receipt; no automatic retry")
    pending_receipt = WORK / "staged-native.pending.json"
    require(load(WORK / "completed.json")["stagedReceiptSHA256"] == sha(pending_receipt), "Worker completion receipt absent")
    # The app-consumable ok receipt is published only after the whole owned Job has drained.
    candidate = load(pending_receipt)
    tree = inventory(RESOURCES / "engine-bundle" / NAME, admit)
    archive = Path(candidate["archive"])
    require(tree and digest(tree) == candidate["payloadInventorySHA256"]
            and archive.stat().st_size == candidate["archiveBytes"] and sha(archive) == candidate["archiveSHA256"],
            "Staging/archive changed after worker exit")
    write_new(RECEIPT, candidate)
    print(json.dumps({"ok": True, "receipt": str(RECEIPT), "releaseQualified": False}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Blocked as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as error:
        # Paths/JSON/child errors can contain private content. Keep only the exception class.
        print(json.dumps({"ok": False, "errorType": type(error).__name__, "rawErrorSuppressed": True}), file=sys.stderr)
        raise SystemExit(1) from None
