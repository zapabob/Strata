"""Finish the preserved release with Copy-mode 7z; keep the failed compression.

Inner EXE, gzip and ZIP payloads are already compressed. Store mode avoids an
expensive second compression pass and does not change any inner bytes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import prepare as p


def checksums() -> dict:
    result = {}
    for line in (p.ASSETS / "BUNDLE-SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        p.require(name not in result and "/" not in name and "\\" not in name, "Invalid bundle manifest")
        path = p.ASSETS / name
        p.require(p.sha(path) == digest, "Preserved input changed")
        result[name] = {"bytes": path.stat().st_size, "sha256": digest}
    result["BUNDLE-SHA256SUMS.txt"] = {"bytes": (p.ASSETS / "BUNDLE-SHA256SUMS.txt").stat().st_size,
                                      "sha256": p.sha(p.ASSETS / "BUNDLE-SHA256SUMS.txt")}
    return result


def worker() -> None:
    p.guard_module().require_current_job(p.ROOT)
    prior = p.load(p.BASE / "receipts/prepare-release.json")
    p.require(prior["run"]["termination_confirmed"] and prior["run"]["job_active_after"] == 0, "Failed worker not drained")
    folder, receipt, _ = p.signed_source()
    p.verify_archives(folder, receipt)
    wanted = checksums()
    tar_path = p.BASE / f"Strata-{p.VERSION}-windows-x64.tar"
    partial = p.ASSETS / p.ARCHIVE
    retained = p.BASE / "attempts/compression-r1"
    p.require(partial.is_file() and not retained.exists() and not (p.BASE / "prepared.json").exists(), "Explicit retained attempt required")
    retained.mkdir(parents=True)
    partial.rename(retained / p.ARCHIVE)
    p.run(str(p.SEVEN), "a", "-t7z", "-mx=0", "-mmt=1", str(partial), str(tar_path), seconds=900)
    p.run(str(p.SEVEN), "t", str(partial), seconds=900)
    process = subprocess.Popen([str(p.SEVEN), "x", "-so", str(partial), tar_path.name], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    found = {}
    with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
        for member in archive:
            prefix = f"Strata-{p.VERSION}-windows-x64/"
            p.require(member.name.startswith(prefix) and member.isfile(), "Unsafe 7z/tar member")
            name = member.name[len(prefix):]
            p.require(name in wanted and name not in found, "Unexpected combined member")
            found[name] = {"bytes": member.size, "sha256": hashlib.file_digest(archive.extractfile(member), "sha256").hexdigest()}
    while process.stdout.read(1024**2):
        pass
    process.stdout.close()
    p.require(process.wait(timeout=60) == 0 and found == wanted, "7z/tar readback changed bytes")
    public = [*wanted, p.ARCHIVE]
    p.require(all((p.ASSETS / n).stat().st_size < 2 * 1024**3 for n in public), "Per-asset size bound exceeded")
    (p.ASSETS / "SHA256SUMS.txt").write_text("".join(f"{p.sha(p.ASSETS / n)}  {n}\n" for n in public), encoding="utf-8", newline="\n")
    public.append("SHA256SUMS.txt")
    result = {"ok": True, "tag": p.TAG, "prerelease": True, "releaseQualified": False,
              "bundleReadbackMatched": True, "sevenZipMode": "Copy; inner files already compressed",
              "priorFailedReceipt": "receipts/prepare-release.json", "resumeRecipeSHA256": p.sha(Path(__file__)),
              "assets": {n: {"bytes": (p.ASSETS / n).stat().st_size, "sha256": p.sha(p.ASSETS / n)} for n in public}}
    p.save(p.BASE / "prepared.json", result)
    print(json.dumps(result, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"execute": False, "mode": "Copy", "preservePriorAttempt": True, "out": str(p.BASE)}))
        return 0
    if args.worker:
        worker()
        return 0
    guard = p.guard_module()
    env = guard.environment()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    row = guard.owned(p.ROOT, "finish-release-copy-r1", [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "--execute"],
                      1800, env=env, output_bytes=16 * 1024**2)
    print(json.dumps(row, indent=2))
    if not row["passed"]:
        print(guard.text("finish-release-copy-r1"))
    return 0 if row["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
