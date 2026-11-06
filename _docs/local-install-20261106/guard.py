"""Bound an owned packaging/QA command with the project Job Object and resource policy."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/local-052-20261106-opencode')
sys.path[:0] = [str(ROOT), str(ROOT/'tools')]
from serve import winjob
from native_model_resource_guard import available_memory, PressurePolicy

def main() -> int:
    name, seconds, cwd, *command = sys.argv[1:]
    assert name.replace('-', '').isalnum() and command
    assert OUT.parent.is_dir()
    OUT.mkdir(exist_ok=True)
    assert not (OUT/(name+'.json')).exists(), 'Use a fresh receipt name'
    policy = PressurePolicy(physical_floor_bytes=3*1024**3, commit_floor_bytes=4*1024**3, physical_grace_seconds=2)
    report = {'ok': False, 'name': name, 'command': command, 'gpuExecution': False, 'abort': None}
    process = None
    start = time.monotonic()
    try:
        assert shutil.disk_usage('C:/').free >= 5*1024**3
        assert shutil.disk_usage('H:/').free >= 10*1024**3
        sample = available_memory()
        assert policy.observe(sample, time.monotonic()) is None
        with (OUT/(name+'.txt')).open('x', encoding='utf-8') as log, (OUT/(name+'-memory.jsonl')).open('x') as trace:
            worker = 'import json,subprocess,sys; assert sys.stdin.readline().strip()=="GO"; raise SystemExit(subprocess.call(json.loads(sys.argv[1])))'
            process = subprocess.Popen([sys.executable, '-B', '-c', worker, json.dumps(command)], cwd=cwd,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.PIPE, stdout=log,
                stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            assert winjob.contain(process), 'Owned process containment failed'
            process.stdin.write('GO\n'); process.stdin.flush(); process.stdin.close()
            while process.poll() is None:
                now = time.monotonic(); sample = available_memory(); reason = policy.observe(sample, now)
                if now-start > int(seconds): reason = 'deadline'
                if shutil.disk_usage('C:/').free < 5*1024**3: reason = 'C disk floor'
                if shutil.disk_usage('H:/').free < 10*1024**3: reason = 'H disk floor'
                trace.write(json.dumps(dict(sample, seconds=now-start, abort=reason))+'\n'); trace.flush()
                if reason:
                    report['abort'] = reason; winjob.terminate(); break
                time.sleep(1)
            report['exitCode'] = process.wait(timeout=15)
            report['ok'] = report['exitCode'] == 0 and report['abort'] is None
    finally:
        winjob.terminate()
        if process and process.poll() is None: process.kill(); process.wait(timeout=10)
        report['seconds'] = round(time.monotonic()-start, 3)
        (OUT/(name+'.json')).write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(report), flush=True)
    return 0 if report['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
