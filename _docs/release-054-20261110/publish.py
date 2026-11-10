"""Publish only the prepared prerelease assets; default plan makes no changes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

import prepare as p
from verify import gh_json, stable_snapshot


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=p.ROOT).decode("utf-8").strip()


def worker() -> None:
    p.guard_module().require_current_job(p.ROOT)
    p.require(not git("status", "--porcelain"), "Commit the reviewed release files first")
    p.require(git("branch", "--show-current") == "main", "Primary main checkout required")
    p.require(git("remote", "get-url", "origin") == "https://github.com/zapabob/Strata.git", "Unexpected release repository")
    target = git("rev-parse", p.TAG + "^{}")
    p.require(target == git("rev-parse", "HEAD") and git("cat-file", "-t", p.TAG) == "tag", "Reviewed annotated tag/HEAD required")
    p.require(p.load(p.BASE / "verified-local.json")["ok"] and p.load(p.BASE / "receipts/verify-release-local-r1.json")["passed"], "Local release gate missing")
    p.require(stable_snapshot() == p.load(p.BASE / "stable-before.json"), "Stable release changed before publication")
    prepared = p.load(p.BASE / "prepared.json")
    for name, expected in prepared["assets"].items():
        path = p.ASSETS / name
        p.require(path.stat().st_size == expected["bytes"] and p.sha(path) == expected["sha256"], "Prepared asset changed before upload")
    # Refuse an existing release; no clobber, replacement, forced tag or asset deletion.
    existing = subprocess.run(["gh", "release", "view", p.TAG, "--repo", "zapabob/Strata", "--json", "tagName"],
                              capture_output=True, timeout=90)
    p.require(existing.returncode != 0 and b"release not found" in existing.stderr.lower(), "Release exists or existence check failed")
    notes = Path(__file__).with_name("RELEASE_NOTES.md")
    command = ["gh", "release", "create", p.TAG, "--repo", "zapabob/Strata", "--draft", "--prerelease", "--latest=false", "--verify-tag",
               "--title", "Hakua / Strata 0.5.4-local.1 — Windows preview", "--notes-file", str(notes)]
    command.extend(str(p.ASSETS / name) for name in prepared["assets"])
    subprocess.run(command, check=True, cwd=p.ROOT, timeout=1500)
    draft = gh_json("release", "view", p.TAG, "--repo", "zapabob/Strata", "--json", "assets,isDraft,isPrerelease,databaseId")
    remote = {a["name"]: a for a in draft["assets"]}
    p.require(draft["isDraft"] and draft["isPrerelease"] and set(remote) == set(prepared["assets"]), "Draft metadata differs")
    for name, expected in prepared["assets"].items():
        actual = remote[name]
        p.require(actual["state"] == "uploaded" and actual["size"] == expected["bytes"] and actual["digest"] == "sha256:" + expected["sha256"], "Draft asset digest differs")
    subprocess.run(["gh", "release", "edit", p.TAG, "--repo", "zapabob/Strata", "--draft=false", "--prerelease", "--latest=false", "--verify-tag"],
                   check=True, cwd=p.ROOT, timeout=90)
    released = gh_json("api", "repos/zapabob/Strata/releases/tags/" + p.TAG)
    p.require(released["prerelease"] and not released["draft"], "Prerelease was not published")
    p.save(p.BASE / "published.json", {"ok": True, "tag": p.TAG, "tagTarget": target, "id": released["id"],
        "url": released["html_url"], "prerelease": True, "draftDigestsMatched": len(remote), "releaseQualified": False,
        "notesSHA256": p.sha(notes), "recipeSHA256": p.sha(Path(__file__))})
    print(released["html_url"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"execute": False, "repo": "zapabob/Strata", "tag": p.TAG, "prerelease": True,
                          "latest": False, "assets": list(p.load(p.BASE / "prepared.json")["assets"])}))
        return 0
    guard = p.guard_module()
    if args.worker:
        worker()
        return 0
    gh = shutil.which("gh")
    p.require(gh, "Authenticated gh CLI required")
    env = guard.environment()
    env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", GH_PROMPT_DISABLED="1")
    env["PATH"] = str(Path(gh).parent) + ";" + env["PATH"]
    row = guard.owned(p.ROOT, "publish-release-r1", [sys.executable, "-B", str(Path(__file__).resolve()), "--execute", "--worker"],
                      1800, env=env, output_bytes=8 * 1024**2)
    print(json.dumps(row, indent=2))
    if not row["passed"]:
        print(guard.text("publish-release-r1"))
    return 0 if row["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
