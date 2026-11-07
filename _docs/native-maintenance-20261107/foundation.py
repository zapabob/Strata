"""Private, read-only inventory and strict ownership/idle primitives for maintenance.

No model start, stop, restore, install or GPU probe is performed by this module's CLI.
Raw CIM commands, credentials, environment and Host settings never reach stdout.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import http.client
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PRIVATE = Path('H:/Strata/private-backups/native-maintenance-20261107')
TARGET = Path('C:/Users/downl/AppData/Local/Programs/Strata')
COMPONENT = Path('C:/Users/downl/AppData/Local/Strata/components/engine/0.5.1-windows-x86_64-cuda-cuda13')
HERMES = Path('C:/Users/downl/.hermes/llama/prism-b10826-c9c34bc/bin/llama-server.exe')
LAUNCHER = Path('C:/Users/downl/.hermes/llama/Ensure-HermesGeneration.ps1')
STATE = Path('C:/Users/downl/.strata/data/state.json')
REGISTRY = STATE.with_name('local-models.json')
PS = str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe')
GIB = 1024**3
sys.path[:0] = [str(ROOT), str(ROOT / 'tools')]
# The project-native guard must resolve from the explicit worktree above.
from native_model_resource_guard import available_memory, PressurePolicy  # noqa: E402


class Blocked(RuntimeError):
    """Only static nonsecret codes may be used as messages."""


def need(condition: Any, code: str) -> None:
    if not condition:
        raise Blocked(code)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def canonical(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def powershell(script: Path, *args: str) -> Any:
    result = subprocess.run(
        [PS, '-NoProfile', '-NonInteractive', '-File', str(script), *args],
        input=b'PRIVATE_PIPE\n',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    need(result.returncode == 0, 'powershell_helper_failed')
    return json.loads(result.stdout.decode('utf-8-sig'))


def private_acl() -> None:
    need(powershell(HERE / 'private-store.ps1')['ok'], 'private_acl_failed')


def private_path(name: str) -> Path:
    need(bool(re.fullmatch(r'[a-z0-9][a-z0-9_.-]*', name)), 'invalid_private_name')
    private_acl()
    path = PRIVATE / name
    need(not path.is_symlink() and not path.is_junction(), 'private_reparse')
    return path


def write_private(name: str, value: Any) -> str:
    path = private_path(name)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    private_acl()
    return sha(path)


def read_private(name: str, digest: str | None = None) -> Any:
    data = private_path(name).read_bytes()
    if digest is not None:
        need(hashlib.sha256(data).hexdigest() == digest, 'private_digest_mismatch')
    return json.loads(data)


def norm(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(path))


class IdentityHandle:
    """Retain a kernel process handle and verify creation time, not just a reusable PID."""

    def __init__(self, pid: int, *, terminate: bool = False) -> None:
        self.k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        self.k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.k32.OpenProcess.restype = wintypes.HANDLE
        self.k32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self.k32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.k32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.handle = self.k32.OpenProcess(0x1000 | 0x100000 | (1 if terminate else 0), False, pid)
        need(self.handle, 'process_handle_unavailable')
        self.can_terminate = terminate
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            need(self.k32.GetProcessTimes(self.handle, *(ctypes.byref(t) for t in times)), 'process_times_failed')
            self.created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            need(
                self.k32.QueryFullProcessImageNameW(self.handle, 0, buffer, ctypes.byref(size)), 'process_image_failed'
            )
            self.exe = buffer.value
        except BaseException:
            self.close()
            raise

    def verify(self, record: dict) -> None:
        need(
            self.alive() and self.created == record['creationFiletime'] and norm(self.exe) == norm(record['exe']),
            'process_identity_changed',
        )

    def alive(self) -> bool:
        return self.k32.WaitForSingleObject(self.handle, 0) == 258

    def stop_exact(self) -> None:
        need(self.can_terminate and self.alive(), 'stop_handle_invalid')
        need(self.k32.TerminateProcess(self.handle, 0), 'owned_stop_failed')
        need(self.k32.WaitForSingleObject(self.handle, 10000) == 0, 'owned_stop_timeout')

    def close(self) -> None:
        if self.handle:
            self.k32.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self) -> IdentityHandle:
        return self

    def __exit__(self, *unused: Any) -> None:
        self.close()


def require_independent_restore_lifetime() -> None:
    """A restored Hermes server must outlive this helper, including its caller's Job."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    member = wintypes.BOOL()
    need(kernel.IsProcessInJob(kernel.GetCurrentProcess(), None, ctypes.byref(member)), 'caller_job_query_failed')
    need(not member.value, 'run_from_standalone_console_for_hermes_lifetime')


