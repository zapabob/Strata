"""Authorized temporary Irodori8089 pause, serial native pilot, exact-config restore.

No settings/task/lease edits. Environment backup is DPAPI CurrentUser ciphertext.
Existing process handles are bound to creation time and image before termination.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.request
import psutil
from tools.perf131k import native_pilot as native
from tools.perf131k.windows_job import api, require

SERVICE_ROOT = Path.home() / "Documents/New project/irodori-tts-server"
SERVICE_EXE = SERVICE_ROOT / ".venv/Scripts/python.exe"
ARGS = [str(SERVICE_EXE), "-I", "-m", "irodori_openai_tts", "--host", "127.0.0.1", "--port", "8089"]
BASE = Path("H:/Strata/evidence/p01-b3-20261026")


class Blob(C.Structure):
    _fields_ = [("length", W.DWORD), ("data", C.c_void_p)]


def crypt(data, decrypt=False):
    library = C.WinDLL("crypt32", use_last_error=True)
    function = library.CryptUnprotectData if decrypt else library.CryptProtectData
    function.argtypes = [C.POINTER(Blob), C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p, W.DWORD, C.POINTER(Blob)]
    function.restype = W.BOOL
    buffer = C.create_string_buffer(data)
    source, output = Blob(len(data), C.cast(buffer, C.c_void_p)), Blob()
    require(function(C.byref(source), None, None, None, None, 1, C.byref(output)), "DPAPI CurrentUser")
    try:
        return C.string_at(output.data, output.length)
    finally:
        kernel = C.WinDLL("kernel32", use_last_error=True)
        kernel.LocalFree.argtypes, kernel.LocalFree.restype = [C.c_void_p], C.c_void_p
        kernel.LocalFree(output.data)


def protect(data):
    return crypt(data)


def unprotect(data):
    return crypt(data, True)


def kernel_api():
    kernel = api()
    kernel.OpenProcess.argtypes, kernel.OpenProcess.restype = [W.DWORD, W.BOOL, W.DWORD], W.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = W.BOOL
    kernel.TerminateProcess.argtypes, kernel.TerminateProcess.restype = [W.HANDLE, W.UINT], W.BOOL
    return kernel


def close_handle(handle):
    require(kernel_api().CloseHandle(handle), "close service process handle")


def hold_process(pid, created, image):
    kernel = kernel_api()
    handle = kernel.OpenProcess(0x101001, False, pid)  # query limited + synchronize + terminate.
    require(bool(handle), "open explicitly identified service process")
    try:
        birth, exited, kern, user = (C.c_ulonglong() for _ in range(4))
        require(kernel.GetProcessTimes(handle, C.byref(birth), C.byref(exited), C.byref(kern), C.byref(user)), "service birth")
        name, size = C.create_unicode_buffer(32768), W.DWORD(32768)
        require(kernel.QueryFullProcessImageNameW(handle, 0, name, C.byref(size)), "service image")
        if (abs(birth.value / 10000000 - 11644473600 - created) > 0.001
                or os.path.normcase(name.value) != os.path.normcase(image)):
            raise ValueError("service PID/creation/image mismatch")
        return handle
    except Exception:
        kernel.CloseHandle(handle)
        raise


def stop_handle(handle):
    kernel = kernel_api()
    if kernel.WaitForSingleObject(handle, 0) == 0:
        return
    require(kernel.TerminateProcess(handle, 0), "stop explicitly authorized service handle")
    require(kernel.WaitForSingleObject(handle, 5000) == 0, "confirm stopped service handle")


def health():
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open("http://127.0.0.1:8089/health", timeout=5) as response:
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("health response exceeds bound")
    return json.loads(raw)


def listening():
    try:
        with socket.create_connection(("127.0.0.1", 8089), timeout=0.1):
            return True
    except OSError:
        return False


def verify_restore_owner(saved, environment, launcher_pid):
    owners = {connection.pid for connection in psutil.net_connections(kind="tcp")
              if connection.status == "LISTEN" and connection.laddr.port == 8089}
    if len(owners) != 1 or None in owners:
        raise ValueError("restore listen owner unconfirmed")
    runtime = psutil.Process(owners.pop())
    parent = psutil.Process(runtime.ppid())
    observed_env = {key.upper(): value for key, value in parent.environ().items()}
    expected_env = {key.upper(): value for key, value in environment.items()}
    if (parent.cmdline() != saved["argv"] or parent.cwd() != saved["cwd"]
            or runtime.cwd() != saved["cwd"]
            or (launcher_pid is not None and parent.pid != launcher_pid)
            or native.sha(parent.exe()) != saved["launcher_sha256"]
            or native.sha(runtime.exe()) != saved["runtime_exe_sha256"]
            or observed_env != expected_env):
        raise ValueError("restore argv/cwd/environment/image identity mismatch")
    return {"launcher_pid": parent.pid, "runtime_pid": runtime.pid,
            "launcher_created": parent.create_time(), "runtime_created": runtime.create_time()}


def restore(directory):
    saved = json.loads((directory / "service-snapshot.json").read_text())
    if saved["argv"] != ARGS or native.sha(SERVICE_EXE) != saved["launcher_sha256"]:
        raise ValueError("restore launcher identity mismatch")
    if native.sha(directory / "environment.dpapi") != saved["environment_ciphertext_sha256"]:
        raise ValueError("restore environment ciphertext changed")
    environment = json.loads(unprotect((directory / "environment.dpapi").read_bytes()))
    already = listening()
    if not already:
        with (directory / "restore-stdout.log").open("ab", buffering=0) as stdout, \
             (directory / "restore-stderr.log").open("ab", buffering=0) as stderr:
            child = subprocess.Popen(saved["argv"], cwd=saved["cwd"], env=environment,
                                     stdout=stdout, stderr=stderr, creationflags=0x08000000, close_fds=True)
        launcher_pid = child.pid
    else:
        launcher_pid = None  # An on-demand owner restarted it; do not replace that process.
    deadline = time.monotonic() + 180
    while True:
        try:
            after = health()
        except (OSError, ValueError, KeyError):
            after = None
        if after and after["status"] == "ok" and after["model"] == saved["health"]["model"]:
            # Identity failure is terminal; do not replace an independently restarted owner.
            identity = verify_restore_owner(saved, environment, launcher_pid)
            record = {"status": "HEALTH_AND_CONFIG_RESTORED", "launcher_pid": launcher_pid,
                      "verified_owner": identity, "already_restarted_by_owner": already, "health": after,
                      "prior_loaded": saved["health"]["runtime"]["loaded"],
                      "minimum_synthesis_verification": "NOT_RUN; separate approval required",
                      "warm_state_restored": after["runtime"]["loaded"] == saved["health"]["runtime"]["loaded"]}
            native.write(directory / f"restore-result-{time.time_ns()}.json", record)
            return record
        if time.monotonic() >= deadline:
            raise TimeoutError("TTS health/config restoration unconfirmed")
        time.sleep(1)


def execute(launcher_pid, runtime_pid):
    directory = BASE / f"service-attempt-{time.time_ns()}"
    directory.mkdir()
    shutil.copytree(BASE / "prepared", directory / "prepared")  # Only three small input JSON files, never model data.
    root, runtime = psutil.Process(launcher_pid), psutil.Process(runtime_pid)
    if (root.cmdline() != ARGS or runtime.ppid() != root.pid or root.cwd() != str(SERVICE_ROOT)
            or not any(c.status == "LISTEN" and c.laddr.port == 8089 for c in runtime.net_connections(kind="tcp"))):
        raise ValueError("Irodori owner/argv/cwd/port mismatch")
    if any(c.status == "ESTABLISHED" and c.laddr.port == 8089 for c in runtime.net_connections(kind="tcp")):
        raise ValueError("TTS has an established client; no stop")
    before = health()
    if before["status"] != "ok" or before["runtime"]["loading"]:
        raise ValueError("TTS not stable for temporary stop")
    environment = root.environ()  # Keep plaintext only in this process; never write or print it.
    with (directory / "environment.dpapi").open("xb") as out:
        out.write(protect(json.dumps(environment).encode()))
    snapshot = {"launcher_pid": root.pid, "runtime_pid": runtime.pid, "argv": root.cmdline(),
                "cwd": root.cwd(), "launcher_created": root.create_time(), "runtime_created": runtime.create_time(),
                "launcher_sha256": native.sha(SERVICE_EXE), "runtime_exe": runtime.exe(),
                "runtime_exe_sha256": native.sha(runtime.exe()), "health": before,
                "environment_ciphertext_sha256": native.sha(directory / "environment.dpapi"),
                "synthesis_busy": None, "restart_contract": "No matching scheduled task observed; on-demand restart aborts pilot",
                "restore_limit": "Same argv/env/config + health; lazy loaded warm state and synthesis remain unverified"}
    native.write(directory / "service-snapshot.json", snapshot)
    root_handle = hold_process(root.pid, root.create_time(), root.exe())
    runtime_handle = None
    stopped = False
    overall = {"status": "PENDING", "cells": [], "service_stopped": False}
    original_base, original_sample = native.BASE, native.system_resources
    try:
        runtime_handle = hold_process(runtime.pid, runtime.create_time(), runtime.exe())
        # Responsibility starts before any termination side effect, including an
        # uncertain wait result after TerminateProcess has already succeeded.
        stopped = True
        overall["stop_requested"] = True
        stop_handle(runtime_handle)
        overall["service_stopped"] = True
        stop_handle(root_handle)
        if listening():
            raise RuntimeError("service restarted before pilot")
        deadline = time.monotonic() + 900  # Whole native pilot window, not900seconds per each cell.
        def sample(path):
            if time.monotonic() >= deadline:
                raise TimeoutError("exclusive pilot window expired")
            if listening():
                raise RuntimeError("Irodori was restarted by another owner")
            return original_sample(path)
        native.BASE, native.system_resources = directory, sample
        binding_sha = native.sha(directory / "prepared/binding.json")
        for count, trace in ((4096, "OFF"), (4096, "ON"), (32768, "OFF"), (32768, "ON")):
            code = native.run_cell(count, trace, binding_sha=binding_sha)
            cell = json.loads((directory / f"native-{count}-{trace.lower()}/result.json").read_text())
            overall["cells"].append({"tokens": count, "trace": trace, "code": code, "status": cell["status"]})
            if code and not cell["measurement_valid"]:
                break
        if len(overall["cells"]) == 4 and all(cell["code"] == 0 for cell in overall["cells"]):
            overall["status"] = "PILOT_MEASURED"
        elif overall["cells"] and overall["cells"][-1]["status"] == "PREFLIGHT_BLOCKED":
            overall["status"] = "PILOT_BLOCKED"
        else:
            overall["status"] = "PILOT_INCOMPLETE"
    except Exception as error:
        overall.update(status="CONTROL_FAILED", error_type=type(error).__name__)
    finally:
        native.BASE, native.system_resources = original_base, original_sample
        cleanup_errors = []
        for handle in (runtime_handle, root_handle):
            if handle:
                try:
                    close_handle(handle)
                except Exception as error:
                    cleanup_errors.append(type(error).__name__)
        if cleanup_errors:
            overall.update(status="HANDLE_CLEANUP_UNCONFIRMED", cleanup_error_types=cleanup_errors)
        if stopped:
            try:
                overall["restoration"] = restore(directory)
            except Exception as error:
                overall.update(status="RESTORE_UNCONFIRMED", restore_error_type=type(error).__name__)
        native.write(directory / "overall.json", overall)
    print(json.dumps({"attempt": str(directory), "status": overall["status"], "cells": overall["cells"],
                      "restoration": overall.get("restoration", {}).get("status")}))
    return 0 if overall["status"] == "PILOT_MEASURED" else 78


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-services-authorized", action="store_true")
    parser.add_argument("--launcher-pid", type=int)
    parser.add_argument("--runtime-pid", type=int)
    parser.add_argument("--restore-only", type=Path)
    args = parser.parse_args()
    if args.restore_only:
        path = args.restore_only.resolve()
        if not path.is_relative_to(BASE) or path == BASE:
            parser.error("owned H service attempt required")
        restore(path)
        return 0
    if not args.execute_services_authorized or not args.launcher_pid or not args.runtime_pid:
        parser.error("explicit authorized service identities required")
    return execute(args.launcher_pid, args.runtime_pid)


if __name__ == "__main__":
    raise SystemExit(main())
