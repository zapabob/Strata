"""Real Git fixtures for the source-byte gate used by the private build."""

from __future__ import annotations
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from verify_frozen_llama_source import verify


class SourceFreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="qwen35-source-proof-")
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name)
        self.file = self.source / "sentinel.cpp"
        self.original = b"int sentinel = 7;\n"
        self.file.write_bytes(self.original)
        self.git("init", "--quiet")
        self.git("add", "sentinel.cpp")
        self.git("status", "--short")
        self.git("diff", "--cached")
        subprocess.run(
            ["git", "log", "--oneline", "-10"],
            cwd=self.source,
            capture_output=True,
            check=False,
        )
        self.git("commit", "--quiet", "-m", "[Test] frozen source fixture")
        self.commit = self.git("rev-parse", "HEAD").strip()

    def git(self, *args: str) -> str:
        return subprocess.check_output(
            ["git", *args],
            cwd=self.source,
            text=True,
            stderr=subprocess.PIPE,
            env=dict(
                os.environ,
                GIT_AUTHOR_NAME="Strata fixture",
                GIT_AUTHOR_EMAIL="fixture@example.invalid",
                GIT_COMMITTER_NAME="Strata fixture",
                GIT_COMMITTER_EMAIL="fixture@example.invalid",
            ),
        )

    def test_clean_source_matches_the_committed_blob(self) -> None:
        result = verify(self.source, self.commit)
        self.assertTrue(result["verified"])
        self.assertEqual(result["trackedFiles"], 1)

    def test_same_size_and_mtime_cannot_hide_nul_corruption(self) -> None:
        before = self.file.stat()
        self.file.write_bytes(bytes(len(self.original)))
        os.utime(self.file, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(self.file.stat().st_size, before.st_size)
        self.assertEqual(self.file.stat().st_mtime_ns, before.st_mtime_ns)
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            verify(self.source, self.commit)

    def test_untracked_inputs_and_wrong_commit_are_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "commit differs"):
            verify(self.source, "0" * 40)
        (self.source / "unreviewed.cpp").write_text("int unexpected;\n")
        with self.assertRaisesRegex(ValueError, "Untracked"):
            verify(self.source, self.commit)


if __name__ == "__main__":
    unittest.main()