def process_record(row: dict, *, environment: bool = False) -> dict:
    proc = psutil.Process(row['pid'])
    with IdentityHandle(row['pid']) as handle:
        need(norm(handle.exe) == norm(row['exe']), 'cim_image_mismatch')
        cim_time = datetime.fromisoformat(row['createdUtc'].replace('Z', '+00:00')).timestamp()
        need(abs(cim_time - (handle.created / 10_000_000 - 11644473600)) < 0.002, 'cim_creation_mismatch')
        result = dict(row, creationFiletime=handle.created, argv=proc.cmdline(), cwd=proc.cwd())
        # The raw command is kept verbatim; argv is for validation, never shell evaluation.
        need(result['commandLine'] and result['argv'], 'command_unavailable')
        if environment:
            result['environment'] = proc.environ()
        handle.verify(result)
    return result


def inventory() -> list[dict]:
    rows = powershell(HERE / 'process-inventory.ps1')
    need(isinstance(rows, list), 'invalid_process_inventory')
    return rows


def listeners(port: int) -> list[tuple[str, int]]:
    return sorted(
        set(
            (conn.laddr.ip, conn.pid)
            for conn in psutil.net_connections(kind='tcp')
            if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port
        )
    )


def bind_owner(record: dict, port: int) -> None:
    need(type(port) is int and 1 <= port <= 65535, 'invalid_port')
    with IdentityHandle(record['pid']) as handle:
        handle.verify(record)
        owners = listeners(port)
        need(owners == [('127.0.0.1', record['pid'])], 'listener_not_exact_loopback_owner')


def request(
    record: dict,
    port: int,
    route: str,
    *,
    key: str = '',
    method: str = 'GET',
    body: Any = None,
    text: bool = False,
    timeout: float = 5,
) -> Any:
    need(
        route.startswith('/') and not route.startswith('//') and '\r' not in route and '\n' not in route,
        'invalid_local_route',
    )
    need(method in {'GET', 'POST', 'PATCH'}, 'invalid_http_method')
    bind_owner(record, port)
    # No proxy, DNS, redirects, external base URL, or credential-bearing query string.
    headers = {'Content-Type': 'application/json', 'Origin': f'http://127.0.0.1:{port}'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout)
    try:
        conn.request(method, route, body=None if body is None else json.dumps(body).encode(), headers=headers)
        response = conn.getresponse()
        raw = response.read(16 * 1024 * 1024 + 1)
        need(response.status == 200, 'local_http_status_' + str(response.status))
        need(len(raw) <= 16 * 1024 * 1024, 'local_response_too_large')
    finally:
        conn.close()
    bind_owner(record, port)
    return raw.decode('utf-8') if text else json.loads(raw)


def argument(argv: list[str], *flags: str) -> str | None:
    found = []
    for index, value in enumerate(argv):
        if value in flags:
            need(index + 1 < len(argv), 'missing_argument_value')
            found.append(argv[index + 1])
        for flag in flags:
            if value.startswith(flag + '='):
                found.append(value[len(flag) + 1 :])
    need(len(found) <= 1, 'duplicate_argument')
    return found[0] if found else None


