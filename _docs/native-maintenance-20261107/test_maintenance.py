"""Offline mocks only: no server, model, GPU, scheduled-task action, or actual job execution."""

from __future__ import annotations

import io
import json
from pathlib import Path
import sys
from unittest.mock import Mock, patch

import pytest

import foundation as f
import maintenance as m
import candidate_guard as g


def operations(fail_at: str | None = None) -> tuple[Mock, list[str]]:
    calls: list[str] = []
    ops = Mock()
    for name in ('preflight', 'wait_idle', 'stop_strata', 'stop_hermes', 'run_candidate', 'cleanup_candidate'):

        def action(name: str = name) -> None:
            calls.append(name)
            if fail_at == name:
                raise f.Blocked('fixture_' + name)

        getattr(ops, name).side_effect = action

    def restore(name: str) -> None:
        calls.append('restore_' + name)
        if fail_at == 'restore_' + name:
            raise f.Blocked('fixture_restore')

    ops.restore.side_effect = restore
    return ops, calls


@pytest.mark.parametrize('at', ['preflight', 'wait_idle'])
def test_pre_stop_failure_never_mutates_or_restarts(at: str) -> None:
    ops, calls = operations(at)
    with pytest.raises(f.Blocked):
        m.run_window(ops, Mock())
    assert 'stop_strata' not in calls and not any(x.startswith('restore_') for x in calls)


@pytest.mark.parametrize('at', ['stop_strata', 'stop_hermes', 'run_candidate', 'cleanup_candidate'])
def test_any_uncertain_mutation_failure_attempts_both_restores(at: str) -> None:
    ops, calls = operations(at)
    journal = Mock()
    report = m.run_window(ops, journal)
    assert calls[-2:] == ['restore_hermes', 'restore_strata']
    assert calls.index('cleanup_candidate') < calls.index('restore_hermes')
    assert not report['ok']
    assert report['restored'] == {'hermes': True, 'strata': True}
    assert journal.event.call_args_list[0].args == ('stop_intent',)


def test_restore_failure_does_not_skip_other_service() -> None:
    ops, calls = operations('restore_hermes')
    result = m.run_window(ops, Mock())
    assert calls[-1] == 'restore_strata'
    assert result['restored'] == {'hermes': False, 'strata': True}
    assert not result['ok']


def test_success_requires_candidate_and_both_health_verifications() -> None:
    ops, calls = operations()
    result = m.run_window(ops, Mock())
    assert result['ok'] and result['candidatePassed']
    assert calls == [
        'preflight',
        'wait_idle',
        'stop_strata',
        'stop_hermes',
        'run_candidate',
        'cleanup_candidate',
        'restore_hermes',
        'restore_strata',
    ]


def test_keyboard_interrupt_uses_same_restore_path() -> None:
    ops, calls = operations()
    ops.run_candidate.side_effect = KeyboardInterrupt
    result = m.run_window(ops, Mock())
    assert result['error'] == 'KeyboardInterrupt'
    assert calls[-2:] == ['restore_hermes', 'restore_strata']


def test_full_disk_journal_failure_cannot_skip_either_restore() -> None:
    ops, calls = operations('run_candidate')
    journal = Mock()

    def event(phase: str, **unused: object) -> None:
        if phase.startswith('restore') or phase == 'window_failed':
            raise OSError('fixture disk full')

    journal.event.side_effect = event
    result = m.run_window(ops, journal)
    assert result['journalError'] is True
    assert calls[-2:] == ['restore_hermes', 'restore_strata']


def test_initial_intent_write_failure_never_stops_or_starts() -> None:
    ops, calls = operations()
    journal = Mock()
    journal.event.side_effect = OSError('fixture disk full')
    result = m.run_window(ops, journal)
    assert not result['ok']
    assert 'stop_strata' not in calls
    assert not any(c.startswith('restore_') for c in calls)


