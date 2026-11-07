"""Prepared build steps. Every mutating build requires parent-reviewed clean source."""
from __future__ import annotations
import argparse
import json
import subprocess
from common import *

def snapshot_cache() -> None:
    destination=OUT/'prior-cargo-artifacts'
    require(not destination.exists(),'Prior cargo artifact receipt must be fresh')
    destination.mkdir()
    paths=[CARGO_TARGET/'release/strata-desktop.exe',CARGO_TARGET/'release/bundle/nsis/Strata_0.5.2-local.1_x64-setup.exe']
    records={}
    for path in paths:
        require(path.is_file(),'Expected prior cargo artifact missing')
        target=destination/path.name;shutil.copy2(path,target)
        require(sha(path)==sha(target),'Prior artifact preservation failed')
        records[path.name]={'sha256':sha(target),'bytes':target.stat().st_size}
    old=load(Path('H:/Strata/releases/local-052-20261106-opencode/app-build.json'))
    require(records[paths[1].name]['sha256']==old['sha256'],'Old cached installer no longer matches its receipt')
    write_new(destination/'receipt.json',{'ok':True,'files':records,'previousSourceCommit':old['sourceCommit']})

def build_control(commit: str) -> None:
    require(not (OUT/'control-build.json').exists(),'Control build already recorded')
    terminal=OUT/'terminal';require(not terminal.exists(),'Fresh terminal output required')
    old=preserved_copy(RESOURCES/'control',OUT/'resource-backups/control-before')
    env=build_env()
    subprocess.run([str(PYTHON),'-B','packaging/package_terminal.py','--out',str(terminal),'--target','windows-x86_64','--keep-staging',
        '--cache','C:/Users/downl/AppData/Local/Temp/strata-packaging-cache'],cwd=ROOT,env=env,check=True,timeout=900)
    archive,=terminal.glob('strata-terminal-*.zip')
    require(inventory(RESOURCES/'control')==old['inventory'],'Staged Control changed during build')
    subprocess.run([str(PYTHON),'-B','apps/desktop/scripts/stage-control.py','--archive',str(archive)],cwd=ROOT,env=env,check=True,timeout=300)
    control=RESOURCES/'control';bundle=load(control/'BUNDLE.json')
    require(bundle['version']==CONTROL and bundle['python']['version']=='3.12.15' and bundle['installed']['hakua-memory']=='0.3.5','Control identities differ')
    require((control/'COMMIT').read_text().strip()==commit,'Control source commit mismatch')
    require(bundle['lock']['sha256']==sha(ROOT/'packaging/locks/runtime-windows-x86_64-cp312.txt'),'Control lock mismatch')
    tree=inventory(control);write_new(OUT/'control-inventory.json',tree)
    write_new(OUT/'control-build.json',{'ok':True,'sourceCommit':commit,'productVersion':PRODUCT,'controlVersion':CONTROL,'archive':str(archive),'archiveSHA256':sha(archive),'bundle':bundle,'inventorySHA256':digest(tree)})

def build_app(commit: str) -> None:
    control=load(OUT/'control-build.json');native=load(OUT/'staged-native.json')
    require(control['ok'] and control['sourceCommit']==commit,'Build fresh Control from the reviewed source')
    require(native['signatureVerified'] and native['releaseQualified'] is False,'Signed private component receipt missing')
    require(sha(SIGNED/'engine-component.json')==native['signedManifestSHA256'],'Signed manifest drift')
    require(sha(RESOURCES/'engine-bundle'/SIGNED.name/'engine-component.json')==native['signedManifestSHA256'],'Staged component differs from the verified signed copy')
    require(native['prismVersion']=='0.4.1' and sha(RESOURCES/'local-backends/prism/runtime.json')==PRISM_MANIFEST_SHA,'Build requires exact Prism 0.4.1 staging')
    require(not (OUT/'app-build.json').exists(),'App artifact already recorded')
    snapshot_cache();env=build_env()
    subprocess.run([str(NODE),str(HERE/'verify-native.mjs'),str(RESOURCES/'engine-bundle'/SIGNED.name)],cwd=ROOT,env=env,check=True,timeout=180)
    source_paths=git('ls-files','-z').split('\0');source_files={p:sha(ROOT/p) for p in source_paths if p and (ROOT/p).is_file()}
    generated={p:load(ROOT/p) for p in source_files if p.startswith('apps/desktop/src-tauri/gen/schemas/') and p.endswith('.json')}
    write_new(OUT/'frozen-source-inventory.json',source_files)
    subprocess.run([str(NODE),'node_modules/@tauri-apps/cli/tauri.js','build','--bundles','nsis','--','--locked','--offline'],cwd=ROOT/'apps/desktop',env=env,check=True,timeout=2700)
    require(all(load(ROOT/p)==generated[p] if p in generated else sha(ROOT/p)==value for p,value in source_files.items()),'Source changed during build')
    built=CARGO_TARGET/f'release/bundle/nsis/Strata_{PRODUCT}_x64-setup.exe';target=OUT/f'Strata-{PRODUCT}-windows-x64-setup.exe'
    require(built.is_file() and not target.exists(),'Unexpected installer destination')
    shutil.copy2(built,target);require(sha(built)==sha(target),'Installer copy mismatch')
    # Freeze the new unbundled shell before the shared cargo cache is reused again.
    shell=OUT/'unbundled-strata-desktop.exe';shutil.copy2(CARGO_TARGET/'release/strata-desktop.exe',shell)
    require(sha(shell)==sha(CARGO_TARGET/'release/strata-desktop.exe'),'Unbundled shell copy mismatch')
    record={'ok':True,'sourceCommit':commit,'sourceInventorySHA256':digest(source_files),'installer':str(target),'sha256':sha(target),'bytes':target.stat().st_size,
        'unbundledShell':str(shell),'unbundledShellSHA256':sha(shell),'productVersion':PRODUCT,'controlVersion':CONTROL,'nativeVersion':ENGINE,
        'nativeSourceCommit':NATIVE_COMMIT,'engineSHA256':ENGINE_SHA,'signedManifestSHA256':native['signedManifestSHA256'],'releaseQualified':False,
        'generatedSchemaOutputs':{p:sha(ROOT/p) for p in generated}}
    write_new(OUT/'app-build.json',record);print(json.dumps(record))

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step',choices=['control','app'])
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--reviewed-commit')
    args=parser.parse_args()
    if not args.execute:
        print(json.dumps({'wouldBuild':False,'step':args.step,'productVersion':PRODUCT,'controlVersion':CONTROL,'nativeVersion':ENGINE,'releaseQualified':False,'blockers':blockers(resources())+['parent-review-and-clean-source']}));return
    commit=approved_source(args.reviewed_commit);require_resources();require(OUT.is_dir(),'Prepare inputs first')
    require(sha(NODE)==NODE_SHA,'Qualified private Node changed')
    if args.step=='control':build_control(commit)
    else:build_app(commit)

if __name__=='__main__':main()