def file_identity(path: Path, *, digest: bool = False) -> dict:
    need(path.is_absolute() and path.is_file(), 'identity_file_unavailable')
    # Existing model/launcher locations can be junctions. Pin their resolved target
    # as well as requested path; the private evidence store itself forbids reparse points.
    resolved = str(path.resolve(strict=True))
    before = path.stat()
    result = {'path': str(path), 'resolvedPath': resolved, 'size': before.st_size, 'mtimeNs': before.st_mtime_ns}
    if digest:
        result['sha256'] = sha(path)
    after = path.stat()
    need((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), 'file_changed_during_inventory')
    need(str(path.resolve(strict=True)) == resolved, 'file_target_changed')
    return result


def model_files(path: Path) -> list[dict]:
    match = re.fullmatch(r'(.+)-(\d{5})-of-(\d{5})\.gguf', path.name, re.I)
    paths = (
        [path]
        if not match
        else [path.with_name(f'{match[1]}-{n:05d}-of-{int(match[3]):05d}.gguf') for n in range(1, int(match[3]) + 1)]
    )
    need(len(paths) <= 1000, 'model_shard_limit')
    return [file_identity(p) for p in paths]


def nonnegative(value: Any) -> int:
    need(type(value) is int and value >= 0, 'unknown_activity_count')
    return value


def slot_counts(value: Any) -> dict:
    need(isinstance(value, list) and len(value) > 0, 'unknown_slots')
    need(all(isinstance(s, dict) and type(s.get('is_processing')) is bool for s in value), 'unknown_slot_state')
    return {'slots': len(value), 'active': sum(int(s['is_processing']) for s in value)}


def metric_counts(text: str) -> dict:
    counts = {}
    for name in ('requests_processing', 'requests_deferred'):
        found = re.findall(r'^(?:llamacpp:)?' + name + r'\s+([0-9]+(?:\.0+)?)\s*$', text, re.M)
        need(len(found) == 1, 'unknown_admission_metrics')
        counts[name] = nonnegative(int(float(found[0])))
    return counts


def backend_key(record: dict) -> str:
    argv = record['argv']
    need(argument(argv, '--api-key-file') is None, 'key_file_requires_review')
    key = argument(argv, '--api-key') or record['environment'].get('LLAMA_API_KEY', '')
    need(isinstance(key, str) and '\n' not in key and '\r' not in key, 'invalid_backend_key')
    return key


def backend_observation(record: dict, port: int) -> dict:
    key = backend_key(record)
    health = request(record, port, '/health', key=key)
    need(health.get('status') == 'ok', 'backend_not_healthy')
    props = request(record, port, '/props', key=key)
    context = props.get('default_generation_settings', {}).get('n_ctx')
    slots = props.get('total_slots')
    need(type(context) is int and context > 0 and type(slots) is int and slots > 0, 'backend_settings_unknown')
    activity = slot_counts(request(record, port, '/slots', key=key))
    need(activity['slots'] == slots, 'slot_count_mismatch')
    # /metrics is the backend's admission/queue view; cached Host metrics are insufficient.
    try:
        metrics = metric_counts(request(record, port, '/metrics', key=key, text=True))
    except (Blocked, OSError, ValueError) as error:
        # Preserve the snapshot while making unknown admission a hard execution blocker.
        metrics = {
            'requests_processing': None,
            'requests_deferred': None,
            'admissionError': str(error) if isinstance(error, Blocked) else type(error).__name__,
        }
    model = argument(record['argv'], '-m', '--model')
    need(model is not None and norm(props.get('model_path', '')) == norm(model), 'model_identity_mismatch')
    return {
        'health': True,
        'modelPath': model,
        'contextPerSlot': context,
        'totalSlots': slots,
        'activity': {**activity, **metrics},
    }


