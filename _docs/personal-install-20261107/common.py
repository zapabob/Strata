"""Constants and fail-closed preparation/build gates for this one personal candidate."""
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

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = Path('H:/Strata/releases/personal-052-local2-20261107')
OUT = BASE/'app'
PRODUCT = '0.5.2-local.2'
CONTROL = '0.5.3'
ENGINE = '0.5.2'
NATIVE_COMMIT = '4a171bdeb33675963edcca51f423519863fb7127'
UNSIGNED = BASE/'component-r3/0.5.2-windows-x86_64-cuda-cuda13'
UNSIGNED_MANIFEST = '1058ccf94a1a78be07a485e968c40b007225a9c7a39b45eae5d78fbe582191e7'
ENGINE_SHA = '13fc3b96fe71afcb98990d828d2c743f85e8b59b16174a1f7da3eb4ef9b4f8e3'
Q36_SHA = '0789a8583c4409bd517357675b96f9507b7d88ae725474a70e05997cc2be5ede'
NODE_SHA = '1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9'
COMPOSITE = BASE/'component-copy-r4'/UNSIGNED.name
COMPOSITE_RECEIPT = OUT/'prism041-r4/staging.json'
SIGNED = OUT/'signed-component-r4'/UNSIGNED.name
RESOURCES = ROOT/'apps/desktop/src-tauri/resources'
INSTALLED = Path('C:/Users/downl/AppData/Local/Programs/Strata')
NODE = INSTALLED/'node/node.exe'
PYTHON = Path('C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe')
UV = Path('C:/Users/downl/.local/bin/uv.exe')
KEY = Path('H:/Strata/private-keys/hakua-feed-20261101/feed-key.json')
CARGO_TARGET = Path('H:/Strata/releases/local-052-20261106-opencode/cargo-target')
PUBLIC_ASSETS = Path('H:/Strata/releases/hakua033-public-assets')
PUBLIC_RECEIPT = Path('H:/Strata/releases/hakua033-public-assets.receipt.json')
QUALITY = BASE/'followup-r3/qualification-summary.json'
MODEL = Path('H:/Strata/models/models/qwen36-UD-Q4_K_XL/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf')
PRISM_ROOT = Path('H:/Strata/validation/qwen35-mtp-load-20261107/runtime-prism-0.4.1-1965755c')
PRISM_HANDOFF = PRISM_ROOT.parent/'handoff-r2.json'
PRISM_MANIFEST_SHA = '9c729c73eb050dc466203fe149a27acd5be48763a33ea2c5d2b89f78e4ddcbaa'
PRISM_EXE_SHA = '5ca5d8bfdfcb6fe46a96a06b71eaf45aedfbd1c6673bda2a10eb6412613be777'
PRISM_SOURCE = '1965755ceee6738b9a04ceaf5d30e6305d6ccd00'
USER_GGUF = Path('H:/Strata/models/models/新しいフォルダー/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf')
USER_GGUF_SHA = '8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949'

def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)

def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write_new(path: Path, value: dict) -> None:
    require(path.parent.is_dir(), 'Receipt parent is absent')
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2);stream.write('\n')

def inventory(root: Path) -> dict[str,str]:
    require(root.is_dir() and not root.is_symlink() and not root.is_junction(),'Invalid inventory root')
    result = {}
    for directory,dirs,names in os.walk(root,followlinks=False):
        for name in sorted(dirs+names):
            path=Path(directory)/name
            require(not path.is_symlink() and not path.is_junction(),'Linked input refused')
            if path.is_file():result[path.relative_to(root).as_posix()]=sha(path)
    return dict(sorted(result.items()))

def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def git(*args: str) -> str:
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True,timeout=30).strip()

def resources() -> dict:
    sys.path.insert(0,str(ROOT/'tools'))
    from native_model_resource_guard import available_memory
    sample=available_memory()
    return {'ramBytes':sample['available_physical_bytes'],'commitBytes':sample['available_commit_bytes'],
            'cFreeBytes':shutil.disk_usage('C:/').free,'hFreeBytes':shutil.disk_usage('H:/').free}

