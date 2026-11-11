"""Inventory old registered worktrees; remove only clean, inactive, archived trees."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import psutil

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-058-20261111-codex/cleanup')
PROTECTED = {ROOT.resolve(), Path('H:/Strata/worktrees/native-055-source-20261110').resolve()}
PARENTS = [Path('H:/Strata/worktrees').resolve(), Path('C:/Users/downl/.codex/worktrees').resolve(), ROOT.parent.resolve()]

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-C', str(cwd), *args], timeout=180).decode('utf-8').strip()

def allowed(path):
    resolved = path.resolve()
    return path.is_absolute() and resolved not in PROTECTED and any(resolved.is_relative_to(parent) and resolved != parent for parent in PARENTS) and not path.is_symlink() and not path.is_junction()

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def active_paths():
    result = []
    for process in psutil.process_iter(['cwd', 'exe']):
        for name in ('cwd', 'exe'):
            value = process.info.get(name)
            if value:
                result.append(Path(value).resolve())
    return result

def inventory():
    entries = []
    for block in git('worktree', 'list', '--porcelain').split('\n\n'):
        lines = block.splitlines()
        if not lines:
            continue
        path = Path(lines[0].removeprefix('worktree '))
        commit = next((line[5:] for line in lines if line.startswith('HEAD ')), None)
        entries.append({'path': str(path), 'commit': commit, 'exists': path.exists()})
    active = active_paths()
    def examine(entry):
        path = Path(entry['path'])
        entry['allowed'] = allowed(path) if path.exists() else False
        entry['active'] = any(p == path.resolve() or p.is_relative_to(path.resolve()) for p in active)
        entry['clean'] = path.exists() and not git('status', '--porcelain', '--untracked-files=all', cwd=path)
        total = 0
        if path.exists():
            for directory, dirs, names in os.walk(path, followlinks=False):
                dirs[:] = [name for name in dirs if not (Path(directory) / name).is_junction() and not (Path(directory) / name).is_symlink()]
                for name in names:
                    try:
                        total += (Path(directory) / name).stat().st_size
                    except OSError:
                        pass
        entry['bytes'] = total
        entry['candidate'] = entry['allowed'] and entry['clean'] and not entry['active']
        return entry
    with ThreadPoolExecutor(max_workers=5) as pool:
        entries = list(pool.map(examine, entries))
    OUT.mkdir(parents=True, exist_ok=True)
    plan = {'worktrees': entries, 'HFreeBefore': psutil.disk_usage('H:/').free, 'CFreeBefore': psutil.disk_usage('C:/').free}
    target = OUT / 'worktrees-plan.json'
    with target.open('x', encoding='utf-8') as stream:
        json.dump(plan, stream, indent=2)
    print(json.dumps({'plan': str(target), 'sha256': sha(target), 'worktrees': entries}, indent=2))

def execute(expected):
    plan_path = OUT / 'worktrees-plan.json'
    assert sha(plan_path) == expected, 'Reviewed cleanup plan changed'
    plan = json.loads(plan_path.read_text())
    archives = OUT / 'source-archives'
    archives.mkdir()
    removed = []
    for entry in plan['worktrees']:
        if not entry['candidate']:
            continue
        path = Path(entry['path'])
        assert allowed(path) and git('rev-parse', 'HEAD', cwd=path) == entry['commit']
        assert not git('status', '--porcelain', '--untracked-files=all', cwd=path), 'Preserve new work'
        assert not any(p == path.resolve() or p.is_relative_to(path.resolve()) for p in active_paths()), 'Preserve active worktree'
        archive = archives / (path.name + '-' + entry['commit'][:12] + '.tar')
        assert not archive.exists()
        subprocess.run(['git', '-C', str(path), 'archive', '--format=tar', '-o', str(archive), entry['commit']], check=True, timeout=180)
        assert archive.stat().st_size > 0
        with archive.open('rb') as stream:
            archived_commit = subprocess.check_output(['git', 'get-tar-commit-id'], stdin=stream, cwd=ROOT, timeout=30).decode().strip()
        assert archived_commit == entry['commit'], 'Source archive commit identity differs'
        ref = 'refs/archive/strata-cleanup-058/' + path.name
        subprocess.run(['git', '-C', str(ROOT), 'update-ref', ref, entry['commit'], '0' * 40], check=True, timeout=30)
        # The archive holds tracked source; branch refs and immutable release
        # objects are retained. No --force: Git must independently accept removal.
        subprocess.run(['git', '-C', str(ROOT), 'worktree', 'remove', str(path)], check=True, timeout=300)
        removed.append({**entry, 'archive': str(archive), 'archiveSHA256': sha(archive), 'retainedLocalRef': ref})
        with (OUT / 'removed-worktrees.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(removed[-1]) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps({'removed': str(path), 'archivedCommit': entry['commit']}), flush=True)
    result = {'removed': removed, 'HFreeAfter': psutil.disk_usage('H:/').free, 'CFreeAfter': psutil.disk_usage('C:/').free}
    with (OUT / 'worktrees-removed.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--execute-plan-sha256')
args = parser.parse_args()
if args.execute_plan_sha256:
    execute(args.execute_plan_sha256)
else:
    inventory()