def test_hermes_replay_is_exact_createprocess_not_shell(tmp_path: Path) -> None:
    command = '"' + str(f.HERMES) + '" -m "H:\\fixture model.gguf" --api-key "$(fixture);&"'
    original = {
        'exe': str(f.HERMES),
        'commandLine': command,
        'cwd': str(tmp_path),
        'environment': {'FIXTURE': 'private'},
    }
    snap = {'backends': {'hermes': {'process': original, 'port': 8080, 'binary': {}, 'models': []}}}
    ops = m.Operations(snap)
    ops.existing_backend = Mock(side_effect=[None, original])
    ops.verify_restored = Mock()
    with patch.object(m, 'check_files'), patch.object(f, 'listeners', return_value=[]), patch.object(
        f, 'private_path', return_value=tmp_path / 'restore.log'
    ), patch.object(f, 'require_independent_restore_lifetime'), patch.object(m.subprocess, 'Popen') as launch:
        launch.return_value.pid = 999
        ops.restore('hermes')
    assert launch.call_args.args == (command,)
    assert launch.call_args.kwargs['executable'] == str(f.HERMES)
    assert launch.call_args.kwargs['shell'] is False
    assert launch.call_args.kwargs['env'] == original['environment']
    ops.verify_restored.assert_called_once_with('hermes', original)


def test_strata_restore_only_uses_real_owner_api() -> None:
    snap = {
        'modelId': 'fixture-model',
        'settings': {'fixture': True},
        'backends': {'strata': {'port': 8081, 'binary': {}, 'models': []}},
    }
    ops = m.Operations(snap)
    ops.existing_backend = Mock(side_effect=[None, {'pid': 99}])
    ops.verify_restored = Mock()
    ops.host = Mock(return_value={'loaded': None})
    with patch.object(m, 'check_files'), patch.object(f, 'listeners', return_value=[]), patch.object(
        f, 'settings', return_value=snap['settings']
    ), patch.object(m.subprocess, 'Popen') as launch:
        ops.restore('strata')
    launch.assert_not_called()
    assert ops.host.call_args_list[1].args == ('/api/models/fixture-model/load',)
    assert ops.host.call_args_list[1].kwargs['method'] == 'POST'


def test_three_idle_samples_are_required_without_any_stop() -> None:
    ops = m.Operations({})
    ops.preflight = Mock()
    idle = {'idle': True, 'backends': {'hermes': {}}}
    with patch.object(
        f, 'idle_counts', side_effect=[{**idle, 'idle': False}, idle, idle, idle]
    ) as sample, patch.object(m.time, 'sleep'):
        ops.wait_idle()
    assert sample.call_count == 4
    ops.preflight.assert_called_once()


@pytest.mark.parametrize(
    'ram,commit,c,h,ok',
    [
        (3, 4, 5, 10, True),
        (2.99, 4, 5, 10, False),
        (3, 3.99, 5, 10, False),
        (3, 4, 4.99, 10, False),
        (3, 4, 5, 9.99, False),
    ],
)
def test_exact_resource_floors(ram: float, commit: float, c: float, h: float, ok: bool) -> None:
    memory = {'available_physical_bytes': int(ram * f.GIB), 'available_commit_bytes': int(commit * f.GIB)}

    def disk(path: str) -> Mock:
        return Mock(free=int((c if path.startswith('C') else h) * f.GIB))

    with patch.object(f, 'available_memory', return_value=memory), patch.object(
        f.shutil, 'disk_usage', side_effect=disk
    ):
        assert f.resource_status()['ok'] is ok


@pytest.mark.parametrize('value', [None, {}, [], [{'state': 0}], [{'is_processing': 0}]])
def test_unknown_slots_never_equal_idle(value: object) -> None:
    with pytest.raises(f.Blocked):
        f.slot_counts(value)


def test_slot_prompts_are_never_returned() -> None:
    result = f.slot_counts([{'is_processing': True, 'prompt': 'SECRET_PROMPT'}, {'is_processing': False}])
    assert result == {'slots': 2, 'active': 1}
    assert 'SECRET' not in json.dumps(result)


@pytest.mark.parametrize(
    'metrics',
    [
        '',
        'llamacpp:requests_processing 0\n',
        'llamacpp:requests_processing NaN\nllamacpp:requests_deferred 0',
        'llamacpp:requests_processing 0\nllamacpp:requests_deferred -1',
    ],
)
def test_missing_admission_never_defaults_to_zero(metrics: str) -> None:
    with pytest.raises(f.Blocked):
        f.metric_counts(metrics)


def test_real_admission_counters() -> None:
    assert f.metric_counts('llamacpp:requests_processing 2\nllamacpp:requests_deferred 3\n') == {
        'requests_processing': 2,
        'requests_deferred': 3,
    }


