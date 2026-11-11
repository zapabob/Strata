"""One authorized normal console interrupt to the identified Hermes model; never force-kill."""
import ctypes
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import time
import psutil

PID = 15428
EXE = Path('C:/Users/downl/.hermes/llama/prism-b10826-c9c34bc/bin/llama-server.exe')
OUT = Path('H:/Strata/releases/stable-058-20261111-codex/hermes-model-normal-stop.json')
record = {'pid': PID, 'exe': str(EXE), 'forceKillUsed': False, 'normalSignalSent': False, 'exited': False}
try:
    process = psutil.Process(PID)
    assert Path(process.exe()).resolve() == EXE.resolve(), 'PID executable identity changed'
    created = process.create_time()
    record['created'] = created
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.FreeConsole.argtypes = []
    kernel.FreeConsole.restype = W.BOOL
    kernel.AttachConsole.argtypes = [W.DWORD]
    kernel.AttachConsole.restype = W.BOOL
    kernel.GetConsoleProcessList.argtypes = [ctypes.POINTER(W.DWORD), W.DWORD]
    kernel.GetConsoleProcessList.restype = W.DWORD
    kernel.SetConsoleCtrlHandler.argtypes = [ctypes.c_void_p, W.BOOL]
    kernel.SetConsoleCtrlHandler.restype = W.BOOL
    kernel.GenerateConsoleCtrlEvent.argtypes = [W.DWORD, W.DWORD]
    kernel.GenerateConsoleCtrlEvent.restype = W.BOOL
    kernel.FreeConsole()
    if not kernel.AttachConsole(PID):
        raise OSError(ctypes.get_last_error(), 'Target has no attachable console; no signal sent')
    try:
        members = (W.DWORD * 128)()
        count = kernel.GetConsoleProcessList(members, len(members))
        assert 0 < count <= len(members), 'Console inventory failed'
        ids = set(members[:count])
        record['consoleMembers'] = sorted(ids)
        assert ids <= {PID, os.getpid()} and PID in ids, 'Shared console contains other processes; signal refused'
        assert process.create_time() == created and Path(process.exe()).resolve() == EXE.resolve()
        assert kernel.SetConsoleCtrlHandler(None, True)
        assert kernel.GenerateConsoleCtrlEvent(0, 0), 'Normal CTRL_C could not be sent'
        record['normalSignalSent'] = True
        try:
            record['exitCode'] = process.wait(timeout=45)
            record['exited'] = True
        except psutil.TimeoutExpired:
            record['error'] = 'Normal interrupt did not finish within 45 seconds; no force used'
    finally:
        kernel.FreeConsole()
except psutil.NoSuchProcess:
    record['absent'] = True
except Exception as error:
    record['error'] = str(error)
finally:
    with OUT.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
print(json.dumps(record))
raise SystemExit(0 if record['exited'] or record.get('absent') else 1)
