"""Exercise the actual pinned UI script against preserved stale dist fixtures."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest
import uuid
import re


class NoEmbeddedUITest(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("SPIN8_PRISM_BUILD"), "linked build not selected")
    def test_linked_empty_ui_and_real_server_header_dependency(self) -> None:
        build = Path(os.environ["SPIN8_PRISM_BUILD"])
        result = subprocess.run([str(build / "bin/strata-spin8-ui-test.exe")], capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("linked_ui_asset_count=0", result.stdout)
        header = build / "tools/ui/ui.h"
        self.assertIn("std::array<llama_ui_asset, 0>", header.read_text(encoding="utf-8"))
        cache = (build / "CMakeCache.txt").read_text(encoding="utf-8")
        ninja = re.search(r"^CMAKE_MAKE_PROGRAM:FILEPATH=(.+)$", cache, re.M).group(1)
        obj = "tools/server/CMakeFiles/llama-server-impl.dir/server-http.cpp.obj"
        dependencies = subprocess.check_output([ninja, "-C", str(build), "-t", "deps", obj], text=True, encoding="utf-8")
        self.assertIn("tools/ui/ui.h", dependencies.replace("\\", "/"))
        self.assertGreaterEqual((build / obj).stat().st_mtime_ns, header.stat().st_mtime_ns)

    @unittest.skipUnless(os.environ.get("SPIN8_PRISM_SOURCE"), "pinned source not selected")
    def test_explicit_disable_ignores_both_stale_dist_and_hf(self) -> None:
        source = Path(os.environ["SPIN8_PRISM_SOURCE"])
        embed = Path(os.environ["SPIN8_UI_EMBED"])
        evidence = Path(os.environ["SPIN8_TEST_TMP"]) / ("no-ui-" + uuid.uuid4().hex)
        for folder in ("source/dist", "binary/dist"):
            directory = evidence / folder
            directory.mkdir(parents=True, exist_ok=False)
            (directory / "index.html").write_text("STALE_UI_MUST_NOT_BE_EMBEDDED", encoding="utf-8")
        command = [
            "cmake", f"-DUI_SOURCE_DIR={evidence / 'source'}",
            f"-DUI_BINARY_DIR={evidence / 'binary'}", f"-DLLAMA_SOURCE_DIR={source}",
            f"-DLLAMA_UI_EMBED={embed}", "-DEMBED_UI=OFF", "-DBUILD_UI=ON",
            "-DHF_ENABLED=ON", "-DHF_BUCKET=invalid.invalid/must-not-be-contacted",
            "-P", str(source / "scripts/ui-assets.cmake"),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
        (evidence / "stdout.log").write_text(result.stdout, encoding="utf-8")
        (evidence / "stderr.log").write_text(result.stderr, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no provisioning or cached assets", result.stdout)
        generated = (evidence / "binary/ui.cpp").read_text(encoding="utf-8")
        self.assertNotIn("STALE_UI_MUST_NOT_BE_EMBEDDED", generated)
        self.assertNotIn("index.html", generated)
        for folder in ("source/dist", "binary/dist"):
            self.assertEqual((evidence / folder / "index.html").read_text(), "STALE_UI_MUST_NOT_BE_EMBEDDED")
        self.assertFalse((evidence / "binary/.ui-stamp").exists())


if __name__ == "__main__":
    unittest.main()
