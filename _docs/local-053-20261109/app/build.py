"""Fresh locked Control and standard Tauri NSIS, invoked only by adapter.py's guard."""
from __future__ import annotations

from common import *


def build_control(commit: str) -> None:
    text = (HISTORY / 'build.py').read_text(encoding='utf-8')
    text = text.replace("'C:/Users/downl/AppData/Local/Temp/strata-packaging-cache'", "str(OUT/'packaging-cache')")
    scope = dict(globals(), __name__='historical_recipe', __file__=str(HISTORY / 'build.py'))
    # Control is built independently; signed native verification still gates app/QA/install.
    scope['build_env'] = lambda: build_env(require_native=False)
    exec(compile(text, str(HISTORY / 'build.py'), 'exec'), scope)
    scope['build_control'](commit)


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
