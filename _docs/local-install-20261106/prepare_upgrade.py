"""Fresh private small-state backup; no model copies and no application changes."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
from datetime import datetime, timezone
import winreg
from prepare_build import OUT, sha, inventory
from installed_state import TARGET, shells

BACKUP = Path('H:/Strata/private-backups/upgrade-052-local1-20261106-opencode-r2')
OLD_H = Path('H:/Programs/Strata-0.4.0-preview.20261103.7')
COMPONENT = Path('C:/Users/downl/AppData/Local/Strata/components/engine/0.5.1-windows-x86_64-cuda-cuda13')
MANAGED = ['control','host','node','harness','engine-bundle','local-backends','notices']

def registration_snapshot() -> dict:
    result = {}
    for label, view in [('32',winreg.KEY_WOW64_32KEY),('64',winreg.KEY_WOW64_64KEY)]:
        for path in [r'Software\Microsoft\Windows\CurrentVersion\Uninstall\Strata',r'Software\strata\Strata']:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,path,0,winreg.KEY_READ|view) as key:
                    values = {}
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        name,value,kind = winreg.EnumValue(key,i)
                        values[name] = {'value':value,'kind':kind}
                    result[label+'/'+path] = values
            except FileNotFoundError:
                pass
    return result

def main() -> None:
    assert not shells(), 'Existing Strata shell must be closed; do not interrupt a chat'
    qa = json.loads((OUT/'app-qualification.json').read_text())
    ui = json.loads((OUT/'packaged-ui.json').read_text())
    build = json.loads((OUT/'app-build.json').read_text())
    assert qa['ok'] and ui['passed'] and qa['selfTests'] == 13
    assert sha(Path(build['installer'])) == build['sha256'] == qa['installerSHA256']
    assert TARGET.resolve() == TARGET and not TARGET.is_junction() and not TARGET.is_symlink()
    assert BACKUP.parent.is_dir() and not BACKUP.exists()
    for name in MANAGED:
        folder = TARGET/name
        if not folder.exists(): continue
        for directory,dirs,files in os.walk(folder,followlinks=False):
            assert all(not p.is_symlink() and not p.is_junction() for p in [Path(directory),*(Path(directory)/n for n in dirs+files)])
    sources = {'host-data':Path('C:/Users/downl/.strata/data'),'roaming-settings':Path('C:/Users/downl/AppData/Roaming/Strata')}
    local = Path('C:/Users/downl/AppData/Local/Strata')
    # install/ and .updates/ also hold downloaded packages/model-derived files.
    # Preserve their selection state, not a second copy of those payloads.
    for name in ['app-settings.json','shell-prefs.json','components/.updates/state.json','tuning','launch']:
        sources['local-settings/'+name] = local/name
    BACKUP.mkdir()
    records = []
    for label,source in sources.items():
        if not source.exists(): continue
        assert not source.is_symlink() and not source.is_junction()
        paths = [source] if source.is_file() else sorted(source.rglob('*'))
        for path in paths:
            assert not path.is_symlink() and not path.is_junction()
            if not path.is_file(): continue
            assert path.stat().st_size < 100*1024**2 and path.suffix.lower() not in {'.gguf','.safetensors','.bin','.pack','.weights'}, 'Not small user state'
            relative = Path(label) if source.is_file() else Path(label)/path.relative_to(source)
            destination = BACKUP/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            digest = sha(path);shutil.copy2(path,destination);assert sha(destination) == digest
            records.append({'source':str(path),'backup':str(destination),'sha256':digest,'bytes':path.stat().st_size})
    report = {'preparedAt':datetime.now(timezone.utc).isoformat(),'installer':build['installer'],'installerSHA256':build['sha256'],
        'target':str(TARGET),'backup':str(BACKUP),'userFiles':records,'modelsCopied':False,'oldShellSHA256':sha(TARGET/'strata-desktop.exe'),
        'sourceRoots':{k:str(v) for k,v in sources.items()},'registrations':registration_snapshot(),
        'oldHExists':OLD_H.exists(),'oldHFiles':inventory(OLD_H) if OLD_H.exists() else {},'componentFiles':inventory(COMPONENT)}
    assert not shells(), 'Strata started while backing up; installation is blocked'
    assert all(sha(Path(r['source'])) == r['sha256'] for r in records), 'User state changed during backup'
    (BACKUP/'preflight.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    summary = {'ok':True,'backup':str(BACKUP),'files':len(records),'bytes':sum(r['bytes'] for r in records),'modelsCopied':False,'oldHFiles':len(report['oldHFiles']),'componentFiles':len(report['componentFiles']),'preflightSHA256':sha(BACKUP/'preflight.json')}
    (OUT/'backup.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))

if __name__ == '__main__':
    main()
