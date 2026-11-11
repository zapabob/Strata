"""Bind later CI-only repairs to the unchanged, already-built and installed app sources."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-058-20261111-codex')
APP = Path('C:/Users/downl/AppData/Local/Programs/Strata')

def verify(ci_commit, app_commit):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, timeout=60)
    assert git('rev-parse', 'HEAD').decode().strip() == ci_commit
    assert not git('status', '--porcelain')
    subprocess.run(['git', 'merge-base', '--is-ancestor', app_commit, ci_commit], cwd=ROOT, check=True)
    names = [name for name in git('diff', '--no-renames', '--name-only', '-z', app_commit, ci_commit).decode().split('\0') if name]
    def unshipped(name):
        return (name.startswith(('_docs/', 'tests/', 'apps/host/tests/'))
                or name in ('apps/host/scripts/test.mjs', 'apps/host/scripts/test-fs-guard.mjs',
                            'apps/host/scripts/test-environment.mjs', 'tools/conftest.py',
                            'tools/perf131k/windows_job.py')
                or name.startswith('tools/test_') and name.endswith('.py')
                or name.startswith('.github/workflows/') and name.endswith(('.yml', '.yaml')))
    assert all(unshipped(name) for name in names), 'A distributed runtime/build input changed; rebuild the app'
    changes = {}
    for name in names:
        values = []
        for commit in (app_commit, ci_commit):
            run = subprocess.run(['git', 'show', commit + ':' + name], cwd=ROOT, capture_output=True)
            values.append(hashlib.sha256(run.stdout).hexdigest() if run.returncode == 0 else None)
        changes[name] = {'builtSourceSHA256': values[0], 'validatedSourceSHA256': values[1]}
    guard = 'tools/perf131k/windows_job.py'
    if guard in names:
        old = git('show', app_commit + ':' + guard).decode()
        new = git('show', ci_commit + ':' + guard).decode()
        declaration = ('# Production storage policy. CPU fixtures may select their own private scratch\n'
                       '# volume through monkeypatch without changing the default H: admission rule.\n'
                       'BOUNDED_STDIN_VOLUME = "H:"\n\n\n')
        assert new.count(declaration) == 1
        expanded = new.replace(declaration, '').replace('!= BOUNDED_STDIN_VOLUME', '!= "H:"')
        assert expanded == old, 'The guard changed beyond its unchanged default-volume constant'
        for base in (ROOT / 'apps/desktop/src-tauri/resources/control', APP / 'control'):
            assert not (base / guard).exists(), 'Guard is now distributed; rebuild Control'
        native = json.loads((ROOT / 'apps/desktop/src-tauri/resources/engine-bundle/0.5.8-windows-x86_64-cuda-cuda13/engine-component.json').read_text())
        assert all(row['path'] != guard for row in native['files'])
    node = ROOT / 'apps/desktop/src-tauri/resources/node/node.exe'
    for helper, arguments in [('source-binding.mjs', ['H:/Strata/worktrees/native-058-source-20261111', 'c629ee37dde049b09bc42bdc00b076906f44fa27']),
                              ('control-binding.mjs', [])]:
        subprocess.run([str(node), str(Path(__file__).with_name(helper)), *arguments], cwd=ROOT,
                       stdout=subprocess.DEVNULL, check=True, timeout=120)
    code = "import{verifyTree}from './apps/host/scripts/release-integrity.mjs';verifyTree('./apps/host/server','C:/Users/downl/AppData/Local/Programs/Strata/host/server');"
    subprocess.run([str(node), '--input-type=module', '-e', code], cwd=ROOT, check=True, timeout=120)
    build = json.loads((OUT / 'app-build.json').read_text())
    assert build['sourceCommit'] == app_commit
    with Path(build['installer']).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == build['installerSHA256']
    return {'ok': True, 'appSourceCommit': app_commit, 'validatedSourceCommit': ci_commit,
            'distributedRuntimeSourcesUnchanged': True, 'installedHostSourcesMatch': True,
            'nativeAndControlSourceBindingsPassed': True, 'installerSHA256': build['installerSHA256'],
            'onlyUnshippedChanges': changes, 'defaultGuardPolicyByteIdenticalAfterConstantExpansion': True}

if __name__ == '__main__':
    print(json.dumps(verify(*sys.argv[1:3]), indent=2))
