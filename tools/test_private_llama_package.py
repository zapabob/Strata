"""Private runtime integrity and non-activating plan checks; no real runtime needed."""

from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "private_package", Path(__file__).with_name("stage_private_llama_runtime.py")
)


class PackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            Path(SPEC.origin).is_file(), "private runtime packager is missing"
        )
        self.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(prefix="qwen35-package-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.stage = self.root / "stage"
        self.stage.mkdir()
        (self.stage / "llama-server.exe").write_bytes(b"synthetic executable")
        (self.stage / "source-patch.diff").write_bytes(b"synthetic reviewed patch")
        self.manifest = {
            "schema": 1,
            "backend": "prism",
            "version": "0.4.1",
            "privateCandidate": True,
            "source": {"commit": "a" * 40, "baseCommit": "b" * 40, "patches": []},
            "files": [
                {
                    "path": p.name,
                    "bytes": p.stat().st_size,
                    "sha256": self.module.sha(p),
                }
                for p in self.stage.iterdir()
            ],
        }
        (self.stage / "runtime.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        self.digest = self.module.sha(self.stage / "runtime.json")

    def test_exact_manifest_and_payload_membership(self) -> None:
        self.assertEqual(
            self.module.verify_package(self.stage, self.digest)["version"], "0.4.1"
        )
        (self.stage / "llama-server.exe").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "payload"):
            self.module.verify_package(self.stage, self.digest)

    def test_copy_checks_bytes_and_never_overwrites_a_prior_payload(self) -> None:
        source = self.stage / "llama-server.exe"
        target = self.root / "copy.exe"
        expected = self.module.sha(source)
        self.module.copy_verified(source, target, expected)
        self.assertEqual(self.module.sha(target), expected)
        with self.assertRaises(FileExistsError):
            self.module.copy_verified(source, target, expected)
        bad = self.root / "bad-copy.exe"
        with patch.object(
            self.module.shutil,
            "copy2",
            side_effect=lambda src, dst: Path(dst).write_bytes(
                bytes(Path(src).stat().st_size)
            ),
        ):
            with self.assertRaisesRegex(ValueError, "Copied payload"):
                self.module.copy_verified(source, bad, expected)

    def test_changed_manifest_and_extra_dll_are_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "manifest"):
            self.module.verify_package(self.stage, "0" * 64)
        (self.stage / "extra.dll").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "membership"):
            self.module.verify_package(self.stage, self.digest)

    def test_path_escape_and_case_collision_are_refused(self) -> None:
        for path in ("../outside.dll", "C:/outside.dll", "llama-server.exe/../x"):
            self.manifest["files"].append(
                {"path": path, "bytes": 0, "sha256": "0" * 64}
            )
            (self.stage / "runtime.json").write_text(
                json.dumps(self.manifest), encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                self.module.verify_package(
                    self.stage, self.module.sha(self.stage / "runtime.json")
                )
            self.manifest["files"].pop()
        self.manifest["files"].append(
            dict(
                self.manifest["files"][0],
                path=self.manifest["files"][0]["path"].upper(),
            )
        )
        (self.stage / "runtime.json").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )
        with self.assertRaises(ValueError):
            self.module.verify_package(
                self.stage, self.module.sha(self.stage / "runtime.json")
            )

    def test_plan_honors_explicit_user_environment_without_writing_it(self) -> None:
        pointer = b'{"folder":"old-runtime"}\n'
        env = {
            "User": "C:/explicit/llama-server.exe",
            "Process": "C:/explicit/llama-server.exe",
            "Machine": None,
        }
        original = dict(env)
        result = self.module.selection_plan("prism-private-new", pointer, env)
        self.assertEqual(result["recommendedBackend"], "PrismML")
        self.assertEqual(result["automaticEnvironment"], env)
        self.assertEqual(env, original)
        self.assertFalse(result["pointerWouldSelectCandidate"])
        self.assertFalse(result["activated"])
        self.assertEqual(
            result["previousPointerSHA256"], hashlib.sha256(pointer).hexdigest()
        )

    def test_plan_without_environment_retains_old_pointer_as_rollback(self) -> None:
        result = self.module.selection_plan(
            "prism-private-new", b'{"folder":"old-runtime"}', {}
        )
        self.assertTrue(result["pointerWouldSelectCandidate"])
        self.assertEqual(result["proposedPointer"]["previous"], "old-runtime")
        self.assertFalse(result["activated"])

    def test_a_successful_link_with_a_failed_resource_guard_is_not_admitted(
        self,
    ) -> None:
        report = {
            "status": "success",
            "sourceCommit": "a" * 40,
            "cudaCubins": ["sm_120"],
            "cudaArchitecture": "120",
            "jobs": 1,
        }
        freeze = {"commit": "a" * 40, "baseCommit": self.module.BASE_COMMIT}
        guard = {
            "status": "passed",
            "containedBeforeGo": True,
            "cleanup": True,
            "abort": None,
            "exitCode": 0,
            "floorsGiB": {"ram": 3, "commit": 4, "c": 5, "h": 10},
        }
        self.module.admit_build(report, freeze, guard)
        for change in (
            {"abort": ["ram"]},
            {"status": "running"},
            {"cleanup": False},
            {"exitCode": 1},
            {"floorsGiB": {"ram": 1, "commit": 4, "c": 5, "h": 10}},
        ):
            with self.assertRaisesRegex(ValueError, "guard"):
                self.module.admit_build(report, freeze, dict(guard, **change))


if __name__ == "__main__":
    unittest.main()