def host_activity(host: dict) -> dict:
    proc, port = host['process'], host['port']
    turns = request(proc, port, '/api/chat/active')
    serving = request(proc, port, '/api/serving')
    need(isinstance(turns.get('turns'), list), 'unknown_host_turns')
    stats = serving.get('stats', {})
    return {
        'activeTurns': len(turns['turns']),
        'running': nonnegative(stats.get('running')),
        'waiting': nonnegative(stats.get('waiting')),
    }


def settings() -> dict:
    state = json.loads(STATE.read_bytes())
    # Exclude chat/history entirely. Serving may contain a key and stays private.
    return {k: state.get(k) for k in ('current', 'beginner', 'expert', 'configExtra', 'serving')}


def resource_status() -> dict:
    sample = available_memory()
    policy = PressurePolicy(physical_floor_bytes=3 * GIB, commit_floor_bytes=4 * GIB, physical_grace_seconds=0)
    reason = policy.observe(sample, 0)
    disks = {drive: shutil.disk_usage(drive + ':/').free for drive in ('C', 'H')}
    return {
        'availableRamGiB': round(sample['available_physical_bytes'] / GIB, 3),
        'availableCommitGiB': round(sample['available_commit_bytes'] / GIB, 3),
        'freeCGiB': round(disks['C'] / GIB, 3),
        'freeHGiB': round(disks['H'] / GIB, 3),
        'ok': reason is None and disks['C'] >= 5 * GIB and disks['H'] >= 10 * GIB,
    }


def host_files() -> list[dict]:
    return [
        file_identity(TARGET / name, digest=True)
        for name in (
            'strata-desktop.exe',
            'node/node.exe',
            'host/server/index.mjs',
            'host/server/models.mjs',
            'host/server/supervisor.mjs',
            'host/server/engine.mjs',
            'host/server/store.mjs',
        )
    ]


def watcher_snapshot() -> dict:
    tasks = powershell(HERE / 'task-inventory.ps1')
    need(isinstance(tasks, list), 'task_inventory_unknown')
    uncertain = []
    for task in tasks:
        if task['state'] == 'Disabled':
            continue
        if task['state'] == 'Running' or any(
            t.get('enabled') is not False
            and (t.get('interval') or t.get('type') not in {'MSFT_TaskLogonTrigger', 'MSFT_TaskBootTrigger'})
            for t in task['triggers']
        ):
            uncertain.append(task['name'])
    return {'tasks': tasks, 'automaticRespawnUnresolved': bool(uncertain)}