@pytest.mark.parametrize('owners', [[('0.0.0.0', 1)], [('127.0.0.1', 2)], [('127.0.0.1', 1), ('::', 1)], []])
def test_listener_must_be_exact_loopback_and_pid(owners: list) -> None:
    with patch.object(f, 'IdentityHandle') as handle, patch.object(f, 'listeners', return_value=owners):
        handle.return_value.__enter__.return_value = Mock()
        with pytest.raises(f.Blocked, match='listener_not_exact_loopback_owner'):
            f.bind_owner({'pid': 1}, 8080)


def test_identity_rejects_pid_reuse_even_same_exe() -> None:
    handle = object.__new__(f.IdentityHandle)
    handle.created, handle.exe = 100, 'C:/fixture.exe'
    handle.alive = lambda: True
    with pytest.raises(f.Blocked, match='process_identity_changed'):
        handle.verify({'creationFiletime': 101, 'exe': 'C:/fixture.exe'})


def test_http_redirect_cannot_send_key_elsewhere() -> None:
    conn = Mock()
    conn.getresponse.return_value.status = 302
    conn.getresponse.return_value.read.return_value = b'private response'
    with patch.object(f, 'bind_owner'), patch.object(f.http.client, 'HTTPConnection', return_value=conn) as factory:
        with pytest.raises(f.Blocked, match='local_http_status_302'):
            f.request({'pid': 1}, 8080, '/props', key='fixture-secret')
        factory.assert_called_once_with('127.0.0.1', 8080, timeout=5)
        assert conn.request.call_count == 1


def test_unknown_backend_metrics_blocks_idle_even_when_slots_empty() -> None:
    snapshot = {
        'host': {'process': {}, 'port': 1234},
        'backends': {
            'hermes': {
                'process': {},
                'port': 8080,
                'observed': {'modelPath': 'fixture', 'contextPerSlot': 8, 'totalSlots': 1},
            }
        },
    }
    observed = {
        'modelPath': 'fixture',
        'contextPerSlot': 8,
        'totalSlots': 1,
        'activity': {'slots': 1, 'active': 0, 'requests_processing': None, 'requests_deferred': None},
    }
    with patch.object(f, 'host_activity', return_value={'activeTurns': 0, 'running': 0, 'waiting': 0}), patch.object(
        f, 'backend_observation', return_value=observed
    ):
        assert f.idle_counts(snapshot)['idle'] is False


def test_default_run_cli_cannot_mutate() -> None:
    with patch.object(sys, 'argv', ['maintenance.py', 'run', '--snapshot-sha256', 'fixture']), patch.object(
        f, 'read_private', return_value={}
    ), patch.object(m, 'inspect_plan', return_value={}), patch.object(m, 'Operations') as ops:
        assert m.main() == 0
        ops.assert_not_called()


def test_execute_without_parent_approval_is_rejected() -> None:
    with patch.object(
        sys, 'argv', ['maintenance.py', 'run', '--execute', '--snapshot-sha256', 'fixture']
    ), patch.object(f, 'read_private', return_value={}), patch.object(m, 'Operations') as ops:
        with pytest.raises(f.Blocked, match='parent_explicit_approval_required'):
            m.main()
        ops.assert_not_called()


def test_private_write_never_overwrites_snapshot(tmp_path: Path) -> None:
    dest = tmp_path / 'fixture.json'
    dest.write_text('original')
    with patch.object(f, 'private_path', return_value=dest), patch.object(f, 'private_acl'):
        with pytest.raises(FileExistsError):
            f.write_private('fixture.json', {'replace': True})
    assert dest.read_text() == 'original'


def test_tampered_snapshot_refused_before_parsing(tmp_path: Path) -> None:
    dest = tmp_path / 'fixture.json'
    dest.write_text('{not json')
    with patch.object(f, 'private_path', return_value=dest):
        with pytest.raises(f.Blocked, match='private_digest_mismatch'):
            f.read_private('fixture.json', '0' * 64)


def test_pinned_model_mtime_and_size_are_checked() -> None:
    identity = {'path': 'H:/fixture.gguf', 'size': 10, 'mtimeNs': 50}
    with patch.object(f, 'file_identity', return_value={**identity, 'mtimeNs': 51}):
        with pytest.raises(f.Blocked, match='pinned_file_changed'):
            m.check_files([identity])


