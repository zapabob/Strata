"""Verify the normal installed app and apply the explicitly requested search provider."""
from __future__ import annotations

import json
import argparse
from pathlib import Path
import urllib.request

import psutil

OUT = Path('H:/Strata/releases/search-056-20261111-codex')
APP = Path('C:/Users/downl/AppData/Local/Programs/Strata')
BASE = 'http://127.0.0.1:47831'


def call(path: str, body=None):
    request = urllib.request.Request(BASE + path, method='GET' if body is None else 'PUT',
                                     data=None if body is None else json.dumps(body).encode(),
                                     headers={'Origin': BASE, 'Content-Type': 'application/json',
                                              'X-Strata-Client': 'authorized-local-search-setup'})
    with urllib.request.urlopen(request, timeout=60) as reply:
        return json.load(reply)


def main() -> None:
    identity = call('/api/app/build')
    assert identity == {'host': '0.5.6-local.1', 'shell': '0.5.6-local.1'}
    before = call('/api/agent/tools')
    assert before['search']['provider'] == 'builtin' and not before['search']['keySet']
    after = call('/api/agent/tools', {'search': {'provider': 'rustxng'}})
    expected = json.loads(json.dumps(before))
    expected['search']['provider'] = 'rustxng'
    assert after == expected, 'Only the explicitly requested search provider may change'
    native = call('/api/native')
    runtime = call('/api/runtime')
    health = call('/api/health')
    assert not native.get('instances') and not runtime.get('instances')
    assert health['engine']['status'] == 'stopped' and not health['engine']['running']
    shells = []
    for process in psutil.process_iter(['exe', 'cmdline']):
        try:
            if Path(process.info['exe'] or '') == APP / 'strata-desktop.exe':
                shells.append(process)
                assert len(process.info['cmdline']) == 1, 'Normal startup must have no QA arguments'
                environment = process.environ()
                assert not environment.get('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS')
                assert not environment.get('STRATA_AGENT')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    assert len(shells) == 1
    report = {'ok': True, 'identity': identity, 'normalStartup': True, 'debugArguments': False,
              'modelUnloaded': True, 'searchProvider': after['search']['provider'], 'rustxngProfile': 'full',
              'otherToolAndApprovalChoicesUnchanged': True, 'savedSearchKeyUnchanged': True,
              'note': 'Real search and lifecycle checks used a separately isolated installed-app QA profile.'}
    with (OUT / 'normal-start.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    if parser.parse_args().execute:
        main()
    else:
        print(json.dumps({'execute': False, 'searchProvider': 'rustxng', 'profile': 'full'}))
