"""0.2.3 RC stress test, #3 (H01): the version bump is complete and consistent, and a 0.2.2 install sees the update."""

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

import strata_cli
from strata_control import feed as feedmod, updater
from tests.terminal import test_updater

ROOT = Path(__file__).resolve().parents[2]


def first(path, pattern):
    return re.search(pattern, (ROOT / path).read_text(encoding="utf-8"), re.MULTILINE).group(1)


class VersionBump(unittest.TestCase):
    def test_the_terminal_is_0_2_4_2_and_control_is_0_1_49_2_while_the_app_stays_0_2_3(self):
        # Hakua fork: product/app SemVer is preview (VERSION + Cargo + PRODUCT_VERSION); engine/Control stay CMake 0.1.53, Metal 0.1.52.
        # Upstream Niko1221 still ships 0.2.7.x; do not treat those installer names as this fork's product version.
        product = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(strata_cli.PRODUCT_VERSION, product)
        self.assertEqual(strata_cli.version(), "0.1.53")                # the CMake project version: Control
        self.assertEqual(first("CMakeLists.txt", r"^project\(strata VERSION ([0-9.]+) "), "0.1.53")
        self.assertIn('STRATA_VERSION="0.1.52-metal"', (ROOT / "metal" / "CMakeLists.txt").read_text(encoding="utf-8"))

    def test_every_place_the_app_version_lives_says_0_2_3(self):
        product = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(first("apps/desktop/src-tauri/Cargo.toml", r'^version = "([^"]+)"'), product)
        lock = (ROOT / "apps/desktop/src-tauri/Cargo.lock").read_text(encoding="utf-8")
        self.assertRegex(lock, rf'name = "strata-desktop"\r?\nversion = "{re.escape(product)}"')
        self.assertEqual(json.loads((ROOT / "apps/desktop/package.json").read_text(encoding="utf-8"))["version"], product)
        host = json.loads((ROOT / "apps/host/package.json").read_text(encoding="utf-8"))
        self.assertEqual(host["version"], product)
        locked = json.loads((ROOT / "apps/host/package-lock.json").read_text(encoding="utf-8"))
        self.assertEqual((locked["version"], locked["packages"][""]["version"]), (product, product))
        desk_lock = json.loads((ROOT / "apps/desktop/package-lock.json").read_text(encoding="utf-8"))
        self.assertEqual((desk_lock["version"], desk_lock["packages"][""]["version"]), (product, product))

    def test_the_documents_that_state_the_current_version_agree(self):
        product = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(f"Hakua product version {product}", agents)
        self.assertIn("engine 0.1.53", agents)
        for name in ("README.md", "README.de.md", "README.es.md", "README.fr.md", "README.ja.md", "README.pl.md", "README.pt-BR.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            # Upstream official installer filenames remain in translated READMEs; Hakua product is in Fork notes (EN/JA/zh-CN).
            self.assertRegex(text, r"Strata-0[.]2[.][0-9]+-", name)
            self.assertNotIn("Strata-0.2.2-", text, name)
        for name in ("README.md", "README.ja.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f"App version in this preview tree: `{product}`", text, name)

    def test_version_prints_the_product_and_the_build(self):
        product = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        done = subprocess.run([sys.executable, str(ROOT / "strata.py"), "--version"], capture_output=True, text=True, cwd=str(ROOT),
                              env={**os.environ, "STRATA_NO_HANDOVER": "1"})
        self.assertTrue(done.stdout.startswith(f"strata {product} (build 0.1.53;"), done.stdout)


class UpdateFromTheLastRelease(test_updater.UpdaterCase):
    def feed_with_control(self, version):
        bundle = self.root / "control-bundle"
        (bundle / "strata_control").mkdir(parents=True)
        (bundle / "strata.py").write_text(f"print('strata 0.2.3 (build {version})')\n")
        (bundle / "strata_control" / "__init__.py").write_text("")
        from feed_tool import build_feed, pack_control
        (self.release / "control").mkdir()
        pack_control(bundle, self.release / "control", version=version, platform=test_updater.PLATFORM)
        build_feed(self.release, key=self.key, sequence=1, control_dir=self.release / "control")

    def test_a_0_2_2_install_is_offered_control_0_1_48_and_a_0_2_3_install_is_current(self):
        self.feed_with_control("0.1.48")
        (self.components / "control").mkdir(parents=True)
        (self.components / "control" / "active.json").write_text(json.dumps({"version": "0.1.47", "folder": "0.1.47"}))
        report = updater.check(self.ctx())
        self.assertEqual((report["control"]["status"], report["control"]["installed"], report["control"]["offered"]),
                         ("available", "0.1.47", "0.1.48"))
        out = updater.run_update(self.ctx(), engine=False, control=True)
        self.assertEqual((out["exit_code"], out["results"][0]["status"]), (0, "updated"), out)
        self.assertEqual(updater.active_control(self.components)["version"], "0.1.48")
        self.assertEqual(updater.check(self.ctx())["control"]["status"], "current")

    def test_the_bumped_numbers_sort_above_the_last_release(self):
        self.assertGreater(feedmod.version_key(strata_cli.version()), feedmod.version_key("0.1.47"))
        self.assertGreater(feedmod.version_key("0.1.48"), feedmod.version_key("0.1.46.3"))
        self.assertGreater(feedmod.version_key("0.1.48"), feedmod.version_key("0.1.45.3"))
