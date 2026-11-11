"""Terminate only the explicitly approved retained handle for PID 15428."""
import ctypes
from ctypes import wintypes as W
import json
from pathlib import Path
import subprocess
import psutil

PID = 15428
CREATED = 1794369738.5290325
EXE = Path('C:/Users/downl/.hermes/llama/prism-b10826-c9c34bc/bin/llama-server.exe')
OUT = Path('H:/Strata/releases/stable-058-20261111-codex/hermes-model-approved-force-stop.json')
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]; k.OpenProcess.restype = W.HANDLE
k.GetProcessTimes.argtypes = [W.HANDLE, ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong)]; k.GetProcessTimes.restype = W.BOOL
k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)]; k.QueryFullProcessImageNameW.restype = W.BOOL
k.TerminateProcess.argtypes = [W.HANDLE, W.UINT]; k.TerminateProcess.restype = W.BOOL
k.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]; k.WaitForSingleObject.restype = W.DWORD
k.CloseHandle.argtypes = [W.HANDLE]; k.CloseHandle.restype = W.BOOL
record = {'pid': PID, 'explicitlyApprovedForce': True, 'terminated': False, 'treeKillUsed': False}
handle = k.OpenProcess(0x100000 | 0x1000 | 1, False, PID)
if not handle:
    record.update(openError=ctypes.get_last_error(), targetAlreadyAbsent=not psutil.pid_exists(PID))
    with OUT.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps(record))
    raise SystemExit(0 if record['targetAlreadyAbsent'] else 1)
assert handle, 'Approved process could not be opened; no other PID is allowed'
try:
    created, exited, kernel, user = [ctypes.c_ulonglong() for _ in range(4)]
    assert k.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(kernel), ctypes.byref(user))
    actual_created = created.value / 10_000_000 - 11_644_473_600
    image, length = ctypes.create_unicode_buffer(32768), W.DWORD(32768)
    assert k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(length))
    assert abs(actual_created - CREATED) < 0.00001 and Path(image.value).resolve() == EXE.resolve(), 'Process identity changed; refused'
    record.update(created=actual_created, exe=image.value)
    assert k.TerminateProcess(handle, 1), 'Explicit target termination failed'
    assert k.WaitForSingleObject(handle, 45_000) == 0, 'Target exit not confirmed'
    record['terminated'] = True
finally:
    k.CloseHandle(handle)
    with OUT.open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
print(json.dumps(record))
subprocess.run(['C:/Windows/System32/nvidia-smi.exe', '--query-gpu=memory.free,memory.used', '--format=csv,noheader,nounits'], check=True, timeout=15)
