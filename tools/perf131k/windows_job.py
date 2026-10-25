"""Windows-only pilot CPU containment, adapted from tests/perf131k/owned_job.py.

Uses the same atomic JOB_LIST + suspended-create pattern as tools/verify_bounded_process.cs.
Only handles created in this invocation can be terminated. No breakaway permission.
"""

import ctypes as C
from ctypes import wintypes as W
import msvcrt
import os
from pathlib import Path
import subprocess
import time


class BasicLimits(C.Structure):
    _fields_ = [
        ("process_time", C.c_longlong),
        ("job_time", C.c_longlong),
        ("flags", W.DWORD),
        ("minimum", C.c_size_t),
        ("maximum", C.c_size_t),
        ("active", W.DWORD),
        ("affinity", C.c_size_t),
        ("priority", W.DWORD),
        ("scheduling", W.DWORD),
    ]


class Limits(C.Structure):
    _fields_ = [
        ("basic", BasicLimits),
        ("io", C.c_ulonglong * 6),
        ("process_memory", C.c_size_t),
        ("job_memory", C.c_size_t),
        ("peak_process", C.c_size_t),
        ("peak_job", C.c_size_t),
    ]


class Accounting(C.Structure):
    _fields_ = [
        ("times", C.c_longlong * 4),
        ("faults", W.DWORD),
        ("total", W.DWORD),
        ("active", W.DWORD),
        ("terminated", W.DWORD),
    ]


class Startup(C.Structure):
    _fields_ = [
        ("size", W.DWORD),
        ("reserved", W.LPWSTR),
        ("desktop", W.LPWSTR),
        ("title", W.LPWSTR),
        ("x", W.DWORD),
        ("y", W.DWORD),
        ("width", W.DWORD),
        ("height", W.DWORD),
        ("chars_x", W.DWORD),
        ("chars_y", W.DWORD),
        ("fill", W.DWORD),
        ("flags", W.DWORD),
        ("show", W.WORD),
        ("reserved_size", W.WORD),
        ("reserved_bytes", C.c_void_p),
        ("stdin", W.HANDLE),
        ("stdout", W.HANDLE),
        ("stderr", W.HANDLE),
    ]


class StartupEx(C.Structure):
    _fields_ = [("startup", Startup), ("attributes", C.c_void_p)]


class Process(C.Structure):
    _fields_ = [("process", W.HANDLE), ("thread", W.HANDLE), ("pid", W.DWORD), ("tid", W.DWORD)]


def api() -> C.WinDLL:
    """Declare pointer-width-safe Win32 signatures before any process creation."""
    kernel = C.WinDLL("kernel32", use_last_error=True)
    signatures = {
        "CreateJobObjectW": (W.HANDLE, [C.c_void_p, W.LPCWSTR]),
        "CloseHandle": (W.BOOL, [W.HANDLE]),
        "SetInformationJobObject": (W.BOOL, [W.HANDLE, C.c_int, C.c_void_p, W.DWORD]),
        "QueryInformationJobObject": (W.BOOL, [W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p]),
        "InitializeProcThreadAttributeList": (W.BOOL, [C.c_void_p, W.DWORD, W.DWORD, C.c_void_p]),
        "UpdateProcThreadAttribute": (
            W.BOOL,
            [C.c_void_p, W.DWORD, C.c_size_t, C.c_void_p, C.c_size_t, C.c_void_p, C.c_void_p],
        ),
        "DeleteProcThreadAttributeList": (None, [C.c_void_p]),
        "CreateProcessW": (
            W.BOOL,
            [
                W.LPCWSTR,
                W.LPWSTR,
                C.c_void_p,
                C.c_void_p,
                W.BOOL,
                W.DWORD,
                C.c_void_p,
                W.LPCWSTR,
                C.c_void_p,
                C.c_void_p,
            ],
        ),
        "IsProcessInJob": (W.BOOL, [W.HANDLE, W.HANDLE, C.c_void_p]),
        "ResumeThread": (W.DWORD, [W.HANDLE]),
        "WaitForSingleObject": (W.DWORD, [W.HANDLE, W.DWORD]),
        "GetExitCodeProcess": (W.BOOL, [W.HANDLE, C.c_void_p]),
        "TerminateJobObject": (W.BOOL, [W.HANDLE, W.UINT]),
        "PeekNamedPipe": (W.BOOL, [W.HANDLE, C.c_void_p, W.DWORD, C.c_void_p, C.c_void_p, C.c_void_p]),
        "GetProcessTimes": (W.BOOL, [W.HANDLE, C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p]),
    }
    for name, (result, arguments) in signatures.items():
        function = getattr(kernel, name)
        function.restype, function.argtypes = result, arguments
    return kernel


