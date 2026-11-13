"""Normally stop current app turns and unload observed models after explicit user approval."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

BASE = 'http://127.0.0.1:47831'
OUT = Path('H:/Strata/releases/stable-059-20261113-codex')

def call(path, body=None):
    request = urllib.request.Request(BASE + path, method='GET' if body is None else 'POST',
        data=None if body is None else json.dumps(body).encode(),
        headers={'Origin': BASE, 'Content-Type': 'application/json',
                 'X-Strata-Client': 'authorized-normal-stop-for-publication'})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)

def main(*, expected_version='0.5.9', receipt_name='normal-unload.json',
         authorization='User explicitly approved normal stop/unload after two upload resource interruptions.'):
    assert call('/api/app/build') == {'host': expected_version, 'shell': expected_version}
    tools_before = call('/api/agent/tools')
    turns = call('/api/chat/active')['turns']
    for turn in turns:
        assert isinstance(turn.get('chatId'), str)
        call('/api/chat/stop', {'sessionId': turn['chatId']})
    assert not call('/api/chat/active')['turns'], 'A new active request must be reviewed, not silently interrupted'
    native = call('/api/native')['instances']
    for instance in native:
        call('/api/native/instances/' + urllib.parse.quote(instance['id'], safe='') + '/unload', {})
    runtime = call('/api/runtime')['instances']
    for instance in runtime:
        call('/api/runtime/' + urllib.parse.quote(instance['id'], safe='') + '/unload', {})
    deadline = time.monotonic() + 60
    while True:
        clean = not call('/api/native')['instances'] and not call('/api/runtime')['instances']
        if clean: break
        assert time.monotonic() < deadline, 'Normal unload did not complete'
        time.sleep(.5)
    assert not call('/api/chat/active')['turns']
    assert call('/api/agent/tools') == tools_before
    report = {'ok': True, 'stoppedActiveTurns': len(turns), 'unloadedNativeInstances': len(native),
              'unloadedRuntimeInstances': len(runtime), 'modelsUnloaded': True,
              'normalAppAPIsOnly': True, 'forceKills': False, 'otherToolAndApprovalChoicesUnchanged': True,
              'authorization': authorization, 'observedAppVersion': expected_version}
    with (OUT / receipt_name).open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2); stream.write('\n')
    print(json.dumps(report))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    if parser.parse_args().execute: main()
    else: print(json.dumps({'execute': False, 'stop': 'observed app turns only', 'unload': 'observed model instances only'}))
