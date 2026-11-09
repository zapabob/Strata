"""Tests for tools/check_cuda_spills.py, without a CUDA toolkit: synthetic resource rows and stand-in demanglers.

    python -m unittest tools.test_check_cuda_spills
"""
from __future__ import annotations

import contextlib
import io
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_cuda_spills as CS  # noqa: E402

MANGLED = "_ZN6strata7kernels10test_spillEv"
DEMANGLED = "void strata::kernels::test_spill()"
ROWS = [("test.cu.o", "sm_86", MANGLED, {"REG": 32, "STACK": 64, "LOCAL": 0})]   # a spilling kernel, not in ALLOWED


def demangler(d, body):
    """An executable stand-in for cu++filt / c++filt: reads names on stdin, runs `body`."""
    p = Path(d, "filt.py")
    p.write_text(body + "\n", encoding="utf-8")
    return str(p)


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        rc = fn(*args)
    return rc, out.getvalue()


def run_main(d, filt, lib_rows=ROWS, argv=()):
    """main() with tool discovery and cuobjdump's rows stood in: the demangler is the only real process."""
    lib = Path(d, "libstrata_kernels.a")
    lib.write_bytes(b"")
    with mock.patch.object(CS, "find_tools", return_value=("cuobjdump", filt)), \
         mock.patch.object(CS, "resource_usage", return_value=lib_rows), \
         mock.patch.object(sys, "argv", ["check_cuda_spills.py", *argv, str(lib)]):
        return quiet(CS.main)


class Classification(unittest.TestCase):
    def test_a_spilling_strata_kernel_is_a_violation(self):
        rc, out = quiet(CS.check, "x.a", ROWS, {MANGLED: DEMANGLED})
        self.assertEqual(rc, 1)
        self.assertIn("not in ALLOWED", out)

    def test_the_shipped_table_allows_its_own_measurements_and_a_lowered_allowance_fails(self):
        mangled = "_ZN6strata7kernels12_GLOBAL__N_113rope_table_kernelEPKiifPf"
        demangled = "strata::kernels::(anonymous namespace)::rope_table_kernel(int const*, int, float, float*)"
        rows = [("dflash2.cu.o", "sm_86", mangled, {"REG": 16, "STACK": 32, "LOCAL": 0})]
        rc, out = quiet(CS.check, "x.a", rows, {mangled: demangled})
        self.assertEqual(rc, 0, out)                       # the measured frame is the allowance
        key = "strata::kernels::{anonymous}::rope_table_kernel"
        self.assertEqual(CS.ALLOWED[key]["sm_86"], (32, 0))
        with mock.patch.dict(CS.ALLOWED, {key: {"sm_86": (16, 0)}}):
            rc, out = quiet(CS.check, "x.a", rows, {mangled: demangled})
        self.assertEqual(rc, 1)                            # one allowance lowered: the same object now fails
        self.assertIn("over its allowance STACK 16 LOCAL 0", out)

    def test_a_vendored_ggml_kernel_is_skipped_and_counted(self):
        rows = [("mmq.cu.o", "sm_86", "_Z9mul_mat_qILi2ELi8EEvPKvS1_PfRiiiiii", {"REG": 128, "STACK": 64})]
        rc, out = quiet(CS.check, "x.a", rows, {rows[0][2]: "void mul_mat_q<2, 8>(void const*, void const*, float*, int&, int, int, int, int, int)"})
        self.assertEqual(rc, 0)
        self.assertIn("1 vendored ggml entries skipped", out)