def require(ok: bool, operation: str) -> None:
    if not ok:
        raise OSError(C.get_last_error(), operation)


def run_owned(command, root, env, raw, budget, sample, *, stdin_path=None):
    """Create contained and suspended, verify membership, then resume; drain job on every exit."""
    if stdin_path is not None:
        stdin_path = Path(stdin_path).resolve()
        owned_root = Path(root).resolve()
        if (owned_root.drive.upper() != "H:" or not stdin_path.is_relative_to(owned_root)
                or not stdin_path.is_file() or stdin_path.stat().st_size > 2 * 1024**2):
            raise ValueError("bounded stdin file inside owned H run directory required")
    kernel = api()
    result = {
        "status": "BLOCKED",
        "exit_code": 77,
        "contained_before_resume": False,
        "termination_confirmed": False,
        "job_active_after": None,
        "owned_root_pid": None,
        "root_creation_filetime": None,
        "written_bytes": 0,
        "observed_dropped_bytes": 0,
        "unread_output_bytes": None,
        "peak_job_commit_bytes": None,
        "resource_samples": 0,
    }
    job, attributes, initialized = None, None, False
    process = Process()
    read_fd, write_fd = None, None
    result["configured_job_commit_bytes"] = budget.job_commit_bytes

    def drain(output):
        """One bounded pipe read; never append more than the declared output cap."""
        available = W.DWORD()
        ok = kernel.PeekNamedPipe(msvcrt.get_osfhandle(read_fd), None, 0, None, C.byref(available), None)
        if not ok and C.get_last_error() == 109:  # ERROR_BROKEN_PIPE, all writers exited.
            return False
        require(ok, "peek private stdout pipe")
        if not available.value:
            return False
        room = budget.output_bytes - result["written_bytes"]
        block = os.read(read_fd, min(65536, available.value, room + 1))
        output.write(block[:room])
        result["written_bytes"] += min(room, len(block))
        result["observed_dropped_bytes"] += max(0, len(block) - room)
        return True

    try:
        job = kernel.CreateJobObjectW(None, None)
        require(bool(job), "create private job")
        limits = Limits()
        limits.basic.flags = 0x2000 | 0x200 | 0x8  # KILL_ON_CLOSE | JOB_MEMORY | ACTIVE_PROCESS.
        limits.basic.active = budget.max_processes
        limits.job_memory = budget.job_commit_bytes
        require(kernel.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)), "set job limits")
        configured = Limits()
        require(kernel.QueryInformationJobObject(job, 9, C.byref(configured), C.sizeof(configured), None),
                "verify installed job limits")
        require(configured.basic.flags & (0x2000 | 0x200 | 0x8) == (0x2000 | 0x200 | 0x8)
                and not configured.basic.flags & (0x800 | 0x1000)
                and configured.job_memory == budget.job_commit_bytes
                and configured.basic.active == budget.max_processes, "job limit readback mismatch")
        size = C.c_size_t()
        kernel.InitializeProcThreadAttributeList(None, 2, 0, C.byref(size))
        attributes = C.create_string_buffer(size.value)
        require(kernel.InitializeProcThreadAttributeList(attributes, 2, 0, C.byref(size)), "initialize attributes")
        initialized = True
        jobs = (W.HANDLE * 1)(job)
        require(
            kernel.UpdateProcThreadAttribute(attributes, 0, 0x2000D, jobs, C.sizeof(jobs), None, None),
            "atomic job assignment unavailable",
        )
        read_fd, write_fd = os.pipe()
        with raw.open("xb", buffering=0) as output, open(stdin_path or os.devnull, "rb", buffering=0) as null:
            out_handle, in_handle = msvcrt.get_osfhandle(write_fd), msvcrt.get_osfhandle(null.fileno())
            os.set_handle_inheritable(out_handle, True)
            os.set_handle_inheritable(in_handle, True)
            handles = (W.HANDLE * 2)(out_handle, in_handle)
            require(
                kernel.UpdateProcThreadAttribute(attributes, 0, 0x20002, handles, C.sizeof(handles), None, None),
                "restrict inherited handles",
            )
            startup = StartupEx()
            startup.startup.size = C.sizeof(startup)
            startup.startup.flags = 0x101  # USESTDHANDLES + USESHOWWINDOW(hidden)
            startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = in_handle, out_handle, out_handle
            startup.attributes = C.cast(attributes, C.c_void_p)
            environment = C.create_unicode_buffer(
                "\0".join(f"{key}={value}" for key, value in sorted(env.items(), key=lambda pair: pair[0].upper()))
                + "\0\0"
            )
            executable = str(Path(command[0]).resolve())
            line = C.create_unicode_buffer(subprocess.list2cmdline([executable, *command[1:]]))
            require(
                kernel.CreateProcessW(
                    executable,
                    line,
                    None,
                    None,
                    True,
                    0x08080404,
                    environment,
                    str(root),
                    C.byref(startup),
                    C.byref(process),
                ),
                "create atomically contained suspended child",
            )
            result["owned_root_pid"] = process.pid
            creation, exited, kern, user = (C.c_ulonglong() for _ in range(4))
            require(kernel.GetProcessTimes(process.process, C.byref(creation), C.byref(exited),
                                           C.byref(kern), C.byref(user)), "read owned creation time")
            result["root_creation_filetime"] = creation.value
            in_job = W.BOOL()
            require(
                kernel.IsProcessInJob(process.process, job, C.byref(in_job)) and in_job.value,
                "verify suspended job membership",
            )
            result["contained_before_resume"] = True
            os.close(write_fd)
            write_fd = None
            require(kernel.ResumeThread(process.thread) != 0xFFFFFFFF, "resume owned child")
            started = time.monotonic()
            while True:
                drain(output)
                if result["observed_dropped_bytes"]:
                    result.update(status="OUTPUT_LIMIT", exit_code=125)
                    break
                resources = sample(root)
                result["resource_samples"] += 1
                result["last_resources"] = resources
                if (resources["available_ram"] < budget.min_available_ram
                        or resources["commit_headroom"] < budget.min_commit_headroom
                        or resources["H_free"] < budget.min_H_free):
                    result.update(status="RESOURCE_PRESSURE", exit_code=125)
                    break
                wait = kernel.WaitForSingleObject(process.process, 20)
                require(wait != 0xFFFFFFFF, "wait owned child")
                if wait == 0:
                    code = W.DWORD()
                    require(kernel.GetExitCodeProcess(process.process, C.byref(code)), "read child exit")
                    result.update(status="FINISHED", exit_code=code.value)
                    # All buffered root/descendant output must be accounted before returning.
                    while drain(output) and not result["observed_dropped_bytes"]:
                        pass
                    if result["observed_dropped_bytes"]:
                        result.update(status="OUTPUT_LIMIT", exit_code=125)
                    break
                if time.monotonic() - started >= budget.timeout_s:
                    result.update(status="TIMEOUT", exit_code=124)
                    break
    except Exception as error:
        result.update(status="CONTROL_ERROR", exit_code=77, error_type=type(error).__name__)
    finally:
        if job:
            try:
                require(kernel.TerminateJobObject(job, 124), "terminate owned job")
                deadline = time.monotonic() + 5
                while True:
                    accounting = Accounting()
                    require(
                        kernel.QueryInformationJobObject(job, 1, C.byref(accounting), C.sizeof(accounting), None),
                        "query owned job accounting",
                    )
                    result["job_total_processes"] = accounting.total
                    result["job_active_after"] = accounting.active
                    if accounting.active == 0 or time.monotonic() >= deadline:
                        break
                    time.sleep(0.01)
                result["termination_confirmed"] = accounting.active == 0
                if not result["termination_confirmed"]:
                    result.update(status="CLEANUP_UNCONFIRMED", exit_code=126)
                measured = Limits()
                require(kernel.QueryInformationJobObject(job, 9, C.byref(measured), C.sizeof(measured), None),
                        "query job peak commit")
                result["peak_job_commit_bytes"] = measured.peak_job
                result["commit_budget_exceeded"] = measured.peak_job > budget.job_commit_bytes
                if result["commit_budget_exceeded"] and result["termination_confirmed"]:
                    # Preserve the measured counter, even when the OS denied the
                    # attempted allocation. Never convert an over-budget peak to PASS.
                    result.update(status="COMMIT_BUDGET_EXCEEDED", exit_code=125)
            except OSError as error:
                result.update(status="CLEANUP_UNCONFIRMED", exit_code=126, cleanup_error_type=type(error).__name__)
        for fd in (read_fd, write_fd):
            if fd is not None:
                os.close(fd)
        for handle in (process.thread, process.process, job):
            if handle:
                kernel.CloseHandle(handle)
        if initialized:
            kernel.DeleteProcThreadAttributeList(attributes)
    return result
