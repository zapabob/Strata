"""Offline download boundary regression tests; never download model weights."""
from __future__ import annotations

import hashlib
from contextlib import redirect_stdout
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from spin8_model_fetch import READ_BYTES, append_range, exclusive_download, fetch, frozen_files, main


class ModelFetchTest(unittest.TestCase):
    def test_selected_shard_does_not_rehash_or_fetch_the_other(self) -> None:
        first = dict(name="model-Q2_0-00001-of-00002.gguf", size=10)
        second = dict(name="model-Q2_0-00002-of-00002.gguf", size=20)
        with tempfile.TemporaryDirectory() as temporary:
            with patch("sys.argv", ["fetch", "--directory", temporary, "--shard", "2"]), \
                 patch("spin8_model_fetch.frozen_files", return_value=[second, first]), \
                 patch("spin8_model_fetch.fetch", return_value=second) as transfer:
                self.assertEqual(main(), 0)
            transfer.assert_called_once_with(second, Path(temporary))

    def test_selected_plan_has_no_directory_or_transfer_side_effect(self) -> None:
        first = dict(name="model-Q2_0-00001-of-00002.gguf", size=10)
        second = dict(name="model-Q2_0-00002-of-00002.gguf", size=20)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "not-created"
            output = io.StringIO()
            with patch("sys.argv", ["fetch", "--directory", str(directory), "--plan", "--shard", "1"]), \
                 patch("spin8_model_fetch.frozen_files", return_value=[second, first]), \
                 patch("spin8_model_fetch.fetch") as transfer, redirect_stdout(output):
                self.assertEqual(main(), 0)
            self.assertFalse(directory.exists())
            transfer.assert_not_called()
            self.assertIn(first["name"], output.getvalue())
            self.assertNotIn(second["name"], output.getvalue())

    def test_default_still_verifies_both_shards(self) -> None:
        files = [dict(name="first.gguf", size=10), dict(name="second.gguf", size=20)]
        with tempfile.TemporaryDirectory() as temporary:
            with patch("sys.argv", ["fetch", "--directory", temporary]), \
                 patch("spin8_model_fetch.frozen_files", return_value=files), \
                 patch("spin8_model_fetch.fetch", side_effect=files) as transfer:
                self.assertEqual(main(), 0)
            self.assertEqual([call.args[0] for call in transfer.call_args_list], files)

    def test_selected_shard_rejects_missing_or_ambiguous_pin(self) -> None:
        selected = dict(name="model-Q2_0-00002-of-00002.gguf", size=20)
        for files in ([], [selected, dict(selected)]):
            with self.subTest(pin_count=len(files)), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary) / "not-created"
                with patch("sys.argv", ["fetch", "--directory", str(directory), "--shard", "2"]), \
                     patch("spin8_model_fetch.frozen_files", return_value=files), \
                     patch("spin8_model_fetch.fetch") as transfer:
                    with self.assertRaisesRegex(ValueError, "selected_shard_pin_missing_or_ambiguous"):
                        main()
                transfer.assert_not_called()
                self.assertFalse(directory.exists())

    def test_frozen_source_contract(self) -> None:
        files = frozen_files()
        self.assertEqual(len(files), 2)
        self.assertEqual(sum(item["size"] for item in files), 66423878624)
        self.assertTrue(all("/ed59f92082b1e93c0e96d60a8b11aab089b52f09/" in item["url"] for item in files))

    def test_existing_bad_model_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "model.gguf"
            path.write_bytes(b"existing")
            item = dict(name=path.name, size=3, sha256=hashlib.sha256(b"new").hexdigest(), url="unused")
            with patch("urllib.request.urlopen") as network:
                with self.assertRaisesRegex(ValueError, "existing_model_digest_mismatch"):
                    fetch(item, root)
                network.assert_not_called()
            self.assertEqual(path.read_bytes(), b"existing")

    def test_complete_partial_verifies_before_rename(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = b"frozen model fixture"
            (root / "model.gguf.partial").write_bytes(data)
            item = dict(name="model.gguf", size=len(data), sha256=hashlib.sha256(data).hexdigest(), url="unused")
            with patch("urllib.request.urlopen") as network:
                self.assertTrue(fetch(item, root)["verified"])
                network.assert_not_called()
            self.assertEqual((root / "model.gguf").read_bytes(), data)

    def test_wrong_range_preserves_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            partial = root / "model.gguf.partial"
            partial.write_bytes(b"old")
            response = io.BytesIO(b"changed")
            response.status = 200
            response.headers = {}
            item = dict(name="model.gguf", size=10, sha256="unused", url="https://example.invalid/model")
            with patch("urllib.request.urlopen", return_value=response):
                with self.assertRaisesRegex(ValueError, "range_resume_rejected"):
                    fetch(item, root)
            self.assertEqual(partial.read_bytes(), b"old")

    def test_valid_range_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = b"GGUF fixture"
            response = io.BytesIO(data)
            response.status = 206
            response.headers = {"Content-Range": f"bytes 0-{len(data)-1}/{len(data)}"}
            item = dict(name="model.gguf", size=len(data), sha256=hashlib.sha256(data).hexdigest(), url="https://example.invalid/model")
            with patch("urllib.request.urlopen", return_value=response):
                self.assertTrue(fetch(item, root)["verified"])
            self.assertEqual((root / "model.gguf").read_bytes(), data)

    def test_destination_appearing_during_transfer_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = root / "model.gguf"
            data = b"GGUF fixture"
            item = dict(name=destination.name, size=len(data), sha256=hashlib.sha256(data).hexdigest(), url="https://example.invalid/model")

            def competing_writer(request, timeout):
                destination.write_bytes(b"separately created model")
                response = io.BytesIO(data)
                response.status = 206
                response.headers = {"Content-Range": f"bytes 0-{len(data)-1}/{len(data)}"}
                return response

            with patch("urllib.request.urlopen", side_effect=competing_writer):
                with self.assertRaises(FileExistsError):
                    fetch(item, root)
            self.assertEqual(destination.read_bytes(), b"separately created model")
            self.assertEqual((root / "model.gguf.partial").read_bytes(), data)

    def test_concurrent_downloader_cannot_modify_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            partial = root / "model.gguf.partial"
            partial.write_bytes(b"prefix")
            item = dict(name="model.gguf", size=20, sha256="unused", url="unused")
            with exclusive_download(root / "model.gguf.lock"):
                with patch("urllib.request.urlopen") as network:
                    with self.assertRaises(OSError):
                        fetch(item, root)
                    network.assert_not_called()
            self.assertEqual(partial.read_bytes(), b"prefix")

    def test_streamed_range_uses_bounded_reads_and_preserves_prefix(self) -> None:
        class TrackedResponse(io.BytesIO):
            def readinto(self, buffer):
                self.assert_count(len(buffer))
                return super().readinto(buffer)

        with tempfile.TemporaryDirectory() as temporary:
            partial = Path(temporary) / "model.gguf.partial"
            partial.write_bytes(b"prefix")
            data = b"x" * (READ_BYTES * 2 + 3)
            response = TrackedResponse(data)
            response.assert_count = lambda count: self.assertTrue(0 < count <= READ_BYTES)
            response.status = 206
            size = 6 + len(data)
            response.headers = {"Content-Range": f"bytes 6-{size-1}/{size}"}
            item = dict(size=size, url="https://example.invalid/model")
            with patch("urllib.request.urlopen", return_value=response):
                append_range(item, partial, 6, size - 1)
            self.assertEqual(partial.read_bytes(), b"prefix" + data)

    def test_short_or_extra_body_never_extends_prefix(self) -> None:
        for body in (b"short", b"too long"):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as temporary:
                partial = Path(temporary) / "model.gguf.partial"
                partial.write_bytes(b"prefix")
                response = io.BytesIO(body)
                response.status = 206
                response.headers = {"Content-Range": "bytes 6-11/12"}
                with patch("urllib.request.urlopen", return_value=response):
                    with self.assertRaisesRegex(ValueError, "range_length_mismatch"):
                        append_range(dict(size=12, url="https://example.invalid/model"), partial, 6, 11)
                self.assertEqual(partial.read_bytes(), b"prefix")

    def test_empty_partial_can_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            partial = Path(temporary) / "model.gguf.partial"
            partial.touch()
            response = io.BytesIO(b"GGUF")
            response.status = 206
            response.headers = {"Content-Range": "bytes 0-3/4"}
            with patch("urllib.request.urlopen", return_value=response):
                append_range(dict(size=4, url="https://example.invalid/model"), partial, 0, 3)
            self.assertEqual(partial.read_bytes(), b"GGUF")


if __name__ == "__main__":
    unittest.main()
