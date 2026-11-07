"""Prepare / inspect by default. Parent-only, single-use execution with exact restoration.

Never supply credentials or commands on this CLI. All operational input is in the
owner-only private directory. Exceptions are reduced to fixed codes at the boundary.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import logging
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterator
from urllib.parse import quote

import foundation as f


def error_code(error: BaseException) -> str:
    return str(error) if isinstance(error, f.Blocked) else type(error).__name__


def check_files(items: list[dict]) -> None:
    for item in items:
        f.need(f.file_identity(Path(item['path']), digest='sha256' in item) == item, 'pinned_file_changed')


def helper_identities() -> list[dict]:
    return [
        f.file_identity(f.HERE / name, digest=True)
        for name in (
            'foundation.py',
            'maintenance.py',
            'candidate_guard.py',
            'private-store.ps1',
            'process-inventory.ps1',
            'task-inventory.ps1',
        )
    ]


def validate_recipe(recipe: dict) -> None:
    f.need(recipe.get('schema') == 1 and recipe.get('candidate') == '044', 'candidate_recipe_schema')
    root = Path(recipe.get('candidateRoot', ''))
    f.need(
        root.is_absolute()
        and root.is_dir()
        and root.resolve() != f.ROOT.resolve()
        and root.resolve().is_relative_to(Path('H:/Strata/worktrees').resolve()),
        'isolated_candidate_root_required',
    )
    f.need(
        recipe.get('originalHostUntouched') is True and recipe.get('noInstall') is True, 'candidate_scope_not_declared'
    )
    f.need(type(recipe.get('windowSeconds')) is int and 1 <= recipe['windowSeconds'] <= 3600, 'window_bound')
    steps = recipe.get('steps')
    f.need(isinstance(steps, list) and 1 <= len(steps) <= 8, 'candidate_steps_required')
    files = recipe.get('files')
    f.need(
        isinstance(files, list) and 1 <= len(files) <= 2000 and all(isinstance(p, str) for p in files),
        'candidate_pins_required',
    )
    pinned = {f.norm(p) for p in files}
    total = 0
    for step in steps:
        argv = step.get('argv')
        f.need(
            isinstance(argv, list) and len(argv) >= 1 and all(isinstance(v, str) and '\0' not in v for v in argv),
            'candidate_argv_invalid',
        )
        exe = Path(argv[0])
        f.need(
            exe.is_absolute() and exe.is_file() and exe.suffix.lower() == '.exe' and f.norm(exe) in pinned,
            'candidate_exe_not_pinned',
        )
        f.need(
            exe.name.lower() not in {'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe'},
            'command_interpreter_rejected',
        )
        if exe.name.lower() in {'powershell.exe', 'pwsh.exe'}:
            f.need(
                len(argv) >= 5
                and argv[1:4] == ['-NoProfile', '-NonInteractive', '-File']
                and Path(argv[4]).is_absolute()
                and f.norm(argv[4]) in pinned,
                'powershell_file_only',
            )
        if exe.name.lower() in {'python.exe', 'python3.exe', 'node.exe'}:
            scripts = [a for a in argv[1:] if a.lower().endswith(('.py', '.mjs', '.js'))]
            f.need(
                len(scripts) == 1
                and Path(scripts[0]).is_absolute()
                and f.norm(scripts[0]) in pinned
                and not any(a in {'-c', '-e', '--eval'} for a in argv[1:]),
                'interpreter_script_not_pinned',
            )
        cwd = Path(step.get('cwd', ''))
        f.need(
            cwd.is_absolute() and cwd.is_dir() and cwd.resolve().is_relative_to(root.resolve()),
            'candidate_cwd_not_isolated',
        )
        seconds = step.get('timeoutSeconds')
        f.need(type(seconds) is int and 1 <= seconds <= recipe['windowSeconds'], 'step_bound')
        total += seconds
        env = step.get('env', {})
        f.need(
            isinstance(env, dict)
            and all(
                isinstance(k, str) and isinstance(v, str) and '\0' not in k + v and '=' not in k for k, v in env.items()
            ),
            'candidate_environment_invalid',
        )
    f.need(total <= recipe['windowSeconds'], 'steps_exceed_window')


def freeze() -> dict:
    """Hash already-built candidate inputs; no build, install, start or stop."""
    recipe = f.read_private('candidate-recipe.json')
    validate_recipe(recipe)
    manifest = dict(
        recipe,
        files=[f.file_identity(Path(p), digest=True) for p in recipe['files']],
        helpers=helper_identities(),
        guards=[
            f.file_identity(f.ROOT / p, digest=True)
            for p in ('serve/winjob.py', 'tools/native_model_resource_guard.py')
        ],
        frozenUtc=f.utc(),
    )
    digest = f.write_private('frozen-candidate.json', manifest)
    return {
        'frozen': True,
        'manifestSHA256': digest,
        'files': len(manifest['files']),
        'windowSeconds': manifest['windowSeconds'],
    }


@contextmanager
def operation_lock() -> Iterator[None]:
    """OS-released lock; recovery can acquire it after the maintenance process dies."""
    path = f.private_path('operation.lock')
    with path.open('a+b') as lock:
        if path.stat().st_size == 0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise f.Blocked('maintenance_or_restore_already_running') from None
        try:
            yield
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


class Journal:
    def __init__(self, name: str) -> None:
        self.stream = f.private_path(name).open('x', encoding='utf-8', newline='\n')

    def event(self, phase: str, **fields: Any) -> None:
        self.stream.write(json.dumps({'utc': f.utc(), 'phase': phase, **fields}) + '\n')
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def close(self) -> None:
        self.stream.close()


def run_window(ops: Any, journal: Any) -> dict:
    """Testable transaction: record intent first; always attempt BOTH restores."""
    report = {'ok': False, 'candidatePassed': False, 'restored': {}, 'error': None, 'journalError': False}

    def recovery_event(phase: str, **fields: Any) -> None:
        try:
            journal.event(phase, **fields)
        except BaseException:
            # A full disk must not prevent the second service's restoration.
            report['journalError'] = True

    ops.preflight()
    ops.wait_idle()
    mutation_started = False
    try:
        # From this point any uncertain unload response still requires reconciliation.
        journal.event('stop_intent', service='strata')
        mutation_started = True
        ops.stop_strata()
        journal.event('stopped', service='strata')
        journal.event('stop_intent', service='hermes')
        ops.stop_hermes()
        journal.event('stopped', service='hermes')
        ops.run_candidate()
        report['candidatePassed'] = True
    except BaseException as error:
        report['error'] = error_code(error)
        recovery_event('window_failed', code=report['error'])
    finally:
        try:
            ops.cleanup_candidate()
        except BaseException as error:
            report['error'] = error_code(error)
        for name in (('hermes', 'strata') if mutation_started else ()):
            recovery_event('restore_intent', service=name)
            try:
                ops.restore(name)
                report['restored'][name] = True
                recovery_event('restore_verified', service=name)
            except BaseException as error:
                report['restored'][name] = False
                recovery_event('restore_failed', service=name, code=error_code(error))
        report['ok'] = (
            report['candidatePassed']
            and report['error'] is None
            and not report['journalError']
            and all(report['restored'].values())
        )
    return report


class Operations:
    def __init__(self, snapshot: dict, manifest: dict | None = None, manifest_sha: str | None = None) -> None:
        self.snapshot, self.manifest, self.manifest_sha = snapshot, manifest, manifest_sha
        self.guard: subprocess.Popen | None = None
        self.guard_log = None
        self.guard_contained = False

    def host(self, route: str, **kwargs: Any) -> Any:
        host = self.snapshot['host']
        f.need(host is not None, 'host_missing')
        return f.request(host['process'], host['port'], route, **kwargs)

    def preflight(self) -> None:
        snap = self.snapshot
        f.need(
            snap.get('host') and set(snap['backends']) == {'strata', 'hermes'} and not snap.get('blockers'),
            'snapshot_incomplete',
        )
        f.require_independent_restore_lifetime()
        f.need('watchers' in snap and not snap['watchers']['automaticRespawnUnresolved'], 'watcher_readiness_unknown')
        watchers = f.watcher_snapshot()
        f.need(
            not watchers['automaticRespawnUnresolved'] and watchers['tasks'] == snap['watchers']['tasks'],
            'watchers_changed',
        )
        with f.IdentityHandle(snap['shell']['pid']) as handle:
            handle.verify(snap['shell'])
        f.need(f.settings() == snap['settings'], 'original_settings_changed')
        f.need(self.host('/api/models')['loaded'] == snap['modelId'], 'host_loaded_model_changed')
        sup = self.host('/api/engine/status')
        f.need(
            sup.get('pid') == snap['backends']['strata']['process']['pid'] and sup.get('running') is True,
            'host_ownership_changed',
        )
        config = self.host('/api/engine')
        f.need(
            config['engine']['args'] == snap['backends']['strata']['process']['argv'][1:],
            'saved_settings_not_exact_reload',
        )
        check_files(
            [
                snap['registry'],
                snap['nativeComponent'],
                snap['hermesLauncher'],
                *snap['guards'],
                *snap.get('hostFiles', []),
            ]
        )
        for backend in snap['backends'].values():
            check_files([backend['binary'], *backend['models']])
            f.bind_owner(backend['process'], backend['port'])
            self.same_command(backend['process'])
        f.need(f.resource_status()['ok'], 'resource_floor')
        if self.manifest is not None:
            check_files([*self.manifest['files'], *self.manifest['helpers'], *self.manifest['guards']])

    @staticmethod
    def same_command(expected: dict) -> None:
        rows = [r for r in f.inventory() if r['pid'] == expected['pid']]
        f.need(len(rows) == 1 and rows[0]['commandLine'] == expected['commandLine'], 'original_command_changed')

    def wait_idle(self, seconds: float = 300) -> None:
        end, stable = time.monotonic() + seconds, 0
        while time.monotonic() < end:
            counts = f.idle_counts(self.snapshot)
            f.need(all('admissionError' not in c for c in counts['backends'].values()), 'admission_readiness_unknown')
            stable = stable + 1 if counts['idle'] else 0
            if stable >= 3:
                self.preflight()
                return
            time.sleep(2)
        raise f.Blocked('idle_timeout_no_stop')

    def stop_strata(self) -> None:
        f.need(f.idle_counts(self.snapshot)['idle'], 'new_activity_before_stop')
        backend = self.snapshot['backends']['strata']
        with f.IdentityHandle(backend['process']['pid']) as handle:
            handle.verify(backend['process'])
            self.host('/api/models/unload', method='POST', body={}, timeout=20)
            end = time.monotonic() + 20
            while handle.alive() and time.monotonic() < end:
                time.sleep(0.25)
            f.need(not handle.alive(), 'host_unload_process_not_exited')
        f.need(not f.listeners(backend['port']), 'strata_port_still_owned')
        f.need(
            self.host('/api/models')['loaded'] is None and self.host('/api/engine/status')['status'] == 'stopped',
            'host_unload_not_confirmed',
        )

    def stop_hermes(self) -> None:
        backend = self.snapshot['backends']['hermes']
        counts = f.backend_observation(backend['process'], backend['port'])['activity']
        f.need(all(counts[k] == 0 for k in ('active', 'requests_processing', 'requests_deferred')), 'hermes_not_idle')
        f.need(all(v == 0 for v in f.host_activity(self.snapshot['host']).values()), 'new_host_activity')
        self.same_command(backend['process'])
        with f.IdentityHandle(backend['process']['pid'], terminate=True) as handle:
            handle.verify(backend['process'])
            f.bind_owner(backend['process'], backend['port'])
            handle.stop_exact()
        f.need(not f.listeners(backend['port']), 'hermes_port_still_owned')

    def run_candidate(self) -> None:
        from serve import winjob

        f.need(self.manifest is not None and self.manifest_sha, 'candidate_not_frozen')
        f.need(f.resource_status()['ok'], 'resource_floor')
        # Full hashes were checked before stopping. Recheck candidate bytes inside
        # the deadline-owned guard so slow file I/O cannot prolong the outage.
        # An outer handshake means even the guard cannot spawn work before its own
        # process is in our kill-on-close job. This also covers an abrupt owner exit.
        worker = (
            'import json,subprocess,sys; '
            'sys.stdin.readline().strip()=="GO" or sys.exit(125); '
            'raise SystemExit(subprocess.call(json.loads(sys.argv[1]),shell=False))'
        )
        command = [
            sys.executable,
            '-B',
            str(f.HERE / 'candidate_guard.py'),
            '--execute',
            '--manifest-sha256',
            self.manifest_sha,
        ]
        self.guard_log = f.private_path('candidate-guard.log').open('xb')
        self.guard = subprocess.Popen(
            [sys.executable, '-B', '-c', worker, json.dumps(command)],
            stdin=subprocess.PIPE,
            stdout=self.guard_log,
            stderr=subprocess.STDOUT,
            cwd=f.HERE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.need(winjob.contain(self.guard), 'outer_containment_failed')
        self.guard_contained = True
        self.guard.stdin.write(b'GO\n')
        self.guard.stdin.flush()
        self.guard.stdin.close()
        end = time.monotonic() + self.manifest['windowSeconds'] + 15
        while self.guard.poll() is None:
            f.need(time.monotonic() < end, 'outer_candidate_timeout')
            f.need(f.resource_status()['ok'], 'resource_floor')
            # A watcher respawn cancels the test; never deduplicate or kill it.
            f.need(
                not any(f.listeners(b['port']) for b in self.snapshot['backends'].values()), 'original_port_reoccupied'
            )
            time.sleep(1)
        f.need(self.guard.returncode == 0, 'candidate_guard_failed')
        f.need(f.read_private('candidate-result.json')['ok'] is True, 'candidate_result_failed')

    def cleanup_candidate(self) -> None:
        if self.guard is not None:
            from serve import winjob

            terminated = winjob.terminate()
            if self.guard.poll() is None:
                self.guard.kill()
            self.guard.wait(timeout=15)
            f.need(not self.guard_contained or terminated, 'outer_job_cleanup_failed')
        if self.guard_log:
            self.guard_log.close()

    def existing_backend(self, name: str) -> dict | None:
        original = self.snapshot['backends'][name]['process']
        rows = [r for r in f.inventory() if f.norm(r['exe']) == f.norm(original['exe'])]
        if name == 'strata':
            status = self.host('/api/engine/status')
            if status.get('status') in {'starting', 'stopping'}:
                raise f.Blocked('host_transition_in_progress')
            f.need(
                not rows
                or (
                    len(rows) == 1
                    and rows[0]['pid'] == status.get('pid')
                    and rows[0]['ppid'] == self.snapshot['host']['process']['pid']
                ),
                'untracked_strata_process',
            )
        f.need(len(rows) <= 1, 'duplicate_server_no_deduplication')
        if not rows:
            return None
        live = f.process_record(rows[0], environment=True)
        f.need(
            live['commandLine'] == original['commandLine'] and live['argv'] == original['argv'],
            'restore_command_mismatch',
        )
        return live

    def verify_restored(self, name: str, live: dict) -> None:
        backend = self.snapshot['backends'][name]
        check_files([backend['binary'], *backend['models']])
        value = f.backend_observation(live, backend['port'])
        f.need(
            all(value[k] == backend['observed'][k] for k in ('modelPath', 'contextPerSlot', 'totalSlots', 'health')),
            'restored_settings_mismatch',
        )
        if name == 'strata':
            f.need(
                self.host('/api/models')['loaded'] == self.snapshot['modelId']
                and self.host('/api/engine/status')['pid'] == live['pid'],
                'restored_host_not_owner',
            )
            f.need(f.settings() == self.snapshot['settings'], 'restored_host_settings_mismatch')

    def restore(self, name: str) -> None:
        end = time.monotonic() + 420
        backend = self.snapshot['backends'][name]
        check_files([backend['binary'], *backend['models']])
        # A lost unload/load reply can leave the Host in a transient state.
        # Reconcile for a bounded period before deciding whether a single load is needed.
        transition_end = time.monotonic() + 30
        while True:
            try:
                live = self.existing_backend(name)
                break
            except f.Blocked as error:
                if str(error) != 'host_transition_in_progress' or time.monotonic() >= transition_end:
                    raise
                time.sleep(1)
        if live is None:
            f.need(not f.listeners(backend['port']), 'restore_port_taken')
            if name == 'strata':
                # Tests are isolated. Never rewrite the user's state.json or adopt an
                # untracked Strata process to conceal a settings/ownership change.
                f.need(f.settings() == self.snapshot['settings'], 'restore_settings_changed')
                check_files(self.snapshot.get('hostFiles', []))
                f.need(self.host('/api/models')['loaded'] is None, 'unexpected_host_loaded_model')
                try:
                    self.host(
                        '/api/models/' + quote(self.snapshot['modelId'], safe='') + '/load',
                        method='POST',
                        body={},
                        timeout=130,
                    )
                except (OSError, f.Blocked):
                    # The Host may still be completing a timed-out load. Poll ownership;
                    # do not send a second load or start an untracked executable.
                    pass
            else:
                original = backend['process']
                f.require_independent_restore_lifetime()
                f.need(f.norm(original['exe']) == f.norm(f.HERMES), 'restore_exe_not_allowlisted')
                # Windows CreateProcess receives the exact captured command string and
                # an explicit executable. No shell, concatenation or PowerShell eval.
                with f.private_path('hermes-restore.log').open('ab') as log:
                    proc = subprocess.Popen(
                        original['commandLine'],
                        executable=original['exe'],
                        cwd=original['cwd'],
                        env=original['environment'],
                        shell=False,
                        stdin=subprocess.DEVNULL,
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    )
                    f.need(proc.pid > 0, 'hermes_launch_failed')
        last_code = 'restore_not_ready'
        while time.monotonic() < end:
            try:
                live = self.existing_backend(name)
                if live is not None:
                    self.verify_restored(name, live)
                    return
            except (OSError, ValueError, f.Blocked) as error:
                last_code = error_code(error)
            time.sleep(2)
        raise f.Blocked('restore_deadline_' + last_code)


def inspect_plan(snapshot: dict, manifest: dict | None) -> dict:
    blockers = list(snapshot.get('blockers', []))
    if manifest is None:
        blockers.append('candidate_044_not_frozen')
    else:
        try:
            check_files([*manifest['files'], *manifest['helpers'], *manifest['guards']])
        except Exception as error:
            blockers.append(error_code(error))
    if snapshot.get('watchers', {}).get('automaticRespawnUnresolved', True):
        blockers.append('watcher_readiness_unknown')
    try:
        counts = f.idle_counts(snapshot)
        if not counts['idle']:
            blockers.append('busy_or_unknown_activity')
        for name, value in counts['backends'].items():
            if 'admissionError' in value:
                blockers.append(name + '_admission_unavailable')
    except Exception as error:
        counts = None
        blockers.append(error_code(error))
    resources = f.resource_status()
    if not resources['ok']:
        blockers.append('resource_floor')
    try:
        f.require_independent_restore_lifetime()
    except Exception as error:
        blockers.append(error_code(error))
    return {
        'prepareOnly': True,
        'readiness': counts,
        'blockers': blockers,
        'routes': {
            'strata': 'owned Host POST /api/models/unload then /api/models/{saved-id}/load',
            'hermes': 'retained exact identity stop; explicit exe + private raw command, shell=False',
        },
        'floorsGiB': {'ram': 3, 'commit': 4, 'H': 10, 'C': 5},
        'resources': resources,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['plan', 'write-recipe', 'freeze', 'run', 'restore'], nargs='?', default='plan')
    parser.add_argument('--snapshot-name', default='snapshot.json')
    parser.add_argument('--snapshot-sha256')
    parser.add_argument('--manifest-sha256')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--parent-approved', action='store_true')
    parser.add_argument('--clients-quiesced', action='store_true')
    parser.add_argument('--report-name', help='Write a new sanitized plan receipt inside the private store')
    args = parser.parse_args()
    if args.mode == 'write-recipe':
        f.need(not args.execute, 'recipe_is_prepare_only')
        raw = sys.stdin.read(1024 * 1024 + 1)
        f.need(len(raw) <= 1024 * 1024, 'recipe_size_limit')
        recipe = json.loads(raw)
        validate_recipe(recipe)
        digest = f.write_private('candidate-recipe.json', recipe)
        logging.info(json.dumps({'recipeWritten': True, 'recipeSHA256': digest}))
        return 0
    if args.mode == 'freeze':
        f.need(not args.execute, 'freeze_is_prepare_only')
        logging.info(json.dumps(freeze()))
        return 0
    f.need(args.snapshot_sha256, 'snapshot_digest_required')
    snap = f.read_private(args.snapshot_name, args.snapshot_sha256)
    manifest = f.read_private('frozen-candidate.json', args.manifest_sha256) if args.manifest_sha256 else None
    if args.mode == 'plan' or not args.execute:
        report = inspect_plan(snap, manifest)
        if args.report_name:
            report['helperHashes'] = {Path(v['path']).name: v['sha256'] for v in helper_identities()}
            report['snapshotSHA256'] = args.snapshot_sha256
            digest = f.write_private(args.report_name, report)
            report['reportSHA256'] = digest
        logging.info(json.dumps(report))
        return 0
    f.need(args.parent_approved, 'parent_explicit_approval_required')
    ops = Operations(snap, manifest, args.manifest_sha256)
    with operation_lock():
        if args.mode == 'run':
            f.need(args.clients_quiesced, 'producers_must_be_quiesced')
            f.need(manifest is not None, 'candidate_not_frozen')
            ops.preflight()
            # A rejected plan does not consume the single-use claim. After claim,
            # failures require restoration/review, never an automatic rerun.
            f.write_private(
                'execution-claim.json',
                {
                    'snapshotName': args.snapshot_name,
                    'snapshotSHA256': args.snapshot_sha256,
                    'manifestSHA256': args.manifest_sha256,
                    'approvedByParent': True,
                    'clientsQuiesced': True,
                    'utc': f.utc(),
                },
            )
            journal = Journal('execution-journal.jsonl')
            try:
                report = run_window(ops, journal)
                journal.event('finished', **report)
                f.write_private('execution-result.json', report)
            finally:
                journal.close()
        else:
            claim = f.read_private('execution-claim.json')
            f.need(
                claim['snapshotSHA256'] == args.snapshot_sha256 and claim['snapshotName'] == args.snapshot_name,
                'restore_claim_mismatch',
            )
            f.need(snap.get('host') is not None, 'incomplete_snapshot_cannot_restore')
            records = [
                json.loads(line)
                for line in f.private_path('execution-journal.jsonl').read_text(encoding='utf-8').splitlines()
                if line.strip()
            ]
            f.need(any(r.get('phase') == 'stop_intent' for r in records), 'no_maintenance_stop_intent')
            restored = {}
            for name in ('hermes', 'strata'):
                try:
                    ops.restore(name)
                    restored[name] = True
                except Exception as error:
                    restored[name] = error_code(error)
            report = {'ok': all(v is True for v in restored.values()), 'restored': restored}
            f.write_private('recovery-' + str(time.time_ns()) + '.json', report)
        logging.info(json.dumps(report))
        return 0 if report['ok'] else 1


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        raise SystemExit(main())
    except Exception as error:
        logging.error(json.dumps({'ok': False, 'code': error_code(error)}))
        raise SystemExit(1) from None
