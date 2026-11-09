"""Candidate-local constants and gates; historical helpers remain read-only inputs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HISTORY = ROOT / '_docs/personal-install-20261107'
RUNTIME = Path('H:/Strata/releases/personal-052-local2-20261107/app/execution-20261108')
BASE = Path('H:/Strata/releases/local-053-20261109-opencode')
OUT = BASE / 'app'
PRODUCT, CONTROL, ENGINE = '0.5.3-local.1', '0.5.4', '0.5.3'
RESOURCES = ROOT / 'apps/desktop/src-tauri/resources'
SIGNED = RESOURCES / 'engine-bundle/0.5.3-windows-x86_64-cuda-cuda13'
INSTALLED = Path('C:/Users/downl/AppData/Local/Programs/Strata')
NODE = INSTALLED / 'node/node.exe'
PYTHON = Path('C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe')
UV = Path('C:/Users/downl/.local/bin/uv.exe')
CARGO_TARGET = Path('H:/Strata/releases/local-052-20261106-opencode/cargo-target')
PUBLIC_ASSETS = Path('H:/Strata/releases/hakua033-public-assets')
PUBLIC_RECEIPT = Path('H:/Strata/releases/hakua033-public-assets.receipt.json')
MODEL = Path('H:/Strata/models/qwen36-UD-Q4_K_XL/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf')
TOKENIZER = Path('H:/Strata/models/packs/qwen36-ud-q4_k_xl/tokenizer')
USER_GGUF = Path('H:/Strata/models/新しいフォルダー/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf')
USER_GGUF_SHA = '8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949'
PRISM_MANIFEST_SHA = '9c729c73eb050dc466203fe149a27acd5be48763a33ea2c5d2b89f78e4ddcbaa'
PRISM_EXE_SHA = '5ca5d8bfdfcb6fe46a96a06b71eaf45aedfbd1c6673bda2a10eb6412613be777'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_new(path: Path, value: dict) -> None:
    require(path.parent.is_dir(), 'Receipt parent absent')
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def inventory(root: Path) -> dict[str, str]:
    require(root.is_dir() and not root.is_symlink() and not root.is_junction(), 'Invalid tree')
    result = {}
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs + names):
            path = Path(directory) / name
            require(not path.is_symlink() and not path.is_junction(), 'Linked input refused')
            if path.is_file():
                result[path.relative_to(root).as_posix()] = sha(path)
    return dict(sorted(result.items()))


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True, timeout=30).strip()


def approved_source(commit: str | None) -> str:
    require(bool(re.fullmatch('[0-9a-f]{40}', commit or '')), 'Full reviewed commit required')
    require(git('rev-parse', 'HEAD') == commit, 'Reviewed source differs from HEAD')
    require(not git('diff', 'HEAD', '--name-only') and not git('ls-files', '--others', '--exclude-standard'), 'Parent must freeze complete source')
    require((ROOT / 'VERSION').read_text().strip() == PRODUCT, 'Product version differs')
    require((ROOT / 'CONTROL_VERSION').read_text().strip() == CONTROL, 'Control version differs')
    return commit


def resources() -> dict:
    sys.path.insert(0, str(ROOT / 'tools'))
    from native_model_resource_guard import available_memory
    sample = available_memory()
    return dict(ramBytes=sample['available_physical_bytes'], commitBytes=sample['available_commit_bytes'],
                cFreeBytes=shutil.disk_usage('C:/').free, hFreeBytes=shutil.disk_usage('H:/').free)


def blockers(sample: dict) -> list[str]:
    return [label for key, floor, label in [('ramBytes', 3, 'RAM<3GiB'), ('commitBytes', 4, 'commit<4GiB'),
            ('cFreeBytes', 5, 'C<5GiB'), ('hFreeBytes', 10, 'H<10GiB')] if sample[key] < floor * 1024**3]


def require_resources() -> None:
    require(not blockers(resources()), 'Resource floors not met')


def process_counts() -> dict:
    counts = dict(shell=0, native=0, llama=0)
    for process in psutil.process_iter(['name']):
        name = (process.info['name'] or '').lower()
        if name == 'strata-desktop.exe':
            counts['shell'] += 1
        elif name in {'strata.exe', 'strata-q36.exe'}:
            counts['native'] += 1
        elif name in {'llama-server.exe', 'llama-server'}:
            counts['llama'] += 1
    return counts


def staged() -> dict:
    receipt = load(OUT / 'staged-native.json')
    require(receipt.get('ok') is True and receipt.get('signatureVerified') is True and receipt.get('releaseQualified') is False, 'Parent signed private staging required')
    for key, length in [('nativeSourceCommit', 40)] + [(key, 64) for key in ['engineSHA256', 'q36SHA256', 'signedManifestSHA256', 'archiveSHA256', 'payloadInventorySHA256']]:
        require(bool(re.fullmatch('[0-9a-f]{' + str(length) + '}', receipt.get(key, ''))), 'Invalid staging identity: ' + key)
    require(receipt['prismVersion'] == '0.4.1' and receipt['prismManifestSHA256'] == PRISM_MANIFEST_SHA and receipt['prismExeSHA256'] == PRISM_EXE_SHA, 'Fixed Prism identity differs')
    require('quality' in receipt, 'Parent quality limits required')
    for name, key in [('engine-component.json', 'signedManifestSHA256'), ('strata.exe', 'engineSHA256'), ('strata-q36.exe', 'q36SHA256'), ('local-backends/prism/runtime.json', 'prismManifestSHA256'), ('local-backends/prism/llama-server.exe', 'prismExeSHA256')]:
        require(sha(SIGNED / name) == receipt[key], 'Staged bytes differ: ' + name)
    archive = Path(receipt['archive'])
    require(archive.is_file() and archive.stat().st_size == receipt['archiveBytes'] and sha(archive) == receipt['archiveSHA256'], 'Signed archive differs')
    require(digest(inventory(SIGNED)) == receipt['payloadInventorySHA256'], 'Staged inventory differs')
    fixed = RUNTIME.parent / 'signed-component-r4/0.5.2-windows-x86_64-cuda-cuda13/local-backends'
    for name, version in [('prism', '0.4.1'), ('turboquant', '0.4.0')]:
        require(load(SIGNED / 'local-backends' / name / 'runtime.json')['version'] == version, 'Fixed runtime version differs')
        require(inventory(SIGNED / 'local-backends' / name) == inventory(fixed / name), 'Fixed runtime bytes changed: ' + name)
    return receipt


def build_env(*, require_native: bool = True) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(('STRATA_', 'DSH_', 'WEBVIEW2_', 'NODE_OPTIONS', 'PYTHONPATH', 'PYTHONHOME', 'TAURI_SIGNING_'))}
    temp = OUT / 'temp'
    temp.mkdir(exist_ok=True)
    env.update(PATH=str(NODE.parent) + ';C:/Users/downl/.cargo/bin;' + env['PATH'], TEMP=str(temp), TMP=str(temp),
               PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', PYTHONIOENCODING='utf-8', NODE_OPTIONS='--max-old-space-size=1024',
               UV_CACHE_DIR=str(OUT / 'uv-cache'), PSModuleAnalysisCachePath=str(temp / 'PSModuleAnalysisCache'),
               npm_config_cache=str(OUT / 'npm-cache'), XDG_CACHE_HOME=str(OUT / 'xdg-cache'),
               STRATA_PUBLIC_PACKAGE='1', STRATA_PUBLIC_ASSETS=str(PUBLIC_ASSETS), STRATA_PUBLIC_ASSETS_RECEIPT=str(PUBLIC_RECEIPT),
                CARGO_TARGET_DIR=str(CARGO_TARGET), CARGO_BUILD_JOBS='5', CMAKE_BUILD_PARALLEL_LEVEL='5',
                RUSTC_WRAPPER='', RUSTC_WORKSPACE_WRAPPER='')
    if not require_native:
        return env
    native_root = os.environ.get('LOCAL053_NATIVE_SOURCE_ROOT')
    require(bool(native_root) and Path(native_root).is_absolute(), 'Explicit native source root required')
    receipt = staged()
    env.update(STRATA_NATIVE_SOURCE_ROOT=native_root, STRATA_NATIVE_SOURCE_COMMIT=receipt['nativeSourceCommit'],
               STRATA_NATIVE_MANIFEST_SHA256=receipt['signedManifestSHA256'])
    return env


def preserved_copy(source: Path, target: Path) -> dict:
    require(not target.exists(), 'Fresh copy destination required')
    before = inventory(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    require(inventory(target) == before, 'Copied resource bytes differ')
    return dict(files=len(before), inventorySHA256=digest(before), inventory=before)


def normal_app_env() -> dict:
    """Use the successful normal-launch environment recipe without inheriting old constants."""
    text = (HISTORY / 'common.py').read_text(encoding='utf-8')
    start = text.index('def normal_app_env()')
    end = text.index('\ndef preserved_copy', start)
    scope = dict(globals())
    exec(compile(text[start:end], str(HISTORY / 'common.py'), 'exec'), scope)
    return scope['normal_app_env']()
