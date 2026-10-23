"""Normalize Japanese-only MSVC diagnostics for Ninja's UTF-8 header parser.

The child compiler and its return code are preserved. No environment is changed.
CUDA uses its original nvcc depfile path and does not use this launcher.
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    result = subprocess.run(sys.argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    try:
        output = result.stdout.decode("utf-8")
    except UnicodeDecodeError:
        try:
            output = result.stdout.decode("cp932")
        except UnicodeDecodeError:
            sys.stderr.buffer.write(result.stdout)
            sys.stderr.write("MSVC diagnostics are neither UTF-8 nor CP932; refusing unreliable header tracking\n")
            return 125
    sys.stdout.buffer.write(output.encode("utf-8"))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