def capture() -> dict:
    private_acl()
    rows = inventory()
    shells = [r for r in rows if norm(r['exe']) == norm(TARGET / 'strata-desktop.exe')]
    if not shells:
        return capture_without_host(rows)
    need(len(shells) == 1, 'exactly_one_installed_shell_required')
    shell = process_record(shells[0])
    nodes = [r for r in rows if r['ppid'] == shell['pid'] and norm(r['exe']) == norm(TARGET / 'node/node.exe')]
    hosts = []
    for row in nodes:
        node = process_record(row)
        for conn in psutil.Process(row['pid']).net_connections(kind='tcp'):
            if conn.status != psutil.CONN_LISTEN or conn.laddr.ip != '127.0.0.1':
                continue
            try:
                if request(node, conn.laddr.port, '/api/health').get('ok') is True:
                    hosts.append({'process': node, 'port': conn.laddr.port})
            except (Blocked, OSError, ValueError):
                continue
    need(len(hosts) == 1, 'exactly_one_owned_host_required')
    host = hosts[0]

    def get(route: str) -> Any:
        return request(host['process'], host['port'], route)

    build = get('/api/app/build')
    need(build.get('host') == '0.5.2-local.1' and build.get('shell') == '0.5.2-local.1', 'installed_version_changed')
    supervisor = get('/api/engine/status')
    library = get('/api/models')
    native = get('/api/native')
    need(native.get('instances') == [], 'native_instance_requires_separate_restore_adapter')
    need(not any(j.get('state') == 'running' for j in native.get('jobs', [])), 'native_job_active')
    need(
        supervisor.get('running') is True and library.get('loaded') == supervisor.get('modelId'),
        'host_model_not_owned_running',
    )
    strata_rows = [r for r in rows if r['pid'] == supervisor.get('pid')]
    hermes_rows = [r for r in rows if norm(r['exe']) == norm(HERMES)]
    need(len(strata_rows) == len(hermes_rows) == 1, 'exact_backend_count_required')
    strata = process_record(strata_rows[0], environment=True)
    hermes = process_record(hermes_rows[0], environment=True)
    need(strata['ppid'] == host['process']['pid'], 'strata_not_host_child')
    need(norm(strata['exe']) == norm(supervisor['binary']['path']), 'host_binary_mismatch')
    need(
        norm(strata['exe']).startswith(norm(TARGET / 'local-backends') + os.sep)
        or norm(strata['exe']).startswith(norm(COMPONENT) + os.sep),
        'unreviewed_strata_binary',
    )
    # Private-memory mode creates a fresh secret on reload. Exact restoration requires a separate adapter.
    need(not strata['environment'].get('LLAMA_API_KEY'), 'private_memory_reload_not_exact')
    original = settings()
    need(original['current'] == library['loaded'], 'saved_selection_differs_from_loaded')
    result = {
        'schema': 1,
        'capturedUtc': utc(),
        'shell': shell,
        'host': host,
        'build': {k: build[k] for k in ('host', 'shell')},
        'settings': original,
        'modelId': library['loaded'],
        'registry': file_identity(REGISTRY, digest=True),
        'resources': resource_status(),
        'hostActivity': host_activity(host),
        'backends': {},
    }
    for name, record, port in [
        ('strata', strata, supervisor['port']),
        ('hermes', hermes, int(argument(hermes['argv'], '--port') or '8080')),
    ]:
        observation = backend_observation(record, port)
        result['backends'][name] = {
            'process': record,
            'port': port,
            'observed': observation,
            'binary': file_identity(Path(record['exe']), digest=True),
            'models': model_files(Path(observation['modelPath'])),
        }
    result['nativeComponent'] = file_identity(COMPONENT / 'strata.exe', digest=True)
    result['hermesLauncher'] = file_identity(LAUNCHER, digest=True)
    result['watchers'] = watcher_snapshot()
    result['hostFiles'] = host_files()
    result['guards'] = [
        file_identity(ROOT / 'serve/winjob.py', digest=True),
        file_identity(ROOT / 'tools/native_model_resource_guard.py', digest=True),
    ]
    need(settings() == original, 'settings_changed_during_snapshot')
    for backend in result['backends'].values():
        bind_owner(backend['process'], backend['port'])
    return result


def capture_without_host(rows: list[dict]) -> dict:
    """Keep useful private evidence, but block maintenance without the real owner API."""
    hermes_rows = [r for r in rows if norm(r['exe']) == norm(HERMES)]
    need(len(hermes_rows) <= 1, 'duplicate_hermes_no_deduplication')
    original = settings()
    result = {
        'schema': 1,
        'capturedUtc': utc(),
        'shell': None,
        'host': None,
        'blockers': ['installed_host_absent_snapshot_not_executable'],
        'settings': original,
        'resources': resource_status(),
        'hostActivity': None,
        'registry': file_identity(REGISTRY, digest=True),
        'backends': {},
        'configuredHermesBinary': file_identity(HERMES, digest=True),
        'nativeComponent': file_identity(COMPONENT / 'strata.exe', digest=True),
        'hermesLauncher': file_identity(LAUNCHER, digest=True),
        'watchers': watcher_snapshot(),
        'hostFiles': host_files(),
        'guards': [
            file_identity(ROOT / 'serve/winjob.py', digest=True),
            file_identity(ROOT / 'tools/native_model_resource_guard.py', digest=True),
        ],
    }
    if hermes_rows:
        hermes = process_record(hermes_rows[0], environment=True)
        port = int(argument(hermes['argv'], '--port') or '8080')
        observation = backend_observation(hermes, port)
        result['backends']['hermes'] = {
            'process': hermes,
            'port': port,
            'observed': observation,
            'binary': file_identity(HERMES, digest=True),
            'models': model_files(Path(observation['modelPath'])),
        }
    else:
        result['blockers'].append('hermes_absent_no_restart_authorized_by_preparation')
    result['unownedInstalledProcesses'] = [process_record(r) for r in rows if r not in hermes_rows]
    need(settings() == original, 'settings_changed_during_snapshot')
    return result


