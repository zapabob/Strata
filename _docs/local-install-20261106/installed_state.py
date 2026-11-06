"""Read only owned Strata process/API status; never print private state or command lines."""
from __future__ import annotations
import json
from pathlib import Path
import time
import urllib.request
import psutil

TARGET = Path('C:/Users/downl/AppData/Local/Programs/Strata')

def shells() -> list[psutil.Process]:
    result = []
    for process in psutil.process_iter(['name','exe']):
        if (process.info['name'] or '').lower() == 'strata-desktop.exe':
            assert process.info['exe'] and Path(process.info['exe']).resolve() == (TARGET/'strata-desktop.exe').resolve(), 'An unrelated Strata shell is running'
            result.append(process)
    return result

def endpoint(process: psutil.Process) -> str:
    for child in process.children():
        if Path(child.exe()).resolve() != (TARGET/'node/node.exe').resolve():
            continue
        for connection in child.net_connections(kind='tcp'):
            if connection.status == psutil.CONN_LISTEN and connection.laddr.ip == '127.0.0.1':
                base = f'http://127.0.0.1:{connection.laddr.port}'
                try:
                    if get(base, '/api/health').get('ok') is True:
                        return base
                except (OSError,ValueError):
                    pass
    raise RuntimeError('Owned installed Host endpoint unavailable')

def get(base: str, route: str) -> dict:
    with urllib.request.urlopen(base+route, timeout=30) as response:
        assert response.status == 200
        return json.load(response)

def idle(base: str) -> dict:
    model = get(base, '/api/models')
    active = get(base, '/api/chat/active')
    serving = get(base, '/api/serving')
    stats = serving['stats']
    result = {'modelUnloaded':model['loaded'] is None,'engineStopped':model['engine']['status']=='stopped',
              'activeTurns':len(active['turns']),'runningRequests':stats['running'],'queuedRequests':stats['waiting']}
    result['idle'] = result['modelUnloaded'] and result['engineStopped'] and result['activeTurns']==0 and result['runningRequests']==0 and result['queuedRequests']==0
    return result

if __name__ == '__main__':
    processes = shells()
    report = {'shellCount':len(processes),'checks':[]}
    for process in processes:
        base = endpoint(process)
        for _ in range(3):
            report['checks'].append(idle(base));time.sleep(1)
    print(json.dumps(report))
