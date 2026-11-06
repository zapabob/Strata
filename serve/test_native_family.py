"""CPU-only Host -> Python family selection and actual pre-READY admission."""

import copy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest import mock

from serve import private_cache, server
from serve import test_q36_kv_contract as kv_tests

PRIVATE_ARGS = [
    "--max-context",
    "256",
    "--prompt-cache",
    "0",
    "--conversation-cache-mib",
    "0",
    "--private-conversation-cache",
]
KV_RECEIPT = (
    "INFO kv_layout_version=1 kv_scale_schema=none kv_cache_k=f16 kv_cache_v=f32 "
    "kv_context=256 kv_sessions=1 kv_heads=2 kv_head_dim=256 kv_attention_states=11 "
    "kv_allocation_bytes=8650752\n"
)


def ready_consumer(cfg: dict, receipt: str) -> tuple:
    """Real constructor admission, with controlled child IO/OS effects."""
    namespace = kv_tests.Q36KvContract._constructor_namespace()
    proc = mock.Mock(
        pid=1, stdin=io.StringIO(), stdout=io.StringIO(receipt + "READY 256 stop\n")
    )
    namespace["popen"] = mock.Mock(return_value=proc)
    with mock.patch.dict(os.environ, {}, clear=True):
        env = server.child_env(cfg)
    obj = namespace["ReadyPrefix"].__new__(namespace["ReadyPrefix"])
    return namespace, proc, env, obj


class NativeFamilyDecisionTests(unittest.TestCase):
    def test_explicit_non_q36_identity_wins_over_both_name_hints(self) -> None:
        for arch in ("qwen4exp", "deepseek41", "future-architecture", 7, {}):
            with self.subTest(arch=arch):
                cfg = {
                    "arch": arch,
                    "exe": "strata-q36.exe",
                    "model_name": "Qwen3.6-35B-A3B",
                    "args": PRIVATE_ARGS,
                    "backend": "cpu",
                }
                self.assertFalse(server.q36_config(cfg))
                self.assertEqual(private_cache.required_capability(cfg), 0)

    def test_absent_identity_retains_legacy_executable_and_model_hints(self) -> None:
        for identity in ({}, {"arch": None}, {"arch": ""}):
            for hint in ({"exe": "strata-q36.exe"}, {"model_name": "Qwen3.6-35B-A3B"}):
                with self.subTest(identity=identity, hint=hint):
                    cfg = {**identity, **hint, "args": PRIVATE_ARGS}
                    self.assertTrue(server.q36_config(cfg))
                    self.assertEqual(private_cache.required_capability(cfg), 2)
        cfg = {"args": PRIVATE_ARGS, "exe": "neutral.exe", "model_name": "Neutral"}
        self.assertFalse(server.q36_config(cfg))
        self.assertEqual(private_cache.required_capability(cfg), 0)

    def test_genuine_q36_requires_its_own_private_receipt_before_ready(self) -> None:
        for arch in ("qwen35moe", "qwen36"):
            for required in (1, 2):
                for reported in (None, 3 - required, required):
                    with self.subTest(arch=arch, required=required, reported=reported):
                        cfg = {
                            "arch": arch,
                            "exe": "neutral.exe",
                            "args": (
                                PRIVATE_ARGS if required == 2 else PRIVATE_ARGS[:-1]
                            ),
                            "env": {
                                "STRATA_REQUIRE_Q36_PRIVATE_CACHE": "0",
                                "STRATA_REQUIRE_Q36_KV": "0",
                            },
                        }
                        marker = (
                            f"INFO q36_private_cache={reported}\n"
                            if reported is not None
                            else ""
                        )
                        namespace, proc, env, obj = ready_consumer(cfg, marker)
                        self.assertEqual(
                            env["STRATA_REQUIRE_Q36_PRIVATE_CACHE"], str(required)
                        )
                        self.assertEqual(env["STRATA_REQUIRE_Q36_KV"], "1")
                        if reported == required:
                            namespace["ReadyPrefix"].__init__(
                                obj, cfg["exe"], list(cfg["args"]), env=env
                            )
                            self.assertEqual(obj.known_ctx, 256)
                            proc.kill.assert_not_called()
                        else:
                            with self.assertRaisesRegex(
                                server.EngineDied, "private conversation cache"
                            ):
                                namespace["ReadyPrefix"].__init__(
                                    obj, cfg["exe"], list(cfg["args"]), env=env
                                )
                            self.assertFalse(hasattr(obj, "known_ctx"))
                            proc.kill.assert_called_once()
                        namespace["q36_probe_kv_capabilities"].assert_not_called()


class HostPythonFamilyConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        node = os.environ.get("STRATA_TEST_NODE_EXE") or shutil.which("node")
        if not node:
            raise RuntimeError(
                "Node is required for the actual Host builder integration fixture"
            )
        root = Path(__file__).resolve().parents[1]
        bridge = root / "apps/host/tests/helpers/native-family-consumer-fixture.mjs"
        output = subprocess.run(
            [node, str(bridge)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
        cls.configs = json.loads(output.stdout)

    def test_host_q38_lookalike_path_needs_no_q36_markers(self) -> None:
        cfg = copy.deepcopy(self.configs["qwen"])
        self.assertEqual(cfg["arch"], "qwen4exp")
        self.assertIn("strata-q36", cfg["exe"])
        self.assertIn("--prompt-cache", cfg["args"])
        args = list(cfg["args"])
        with mock.patch.object(server, "q36_probe_kv_capabilities") as probe:
            args += server.native_cache_args(cfg, args, cfg["exe"])
            probe.assert_not_called()
        namespace, proc, env, obj = ready_consumer(cfg, "")
        namespace["ReadyPrefix"].__init__(obj, cfg["exe"], args, env=env)
        self.assertEqual(env["STRATA_REQUIRE_Q36_PRIVATE_CACHE"], "0")
        self.assertEqual(env["STRATA_REQUIRE_Q36_KV"], "0")
        self.assertEqual(obj.known_ctx, 256)
        namespace["q36_probe_kv_capabilities"].assert_not_called()
        proc.kill.assert_not_called()

    def test_catalog_q36_checks_binary_and_both_ready_receipts(self) -> None:
        cfg = copy.deepcopy(self.configs["qwen36"])
        self.assertEqual(cfg["arch"], "qwen35moe")
        self.assertEqual(cfg["model_name"], "Neutral model")
        self.assertNotIn("q36", cfg["exe"])
        for private, kv, accepted in (
            ("INFO q36_private_cache=2\n", KV_RECEIPT, True),
            ("", KV_RECEIPT, False),
            ("INFO q36_private_cache=2\n", "", False),
        ):
            with self.subTest(private=bool(private), kv=bool(kv)):
                args = list(cfg["args"])
                with mock.patch.object(
                    server, "q36_probe_kv_capabilities", return_value=kv_tests.VERIFIED
                ) as probe:
                    args += server.native_cache_args(cfg, args, cfg["exe"])
                    probe.assert_called_once_with(cfg["exe"])
                namespace, proc, env, obj = ready_consumer(cfg, private + kv)
                self.assertEqual(env["STRATA_REQUIRE_Q36_PRIVATE_CACHE"], "2")
                self.assertEqual(env["STRATA_REQUIRE_Q36_KV"], "1")
                if accepted:
                    namespace["ReadyPrefix"].__init__(obj, cfg["exe"], args, env=env)
                    self.assertEqual(obj.known_ctx, 256)
                    proc.kill.assert_not_called()
                else:
                    with self.assertRaisesRegex(
                        server.EngineDied, "private conversation cache|KV layout"
                    ):
                        namespace["ReadyPrefix"].__init__(
                            obj, cfg["exe"], args, env=env
                        )
                    self.assertFalse(hasattr(obj, "known_ctx"))
                    proc.kill.assert_called_once()
                namespace["q36_probe_kv_capabilities"].assert_called_once_with(
                    cfg["exe"]
                )

    def test_host_claim_cannot_replace_child_verification(self) -> None:
        cfg = copy.deepcopy(self.configs["qwen36"])
        for actual in (None, {**kv_tests.VERIFIED, "binarySha256": "cd" * 32}):
            with self.subTest(actual=actual):
                namespace, proc, env, obj = ready_consumer(
                    cfg, "INFO q36_private_cache=2\n" + KV_RECEIPT
                )
                namespace["q36_probe_kv_capabilities"].return_value = actual
                with self.assertRaisesRegex(ValueError, "Host-negotiated binary"):
                    namespace["ReadyPrefix"].__init__(
                        obj, cfg["exe"], list(cfg["args"]), env=env
                    )
                namespace["popen"].assert_not_called()


if __name__ == "__main__":
    unittest.main()