def blockers(sample: dict) -> list[str]:
    return [label for key,floor,label in [('ramBytes',3,'RAM<3GiB'),('commitBytes',4,'commit<4GiB'),('cFreeBytes',5,'C<5GiB'),('hFreeBytes',10,'H<10GiB')] if sample[key]<floor*1024**3]

def require_resources() -> None:
    require(not blockers(resources()),'Resource floors not met')

def process_counts() -> dict:
    counts={'shell':0,'native':0,'llama':0}
    for process in psutil.process_iter(['name']):
        name=(process.info['name'] or '').lower()
        if name=='strata-desktop.exe':counts['shell']+=1
        elif name in {'strata.exe','strata-q36.exe'}:counts['native']+=1
        elif name in {'llama-server.exe','llama-server'}:counts['llama']+=1
    return counts

def approved_source(commit: str | None) -> str:
    require(bool(re.fullmatch('[0-9a-f]{40}',commit or '')),'Parent review must supply the full frozen commit')
    require(git('rev-parse','HEAD')==commit,'Reviewed source is not current HEAD')
    require(not git('diff','HEAD','--name-only') and not git('ls-files','--others','--exclude-standard'),'Parent must freeze the complete source first')
    require((ROOT/'VERSION').read_text().strip()==PRODUCT,'Product version differs')
    require((ROOT/'CONTROL_VERSION').read_text().strip()==CONTROL,'Control version differs')
    return commit

def build_env() -> dict:
    # In particular, never inherit the previous c50ca06a independent-source override.
    env={k:v for k,v in os.environ.items() if not k.upper().startswith(('STRATA_','DSH_','WEBVIEW2_'))}
    temp=OUT/'temp';temp.mkdir(exist_ok=True)
    env.update(PATH=str(NODE.parent)+';C:/Users/downl/.cargo/bin;'+env['PATH'],TEMP=str(temp),TMP=str(temp),
        PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',NODE_OPTIONS='--max-old-space-size=1024',
        STRATA_PUBLIC_PACKAGE='1',STRATA_PUBLIC_ASSETS=str(PUBLIC_ASSETS),STRATA_PUBLIC_ASSETS_RECEIPT=str(PUBLIC_RECEIPT),
        CARGO_TARGET_DIR=str(CARGO_TARGET),CARGO_BUILD_JOBS='1',RUSTC_WRAPPER='',RUSTC_WORKSPACE_WRAPPER='')
    return env

def normal_app_env() -> dict:
    """Keep the existing Automatic executable override; never change global environment."""
    env={k:v for k,v in os.environ.items() if not k.upper().startswith(('STRATA_','DSH_','WEBVIEW2_','NODE_OPTIONS'))}
    automatic=next((v for k,v in os.environ.items() if k.upper()=='STRATA_LLAMA_SERVER'),None)
    if automatic is None:
        import winreg
        for hive,key in [(winreg.HKEY_CURRENT_USER,'Environment'),(winreg.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')]:
            try:
                with winreg.OpenKey(hive,key) as handle:automatic=winreg.QueryValueEx(handle,'STRATA_LLAMA_SERVER')[0]
                break
            except FileNotFoundError:pass
    if isinstance(automatic,str):env['STRATA_LLAMA_SERVER']=automatic
    return env

def preserved_copy(source: Path, target: Path) -> dict:
    require(not target.exists(),'Fresh copy destination required')
    before=inventory(source)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(source,target)
    require(inventory(target)==before,'Copied resource bytes differ')
    return {'files':len(before),'inventorySHA256':digest(before),'inventory':before}

def quality_record() -> dict:
    q=load(QUALITY)
    require(q['sourceCommit']==NATIVE_COMMIT and q['manifestSHA256']==UNSIGNED_MANIFEST,'Wrong r3 qualification identity')
    require(q['strataSHA256']==ENGINE_SHA and q['nativeFunctionalChecksPassed'] and q['suitePassed']==17,'Wrong r3 functional receipt')
    require(q['releaseQualified'] is False and q['resourceGuard']=='FAIL' and len(q['resourceViolations'])==4,'Known resource failure must remain recorded')
    return {'releaseQualified':False,'resourceGuardPassed':False,'resourceViolationCount':4,'inheritedFunctionalChecks':17,
            'qualityReceiptSHA256':sha(QUALITY),'resourceOriginSHA256':sha(BASE/'followup-r3/resource-origin.json')}
