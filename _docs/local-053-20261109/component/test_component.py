"""Small synthetic fixtures only: no signing, production imports, native/model/tool execution."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import compose as cli
import core
import deps as dependency_cli
import quality


class Fixtures(unittest.TestCase):
    def test_dependency_scope_tracks_same_volume_primary_staging(self) -> None:
        pending = core.STAGING / 'pending-engine-bundle' / core.NAME
        with patch('sys.argv', ['deps.py', str(pending)]), patch.object(dependency_cli, 'production_modules', return_value=(None, None, 'fixture')), patch.object(dependency_cli, 'check_dependencies') as check:
            dependency_cli.main()
            check.assert_called_once_with(pending, 'fixture')
        old = core.WORK / 'pending-engine-bundle' / core.NAME
        with patch('sys.argv', ['deps.py', str(old)]), patch.object(dependency_cli, 'production_modules') as production:
            with self.assertRaises(core.Blocked):
                dependency_cli.main()
            production.assert_not_called()

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="fixture-", dir=core.HERE)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            path.write_text(json.dumps(value), encoding="utf-8")

    def test_plan_does_not_open_key_or_spawn(self) -> None:
        args = cli.parser().parse_args(["--key", str(self.root / "absent-key")])
        result = cli.plan(args)
        self.assertFalse(result["execution"])
        self.assertFalse(result["checksRun"])
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertNotIn(str(args.key), json.dumps(result))

    def test_paths_and_duplicate_json_fail_closed(self) -> None:
        for name in ("../x", "C:/x", "a\\b", "a//b", "/root", "a/./b", "a:stream", "a. /b"):
            with self.subTest(name=name), self.assertRaises(core.Blocked):
                core.relative(name)
        self.put(self.root / "duplicate.json", b'{"ok":true,"ok":false}')
        with self.assertRaises(core.Blocked):
            core.load(self.root / "duplicate.json")

    def test_fresh_native_wins_retains_notices_and_no_old_build_record(self) -> None:
        native, old, output = (self.root / name for name in ("native", "old", "output"))
        self.put(native / core.MANIFEST, {"version": "0.5.3", "files": [], "build_id": core.NATIVE_COMMIT})
        for name in ("strata.exe", "strata-q36.exe", "native-build.json", "fresh.dll"):
            self.put(native / name, b"new")
            self.put(old / name, b"obsolete")
        self.put(old / "BUILD.json", b"obsolete metadata")
        self.put(old / "strata-dsv41.exe", b"obsolete")
        self.put(old / core.MANIFEST, {})
        for name in ("local-backends/prism/runtime.json", "local-backends/turboquant/runtime.json", "notices/LICENSE"):
            self.put(old / name, b"retain")
        before = core.inventory(native)
        core.compose(native, old, output, lambda: None)
        actual = core.inventory(output)
        self.assertEqual(actual["strata.exe"], before["strata.exe"])
        self.assertEqual(actual["native-build.json"], before["native-build.json"])
        self.assertIn("notices/LICENSE", actual)
        self.assertNotIn("BUILD.json", actual)
        self.assertNotIn("strata-dsv41.exe", actual)
        self.assertEqual(core.inventory(native), before)
        with self.assertRaises(core.Blocked):
            core.compose(native, old, output, lambda: None)

    def test_signature_must_pass_before_full_production_payload_check(self) -> None:
        self.put(self.root / core.MANIFEST, {"signature": {"alg": "ed25519"}})
        calls = []
        def refuse(*_args: object) -> None:
            calls.append("signature")
            raise core.Blocked("untrusted fixture")
        ec = SimpleNamespace(read_manifest=lambda _: object(), signing_payload=lambda _: b"payload",
                             verify=lambda *a, **k: calls.append("payload"))
        signing = SimpleNamespace(load_trusted_keys=lambda **k: {}, verify_bytes=refuse)
        with self.assertRaises(core.Blocked):
            core.verify_payload(self.root, ec, signing, signed=True)
        self.assertEqual(calls, ["signature"])

    def test_managed_root_scaffolding_is_preserved_without_old_component(self) -> None:
        bundle, pending = (self.root / name for name in ("bundle", "pending"))
        pending.mkdir()
        self.put(bundle / ".gitignore", b"*\n!.gitignore\n!README.txt\n")
        self.put(bundle / "README.txt", b"reviewed source scaffolding")
        self.put(bundle / "old-component/strata.exe", b"old")
        original = core.inventory(bundle)
        self.assertEqual(core.preserve_bundle_metadata(bundle, pending, lambda: None), original)
        self.assertEqual(core.inventory(pending), {k: v for k, v in original.items() if "/" not in k})
        self.assertEqual(core.inventory(bundle), original)
        self.put(bundle / "unexpected.txt", b"parent must inspect")
        with self.assertRaises(core.Blocked):
            core.preserve_bundle_metadata(bundle, pending, lambda: None)

    def test_archive_payload_and_flat_url_are_bound(self) -> None:
        archive = self.root / "fixture.zip"
        payload = self.root / "payload"
        payload.mkdir()
        self.put(payload / core.MANIFEST, {})
        self.put(payload / "strata.exe", b"fixture, never executable")
        tree = core.inventory(payload)
        with zipfile.ZipFile(archive, "x") as bundle:
            for name in tree:
                bundle.write(payload / name, name)
        entry = {"url": archive.name, "format": "zip", "size": archive.stat().st_size,
                 "sha256": core.sha(archive), "manifest_sha256": tree[core.MANIFEST],
                 "installed_bytes": sum((payload / k).stat().st_size for k in tree)}
        core.check_archive(archive, entry, tree)
        entry["url"] = "engine/fixture.zip"
        with self.assertRaises(core.Blocked):
            core.check_archive(archive, entry, tree)
        entry["url"] = archive.name
        tree["strata.exe"] = "0" * 64
        with self.assertRaises(core.Blocked):
            core.check_archive(archive, entry, tree)

    def report_fixture(self, resource_pass: bool = False) -> tuple[Path, Path, Path, Path]:
        base, native, source, adapters = (self.root / k for k in ("base", "native", "source", "adapters"))
        source.mkdir()
        self.put(adapters / "phases.py", b'CPU_REQUIRED = ("cpu_required",)\nGPU_REQUIRED = ("gpu_required",)\n')
        for name in ("model.py", "common.py", "binding.mjs"):
            self.put(adapters / name, b"fixture")
        freeze = {"sourceCommit": core.NATIVE_COMMIT, "sourceRoot": str(source), "adapters": core.inventory(adapters)}
        self.put(base / "freeze.json", freeze)
        for name in ("strata.exe", "strata-q36.exe", "native-build.json"):
            self.put(native / name, b"never executable fixture")
        manifest = {"files": []}
        self.put(native / core.MANIFEST, manifest)
        package = {"nativeSourceCommit": core.NATIVE_COMMIT, "sourceRoot": str(source), "component": str(native),
                   "signed": False, "installed": False, "version": "0.5.3", "manifestSHA256": core.sha(native / core.MANIFEST),
                   "files": [], "strataSHA256": core.sha(native / "strata.exe"), "q36SHA256": core.sha(native / "strata-q36.exe"),
                   "nativeBuildSHA256": core.sha(native / "native-build.json")}
        self.put(base / "results/package.json", package)
        def run(code: int = 0) -> dict:
            return {"status": "FINISHED", "native_exit_code": code, "contained_before_resume": True,
                    "termination_confirmed": True, "job_active_after": 0, "observed_dropped_bytes": 0}
        def row(name: str) -> dict:
            return {"passed": True, "name": name, "run": run()}
        phases = {}
        for name in ("build", "stage", "cpu", "gpu", "sanitizer", "spill", "model-bounded", "model-legacy7", "model-restart", "compare"):
            phases[name] = {**row(name + "-phase"), "frozenIdentity": freeze}
            if name == "spill" and not resource_pass:
                phases[name].update(passed=False, run=run(1))
            self.put(base / "receipts" / (name + "-phase.json"), phases[name])
        phases["bind"] = {"passed": False}
        for kind, names in (("cpu", ["cpu_required", "strata-version", "strata-help", "strata-q36-version", "strata-q36-help"]),
                            ("gpu", ["gpu_required", "spin8-b2-first-use", "spin8-b2-full"]),
                            ("sanitizer", ["version", "q36_kv_lifecycle_test", "q36_kv_cache_test"])):
            self.put(base / "results" / (kind + ".json"), {"passed": True, "releaseQualified": False,
                     "optionalTestsPassedWhenPresent": True, "cases": [row(kind + "-" + name) for name in names]})
        names = ["first-owner-A", "same-owner-A", "different-owner-B", "missing-owner", "cancel-decode", "after-cancel-clears", "short-generation"]
        inputs = {"fixture.gguf": {"sha256": "f" * 64, "bytes": 1, "mtime_ns": 1}}
        for phase in ("model-bounded", "model-legacy7", "model-restart"):
            requests = [{"name": name, "submittedCount": 1, "nativePromptCount": 1, "nativeFreshReadCount": 1,
                         "nativeReuseCount": 0, "generatedCount": 1, "generatedIds": [2], "generatedText": " text",
                         "requestedMaxNew": 8, "finish": "cancel" if name == "cancel-decode" else "length"}
                        for name in (names if phase != "model-restart" else [names[0], names[-1]])]
            protocol = {"passed": True, "exeSHA256": package["strataSHA256"], "capacity": 4096,
                        "ready": "READY 4096 stop", "fullInputQuality": False, "exitCodeBeforeJobCleanup": 0,
                        "memorySamples": 7, "mode": "legacy" if phase == "model-legacy7" else "bounded-experts-v1",
                        "requests": requests, "inputIds": [1], "inputCount": 1,
                        "memoryReceipt": {"q36_memory_mode": "legacy" if phase == "model-legacy7" else "bounded-experts-v1",
                                          "q36_memory_scope": "expert-working-storage", "q36_memory_total_process_bound": "0",
                                          "q36_memory_h2d_stage_bytes": "67108864",
                                          "q36_memory_cpu_stage_bytes": "0" if phase == "model-legacy7" else "18512896",
                                          "q36_memory_io_scratch_bytes": "0" if phase == "model-legacy7" else "1048576"}}
            self.put(base / "results" / (phase + "-protocol.json"), protocol)
            self.put(base / "results" / (phase + ".json"), {"passed": True, "sourceRoot": str(source), "releaseQualified": False,
                     "ownedJobDrained": True, "modelFilesPreserved": True, "modelFilesBefore": inputs,
                     "modelFilesAfter": inputs, "driver": row(phase + "-driver"), "protocol": protocol})
        self.put(base / "results/comparison.json", {"passed": True, "restartPassed": True, "releaseQualified": False,
                 "exeSHA256": package["strataSHA256"], "cases": [{"case": name, "sameLegacy": True} for name in names]})
        guard = {"passed": resource_pass, "name": "spill-cuda_spill_guard", "run": run(0 if resource_pass else 8)}
        self.put(base / "results/spill.json", {"passed": resource_pass, "releaseQualified": False, "cases": [guard]})
        violations = [] if resource_pass else ["VIOLATION fixture A", "VIOLATION fixture B"]
        self.put(base / "receipts/spill-cuda_spill_guard.txt", ("\n".join(violations) + "\n").encode())
        self.put(base / "results/qualification-summary.json", {**package, "releaseQualified": False, "phases": phases,
                 "resourceGuardPassed": resource_pass, "resourceViolations": violations, "nativeFunctionalChecksPassed": True})
        self.put(base / "receipts/audit-phase.json", {"passed": resource_pass, "frozenIdentity": freeze,
                 "run": run(0 if resource_pass else 1)})
        return base, native, source, adapters

    def test_current_resource_failure_is_not_promoted_or_count_assumed(self) -> None:
        result = quality.validate(*self.report_fixture())
        self.assertEqual(result["nativeResourceGuard"]["status"], "FAIL")
        self.assertEqual(len(result["nativeResourceGuard"]["violations"]), 2)
        self.assertFalse(result["releaseQualified"])
        self.assertFalse(result["newNativeQualified"])

    def test_current_resource_pass_still_does_not_qualify_release(self) -> None:
        result = quality.validate(*self.report_fixture(True))
        self.assertTrue(result["nativeResourceGuard"]["passed"])
        self.assertFalse(result["releaseQualified"])

    def test_unknown_report_field_fails(self) -> None:
        paths = self.report_fixture()
        path = paths[0] / "results/model-bounded.json"
        value = core.load(path)
        del value["modelFilesPreserved"]
        self.put(path, value)
        with self.assertRaises((core.Blocked, KeyError)):
            quality.validate(*paths)

    def test_resource_timeout_is_not_an_acceptable_guard_failure(self) -> None:
        paths = self.report_fixture()
        path = paths[0] / "results/spill.json"
        value = core.load(path)
        value["cases"][0]["run"]["status"] = "TIMEOUT"
        self.put(path, value)
        with self.assertRaises(core.Blocked):
            quality.validate(*paths)

    def test_required_cases_cannot_be_replaced_by_an_aggregate_pass(self) -> None:
        paths = self.report_fixture()
        path = paths[0] / "results/cpu.json"
        value = core.load(path)
        value["cases"] = [r for r in value["cases"] if r["name"] != "cpu-cpu_required"]
        self.put(path, value)
        with self.assertRaises(core.Blocked):
            quality.validate(*paths)

    def test_unknown_memory_receipt_cannot_use_truthiness_bypass(self) -> None:
        paths = self.report_fixture()
        path = paths[0] / "results/model-bounded.json"
        value = core.load(path)
        value["protocol"]["memoryReceipt"] = {"unknown": True}
        self.put(path, value)
        self.put(paths[0] / "results/model-bounded-protocol.json", value["protocol"])
        with self.assertRaises(core.Blocked):
            quality.validate(*paths)

    def test_native_payload_drift_and_missing_restart_are_rejected(self) -> None:
        paths = self.report_fixture()
        self.put(paths[1] / "strata.exe", b"changed")
        with self.assertRaises(core.Blocked):
            quality.validate(*paths)
        self.put(paths[1] / "strata.exe", b"never executable fixture")
        (paths[0] / "results/model-restart.json").unlink()
        with self.assertRaises(FileNotFoundError):
            quality.validate(*paths)


if __name__ == "__main__":
    unittest.main()
