"""Check generated recipes and plans without building or launching the application."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys

from delivery import DEST, OUT, ROOT, outputs
from native import require

NODE = Path('C:/Users/downl/AppData/Local/Programs/Strata/node/node.exe')


def node_check(text: str) -> None:
    result = subprocess.run([str(NODE), '--input-type=module', '--check'], input=text,
        capture_output=True, text=True, encoding='utf-8', timeout=20)
    require(result.returncode == 0, 'Generated JavaScript syntax failed: ' + result.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', action='store_true', help='Also validate the completed native reports')
    args = parser.parse_args()
    files, _ = outputs()
    for name, text in files.items():
        require((DEST / name).read_text(encoding='utf-8') == text, 'Prepared adapter differs: ' + name)
        if name.endswith('.mjs'):
            node_check(text)
    sys.path.insert(0, str(DEST / 'app'))
    recipes = importlib.import_module('recipes')
    import common
    require((common.PRODUCT, common.CONTROL, common.ENGINE) == ('0.5.5-local.1', '0.5.6', '0.5.5'), 'Delivery versions differ')
    qualification = recipes.qualify()
    node_check(qualification)
    require("controlVersion='0.5.6'" in qualification, 'Fresh Control qualification version missing')
    checks = []
    for target in ('candidate', 'installed'):
        for kind in ('q36', 'prism'):
            work = OUT / 'app-native055/qa' / f'{target}-{kind}-r1'
            text = recipes.qa(kind, target, 'r1', work)
            node_check(text)
            require('upstream-0213-20261109-opencode' not in text, 'Historical output in fresh QA')
            require('0.5.4-local.1' not in text and '0.5.4-windows-x86_64' not in text, 'Historical version in fresh QA')
            if kind == 'prism':
                for marker in ("STRATA_AGENT:'on'", "f.agent===true", "f.type==='done'", 'actualSupervisorAgent=true',
                               'actualTeardownChecks=', "raw.split('\\n')"):
                    require(marker in text, 'Real agent/teardown assertion missing: ' + marker)
                require("preferences:{agent:false" in text, 'Original plain-chat test was lost')
            checks.append(f'{target}-{kind}-syntax-and-contract')
    for step in ('build-control', 'build-app', 'qualify', 'qa-q36', 'qa-prism', 'backup', 'install', 'verify', 'activate', 'normal-start'):
        run = subprocess.run([sys.executable, '-B', str(DEST / 'app/adapter.py'), step, '--plan'],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=20)
        require(run.returncode == 0, 'App plan failed: ' + step + ': ' + run.stderr)
        plan = json.loads(run.stdout)
        require(plan['wouldExecute'] is False and plan['product'] == common.PRODUCT and plan['control'] == common.CONTROL,
                'Read-only plan contract differs')
    run = subprocess.run([sys.executable, '-B', str(DEST / 'component/compose.py'), '--plan'],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=20)
    require(run.returncode == 0 and json.loads(run.stdout)['execution'] is False, 'Component plan failed')
    if args.native:
        command = ('import sys,json;sys.path.insert(0,sys.argv[1]);from quality import validate;'
                   'value=validate();assert value["nativeResourceGuard"]["passed"] is True;'
                   'assert value["finalNumericalChecksPassed"] is True;'
                   'print(json.dumps({"passed":True,"nativeResourceGuard":value["nativeResourceGuard"],'
                   '"finalNumericalChecksPassed":True,"releaseQualified":value["releaseQualified"]}))')
        run = subprocess.run([sys.executable, '-B', '-c', command, str(DEST / 'component')],
            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=120)
        require(run.returncode == 0, 'Completed native evidence validation failed: ' + run.stderr)
        print(run.stdout.strip())
    print(json.dumps({'passed': True, 'syntaxAndIdentityFiles': len(files), 'qaRecipes': checks,
        'appReadOnlyPlans': 10, 'componentReadOnlyPlans': 1, 'modelOrAppLaunched': False,
        'candidateAcceptance': False, 'completedNativeReportsValidated': args.native}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
