"""Fresh locked Control and standard Tauri NSIS, invoked only by adapter.py's guard."""
from __future__ import annotations

from common import *


def build_control(commit: str) -> None:
    require(not (OUT / 'control-build.json').exists(), 'Control build already recorded')
    terminal = OUT / 'terminal'
    require(not terminal.exists(), 'Fresh terminal output required')
    control = RESOURCES / 'control'
    old = inventory(control)
    staging = ROOT / '_docs/local-archive/2026-11-09-pre-main/control-staging-files'
    require(not staging.exists(), 'Retain prior Control staging')
    env = build_env(require_native=False)
    subprocess.run([str(PYTHON), '-B', 'packaging/package_terminal.py', '--out', str(terminal),
                    '--target', 'windows-x86_64', '--keep-staging', '--cache', str(OUT / 'packaging-cache')],
                   cwd=ROOT, env=env, check=True, timeout=900)
    archive, = terminal.glob('strata-terminal-*.zip')
    require(inventory(control) == old, 'Staged Control changed during build')
    staging.mkdir(parents=True)
    fresh = staging / 'fresh-control'
    # The production stager only cleans fresh scratch here; the existing Control is preserved whole.
    subprocess.run([str(PYTHON), '-B', 'apps/desktop/scripts/stage-control.py', '--archive', str(archive),
                    '--out', str(fresh)], cwd=ROOT, env=env, check=True, timeout=300)
    bundle = load(fresh / 'BUNDLE.json')
    require(bundle['version'] == CONTROL and bundle['python']['version'] == '3.12.15'
            and bundle['installed']['hakua-memory'] == '0.3.5', 'Control identities differ')
    require((fresh / 'COMMIT').read_text().strip() == commit, 'Control source commit mismatch')
    require(bundle['lock']['sha256'] == sha(ROOT / 'packaging/locks/runtime-windows-x86_64-cp312.txt'), 'Control lock mismatch')
    shutil.copy2(control / '.gitignore', fresh / '.gitignore')
    tree = inventory(fresh)
    require(inventory(control) == old, 'Existing Control changed before preservation')
    control.rename(staging / 'prior-control')
    require(inventory(staging / 'prior-control') == old, 'Preserved Control differs')
    fresh.rename(control)
    require(inventory(control) == tree, 'New Control staging differs')
    write_new(OUT / 'control-inventory.json', tree)
    write_new(OUT / 'control-build.json', dict(ok=True, sourceCommit=commit, productVersion=PRODUCT,
              controlVersion=CONTROL, archive=str(archive), archiveSHA256=sha(archive), bundle=bundle,
              inventorySHA256=digest(tree), priorControl=str(staging / 'prior-control'),
              priorControlInventorySHA256=digest(old), repositoryFilesDeleted=False))


def snapshot_cache() -> None:
    destination = OUT / 'prior-cargo-artifacts'
    require(not destination.exists(), 'Fresh cache preservation destination required')
    paths = [CARGO_TARGET / 'release/strata-desktop.exe']
    paths += sorted((CARGO_TARGET / 'release/bundle/nsis').glob('*.exe'))
    require(paths[0].is_file(), 'Existing cached shell missing')
    require(len(paths) > 1, 'Existing cached installers missing')
    destination.mkdir()
    records = []
    for index, path in enumerate(paths):
        before = sha(path)
        target = destination / f'{index}-{path.name}'
        shutil.copy2(path, target)
        require(sha(target) == before == sha(path), 'Cache preservation differs')
        records.append(dict(source=str(path), backup=str(target), sha256=before, bytes=target.stat().st_size))
    write_new(destination / 'receipt.json', dict(ok=True, actualExistingBytes=True, files=records))


def build_app(commit: str) -> None:
    control = load(OUT / 'control-build.json')
    require(control['ok'] and control['sourceCommit'] == commit, 'Fresh reviewed Control required')
    require(inventory(RESOURCES / 'control') == load(OUT / 'control-inventory.json'), 'Staged Control drift')
    native = staged()
    require(not (OUT / 'app-build.json').exists(), 'App artifact already recorded')
    require(subprocess.check_output([str(NODE), '--version'], text=True).strip() == 'v24.22.2', 'Private Node version differs')
    snapshot_cache()
    env = build_env()
    subprocess.run([str(NODE), str(HERE / 'verify-native.mjs'), '--execute'], cwd=ROOT, env=env, check=True, timeout=240)
    source_files = {p: sha(ROOT / p) for p in git('ls-files', '-z').split('\0') if p and (ROOT / p).is_file()}
    generated = {p: load(ROOT / p) for p in source_files if p.startswith('apps/desktop/src-tauri/gen/schemas/') and p.endswith('.json')}
    write_new(OUT / 'frozen-source-inventory.json', source_files)
    subprocess.run([str(NODE), 'node_modules/@tauri-apps/cli/tauri.js', 'build', '--bundles', 'nsis', '--', '--locked', '--offline'], cwd=ROOT / 'apps/desktop', env=env, check=True, timeout=2700)
    require(all(load(ROOT / p) == generated[p] if p in generated else sha(ROOT / p) == value for p, value in source_files.items()), 'Source changed during build')
    built = CARGO_TARGET / f'release/bundle/nsis/Strata_{PRODUCT}_x64-setup.exe'
    target = OUT / f'Strata-{PRODUCT}-windows-x64-setup.exe'
    shell = OUT / 'unbundled-strata-desktop.exe'
    require(built.is_file() and not target.exists() and not shell.exists(), 'Unexpected artifact state')
    shutil.copy2(built, target)
    shutil.copy2(CARGO_TARGET / 'release/strata-desktop.exe', shell)
    require(sha(built) == sha(target) and sha(shell) == sha(CARGO_TARGET / 'release/strata-desktop.exe'), 'Artifact copy differs')
    write_new(OUT / 'app-build.json', dict(ok=True, sourceCommit=commit, appSourceCommit=commit,
              controlSourceCommit=control['sourceCommit'], nativeSourceCommit=native['nativeSourceCommit'],
              sourceInventorySHA256=digest(source_files), installer=str(target), sha256=sha(target), bytes=target.stat().st_size,
              unbundledShell=str(shell), unbundledShellSHA256=sha(shell), productVersion=PRODUCT, controlVersion=CONTROL,
              nativeVersion=ENGINE, engineSHA256=native['engineSHA256'], signedManifestSHA256=native['signedManifestSHA256'],
              releaseQualified=False, quality=native['quality'], generatedSchemaOutputs={p: sha(ROOT / p) for p in generated}))