def test_guard_containment_failure_never_releases_handshake(tmp_path: Path) -> None:
    process = Mock()
    process.poll.return_value = None
    fake_job = Mock()
    fake_job.contain.return_value = False
    # Prevent importing winjob (which opts the caller out of power throttling).
    with patch.dict(sys.modules, {'serve.winjob': fake_job}), patch.object(
        g.subprocess, 'Popen', return_value=process
    ), patch.object(f, 'resource_status', return_value={'ok': True}), patch.object(
        f, 'private_path', return_value=tmp_path / 'private.log'
    ), patch.object(
        f, 'write_private'
    ):
        result = g.bounded_steps({'files': [], 'steps': [{'argv': ['fixture.exe'], 'cwd': str(tmp_path)}]})
    assert result['abort'] == 'candidate_containment_failed'
    process.stdin.write.assert_not_called()
    process.kill.assert_called_once()
    fake_job.terminate.assert_called_once()


def test_guard_deadline_kills_only_owned_job(tmp_path: Path) -> None:
    process = Mock()
    process.poll.return_value = None
    process.stdin = io.BytesIO()
    fake_job = Mock()
    fake_job.contain.return_value = True
    with patch.dict(sys.modules, {'serve.winjob': fake_job}), patch.object(
        g.subprocess, 'Popen', return_value=process
    ), patch.object(g.time, 'monotonic', side_effect=[0, 0, 3, 3]), patch.object(
        f, 'resource_status', return_value={'ok': True}
    ), patch.object(
        f, 'private_path', return_value=tmp_path / 'private.log'
    ), patch.object(
        f, 'write_private'
    ):
        result = g.bounded_steps(
            {
                'files': [],
                'windowSeconds': 2,
                'steps': [{'argv': ['fixture.exe'], 'cwd': str(tmp_path), 'timeoutSeconds': 2}],
            }
        )
    assert result['abort'] == 'candidate_timeout'
    fake_job.terminate.assert_called_once()
    process.kill.assert_called_once()


def test_exception_text_never_exposes_credentials() -> None:
    assert m.error_code(RuntimeError('raw-secret-command')) == 'RuntimeError'


def test_guard_cannot_report_success_if_job_cleanup_fails(tmp_path: Path) -> None:
    process = Mock()
    process.poll.return_value = 0
    process.returncode = 0
    fake_job = Mock()
    fake_job.contain.return_value = True
    fake_job.terminate.return_value = False
    with patch.dict(sys.modules, {'serve.winjob': fake_job}), patch.object(
        g.subprocess, 'Popen', return_value=process
    ), patch.object(f, 'resource_status', return_value={'ok': True}), patch.object(
        f, 'private_path', return_value=tmp_path / 'private.log'
    ), patch.object(
        f, 'write_private'
    ):
        result = g.bounded_steps({'files': [], 'steps': [{'argv': ['fixture.exe'], 'cwd': str(tmp_path)}]})
    assert result['ok'] is False
    assert result['abort'] == 'candidate_job_cleanup_failed'


def test_duplicate_hermes_is_not_killed_or_relaunched() -> None:
    ops = m.Operations({'backends': {'hermes': {'process': {'exe': str(f.HERMES)}}}})
    with patch.object(f, 'inventory', return_value=[{'exe': str(f.HERMES)}, {'exe': str(f.HERMES)}]):
        with pytest.raises(f.Blocked, match='duplicate_server_no_deduplication'):
            ops.existing_backend('hermes')


@pytest.mark.parametrize(
    'exe,args,code',
    [
        ('powershell.exe', ['-Command', 'fixture'], 'powershell_file_only'),
        ('cmd.exe', ['/c', 'fixture'], 'command_interpreter_rejected'),
        ('python.exe', ['-c', 'fixture'], 'interpreter_script_not_pinned'),
    ],
)
def test_candidate_shell_code_rejected(exe: str, args: list[str], code: str) -> None:
    root = 'H:/Strata/worktrees/fixture-candidate-044'
    program = 'C:/fixture/' + exe
    recipe = {
        'schema': 1,
        'candidate': '044',
        'candidateRoot': root,
        'originalHostUntouched': True,
        'noInstall': True,
        'windowSeconds': 30,
        'files': [program],
        'steps': [{'argv': [program, *args], 'cwd': root, 'timeoutSeconds': 30}],
    }
    with patch.object(Path, 'is_dir', return_value=True), patch.object(Path, 'is_file', return_value=True):
        with pytest.raises(f.Blocked, match=code):
            m.validate_recipe(recipe)
