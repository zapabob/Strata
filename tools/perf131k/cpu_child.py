"""Owned stdlib-only CPU fixture. No engine/GPU/network imports or user commands."""
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    scenario = sys.argv[1]
    if scenario == "ok":
        os.write(1, ("GUARD=" + os.environ.get("STRATA_KEEP_LEFTOVERS", "missing") + "\n").encode())
    elif scenario == "sleep":
        time.sleep(20)
    elif scenario == "flood":
        while True:
            os.write(1, b"x" * 4096)
    elif scenario in ("grandchild", "tree_hold"):
        try:
            child = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "sleep"])
        except OSError:
            os.write(1, b"PROCESS_DENIED\n")
            return 24
        os.write(1, b"GRANDCHILD\n")
        if scenario == "tree_hold":
            os.write(1, f"TREE {os.getpid()} {child.pid}\n".encode())
        time.sleep(20 if scenario == "tree_hold" else 0.15)
    elif scenario == "memory":
        blocks = []
        try:
            for _ in range(512):
                blocks.append(bytearray(1024**2))
        except MemoryError:
            os.write(1, b"MEM_DENIED\n")
            return 23
        return 0
    else:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
