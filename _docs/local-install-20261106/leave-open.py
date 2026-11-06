"""Launch the installed app normally for the user; bounded verification, no debug endpoint."""
from __future__ import annotations
import json
import os
import subprocess
import time
from pathlib import Path
import psutil
from installed_state import TARGET, shells, endpoint, idle, get
from prepare_build import OUT, sha

assert json.loads((OUT/'installed-startup-qualified.json').read_text())['passed']
assert not shells(), 'Another shell is already open'
state_path=Path('C:/Users/downl/.strata/data/state.json')
registry_path=Path('C:/Users/downl/.strata/data/local-models.json')
before=json.loads(state_path.read_text());registry_hash=sha(registry_path)
env={k:v for k,v in os.environ.items() if not k.upper().startswith(('STRATA_','DSH_','WEBVIEW2_','NODE_OPTIONS'))}
process=subprocess.Popen([str(TARGET/'strata-desktop.exe')],cwd=TARGET,env=env,
    stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
    creationflags=subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP,close_fds=True)
report={'ok':False,'pid':process.pid,'normalLaunch':True,'debuggingEnabled':False,'modelLoadRequested':False}
deadline=time.monotonic()+90
base=None
try:
    while time.monotonic()<deadline:
        assert process.poll() is None, 'Normal shell exited'
        try:
            base=endpoint(psutil.Process(process.pid));break
        except (RuntimeError,OSError,psutil.NoSuchProcess):
            time.sleep(.5)
    assert base is not None
    for _ in range(10):
        assert idle(base)['idle'], 'Normal startup is not idle'
        time.sleep(1)
    versions=get(base,'/api/app/build')
    assert versions['host']==versions['shell']=='0.5.2-local.1'
    after=json.loads(state_path.read_text())
    assert after.get('current')==before.get('current') and after.get('beginner')==before.get('beginner') and after.get('expert')==before.get('expert')
    assert sha(registry_path)==registry_hash
    assert not any('--remote-debugging' in ' '.join(p.cmdline()) for p in psutil.Process(process.pid).children(recursive=True))
    report.update(ok=True,hostVersion=versions['host'],shellVersion=versions['shell'],manualUnloaded=True,settingsRetained=True,localRegistrationsRetained=True,leftOpen=True)
finally:
    # A user-facing handoff is intentional. Never kill a newly active conversation.
    (OUT/'user-handoff.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
