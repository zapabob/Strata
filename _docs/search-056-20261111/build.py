"""Build only the new app; retain independently signed native and Control components."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/search-056-20261111-codex')
RES = ROOT / 'apps/desktop/src-tauri/resources'
TARGET = Path('H:/Strata/releases/local-052-20261106-opencode/cargo-target')
PRODUCT = '0.5.6-local.1'


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main() -> None:
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT):
        raise RuntimeError('Commit reviewed source before the candidate build')
    if (OUT / 'app-build.json').exists():
        raise RuntimeError('Preserve prior candidate evidence')
    prior = OUT / 'prior-cargo-artifacts'
    prior.mkdir()
    preserved = []
    for index, path in enumerate([TARGET / 'release/strata-desktop.exe', *sorted((TARGET / 'release/bundle/nsis').glob('*.exe'))]):
        destination = prior / f'{index}-{path.name}'
        shutil.copy2(path, destination)
        if sha(path) != sha(destination):
            raise RuntimeError('Prior artifact backup differs')
        preserved.append({'source': str(path), 'backup': str(destination), 'sha256': sha(destination)})
    (prior / 'receipt.json').write_text(json.dumps(preserved, indent=2), encoding='utf-8')
    env = dict(os.environ)
    env.update(STRATA_PUBLIC_PACKAGE='1', STRATA_PUBLIC_ASSETS='H:/Strata/releases/hakua033-public-assets',
               STRATA_PUBLIC_ASSETS_RECEIPT='H:/Strata/releases/hakua033-public-assets.receipt.json',
               STRATA_NATIVE_SOURCE_ROOT='H:/Strata/worktrees/native-055-source-20261110',
               STRATA_NATIVE_SOURCE_COMMIT='b995af139cc823537489b886bc1e8602cf10301c',
               STRATA_NATIVE_MANIFEST_SHA256=sha(RES / 'engine-bundle/0.5.5-windows-x86_64-cuda-cuda13/engine-component.json'),
               CARGO_TARGET_DIR=str(TARGET), CARGO_BUILD_JOBS='5', CMAKE_BUILD_PARALLEL_LEVEL='5',
               NODE_OPTIONS='--max-old-space-size=1024', RUSTC_WRAPPER='', RUSTC_WORKSPACE_WRAPPER='')
    node = RES / 'node/node.exe'
    if subprocess.check_output([str(node), '--version'], text=True).strip() != 'v24.22.2':
        raise RuntimeError('Unexpected build Node version')
    generated = [path for path in (ROOT / 'apps/desktop/src-tauri/gen/schemas').glob('*.json')]
    saved = {path: path.read_bytes() for path in generated}
    subprocess.run([str(node), 'node_modules/@tauri-apps/cli/tauri.js', 'build', '--bundles', 'nsis', '--', '--locked', '--offline'],
                   cwd=ROOT / 'apps/desktop', env=env, check=True, timeout=2700)
    # Tauri may normalize JSON schemas; preserve tracked schema bytes after validating semantics.
    for path, before in saved.items():
        if json.loads(before) != json.loads(path.read_bytes()):
            raise RuntimeError('Generated schema changed semantically')
        path.write_bytes(before)
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT):
        raise RuntimeError('Source changed during build')
    installer = OUT / f'Strata-{PRODUCT}-windows-x64-setup.exe'
    shell = OUT / 'strata-desktop.exe'
    shutil.copy2(TARGET / f'release/bundle/nsis/Strata_{PRODUCT}_x64-setup.exe', installer)
    shutil.copy2(TARGET / 'release/strata-desktop.exe', shell)
    record = {'sourceCommit': commit, 'productVersion': PRODUCT, 'compilerJobs': 5,
              'nativeVersion': '0.5.5', 'nativeSourceCommit': env['STRATA_NATIVE_SOURCE_COMMIT'],
              'nativeManifestSHA256': env['STRATA_NATIVE_MANIFEST_SHA256'],
              'controlVersion': '0.5.6', 'controlSourceCommit': (RES / 'control/COMMIT').read_text().strip(),
              'installer': str(installer), 'installerSHA256': sha(installer), 'installerBytes': installer.stat().st_size,
              'shell': str(shell), 'shellSHA256': sha(shell), 'releaseQualified': False}
    with (OUT / 'app-build.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
