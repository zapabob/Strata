"""Run explicit source checks with a small environment and isolated scratch home.

Do not inherit live agent credentials, model settings or acquisition overrides.
The command is given after --; `python` uses this uv-selected interpreter.
This runner does not admit native builds, model launches or packaging jobs.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
NODE = Path("C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe")
SAFE_KEYS = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "SYSTEMDRIVE",
    "COMSPEC",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMW6432",
    "PROGRAMDATA",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
    "OS",
}


def main() -> int:
    """Isolate profile/temp locations before passing control to a test command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", choices=("root", "host"), default="root")
    parser.add_argument(
        "--scratch-parent",
        type=Path,
        default=Path("C:/Users/downl/AppData/Local/Temp/opencode"),
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or command[0] not in ("python", "node"):
        parser.error("supply an explicit python or node check after --")
    command[0] = sys.executable if command[0] == "python" else str(NODE)
    parent = args.scratch_parent
    if not parent.is_dir():
        raise ValueError("Approved scratch parent missing")
    env = {key: value for key, value in os.environ.items() if key.upper() in SAFE_KEYS}
    with tempfile.TemporaryDirectory(
        prefix="strata-0212-check-", dir=parent
    ) as scratch:
        home = Path(scratch)
        for name in ("tmp", "Local", "Roaming", "components"):
            (home / name).mkdir()
        env.update(
            HOME=scratch,
            USERPROFILE=scratch,
            LOCALAPPDATA=str(home / "Local"),
            APPDATA=str(home / "Roaming"),
            TEMP=str(home / "tmp"),
            TMP=str(home / "tmp"),
            TMPDIR=str(home / "tmp"),
            STRATA_HOME=scratch,
            STRATA_TEST_SCRATCH=scratch,
            STRATA_COMPONENTS_DIR=str(home / "components"),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONIOENCODING="utf-8",
            PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
            PYTHONPATH=str(ROOT),
            STRATA_TEST_NODE_EXE=str(NODE),
            STRATA_TEST_PYTHON_EXE=sys.executable,
            STRATA_TEST_CONCURRENCY="1",
            STRATA_TEST_TIMEOUT_MS="120000",
            NODE_OPTIONS="--max-old-space-size=256",
        )
        cwd = ROOT / "apps/host" if args.cwd == "host" else ROOT
        result = subprocess.run(command, cwd=cwd, env=env, check=False)
    logging.info("Check exit code: %d", result.returncode)
    return result.returncode


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
