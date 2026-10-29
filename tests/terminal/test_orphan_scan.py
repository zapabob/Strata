"""Startup must not inspect command lines of unrelated processes."""
import unittest
from unittest import mock

from strata_control import procs


class OrphanScan(unittest.TestCase):
    def test_foreign_executable_is_filtered_before_command_line_access(self):
        foreign = mock.Mock(pid=70001)
        foreign.exe.return_value = "/other/application"
        foreign.cmdline.side_effect = AssertionError("unrelated command-line read")
        fake = mock.Mock()
        fake.Error = RuntimeError
        fake.NoSuchProcess = ProcessLookupError
        fake.Process.return_value.parents.return_value = []
        fake.process_iter.return_value = [foreign]
        with mock.patch.object(procs, "psutil", fake), mock.patch.object(procs, "same_file", return_value=False):
            self.assertEqual(procs.orphans_of("/wanted/engine"), [])
        fake.process_iter.assert_called_once_with(["pid"])
        foreign.cmdline.assert_not_called()
        foreign.ppid.assert_not_called()
