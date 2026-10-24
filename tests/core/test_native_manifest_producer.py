"""Admission tests use tiny local files; no model or GPU is loaded."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import native_cache_capsule as M

class Admission(unittest.TestCase):
    def test_same_verified_receipt_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"receipt.json"
            p.write_bytes(b'{"a":1}')
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(M.trusted_json(p,digest),{"a":1})
            with self.assertRaises(ValueError): M.trusted_json(p,"0"*64)
            p.write_bytes(b'{"a":1,"a":2}')
            with self.assertRaises(ValueError): M.trusted_json(p,hashlib.sha256(p.read_bytes()).hexdigest())

    def test_actual_selected_sources_independent(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"source space.gguf";p.write_bytes(b"original")
            h=hashlib.sha256(p.read_bytes()).hexdigest()
            record={"path":str(p),"bytes":8,"sha256":h,"expected_sha256":h,
                    "matches":True,"metadata_unchanged":True,"mtime_ns":p.stat().st_mtime_ns}
            self.assertEqual(M.validate_source(record,p,h)[0],h)
            q=Path(root)/"wrong.gguf";q.write_bytes(b"original")
            with self.assertRaises(ValueError): M.validate_source(record,q,h)
            with self.assertRaises(ValueError): M.validate_source(record,p,"0"*64)
            p.write_bytes(b"changed!")
            with self.assertRaises(ValueError): M.validate_source(record,p,h)

    def test_oversize_is_rejected_before_content_read(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)/"metadata.json"
            with p.open("wb") as f: f.truncate(33*1024*1024)
            with self.assertRaises(ValueError): M.trusted_json(p,"0"*64)
            with self.assertRaises(ValueError): M.pack_metadata(Path(root),{"metadata.json":"0"*64})
            with self.assertRaises(ValueError): M.pack_metadata(Path(root),{})

    def test_unicode_path_and_canonical_position(self):
        self.assertEqual(M.text("パック / a\\b")[4:].decode("utf-8"),"パック / a\\b")
        with self.assertRaises(ValueError): M.text("bad\0path")
        self.assertNotEqual(M.position_digest(64,1e7),M.position_digest(128,1e7))
        self.assertNotEqual(M.position_digest(64,1e7),M.position_digest(64,1e6))

if __name__ == "__main__": unittest.main()
