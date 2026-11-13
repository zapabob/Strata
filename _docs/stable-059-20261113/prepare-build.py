"""Freeze 0.5.9 and adapt the retained successful 0.5.8 build recipes without copying results."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-059-20261113-codex')
OLD = Path('H:/Strata/releases/stable-058-20261111-codex')
FROZEN = Path('H:/Strata/worktrees/native-059-source-20261113')

def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(['git', '-C', str(cwd), *args], timeout=180).decode().strip()

def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def save(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)

def prepare(commit: str) -> None:
    assert git('rev-parse', 'HEAD') == commit and not git('status', '--porcelain')
    assert not FROZEN.exists() and FROZEN.parent.resolve() == Path('H:/Strata/worktrees').resolve()
    subprocess.run(['git', '-C', str(ROOT), 'worktree', 'add', '--detach', str(FROZEN), commit], check=True, timeout=180)
    rows = {}
    tree = git('rev-parse', 'HEAD^{tree}')
    for name in git('ls-files', '-z').split('\0'):
        if not name:
            continue
        source, target = ROOT / name, FROZEN / name
        assert source.is_file() and target.is_file() and not source.is_symlink() and not source.is_junction()
        checksum = sha(source)
        if sha(target) != checksum:
            shutil.copy2(source, target)
        assert sha(target) == checksum
        rows[name] = checksum
    subprocess.run(['git', '-C', str(FROZEN), 'add', '-u'], check=True, timeout=180)
    assert git('write-tree', cwd=FROZEN) == tree and not git('status', '--porcelain', cwd=FROZEN)
    save(OUT / 'frozen-source.json', {'sourceCommit': commit, 'sourceRoot': str(FROZEN), 'tree': tree, 'files': rows, 'physicalBytesMatched': True})
    provenance = {}
    for group in ('native-r2', 'component-r2', 'app-control-r2'):
        source = OLD / 'adapters' / group
        target = OUT / 'adapters' / group
        target.mkdir(parents=True)
        for path in source.iterdir():
            if path.suffix not in ('.py', '.mjs'):
                continue
            text = path.read_text(encoding='utf-8')
            text = text.replace('stable-058-20261111', 'stable-059-20261113').replace('native-058-source-20261111', FROZEN.name)
            text = text.replace('0.5.8', '0.5.9').replace(r'0\.5\.8', r'0\.5\.9').replace('app-058-', 'app-059-').replace('component-058', 'component-059').replace('staging-058', 'staging-059')
            text = text.replace('c629ee37dde049b09bc42bdc00b076906f44fa27', commit)
            if path.suffix == '.py':
                compile(text, str(target / path.name), 'exec')
            (target / path.name).write_text(text, encoding='utf-8', newline='\n')
            provenance[group + '/' + path.name] = {'template': str(path), 'templateSHA256': sha(path), 'sha256': sha(target / path.name)}
    (OUT / 'app-059-components').mkdir()
    save(OUT / 'adapter-provenance.json', {'sourceCommit': commit, 'files': provenance, 'jobs': 5, 'historicalResultsCopied': False})

def seed() -> None:
    source, target = OLD / 'native-build', OUT / 'native-build'
    assert source.is_dir() and not target.exists() and (OUT / 'native-evidence-r2/freeze.json').is_file()
    paths = [p for p in source.rglob('*') if p.is_file()]
    assert all(not p.is_symlink() and not p.is_junction() for p in source.rglob('*'))
    assert shutil.disk_usage(OUT).free > sum(p.stat().st_size for p in paths) + 10 * 1024**3
    with ThreadPoolExecutor(max_workers=5) as pool:
        before = dict(zip((p.relative_to(source).as_posix() for p in paths), pool.map(sha, paths)))
    shutil.copytree(source, target)
    assert all(sha(target / name) == checksum == sha(source / name) for name, checksum in before.items())
    (target / 'CMakeCache.txt').rename(target / 'CMakeCache.pre-059.txt')
    save(OUT / 'native-seed.json', {'source': str(source), 'target': str(target), 'allHashesMatched': True, 'files': before, 'newBuildMustReconfigureAndRebind': True})

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=['plan', 'prepare', 'seed'], default='plan', nargs='?')
parser.add_argument('--commit')
args = parser.parse_args()
if args.action == 'prepare':
    prepare(args.commit)
elif args.action == 'seed':
    seed()
else:
    print(json.dumps({'execute': False, 'out': str(OUT), 'frozen': str(FROZEN), 'jobs': 5}))
