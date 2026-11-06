"""Build a locked CPU-only NSIS candidate; bind the retained native component separately."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
from prepare_build import ROOT, OUT, FROZEN, sha

node = 'C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe'
assert sha(__import__('pathlib').Path(node)) == '1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9'
resources = json.loads((OUT/'resources.json').read_text())
assert resources['ok']
target = OUT/'cargo-target'
scratch = OUT/'app-scratch'
assert not scratch.exists()
scratch.mkdir()
env = dict(os.environ, PATH=str(__import__('pathlib').Path(node).parent)+';C:/Users/downl/.cargo/bin;'+os.environ['PATH'],
    STRATA_PUBLIC_PACKAGE='1', STRATA_PUBLIC_ASSETS='H:/Strata/releases/hakua033-public-assets',
    STRATA_PUBLIC_ASSETS_RECEIPT='H:/Strata/releases/hakua033-public-assets.receipt.json',
    STRATA_NATIVE_SOURCE_ROOT=str(FROZEN), STRATA_NATIVE_SOURCE_COMMIT=resources['nativeSourceCommit'],
    STRATA_NATIVE_MANIFEST_SHA256=resources['nativeManifestSHA256'], CARGO_TARGET_DIR=str(target), CARGO_BUILD_JOBS='1',
    NODE_OPTIONS='--max-old-space-size=1024', TEMP=str(scratch), TMP=str(scratch), RUSTC_WRAPPER='', RUSTC_WORKSPACE_WRAPPER='')
commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).strip()
subprocess.run([node,'node_modules/@tauri-apps/cli/tauri.js','build','--bundles','nsis','--','--locked','--offline'],cwd=ROOT/'apps/desktop',env=env,check=True,timeout=2400)
built = target/'release/bundle/nsis/Strata_0.5.2-local.1_x64-setup.exe'
installer = OUT/'Strata-0.5.2-local.1-windows-x64-setup.exe'
assert built.is_file() and not installer.exists()
shutil.copy2(built,installer)
assert sha(built) == sha(installer)
report = {'ok':True,'sourceCommit':commit,'installer':str(installer),'sha256':sha(installer),'bytes':installer.stat().st_size,'nativeSourceCommit':resources['nativeSourceCommit'],'nativeSHA256':resources['nativeSHA256'],'nativeManifestSHA256':resources['nativeManifestSHA256'],'target':str(target)}
(OUT/'app-build.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
