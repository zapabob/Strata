"""Keep simulated PC setup tests independent of the machine running pytest.

The source setup tests supply fake NVIDIA/AMD/Intel cards and installation
roots. Their default target is an x86 PC, including on an Apple Silicon runner.
Mac handoff and Metal setup have their own explicit tests in test_setup_mac.py.
"""
import sys
from pathlib import Path

import pytest


class _TargetModule:
    def __init__(self, module, **overrides):
        self._module = module
        self.__dict__.update(overrides)

    def __getattr__(self, name):
        return getattr(self._module, name)


@pytest.fixture(autouse=True)
def simulated_pc_setup_target(request, monkeypatch):
    name = Path(str(request.path)).name
    pc_fixture = (name.startswith('test_setup_') and name != 'test_setup_mac.py') or name in {
        'test_calibrate.py', 'test_picture_defaults.py', 'test_user_args.py',
    }
    if sys.platform == 'darwin' and pc_fixture:
        import setup
        # Do not alter the interpreter's own platform or the subprocess module.
        # An individual test may still select a different target through setup.
        monkeypatch.setattr(setup, 'sys', _TargetModule(sys, platform='linux'))
        monkeypatch.setattr(setup, 'platform', _TargetModule(setup.platform, machine=lambda: 'x86_64'))
        monkeypatch.setattr(setup.sysinfo, 'machine', lambda: 'x86_64')