def idle_counts(snapshot: dict) -> dict:
    host = host_activity(snapshot['host']) if snapshot['host'] else None
    backends = {}
    for name, value in snapshot['backends'].items():
        live = backend_observation(value['process'], value['port'])
        need(
            all(live[k] == value['observed'][k] for k in ('modelPath', 'contextPerSlot', 'totalSlots')),
            'backend_settings_changed',
        )
        backends[name] = live['activity']
    idle = (
        host is not None
        and all(v == 0 for v in host.values())
        and all(
            all(counts[k] == 0 for k in ('active', 'requests_processing', 'requests_deferred'))
            for counts in backends.values()
        )
    )
    return {'observedUtc': utc(), 'host': host, 'backends': backends, 'idle': idle}


def summary(snapshot: dict, digest: str) -> dict:
    return {
        'snapshotSHA256': digest,
        'capturedUtc': snapshot['capturedUtc'],
        'shellPid': snapshot['shell']['pid'] if snapshot['shell'] else None,
        'hostPid': snapshot['host']['process']['pid'] if snapshot['host'] else None,
        'hostPort': snapshot['host']['port'] if snapshot['host'] else None,
        'blockers': snapshot.get('blockers', []),
        'hostActivity': snapshot['hostActivity'],
        'watcherCount': len(snapshot.get('watchers', {}).get('tasks', [])),
        'automaticRespawnUnresolved': snapshot.get('watchers', {}).get('automaticRespawnUnresolved'),
        'resources': snapshot['resources'],
        'backends': {
            name: {
                'pid': b['process']['pid'],
                'creationFiletime': b['process']['creationFiletime'],
                'exe': b['process']['exe'],
                'exeSHA256': b['binary']['sha256'],
                'port': b['port'],
                'health': b['observed']['health'],
                'contextPerSlot': b['observed']['contextPerSlot'],
                'slots': b['observed']['totalSlots'],
                'activity': b['observed']['activity'],
                'modelFiles': len(b['models']),
                'modelBytes': sum(m['size'] for m in b['models']),
                'modelMtimeNs': [m['mtimeNs'] for m in b['models']],
                'commandSHA256': hashlib.sha256(b['process']['commandLine'].encode('utf-8')).hexdigest(),
            }
            for name, b in snapshot['backends'].items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['snapshot', 'readiness'])
    parser.add_argument('--snapshot-name', default='snapshot.json')
    parser.add_argument('--snapshot-sha256')
    args = parser.parse_args()
    if args.mode == 'snapshot':
        snap = capture()
        digest = write_private(args.snapshot_name, snap)
        result = summary(snap, digest)
        write_private(args.snapshot_name.removesuffix('.json') + '-summary.json', result)
    else:
        need(args.snapshot_sha256, 'snapshot_digest_required')
        snap = read_private(args.snapshot_name, args.snapshot_sha256)
        result = idle_counts(snap)
        result['resources'] = resource_status()
    logging.info(json.dumps(result))
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        raise SystemExit(main())
    except Exception as error:
        logging.error(
            json.dumps({'ok': False, 'code': str(error) if isinstance(error, Blocked) else type(error).__name__})
        )
        raise SystemExit(1) from None
