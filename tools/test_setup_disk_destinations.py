"""Disk preflight follows actual writes; no engines, downloads or GPU.

Ported from c02303b4, with main's allocated partial-pack credit retained.
Volume separation is emulated; hard links use the real test filesystem.
Run: python -m unittest tools.test_setup_disk_destinations
"""
from __future__ import annotations

import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import setup
from tools import test_setup_dsv41 as ds
from tools import test_setup_qwen36 as qw
from tools import test_setup_unsloth as flash


class DiskPools(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.c, self.h = self.root / "C", self.root / "H"
        self.c.mkdir()
        self.h.mkdir()

    def check(self, writes, free, separate=False):
        def same(a, b):
            return (self.c in Path(a).parents or Path(a) == self.c) == (self.c in Path(b).parents or Path(b) == self.c)
        out = io.StringIO()
        with mock.patch.object(setup, "same_drive", side_effect=same if separate else lambda a, b: True), \
             mock.patch.object(setup, "free_gb", side_effect=free), contextlib.redirect_stdout(out):
            try:
                setup.check_setup_space(writes)
                return 0, out.getvalue()
            except SystemExit as exc:
                return exc.code, out.getvalue()

    def test_folders_on_one_volume_share_one_budget(self):
        code, out = self.check([(self.c / "models", 6e9), (self.c / "packs", 6e9)], lambda p: 10)
        self.assertEqual(code, 1, out)
        self.assertIn("need ~12 GB", out)

    def test_separate_volumes_pay_only_their_own_writes(self):
        code, out = self.check([(self.c / "models", 6e9), (self.h / "packs", 8e9)], lambda p: 10, True)
        self.assertEqual(code, 0, out)
        code, out = self.check([(self.c / "models", 8e9), (self.h / "packs", 3e9)],
                               lambda p: 2 if p == self.h else 100, True)
        self.assertEqual(code, 1, out)
        self.assertIn(str(self.h / "packs"), out)

    def test_only_nonzero_destinations_probe_the_nearest_existing_ancestor(self):
        probes = []
        source = self.c / "absent-source"
        def free(path):
            probes.append(path)
            return 10
        code, out = self.check([(source, 0), (self.h / "new" / "nested", 2e9)], free, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(probes, [self.h])
        self.assertFalse(source.exists())
        self.assertFalse((self.h / "new").exists())

    def test_real_filesystem_identity_pools_different_directory_names(self):
        self.assertTrue(setup.same_drive(self.c, self.h))
        with mock.patch.object(setup, "free_gb", return_value=10), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit):
                setup.check_setup_space([(self.c, 6e9), (self.h, 6e9)])


class PartialFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / "model.gguf"
        self.part = self.dest.with_name(self.dest.name + ".part")

    def test_sequential_and_oversized_partials(self):
        self.part.write_bytes(b"abcdef")
        self.assertEqual(setup.setup_partial_bytes(self.dest, 10), 6)
        self.assertEqual(setup.setup_partial_bytes(self.dest, 5), 0)
        self.assertEqual(self.part.read_bytes(), b"abcdef")

    def test_sparse_chunk_maps_count_only_complete_unique_pieces(self):
        with self.part.open("wb") as f:
            f.seek(11)
            f.write(b"x")
        side = self.part.with_name(self.part.name + ".chunks")
        for ranges, expected in [([[2, 3]], 4), ([[0, 2], [1, 3]], 12), ([[0, 1], [2, 4]], 8)]:
            with self.subTest(ranges=ranges), mock.patch.object(setup, "DL_CHUNK", 4):
                side.write_text(json.dumps({"v": 1, "total": 12, "chunk": 4, "done": ranges}))
                self.assertEqual(setup.setup_partial_bytes(self.dest, 12), expected)
                self.assertEqual(setup.setup_partial_bytes(self.dest, 16), 0)
        side.write_text("not json")
        self.assertEqual(setup.setup_partial_bytes(self.dest, 12), 0)
        side.write_text('{"v":1,"total":12,"chunk":4,"done":[[0,Infinity]]}')
        with mock.patch.object(setup, "DL_CHUNK", 4):
            self.assertEqual(setup.setup_partial_bytes(self.dest, 12), 0)

    def test_truncated_parallel_partial_does_not_credit_absent_pieces(self):
        self.part.write_bytes(b"x" * 6)
        self.part.with_name(self.part.name + ".chunks").write_text(
            json.dumps({"v": 1, "total": 10, "chunk": 4, "done": [[0, 3]]}))
        with mock.patch.object(setup, "DL_CHUNK", 4):
            self.assertEqual(setup.setup_partial_bytes(self.dest, 10), 4)

    def test_shared_plan_uses_the_same_parallel_credit(self):
        models = self.dest.parent / "models"
        folder = models / "deepseek-v4.1-flash-shared"
        folder.mkdir(parents=True)
        name = setup.DSV41_ISTA_ENGRAM
        part = folder / (name + ".part")
        part.write_bytes(b"x" * 12)
        part.with_name(part.name + ".chunks").write_text(json.dumps({"v": 1, "total": 12, "chunk": 4, "done": [[2, 3]]}))
        with mock.patch.dict(setup.MULTI_FILE_FAMILIES["deepseek41"]["sha256"], {name: (12, "0" * 64)}), \
             mock.patch.object(setup, "DL_CHUNK", 4):
            self.assertEqual(dict(setup.dsv41_shared_missing(ds.ISTA, models, vision=False))[name], 8)


class QwenFiles(unittest.TestCase):
    def setUp(self):
        self.case = qw.InstallOwnPath()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.fam = setup.OWN_PATH_FAMILIES["qwen36"]
        self.name = self.fam["file"].format(q="UD-Q4_K_XL")
        self.folder = self.case.root / "models" / "qwen36-UD-Q4_K_XL"
        self.folder.mkdir(parents=True)

    def test_missing_or_partial_owned_model_fails_before_engine_or_disk(self):
        own = self.case.root / "own"
        own.mkdir()
        for partial in (False, True):
            if partial:
                (own / (self.name + ".part")).write_bytes(b"GGUF")
            with mock.patch.object(setup, "free_gb", return_value=0):
                code, out = self.case.install(model="UD-Q4_K_XL", vision="no", gguf_dir=str(own))
            self.assertEqual(code, 1, out)
            self.assertIn("is missing", out)
            self.assertNotIn("not enough free disk space", out)
            self.assertEqual(self.case.calls, [])

    def test_combined_model_and_picture_budget_precedes_both_downloads(self):
        with mock.patch.object(setup, "free_gb", return_value=self.fam["sha256"][self.name][0] / 1e9 + 0.1):
            code, out = self.case.install(model="UD-Q4_K_XL", vision="cpu")
        self.assertEqual(code, 1, out)
        self.assertIn("not enough free disk space", out)
        self.assertFalse([c for c in self.case.calls if c[0] == "get"])

    def test_text_only_engine_does_not_require_an_owned_picture(self):
        (self.folder / self.name).write_bytes(b"GGUF")
        eng = self.case.root / "text-only-engine"
        eng.mkdir()
        def engine(a, gpu, hip, amd, cuda_tk, vision):
            return self.case.root / "llama", eng, {"version": "0.1.44"}, [], gpu, vision
        with mock.patch.object(setup, "engine_step", side_effect=engine):
            code, out = self.case.install(model="UD-Q4_K_XL", vision="cpu", gguf_dir=str(self.folder))
        self.assertEqual(code, 0, out)
        self.assertNotIn("vision", self.case.cfg)
        self.assertFalse([c for c in self.case.calls if c[0] == "get"])

    def test_partial_resume_and_oversized_partial_budget(self):
        part = self.folder / (self.name + ".part")
        for size, expected in [(800, 0), (2000, 1)]:
            with self.subTest(size=size):
                self.case.calls.clear()
                part.write_bytes(b"x" * size)
                with mock.patch.dict(self.fam["sha256"], {self.name: (1000, "0" * 64)}), \
                     mock.patch.object(setup, "free_gb", return_value=250 / 1e9):
                    code, out = self.case.install(model="UD-Q4_K_XL", vision="no")
                self.assertEqual(code, expected, out)
                self.assertEqual(part.stat().st_size, size)
                self.assertEqual(bool([c for c in self.case.calls if c[0] == "get"]), expected == 0)

    def test_picture_links_are_exhausted_before_copy_space_is_required(self):
        (self.folder / self.name).write_bytes(b"GGUF")
        setup.mark(self.folder / self.name)
        for name in ("a-denied", "z-linkable"):
            sibling = self.folder.parent / name
            sibling.mkdir()
            (sibling / self.fam["mmproj"]).write_bytes(b"picture")
        real_link = setup.os.link
        tried = []
        def link(src, dst):
            tried.append(Path(src).parent.name)
            if Path(src).parent.name == "a-denied":
                raise OSError("hard link denied")
            return real_link(src, dst)
        with mock.patch.dict(self.fam["sha256"], {self.fam["mmproj"]: (7, "0" * 64)}), \
             mock.patch.object(setup, "free_gb", return_value=0), mock.patch.object(setup.os, "link", side_effect=link):
            code, out = self.case.install(model="UD-Q4_K_XL", vision="cpu")
        self.assertEqual(code, 0, out)
        self.assertEqual(tried, ["a-denied", "z-linkable"])
        dest = self.folder / self.fam["mmproj"]
        self.assertTrue(dest.samefile(self.folder.parent / "z-linkable" / self.fam["mmproj"]))
        dest.unlink()
        with mock.patch.dict(self.fam["sha256"], {self.fam["mmproj"]: (7, "0" * 64)}), \
             mock.patch.object(setup, "free_gb", return_value=0), mock.patch.object(setup.os, "link", side_effect=OSError("denied")):
            code, out = self.case.install(model="UD-Q4_K_XL", vision="cpu")
        self.assertEqual(code, 1, out)
        self.assertIn("not enough free disk space", out)
        self.assertFalse(dest.exists())
        self.assertFalse(dest.with_name(dest.name + ".copying").exists())


class DeepSeekFiles(unittest.TestCase):
    def setUp(self):
        self.case = ds.InstallOfficial()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.own = self.case.root / "own"
        self.own.mkdir()
        self.shared = self.case.root / "models" / "deepseek-v4.1-flash-shared"
        self.shared.mkdir(parents=True)
        for name in setup.MULTI_FILE_FAMILIES["deepseek41"]["models"][ds.ISTA]["shards"]:
            (self.own / name).write_bytes(b"GGUF")

    def test_shared_download_pays_data_not_owned_gguf_source(self):
        for own_free, data_free, expected in [(0.01, 900, 0), (900, 0.01, 1)]:
            with self.subTest(own_free=own_free):
                self.case.calls.clear()
                with mock.patch.object(setup, "free_gb", side_effect=lambda p: own_free if p == self.own else data_free):
                    code, out = self.case.install_ista(gguf_dir=str(self.own))
                self.assertEqual(code, expected, out)
                downloads = [c for c in self.case.calls if c[0] == "get"]
                self.assertEqual(bool(downloads), expected == 0)
                self.assertTrue(all(c[2].parent == self.shared for c in downloads))
                if expected:
                    self.assertIn(str(self.shared), out)

    def test_missing_owned_shard_precedes_disk_error(self):
        missing = next(self.own.glob("*.gguf"))
        missing.unlink()
        with mock.patch.object(setup, "free_gb", return_value=0):
            code, out = self.case.install_ista(gguf_dir=str(self.own))
        self.assertEqual(code, 1, out)
        self.assertIn(f"{missing} is missing", out)
        self.assertEqual(self.case.calls, [])


class FlashNextFiles(flash.Base):
    def existing_q2(self):
        own = self.t / "own"
        own.mkdir()
        fam = setup.FAMILIES["qwen"]
        for i in range(1, setup.model_shards(fam, "Q2_0") + 1):
            file = own / setup.model_file(fam, "Q2_0", i)
            file.write_bytes(b"GGUF")
            setup.mark(file)
        return own

    def q2(self, own, free_at):
        return self.main(["--family", "qwen", "--gguf-dir", str(own), "--vision", "no", "--context", "8192"],
                         family=False, m="Q2_0", ram=128, free_at=free_at)

    def test_missing_owned_shard_precedes_pack_space_error(self):
        own = self.existing_q2()
        missing = sorted(own.glob("*.gguf"))[-1]
        missing.unlink()
        code, out, _ = self.q2(own, lambda p: 0)
        self.assertEqual(code, 1, out)
        self.assertIn(f"{missing} is missing", out)
        self.assertEqual(self.downloads, [])
        self.assertEqual(self.runs, [])

    def test_new_pack_pays_data_not_owned_gguf_source(self):
        own = self.existing_q2()
        code, out, _ = self.q2(own, lambda p: 1 if p == own or own in Path(p).parents else 100)
        self.assertEqual(code, 0, out)
        self.assertTrue([r for r in self.runs if "strata_pack.py" in r[1]])
        self.runs.clear()
        code, out, _ = self.q2(own, lambda p: 100 if p == own or own in Path(p).parents else 1)
        self.assertEqual(code, 1, out)
        self.assertIn(str(self.t / "data" / "packs"), out)
        self.assertEqual(self.runs, [])

    def test_explicit_models_destination_pays_for_picture(self):
        own = self.t / "own"
        own.mkdir()
        for name in setup.UNSLOTH_SHARDS:
            (own / name).write_bytes(b"GGUF")
            setup.mark(own / name)
        (self.t / "models").mkdir()
        with mock.patch.object(setup, "same_drive", side_effect=lambda a, b: (a == self.t / "models") == (b == self.t / "models")):
            code, out, _ = self.main(["--gguf-dir", str(own), "--vision", "cpu", "--context", "8192"],
                                     free_at=lambda p: 0.01 if p == self.t / "models" else 1000)
        self.assertEqual(code, 1, out)
        self.assertIn(str(self.t / "models"), out)
        self.assertEqual(self.downloads, [])

    def test_download_and_pack_on_separate_volumes_each_fit(self):
        models = self.t / "models"
        models.mkdir()
        def same(a, b):
            return (models == a or models in Path(a).parents) == (models == b or models in Path(b).parents)
        with mock.patch.object(setup, "same_drive", side_effect=same):
            code, out, _ = self.main(["--family", "qwen", "--vision", "no", "--context", "8192"],
                                     family=False, m="Q2_0", ram=128,
                                     free_at=lambda p: 75 if p == models or models in Path(p).parents else 45)
        self.assertEqual(code, 0, out)

    def test_completed_pack_is_not_charged_but_missing_draft_is(self):
        own = self.existing_q2()
        pack = self.t / "data" / "packs" / "q2_0"
        (pack / "tokenizer").mkdir(parents=True)
        for file in (pack / "experts.bin", pack / "index.txt", pack / "tokenizer" / "vocab.json"):
            file.write_text("x")
        code, out, _ = self.q2(own, lambda p: 0)
        self.assertEqual(code, 0, out)
        self.assertFalse([r for r in self.runs if "strata_pack.py" in r[1]])
        (self.t / "data" / "mtp" / "rt" / "experts.bin").unlink()
        code, out, _ = self.q2(own, lambda p: 100 if p == own else 3)
        self.assertEqual(code, 1, out)
        self.assertIn(str(self.t / "data" / "mtp"), out)

    def test_main_keeps_allocated_partial_pack_credit(self):
        # Other setup fixtures restore sys.modules after mocking the GGUF reader.
        pack_space = importlib.import_module("strata_control.pack_space")
        with mock.patch.object(pack_space, "remaining_pack_gb", return_value=0.5) as remaining:
            code, out, _ = self.main(["--family", "qwen", "--low-ram", "mmap", "--vision", "no", "--context", "8192"],
                                     family=False, m="IQ3_S", ram=128, free=90)
        self.assertEqual(code, 0, out)
        remaining.assert_called_once()
        self.assertEqual(remaining.call_args.args[0], self.t / "data" / "packs" / "iq3_s")


if __name__ == "__main__":
    unittest.main()
