"""One bounded NSIS invocation to the explicit C-drive target, gated by backup and QA."""
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone
from prepare_build import OUT, sha
from prepare_upgrade import BACKUP
from installed_state import TARGET, shells

receipt_path = OUT/'nsis-install.json'
assert not receipt_path.exists(), 'Do not repeat an installer invocation'
qa = json.loads((OUT/'app-qualification.json').read_text())
ui = json.loads((OUT/'packaged-ui.json').read_text())
backup = json.loads((OUT/'backup.json').read_text())
assert qa['ok'] and ui['passed'] and backup['ok']
assert sha(BACKUP/'preflight.json') == backup['preflightSHA256']
pre = json.loads((BACKUP/'preflight.json').read_text())
assert Path(pre['target']) == TARGET and TARGET.resolve() == TARGET
assert not TARGET.is_junction() and not TARGET.is_symlink()
assert sha(Path(pre['installer'])) == pre['installerSHA256'] == qa['installerSHA256']
assert all(sha(Path(r['source'])) == r['sha256'] for r in pre['userFiles'])
assert not shells(), 'Existing Strata must be closed'
report = {'ok':False,'startedAt':datetime.now(timezone.utc).isoformat(),'installerSHA256':qa['installerSHA256'],'target':str(TARGET)}
receipt_path.write_text(json.dumps(report,indent=2)+'\n')
try:
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith(('STRATA_','DSH_','WEBVIEW2_'))}
    process = subprocess.Popen([pre['installer'],'/S','/D='+str(TARGET)],env=env,creationflags=subprocess.CREATE_NO_WINDOW)
    report['pid'] = process.pid;receipt_path.write_text(json.dumps(report,indent=2)+'\n')
    try:
        report['exitCode'] = process.wait(timeout=600)
    except subprocess.TimeoutExpired:
        # The outer guard owns the Job Object and terminates all descendants.
        process.kill()
        process.wait(timeout=15)
        raise
    assert report['exitCode'] == 0, 'NSIS failed'
    assert sha(TARGET/'strata-desktop.exe') == qa['shellSHA256']
    report['ok'] = True
finally:
    report['finishedAt'] = datetime.now(timezone.utc).isoformat()
    receipt_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
