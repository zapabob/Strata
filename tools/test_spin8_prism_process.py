"""Regression coverage for inherited Prism argument contamination."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from spin8_prism_process import controlled_environment, run_child


class EnvironmentTest(unittest.TestCase):
    def test_copy_removes_empty_and_invalid_without_mutation(self) -> None:
        original = {"LLAMA_ARG_CACHE_TYPE_V": "turbo3", "llama_arg_model": "",
                    "PATH": "preserved", "EXPLICIT_CACHE": "q8_0"}
        before = original.copy()
        environment, removed = controlled_environment(original)
        self.assertEqual(original, before)
        self.assertEqual(environment, {"PATH": "preserved", "EXPLICIT_CACHE": "q8_0"})
        self.assertEqual(removed, ["LLAMA_ARG_CACHE_TYPE_V", "llama_arg_model"])

    def test_actual_child_and_parent_environment(self) -> None:
        for value in ("turbo3", ""):
            with self.subTest(value=value), patch.dict(
                os.environ, {"LLAMA_ARG_CACHE_TYPE_V": value}
            ):
                before = dict(os.environ)
                result = run_child([
                    sys.executable, "-B", "-c",
                    "import os; assert not any(k.upper().startswith('LLAMA_ARG_') for k in os.environ)",
                ])
                self.assertEqual(result["returncode"], 0, result)
                self.assertEqual(dict(os.environ), before)

    def test_timeout_preserves_failure_and_output(self) -> None:
        result = run_child([sys.executable, "-B", "-c",
                            "import time; print('started', flush=True); time.sleep(30)"], timeout=1)
        self.assertEqual(result["returncode"], 124)
        self.assertTrue(result["timedOut"])
        self.assertIn("started", result["stdout"])

    @unittest.skipUnless(os.environ.get("SPIN8_PRISM_SERVER"), "real binary not selected")
    def test_real_version(self) -> None:
        binary = Path(os.environ["SPIN8_PRISM_SERVER"])
        self.assertTrue(binary.is_file())
        for value in ("turbo3", ""):
            with self.subTest(value=value), patch.dict(
                os.environ, {"LLAMA_ARG_CACHE_TYPE_V": value,
                             "LLAMA_ARG_CACHE_TYPE_K": value}
            ):
                before = dict(os.environ)
                result = run_child([str(binary), "--version"])
                self.assertEqual(result["returncode"], 0, result)
                self.assertIn("73bfe6cc", str(result))
                self.assertEqual(dict(os.environ), before)


if __name__ == "__main__":
    unittest.main()
