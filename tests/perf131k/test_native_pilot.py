"""CPU-only preparation/consumer tests. Never start a model or GPU process."""
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import uuid
import shutil
import os
import importlib.util
import sys
from tools.perf131k import native_pilot as native
if os.environ.get("P01_NATIVE_UNDER_TEST"):
    spec = importlib.util.spec_from_file_location("native_under_test", os.environ["P01_NATIVE_UNDER_TEST"])
    native = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = native
    spec.loader.exec_module(native)


class NativePilotTests(TestCase):
    def fake_cell(self, *, raw=None, stale_tokenizer=False, trace="OFF"):
        base = Path("H:/Strata/worktrees/p01-a-20261025/_scratch/perf131k/b2-fixtures") / uuid.uuid4().hex
        base.mkdir(parents=True)
        shutil.copytree(native.BASE / "prepared", base / "prepared")
        path = base / "prepared/binding.json"
        if stale_tokenizer:
            binding = json.loads(path.read_text())
            binding["tokenizer"]["vocab.json"] = "0" * 64
            path.write_text(json.dumps(binding))
        def fake_runtime(command, root, env, output, budget, sample, *, stdin_path):
            output.write_text(raw or "READY 131072 stop\nT 1\nDONE 1 4096 100 200 stop 0 0 0\n"
                              "T 1\nDONE 1 4096 10 200 stop 0 0 4096\n")
            return {"status": "FINISHED", "exit_code": 0, "termination_confirmed": True,
                    "job_active_after": 0, "owned_root_pid": 123}
        class Tok:
            def decode(self, ids):
                return native.SENTINEL
        resources = {"available_ram": 20 * 1024**3, "commit_headroom": 30 * 1024**3, "H_free": 30 * 1024**3}
        with patch.object(native, "BASE", base), patch.object(native.windows_job, "run_owned", side_effect=fake_runtime) as spawn, \
             patch.object(native, "system_resources", return_value=resources), patch.object(native, "tokenizer", return_value=Tok()):
            code = native.run_cell(4096, trace, binding_sha=native.sha(path))
        result = json.loads((base / f"native-4096-{trace.lower()}/result.json").read_text())
        return code, result, spawn.call_count

    def test_malformed_DONE_retains_known_cleanup(self):
        code, result, _ = self.fake_cell(raw="READY 131072 stop\nDONE 1\n")
        self.assertNotEqual(code, 0)
        self.assertEqual(result["status"], "ANALYSIS_FAILED")
        self.assertFalse(result["measurement_valid"])
        self.assertTrue(result["termination_confirmed"])
        self.assertEqual(result["job_active_after"], 0)
        self.assertEqual(result["owned_root_pid"], 123)

    def test_stale_tokenizer_prevents_child_creation(self):
        code, result, calls = self.fake_cell(stale_tokenizer=True)
        self.assertNotEqual(code, 0)
        self.assertEqual(calls, 0)
        self.assertEqual(result["status"], "INPUT_BINDING_FAILED")

    def test_missing_ON_trace_invalidates_comparison(self):
        code, result, _ = self.fake_cell(trace="ON")
        self.assertNotEqual(code, 0)
        self.assertFalse(result["comparison_valid"])
        self.assertEqual(result["status"], "TRACE_INVALID")
        self.assertIsNone(result["requests"][0]["engine_reported_tokens_per_second"])

    def test_incomplete_trace_does_not_invalidate_native_request_totals(self):
        from tools.perf131k import capture_trace
        with patch.object(capture_trace, "analyze", return_value={"trace_status": "INCOMPLETE",
                          "counts": {"dropped": 1}, "record_count": 4096, "source": "host_only"}):
            code, result, _ = self.fake_cell(trace="ON")
        self.assertNotEqual(code, 0)
        self.assertTrue(result["measurement_valid"])
        self.assertFalse(result["comparison_valid"])
        self.assertEqual(len(result["requests"]), 2)

    def test_post_run_identity_failure_keeps_cleanup_and_rejects_measurement(self):
        original = native.verify_inputs
        calls = 0
        def verify(binding):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected post-run identity read failure")
            return original(binding)
        with patch.object(native, "verify_inputs", side_effect=verify):
            code, result, _ = self.fake_cell()
        self.assertNotEqual(code, 0)
        self.assertEqual(result["status"], "INPUT_BINDING_FAILED")
        self.assertFalse(result["measurement_valid"])
        self.assertEqual(result["job_active_after"], 0)
        self.assertTrue(result["termination_confirmed"])

    def test_real_tokenizer_fixtures_and_fake_runtime_connection(self):
        base = Path("H:/Strata/worktrees/p01-a-20261025/_scratch/perf131k/b2-fixtures") / uuid.uuid4().hex
        base.mkdir(parents=True)
        (base / "CPU_UNIT_FIXTURE").write_text("All runtime counters in this directory are scripted CPU fixtures.")
        with patch.object(native, "BASE", base):
            native.prepare()  # Reads tokenizer and verification exe only; no model tensor reads.
            binding = json.loads((base / "prepared/binding.json").read_text())
            for count in (4096, 32768):
                ids = json.loads((base / f"prepared/tokens-{count}.json").read_text())
                self.assertEqual(len(ids), count)
                self.assertEqual(binding["capacity"], 131072)
            def fake_runtime(command, root, env, raw, budget, sample, *, stdin_path):
                self.assertEqual(command[:2], [str(native.BINARY), "generate"])
                self.assertIn("--serve", command)
                self.assertIn("131072", command)
                self.assertEqual(stdin_path.read_text().count("GEN 256 "), 2)
                raw.write_text("READY 131072 stop\nT 1\nDONE 1 4096 100 200 stop 0 0 0\n"
                               "T 1\nDONE 1 4096 10 200 stop 0 0 4096\n")
                return {"status": "FINISHED", "exit_code": 0, "termination_confirmed": True,
                        "job_active_after": 0}
            resources = {"available_ram": 20 * 1024**3, "commit_headroom": 30 * 1024**3, "H_free": 30 * 1024**3}
            class Tok:
                def decode(self, ids):
                    return native.SENTINEL
            with patch.object(native.windows_job, "run_owned", side_effect=fake_runtime), \
                 patch.object(native, "system_resources", return_value=resources), \
                 patch.object(native, "tokenizer", return_value=Tok()):
                self.assertEqual(native.run_cell(4096, "OFF", binding_sha=native.sha(base / "prepared/binding.json")), 0)
            result = json.loads((base / "native-4096-off/result.json").read_text())
            self.assertTrue(result["measurement_valid"])
            self.assertTrue(result["requests"][0]["recall_probe_pass"])
            self.assertEqual(result["P17_PPL_full_quality"], "NOT_RUN")
