"""Preserve explicitly recorded, inactive synthetic test profiles on H: before removal."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import psutil

SOURCE = Path("C:/Users/downl/AppData/Local/Temp/opencode")
DESTINATION = Path("H:/Strata/validation/retired-test-profiles-20261107")
# Names are from this session's retained GUI test logs, not a directory wildcard.
NAMES = [
    "strata-hybrid-d7C3yX", "strata-hybrid-FZxRAF", "strata-hybrid-drQUmL",
    "strata-hybrid-Iy9udq", "strata-hybrid-jokDIq", "strata-hybrid-J2dAk3",
    "strata-hybrid-NGoGhZ", "strata-hybrid-xeFqe3", "strata-hybrid-IREUyq",
    "strata-hybrid-QqggpA", "strata-hybrid-8LeQYs", "strata-hybrid-NliaKw",
    "strata-hybrid-MVize9", "strata-hybrid-7uJwlz", "strata-hybrid-xuNOMy",
    "strata-hybrid-Sm4GqG", "strata-hybrid-YUbY5n", "strata-hybrid-KP7gpU",
    "strata-hybrid-TuVzjc", "strata-hybrid-osOzMt", "strata-hybrid-ZA07rc",
    "strata-hybrid-OV6Wlb", "strata-hybrid-PiZ0zv", "strata-hybrid-wOLcr7",
    "strata-hybrid-yoCVoi", "strata-hybrid-96syRf", "strata-hybrid-26vEid",
    "strata-hybrid-f3M5Pe", "strata-hybrid-Agu61p", "strata-hybrid-o3CAIG",
    "strata-hybrid-rZL93v", "strata-hybrid-n5FTqy", "strata-hybrid-kcknoC",
]


def inventory(root: Path, hashes: bool) -> dict:
    result = {}
    pending = [root]
    while pending:
        folder = pending.pop()
        if folder.is_symlink() or folder.is_junction():
            raise ValueError("linked profile tree")
        for path in folder.iterdir():
            if path.is_symlink() or path.is_junction():
                raise ValueError("linked profile entry")
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                stat = path.stat()
                entry = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
                if hashes:
                    with path.open("rb") as stream:
                        entry["sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
                result[path.relative_to(root).as_posix()] = entry
            else:
                raise ValueError("unsupported profile entry")
    return result


def inactive(path: Path) -> bool:
    needle = str(path).lower().replace("\\", "/")
    for process in psutil.process_iter(["cmdline"]):
        try:
            text = " ".join(process.info["cmdline"] or []).lower().replace("\\", "/")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if needle in text:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--target-free-gib", type=int, default=12)
    args = parser.parse_args()
    if not 5 <= args.target_free_gib <= 30:
        raise ValueError("bounded target free space required")
    assert SOURCE.is_dir() and not SOURCE.is_junction() and not SOURCE.is_symlink()
    assert DESTINATION.parent.is_dir()
    if args.execute:
        DESTINATION.mkdir(exist_ok=True)
        assert not DESTINATION.is_junction() and not DESTINATION.is_symlink()
    report = {"executed": args.execute, "before_free": shutil.disk_usage(SOURCE).free, "profiles": []}
    for name in NAMES:
        if args.execute and shutil.disk_usage(SOURCE).free >= args.target_free_gib * 1024**3:
            break
        source, target = SOURCE / name, DESTINATION / name
        if not source.is_dir():
            continue
        row = {"name": name}
        try:
            assert inactive(source), "profile is still in use"
            files = inventory(source, args.execute)
            row.update(files=len(files), bytes=sum(f["bytes"] for f in files.values()))
            if args.execute:
                assert not target.exists(), "preserve prior destination"
                assert shutil.disk_usage(DESTINATION).free > row["bytes"] + 10 * 1024**3
                shutil.copytree(source, target, copy_function=shutil.copy2)
                assert inventory(target, True) == files, "copied profile differs"
                assert inventory(source, True) == files and inactive(source), "source changed during copy"
                receipt = DESTINATION / (name + ".inventory.json")
                with receipt.open("x", encoding="utf-8") as stream:
                    json.dump({"source": str(source), "destination": str(target), "files": files}, stream)
                # Only an exact, verified copy of this explicitly owned inactive tree is removed.
                shutil.rmtree(source)
                row["preserved_and_removed"] = not source.exists()
        except (OSError, AssertionError, ValueError) as error:
            row["error"] = str(error)
        report["profiles"].append(row)
        print(json.dumps(row), flush=True)
    report["after_free"] = shutil.disk_usage(SOURCE).free
    if args.execute:
        with (DESTINATION / "relocation.json").open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2)
    print(json.dumps({k: v for k, v in report.items() if k != "profiles"}), flush=True)


if __name__ == "__main__":
    main()
