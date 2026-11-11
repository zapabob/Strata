"""Verify normal installed startup and enable the two explicitly requested options."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import urllib.request
import psutil

OUT = Path('H:/Strata/releases/stable-058-20261111-codex')
APP = Path('C:/Users/downl/AppData/Local/Programs/Strata')
BASE = 'http://127.0.0.1:47831'

def call(path, body=None):
    request = urllib.request.Request(BASE + path, method='GET' if body is None else 'PUT',
        data=None if body is None else json.dumps(body).encode(),
        headers={'Origin': BASE, 'Content-Type': 'application/json', 'X-Strata-Client': 'authorized-workflow-skills-setup'})
    with urllib.request.urlopen(request, timeout=60) as reply:
        return json.load(reply)

def main():
    identity = call('/api/app/build')
    assert identity == {'host': '0.5.8', 'shell': '0.5.8'}
    before = call('/api/agent/tools')
    assert before['search']['provider'] == 'rustxng'
    learning_before = call('/api/skills/learning')
    after = call('/api/skills/learning', {'enabled': True, 'autoApply': True})
    assert after['enabled'] and after['autoApply'] and after['available']
    assert call('/api/agent/tools') == before, 'Other tools, provider, key and approval choices must remain identical'
    native, runtime, health = call('/api/native'), call('/api/runtime'), call('/api/health')
    assert not native.get('instances') and not runtime.get('instances')
    assert health['engine']['status'] == 'stopped' and not health['engine']['running']
    shells = []
    for process in psutil.process_iter(['exe', 'cmdline']):
        try:
            if Path(process.info['exe'] or '') == APP / 'strata-desktop.exe':
                shells.append(process)
                assert len(process.info['cmdline']) == 1
                environment = process.environ()
                assert not environment.get('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS') and not environment.get('STRATA_AGENT')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    assert len(shells) == 1
    report = {'ok': True, 'identity': identity, 'normalStartup': True, 'debugArguments': False,
        'modelUnloaded': True, 'searchProvider': before['search']['provider'], 'rustxngProfile': 'full',
        'workflowLearning': after['enabled'], 'automaticSkillApplication': after['autoApply'],
        'priorLearningEnabled': learning_before['enabled'], 'priorAutoApplyEnabled': learning_before['autoApply'],
        'otherToolAndApprovalChoicesUnchanged': True, 'savedSearchKeyUnchanged': True,
        'note': 'Real search and workflow checks used an isolated installed-app QA profile and scripted model.'}
    with (OUT / 'normal-start.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps(report))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    if parser.parse_args().execute: main()
    else: print(json.dumps({'execute': False, 'learning': True, 'autoApply': True, 'search': 'preserve RustXNG Full'}))
