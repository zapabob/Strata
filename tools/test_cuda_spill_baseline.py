"""A measured budget cannot silently follow source, flags or kernel growth."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from tools import cuda_spill_baseline as b, check_cuda_spills as check

class CudaSpillBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/"CMakeLists.txt").write_text("project(fixture)\n")
        (self.root/"src").mkdir()
        (self.root/"src"/"kernel.cu").write_bytes(b"kernel\r\n")
        self.key=self.root/"key.txt";self.key.write_text("a"*64)
        with mock.patch.object(b,"dependency_commit",return_value="b"*40):
            self.expected=b.bindings(self.root,self.key,self.root)
        self.file=self.root/"baseline.json"
        b.save(self.file,self.expected,{"lib|obj|sm_120|fn":(8,0)},[])

    def test_source_and_configuration_changes_are_rejected(self):
        self.assertEqual(b.load(self.file,self.expected)["lib|obj|sm_120|fn"],(8,0))
        for name in ["sourceDigest","compilerKey","ggmlCommit"]:
            changed={**self.expected,name:"changed"}
            with self.assertRaisesRegex(ValueError,"identity changed"):b.load(self.file,changed)
        before=b.source_digest(self.root)
        (self.root/"src"/"kernel.cu").write_bytes(b"kernel\n")
        self.assertEqual(b.source_digest(self.root),before,"line-ending conversion is not a kernel edit")
        (self.root/"src"/"kernel.cu").write_text("changed kernel\n")
        self.assertNotEqual(b.source_digest(self.root),before)

    def test_each_entry_is_stricter_than_family_allowance(self):
        func="mangled";names={func:"strata::kernels::{anonymous}::native_gu_kernel()"}
        key=b.entry_key("lib","obj","sm_120",func)
        rows=[("obj","sm_120",func,{"STACK":8,"LOCAL":0})]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check.check("lib",rows,names,{key:(8,0)}),0)
            rows[0][3]["STACK"]=9
            self.assertEqual(check.check("lib",rows,names,{key:(8,0)}),1)
            rows[0][3]["STACK"]=1
            self.assertEqual(check.check("lib",rows,names,{}),1,"an unmeasured entry has no nonzero allowance")
            rows[0][3]["STACK"]=0
            self.assertEqual(check.check("lib",rows,names,{}),0)

    def test_capture_refuses_to_overwrite_a_reviewed_file(self):
        with self.assertRaises(FileExistsError):b.save(self.file,self.expected,{},[])
        record=json.loads(self.file.read_text())
        record["entries"]["bad"]=[True,0]
        self.file.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,"resource amount"):b.load(self.file,self.expected)

if __name__=="__main__":unittest.main()
