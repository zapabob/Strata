"""Metadata-only diagnostics for this QA shell and its WebView processes."""
import json
import re
import sys
import psutil
import winreg

pid, port = map(int, sys.argv[1:])
process = psutil.Process(pid)
rows = []
for child in [process, *process.children(recursive=True)]:
    try:
        command = ' '.join(child.cmdline())
        connections = child.net_connections(kind='tcp')
        rows.append({'pid':child.pid,'name':child.name(),
            'debugPortMatches':f'--remote-debugging-port={port}' in command,
            'debugFlags':re.findall(r'--remote-debugging-[a-z-]+(?:=[0-9.:]+)?',command),
            'listeningPorts':[c.laddr.port for c in connections if c.status==psutil.CONN_LISTEN]})
    except (psutil.NoSuchProcess,psutil.AccessDenied):
        continue
policy = []
for hive in [winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE]:
    for key in [r'Software\Policies\Microsoft\Edge',r'Software\Policies\Microsoft\Edge\WebView2']:
        try:
            with winreg.OpenKey(hive,key) as handle:
                policy.append({'remoteDebuggingAllowed':winreg.QueryValueEx(handle,'RemoteDebuggingAllowed')[0]})
        except FileNotFoundError:
            pass
print(json.dumps({'processes':rows,'policy':policy}))
