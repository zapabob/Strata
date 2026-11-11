"""Create source-bound 0.5.8 native/Control adapters from retained successful recipes."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-058-20261111-codex')
OLD = Path('H:/Strata/releases/repair-055-20261110-opencode')
FROZEN = Path('H:/Strata/worktrees/native-058-source-20261111')
BUILD = OUT / 'native-build'
OLD_COMMIT = 'b995af139cc823537489b886bc1e8602cf10301c'

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-C', str(cwd), *args], timeout=180).decode('utf-8').strip()

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)

def freeze(commit):
    assert git('rev-parse', 'HEAD') == commit and not git('status', '--porcelain', '--untracked-files=all')
    assert not FROZEN.exists() and FROZEN.parent.resolve() == Path('H:/Strata/worktrees').resolve()
    subprocess.run(['git', '-C', str(ROOT), 'worktree', 'add', '--detach', str(FROZEN), commit], check=True, timeout=180)
    tree = git('rev-parse', 'HEAD^{tree}', cwd=FROZEN)
    names = git('ls-files', '-z').split('\0')
    rows, overrides = {}, []
    for name in filter(None, names):
        source, target = ROOT / name, FROZEN / name
        assert source.is_file() and target.is_file() and not source.is_symlink() and not source.is_junction()
        checksum = sha(source)
        if sha(target) != checksum:
            shutil.copy2(source, target)
            overrides.append(name)
        assert sha(target) == checksum
        rows[name] = checksum
    subprocess.run(['git', '-C', str(FROZEN), 'add', '-u'], check=True, timeout=180)
    assert git('write-tree', cwd=FROZEN) == tree and not git('status', '--porcelain', '--untracked-files=all', cwd=FROZEN)
    save(OUT / 'frozen-source.json', {'sourceCommit': commit, 'sourceRoot': str(FROZEN), 'tree': tree,
        'files': rows, 'physicalBytesMatched': True, 'normalizationOverrides': overrides})

def adapters(commit):
    groups = {
        'native': OLD / 'adapters/native',
        'component': OLD / 'adapters/delivery-ui-search-r1/component',
        'app': OLD / 'adapters/delivery-ui-search-r1/app',
    }
    provenance = {}
    for group, source in groups.items():
        destination = OUT / 'adapters' / group
        destination.mkdir(parents=True)
        for path in source.iterdir():
            if path.suffix not in ('.py', '.mjs'):
                continue
            text = path.read_text(encoding='utf-8').replace(OLD.as_posix(), OUT.as_posix())
            text = text.replace('0.5.5-local.1', '0.5.8').replace('0.5.6', '0.5.8').replace('0.5.5', '0.5.8').replace(r'0\.5\.5', r'0\.5\.8')
            text = text.replace('native-055-source-20261110', FROZEN.name).replace(OLD_COMMIT, commit)
            text = text.replace('app-native055-ui-search', 'app-058-components').replace('component-055-ui-search', 'component-058')
            text = text.replace('component-staging-055-ui-search', 'component-staging-058').replace('control-staging-055-ui-search', 'control-staging-058')
            if group == 'native' and path.name == 'common.py':
                text = text.replace('CMAKE_BUILD_PARALLEL_LEVEL="4"', 'CMAKE_BUILD_PARALLEL_LEVEL="5"')
            if group == 'native' and path.name == 'phases.py':
                old = 'require(not BUILD.exists() and not any(NATIVE.iterdir()), "Fresh build/native outputs required")'
                assert text.count(old) == 1
                text = text.replace(old, 'require(BUILD.is_dir() and (BASE.parent / "native-seed.json").is_file() and not any(NATIVE.iterdir()), "Fresh verified seed/native outputs required")')
            if path.suffix == '.py':
                compile(text, str(destination / path.name), 'exec')
            (destination / path.name).write_text(text, encoding='utf-8', newline='\n')
            provenance[group + '/' + path.name] = {'template': str(path), 'templateSHA256': sha(path), 'sha256': sha(destination / path.name)}
    gpu_source = ROOT / '_docs/repair-055-20261110/gpu.py'
    text = gpu_source.read_text(encoding='utf-8').replace(OLD.as_posix(), OUT.as_posix())
    text = text.replace('ROOT = Path(__file__).resolve().parents[2]', 'ROOT = Path(' + repr(ROOT.as_posix()) + ')')
    gpu_target = OUT / 'adapters/gpu.py'
    gpu_target.write_text(text, encoding='utf-8', newline='\n')
    provenance['gpu.py'] = {'template': str(gpu_source), 'templateSHA256': sha(gpu_source), 'sha256': sha(gpu_target)}
    (OUT / 'app-058-components').mkdir()
    save(OUT / 'adapter-provenance.json', {'sourceCommit': commit, 'compilerSourceRoot': str(ROOT),
        'frozenSourceRoot': str(FROZEN), 'jobs': 5, 'retainedGates': True, 'files': provenance})

def inventory(root):
    paths = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            path = Path(directory) / name
            assert not path.is_symlink() and not path.is_junction(), 'Linked cache refused'
        paths.extend(Path(directory) / name for name in names)
    with ThreadPoolExecutor(max_workers=5) as pool:
        hashes = list(pool.map(sha, paths))
    return {path.relative_to(root).as_posix(): {'bytes': path.stat().st_size, 'sha256': digest} for path, digest in zip(paths, hashes)}

def seed():
    source = OLD / 'native-build'
    assert source.is_dir() and not BUILD.exists() and (OUT / 'native-evidence/freeze.json').is_file()
    before = inventory(source)
    assert shutil.disk_usage(OUT).free > sum(row['bytes'] for row in before.values()) + 10 * 1024**3
    shutil.copytree(source, BUILD, copy_function=shutil.copy2)
    assert inventory(BUILD) == before and inventory(source) == before
    (BUILD / 'CMakeCache.txt').rename(BUILD / 'CMakeCache.pre-058.txt')
    save(OUT / 'native-seed.json', {'source': str(source), 'target': str(BUILD), 'files': before,
        'allHashesMatched': True, 'newBuildMustReconfigureAndRebind': True})

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=('plan', 'prepare', 'seed'), nargs='?', default='plan')
parser.add_argument('--commit')
args = parser.parse_args()
if args.action == 'prepare':
    assert re.fullmatch('[0-9a-f]{40}', args.commit or '')
    freeze(args.commit)
    adapters(args.commit)
elif args.action == 'seed':
    seed()
else:
    print(json.dumps({'execute': False, 'versions': ['0.5.8'] * 4, 'frozen': str(FROZEN), 'cache': str(OLD / 'native-build'), 'target': str(BUILD), 'jobs': 5}))
