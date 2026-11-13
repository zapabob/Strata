"""Run candidate commands under the preserved resource/process guard."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-059-20261113-codex')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--seconds', type=int, default=300)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not args.execute:
        print(json.dumps({'execute': False, 'out': str(OUT), 'command': command}))
        return 0
    if not command or command[0] not in ('node', 'python'):
        parser.error('An explicit Node or Python driver is required')
    OUT.mkdir(exist_ok=True)
    for name in ('receipts', 'temp', 'cache'):
        (OUT / name).mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location('candidate_guard', ROOT / '_docs/local-053-20261109/native/common.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE = OUT
    guard.NODE = ROOT / 'apps/desktop/src-tauri/resources/node/node.exe'
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    command[0] = str(guard.NODE) if command[0] == 'node' else sys.executable
    for index, part in enumerate(command[1:], 1):
        if (ROOT / part).is_file():
            command[index] = str(ROOT / part)
    env = guard.environment()
    env['PATH'] += ';C:/Windows/System32/WindowsPowerShell/v1.0;C:/Users/downl/.cargo/bin;' + str(Path(shutil.which('pwsh')).parent)
    env['PATHEXT'] = os.environ.get('PATHEXT', '.COM;.EXE;.BAT;.CMD')
    env.update(CARGO_BUILD_JOBS='5', CMAKE_BUILD_PARALLEL_LEVEL='5', PYTHONUTF8='1',
               PYTHONIOENCODING='utf-8', STRATA_TEST_CONCURRENCY='2')
    result = guard.owned(ROOT, args.name, command, args.seconds, env=env, output_bytes=32 * 1024**2)
    print(json.dumps(result, indent=2))
    if not result['passed']:
        output = re.sub(r'data:text/javascript;base64,[A-Za-z0-9+/=]+', '<bundled-test-module>', guard.text(args.name))
        print(output[-16000:])
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
