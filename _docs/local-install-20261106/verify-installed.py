"""Compare all exact archive members and unchanged user data before the first launch."""
import json
from pathlib import Path
from prepare_build import OUT, sha, inventory
from prepare_upgrade import BACKUP, OLD_H, COMPONENT, MANAGED, registration_snapshot
from installed_state import TARGET, shells

assert not shells(), 'Verify user hashes before first startup'
installed = json.loads((OUT/'nsis-install.json').read_text())
assert installed['ok'] and installed['exitCode'] == 0
pre = json.loads((BACKUP/'preflight.json').read_text())
expected = json.loads((OUT/'qualified-payload.json').read_text())
qa = json.loads((OUT/'app-qualification.json').read_text())
assert sha(OUT/'qualified-payload.json') == qa['payloadInventorySHA256']
actual = {'strata-desktop.exe':sha(TARGET/'strata-desktop.exe')}
for name in MANAGED:
    folder = TARGET/name
    if folder.exists():
        actual.update({name+'/'+key:value for key,value in inventory(folder).items()})
assert actual == expected, 'Installed membership or payload differs from qualified archive'
for record in pre['userFiles']:
    assert sha(Path(record['source'])) == record['sha256'], 'User data changed before first startup'
assert OLD_H.exists() == pre['oldHExists']
assert (inventory(OLD_H) if OLD_H.exists() else {}) == pre['oldHFiles'], 'Old H installation changed'
assert inventory(COMPONENT) == pre['componentFiles'], 'Native component changed'
registrations = registration_snapshot()
uninstalls = [values for path,values in registrations.items() if path.endswith(r'Uninstall\Strata')]
assert uninstalls
for values in uninstalls:
    assert values['DisplayVersion']['value'] == '0.5.2-local.1'
    assert Path(values['InstallLocation']['value'].strip('"')).resolve() == TARGET.resolve()
    assert Path(values['UninstallString']['value'].strip('"')).resolve() == (TARGET/'uninstall.exe').resolve()
for path,values in registrations.items():
    if path.endswith(r'strata\Strata'):
        assert Path(values['']['value']).resolve() == TARGET.resolve()
report = {'ok':True,'payloadFilesMatched':len(actual),'userFilesUnchanged':len(pre['userFiles']),
    'nativeFilesUnchanged':len(pre['componentFiles']),'oldHFilesUnchanged':len(pre['oldHFiles']),
    'registrationViewsChecked':len(uninstalls),'registrationTargetCorrect':True,'controlVersion':(TARGET/'control/VERSION').read_text().strip(),
    'shellSHA256':actual['strata-desktop.exe'],'beforeFirstLaunch':True}
assert report['controlVersion'] == '0.5.2'
(OUT/'installed-payload.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
