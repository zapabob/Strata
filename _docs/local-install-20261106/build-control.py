"""Build fresh Control using the repository's pinned standalone runtime recipe."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
from prepare_build import ROOT, OUT, sha

def main() -> None:
    assert not subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).strip()
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    terminal = OUT/'terminal'
    scratch = OUT/'control-scratch'
    control = ROOT/'apps/desktop/src-tauri/resources/control'
    assert not terminal.exists() and not scratch.exists()
    assert {p.name for p in control.iterdir()} == {'.gitignore'}
    scratch.mkdir()
    env = dict(os.environ, TEMP=str(scratch), TMP=str(scratch), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
    subprocess.run([sys.executable,'-B','packaging/package_terminal.py','--out',str(terminal),'--target','windows-x86_64','--keep-staging','--cache','C:/Users/downl/AppData/Local/Temp/strata-packaging-cache'],cwd=ROOT,env=env,check=True,timeout=900)
    archives = list(terminal.glob('strata-terminal-*.zip'))
    assert len(archives) == 1
    subprocess.run([sys.executable,'-B','apps/desktop/scripts/stage-control.py','--archive',str(archives[0]),'--out',str(control)],cwd=ROOT,env=env,check=True,timeout=300)
    record = json.loads((control/'BUNDLE.json').read_text())
    assert record['version'] == '0.5.2'
    assert record['python']['version'] == '3.12.15'
    assert record['installed']['hakua-memory'] == '0.3.5' and record['installed']['pillow'] == '13.0.0'
    assert (control/'COMMIT').read_text().strip() == commit
    assert sha(ROOT/'packaging/locks/runtime-windows-x86_64-cp312.txt') == record['lock']['sha256']
    report = {'ok':True,'sourceCommit':commit,'controlVersion':'0.5.2','productVersion':'0.5.2-local.1','archive':str(archives[0]),'archiveSHA256':sha(archives[0]),'bundle':record}
    (OUT/'control-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'ok':True,'sourceCommit':commit,'controlVersion':'0.5.2','archiveSHA256':report['archiveSHA256']}))

if __name__ == '__main__':
    main()