@unittest.skipIf(os.name == "nt", "the stand-in demangler is a #!/bin/sh script; Windows cannot run it as a program (needs a POSIX shell and exec of a shebang file)")
class Demangling(unittest.TestCase):
    """A mangled name has no "::", so a kernel the demangler did not translate would read as vendored and be skipped:
    every way the demangler can be absent or wrong must end in 77, never in a pass."""

    def setUp(self):
        # Windows cannot execute a POSIX shebang. Still exercise a real child
        # process and its stdin/status/output; only the fixture launch changes.
        real_run = CS.subprocess.run

        def run_fixture(args, **kwargs):
            if Path(args[0]).name == "filt.py":
                args = [sys.executable, *args]
            return real_run(args, **kwargs)

        launch = mock.patch.object(CS.subprocess, "run", side_effect=run_fixture)
        launch.start()
        self.addCleanup(launch.stop)

    def test_no_demangler_is_not_a_pass(self):
        rc, out = quiet(CS.demangle, None, [MANGLED])
        self.assertIsNone(rc)
        with tempfile.TemporaryDirectory() as d:
            lib = Path(d, "libstrata_kernels.a")
            lib.write_bytes(b"")
            with mock.patch.object(CS, "find_tools", return_value=("cuobjdump", None)), \
                 mock.patch.object(CS, "resource_usage", side_effect=AssertionError("read a library with no demangler")), \
                 mock.patch.object(sys, "argv", ["check_cuda_spills.py", str(lib)]):
                rc, out = quiet(CS.main)
        self.assertEqual(rc, 77)
        self.assertIn("no demangler", out)

    def test_a_demangler_that_exits_nonzero_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as d:
            filt = demangler(d, "import sys; sys.stdin.read(); print('no such tool', file=sys.stderr); sys.exit(3)")
            self.assertIsNone(quiet(CS.demangle, filt, [MANGLED])[0])
            rc, out = run_main(d, filt)
        self.assertEqual(rc, 77)
        self.assertIn("exited 3", out)
        self.assertNotIn("not allowed", out)

    def test_a_demangler_that_prints_the_wrong_number_of_lines_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as d:
            filt = demangler(d, "import sys; sys.stdin.read()")
            self.assertIsNone(quiet(CS.demangle, filt, [MANGLED])[0])
            rc, out = run_main(d, filt)
        self.assertEqual(rc, 77)
        self.assertIn("printed 0 lines for 1 names", out)

    def test_a_demangler_that_hands_a_mangled_name_back_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as d:
            filt = demangler(d, "import sys; sys.stdout.write(sys.stdin.read())")  # echoes every name as it came
            self.assertIsNone(quiet(CS.demangle, filt, [MANGLED])[0])
            rc, out = run_main(d, filt)
            rc_list, _ = run_main(d, filt, argv=["--list"])
        self.assertEqual(rc, 77)
        self.assertEqual(rc_list, 77)
        self.assertIn("left 1 of 1 names mangled", out)

    def test_a_demangler_that_prints_a_blank_name_is_not_a_pass(self):
        # exit 0 and one line per name, but the line is empty: the key would be "" and vendored("") is true, so a
        # spilling Strata kernel would be skipped as ggml's
        with tempfile.TemporaryDirectory() as d:
            filt = demangler(d, "import sys\nfor _ in sys.stdin:\n    print()")
            self.assertIsNone(quiet(CS.demangle, filt, [MANGLED])[0])
            rc, out = run_main(d, filt)
        self.assertEqual(rc, 77)
        self.assertIn("printed a blank name for 1 of 1 names", out)
        self.assertNotIn("VIOLATION", out)

    def test_an_unmangled_name_may_come_back_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            filt = demangler(d, "import sys; sys.stdout.write(sys.stdin.read())")
            names, _ = quiet(CS.demangle, filt, ["plain_c_kernel"])     # extern "C": nothing to demangle
        self.assertEqual(names, {"plain_c_kernel": "plain_c_kernel"})

    def test_a_working_demangler_reaches_the_verdict(self):
        with tempfile.TemporaryDirectory() as d:
            filt = demangler(d, "import sys\nfor _ in sys.stdin:\n    print(%r)" % DEMANGLED)
            rc, out = run_main(d, filt)
        self.assertEqual(rc, 1)
        self.assertIn("VIOLATION %s sm_86: STACK 64 LOCAL 0 (not in ALLOWED)" % DEMANGLED, out)


if __name__ == "__main__":
    unittest.main()
