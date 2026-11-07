"""Verify tracked checkout bytes against a frozen commit, not cached Git stat data."""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def verify(source: Path, commit: str) -> dict:
    """Accept exact Git blobs or the repository's checkout line-ending conversion."""

    def git(*args: str, data: bytes | None = None) -> bytes:
        return subprocess.check_output(["git", *args], cwd=source, input=data)

    if git("rev-parse", "HEAD").decode().strip() != commit:
        raise ValueError("Source commit differs")
    if git("ls-files", "--others", "--exclude-standard").strip():
        raise ValueError("Untracked source files are not frozen")
    entries = []
    for entry in git("ls-tree", "-r", "-z", commit).split(b"\0"):
        if not entry:
            continue
        fields, name = entry.split(b"\t", 1)
        mode, kind, oid = fields.decode().split()
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError("Unsupported source member")
        path = source / name.decode("utf-8")
        if (
            not path.resolve().is_relative_to(source.resolve())
            or path.is_symlink()
            or path.is_junction()
        ):
            raise ValueError("Linked source member")
        entries.append((name.decode("utf-8"), oid))
    paths = (
        "\n".join(json.dumps(name, ensure_ascii=False) for name, _ in entries) + "\n"
    ).encode()
    actual = git("hash-object", "--stdin-paths", data=paths).decode().splitlines()
    if len(actual) != len(entries):
        raise ValueError("Incomplete source inventory")
    raw_matches = 0
    for (name, oid), digest in zip(entries, actual):
        if digest == oid:
            continue
        data = (source / name).read_bytes()
        raw = hashlib.sha1(
            b"blob " + str(len(data)).encode() + b"\0" + data
        ).hexdigest()
        if raw != oid:
            raise ValueError("Source bytes differ from frozen Git blob: " + name)
        raw_matches += 1
    return {
        "sourceCommit": commit,
        "sourceTree": git("rev-parse", commit + "^{tree}").decode().strip(),
        "trackedFiles": len(entries),
        "exactRawOverrides": raw_matches,
        "verified": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.source, args.commit)
    with args.receipt.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
