"""Preserve diagnostics, freeze reviewed source and generate new qualification adapters.

Default plan is read-only. Execution is only through the parent's owned runner.
Historical sources/adapters/artifacts are never rewritten.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

from native import BUILD, OUT, ROOT, inventory, require, sha

FROZEN = Path('H:/Strata/worktrees/native-055-source-20261110')
HISTORY = Path('H:/Strata/releases/upstream-0213-20261109-opencode')


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(root), *args], timeout=120).decode('utf-8').strip()


def checked_replace(text: str, old: str, new: str) -> str:
    require(text.count(old) == 1, 'Reviewed adapter anchor changed: ' + old)
    return text.replace(old, new)


def preserve(guard) -> None:
    target = OUT / 'native-diagnostic-pre055'
    require(BUILD.is_dir() and not target.exists(), 'Fresh diagnostic snapshot required')
    before = inventory(BUILD)
    require(shutil.disk_usage(OUT).free > sum(row['bytes'] for row in before.values()) + 10 * 1024**3, 'Keep unchanged H: floor')
    shutil.copytree(BUILD, target, copy_function=shutil.copy2)
    require(inventory(target) == before and inventory(BUILD) == before, 'Diagnostic snapshot changed bytes')
    guard.save(OUT / 'diagnostic-snapshot.json', {'files': len(before), 'bytes': sum(row['bytes'] for row in before.values()),
        'snapshot': str(target), 'inventory': before, 'allHashesMatched': True}, fresh=True)
    intake = ROOT / '_docs/2026-11-10_cuda13-98k-handover_Antigravity-to-Sol61.md'
    folder = OUT / 'intake'
    require(not folder.exists(), 'Preserve prior intake snapshots')
    folder.mkdir()
    shutil.copy2(intake, folder / intake.name)
    require(sha(intake) == sha(folder / intake.name), 'Intake snapshot differs')
    guard.save(OUT / 'intake-snapshot.json', {'path': str(intake), 'sha256': sha(intake),
        'status': 'user-supplied static analysis; independent corrections in repair log; not acceptance evidence'}, fresh=True)


def freeze(guard, commit: str) -> None:
    require(re.fullmatch(r'[0-9a-f]{40}', commit) and git(ROOT, 'rev-parse', 'HEAD') == commit, 'Reviewed source commit required')
    require(not git(ROOT, 'status', '--porcelain', '--untracked-files=all'), 'Commit reviewed source/evidence first')
    require(FROZEN.parent.is_dir() and not FROZEN.exists(), 'Fresh H: frozen checkout required')
    subprocess.run(['git', '-C', str(ROOT), 'worktree', 'add', '--detach', str(FROZEN), commit], check=True, timeout=180)
    tree = git(FROZEN, 'rev-parse', 'HEAD^{tree}')
    names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z'], timeout=30).decode('utf-8').split('\0')
    rows, overrides = {}, []
    for name in filter(None, names):
        source, target = ROOT / name, FROZEN / name
        require(source.is_file() and target.is_file() and not source.is_symlink() and not source.is_junction(), 'Unexpected tracked source kind')
        digest = sha(source)
        if sha(target) != digest:
            shutil.copy2(source, target)
            overrides.append(name)
        require(sha(target) == digest, 'Frozen physical bytes differ')
        rows[name] = digest
    subprocess.run(['git', '-C', str(FROZEN), 'add', '-u'], check=True, timeout=120)
    require(git(FROZEN, 'write-tree') == tree and not git(FROZEN, 'status', '--porcelain', '--untracked-files=all'), 'Physical-copy normalization changed Git source')
    guard.save(OUT / 'frozen-source.json', {'sourceCommit': commit, 'sourceRoot': str(FROZEN), 'tree': tree,
        'files': rows, 'physicalBytesMatched': True, 'normalizationOverrides': overrides}, fresh=True)


def adapters(guard, commit: str) -> None:
    require(git(FROZEN, 'rev-parse', 'HEAD') == commit and not git(FROZEN, 'status', '--porcelain'), 'Reviewed native freeze required')
    destination = OUT / 'adapters/native'
    require(not destination.exists(), 'Fresh native adapters required')
    outputs, provenance = {}, {}
    for name in ('adapter.py', 'common.py', 'phases.py', 'model.py', 'binding.mjs'):
        source = HISTORY / 'adapters/native-r2' / name
        raw = source.read_bytes()
        text = raw.decode('utf-8').replace('\r\n', '\n')
        text = text.replace('"control": "0.5.5"', '"control": "__CONTROL__"')
        text = text.replace(r'0\.5\.4', r'0\.5\.5').replace('0.5.4', '0.5.5').replace('__CONTROL__', '0.5.6')
        text = text.replace(HISTORY.as_posix(), OUT.as_posix())
        if name == 'common.py':
            text = checked_replace(text, '"-S", str(root)', '"-S", "' + ROOT.as_posix() + '"')
        if name == 'phases.py':
            text = checked_replace(text, '"CMAKE_HOME_DIRECTORY": str(root)', '"CMAKE_HOME_DIRECTORY": "' + ROOT.as_posix() + '"')
        if name.endswith('.py'):
            compile(text, str(destination / name), 'exec')
        outputs[name] = text
        provenance[name] = {'template': str(source), 'templateSHA256': hashlib.sha256(raw).hexdigest(), 'sha256': hashlib.sha256(text.encode()).hexdigest()}
    destination.mkdir(parents=True)
    for name, text in outputs.items():
        with (destination / name).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    guard.save(OUT / 'native-adapter-provenance.json', {'sourceCommit': commit, 'sourceRoot': str(FROZEN),
        'compilerSourceRoot': str(ROOT), 'jobs': 5, 'files': provenance, 'functionalResourceModelGatesRetained': True}, fresh=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'preserve', 'freeze', 'adapters'), nargs='?', default='plan')
    parser.add_argument('--commit')
    args = parser.parse_args()
    if args.action == 'plan':
        print(json.dumps({'execute': False, 'source': str(ROOT), 'freeze': str(FROZEN), 'out': str(OUT),
                          'jobs': 5, 'oldEvidencePreserved': True, 'releaseQualificationTransferred': False}))
        return 0
    spec = importlib.util.spec_from_file_location('prepare_repair_guard', ROOT / '_docs/local-053-20261109/native/common.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE = OUT
    guard.require_current_job(ROOT)
    if args.action == 'preserve':
        preserve(guard)
    else:
        require(bool(args.commit), 'Explicit reviewed commit required')
        {'freeze': freeze, 'adapters': adapters}[args.action](guard, args.commit)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
