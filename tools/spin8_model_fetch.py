"""Fetch only the frozen Strata Q2_0 shards, with size and SHA-256 verification."""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import tempfile
import urllib.request
from typing import Iterator


def frozen_files() -> list[dict]:
    """Read literal pins without executing the installer."""
    tree = ast.parse((Path(__file__).resolve().parents[1] / "setup.py").read_text(encoding="utf-8-sig"))
    values = {}
    for item in tree.body:
        if isinstance(item, ast.Assign):
            for name in item.targets:
                if isinstance(name, ast.Name) and name.id in {"HF_REVISIONS", "ISTA_FILES"}:
                    values[name.id] = ast.literal_eval(item.value)
    repo = "ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF"
    revision = values["HF_REVISIONS"][repo]
    return [dict(name=name, size=size, sha256=digest,
                 url=f"https://huggingface.co/{repo}/resolve/{revision}/Q2_0/{name}")
            for name, (size, digest) in values["ISTA_FILES"].items() if "-Q2_0-" in name]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@contextmanager
def exclusive_download(path: Path) -> Iterator[None]:
    """Use an OS lock that is released even if the downloader is terminated."""
    with path.open("a+b") as lock:
        if lock.seek(0, 2) == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def fetch(item: dict, directory: Path) -> dict:
    with exclusive_download(directory / (item["name"] + ".lock")):
        return _fetch_locked(item, directory)


READ_BYTES = 128 * 1024
RANGE_BYTES = 64 * 1024**2


def append_range(item: dict, partial: Path, start: int, end: int) -> None:
    """Validate a disk-staged range before extending the existing prefix.

    A large request amortizes connection setup; one 128KiB buffer is reused.
    Interrupted appends contain only bytes from a fully validated response.
    Invalid/short/oversized responses never modify the preexisting prefix.
    """
    request = urllib.request.Request(item["url"], headers={"Range": f"bytes={start}-{end}"})
    buffer = bytearray(READ_BYTES)
    view = memoryview(buffer)
    with tempfile.TemporaryFile(dir=partial.parent) as staged:
        with urllib.request.urlopen(request, timeout=30) as response:
            expected = f"bytes {start}-{end}/{item['size']}"
            if response.status != 206 or response.headers.get("Content-Range") != expected:
                raise ValueError("range_resume_rejected")
            remaining = end - start + 1
            while remaining:
                count = response.readinto(view[:min(remaining, READ_BYTES)])
                if not count or count < 0 or count > min(remaining, READ_BYTES):
                    raise ValueError("range_length_mismatch")
                if staged.write(view[:count]) != count:
                    raise OSError("short_staging_write")
                remaining -= count
            if response.read(1):
                raise ValueError("range_length_mismatch")
        staged.seek(0)
        with partial.open("r+b" if start or partial.exists() else "xb") as output:
            if output.seek(0, 2) != start:
                raise ValueError("partial_model_changed_during_transfer")
            while count := staged.readinto(buffer):
                if output.write(view[:count]) != count:
                    raise OSError("short_partial_write")


def _fetch_locked(item: dict, directory: Path) -> dict:
    destination = directory / item["name"]
    partial = destination.with_suffix(destination.suffix + ".partial")
    if destination.exists():
        if destination.stat().st_size != item["size"] or sha256(destination) != item["sha256"]:
            raise ValueError(f"existing_model_digest_mismatch: {destination.name}")
        return dict(name=destination.name, verified=True, sha256=item["sha256"])
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > item["size"]:
        raise ValueError("partial_model_too_large")
    if shutil.disk_usage(directory).free < item["size"] - offset + 10 * 1024**3:
        raise ValueError("insufficient_disk_reserve")
    # One transfer at a time. Temporary staging uses disk, not a 64MiB body in
    # RAM, and the existing contiguous prefix remains a resumable artifact.
    reported = offset // (512 * 1024**2)
    while offset < item["size"]:
        end = min(offset + RANGE_BYTES, item["size"]) - 1
        append_range(item, partial, offset, end)
        offset = end + 1
        if offset // (512 * 1024**2) > reported or offset == item["size"]:
            logging.info("%s: %d / %d bytes", item["name"], offset, item["size"])
            reported = offset // (512 * 1024**2)
    if partial.stat().st_size != item["size"] or sha256(partial) != item["sha256"]:
        raise ValueError("download_digest_mismatch")
    # Hard-link publication is atomic and fails if a destination appeared during
    # transfer. Never clobber a separately created model after a long download.
    os.link(partial, destination)
    partial.unlink()
    return dict(name=destination.name, verified=True, sha256=item["sha256"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("H:/Strata/models/q2_0"))
    parser.add_argument("--plan", action="store_true", help="Show pins; do not create files or download")
    parser.add_argument("--shard", type=int, choices=(1, 2),
                        help="Verify/fetch only this shard; does not verify the other shard")
    args = parser.parse_args()
    files = frozen_files()
    if args.shard is not None:
        suffix = f"-{args.shard:05d}-of-00002.gguf"
        files = [item for item in files if item["name"].endswith(suffix)]
        if len(files) != 1:
            raise ValueError("selected_shard_pin_missing_or_ambiguous")
    if args.plan:
        print(json.dumps(files, indent=2))
        return 0
    args.directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO)
    if args.shard is not None:
        logging.info("Selected shard %d only; the other shard is not verified in this run", args.shard)
    for item in files:
        logging.info("Fetching %s (%d bytes)", item["name"], item["size"])
        result = fetch(item, args.directory)
        logging.info("Verified %s", result["name"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
