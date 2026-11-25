"""Run the normal Strata Terminal entry point, check chat, and exercise the Windows Hermes agent."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import psutil

import requests

from benchmark_generation import local_server, read, save


def run(args):
    root = args.root / 'evaluation'
    work = root / ('sm120-' + args.variant) / 'strata-native'
    work.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    entry = Path(__file__).resolve().parents[2] / 'terminal' / 'strata.py'
    folder = work / ('server-' + stamp)
    python = [sys.executable, '-B', str(entry)]
    def launcher(port):
        return python + ['launch', '--family', 'inkling-2-mini', '--inkling-engine', str(args.bin),
                         '--model-path', str(args.model), '--context', '65536', '--parallel', '1',
                         '--data-dir', str(folder / 'profile'), '--port', str(port)]
    checked = subprocess.run(launcher(8080) + ['--plan', '--output', 'json'], capture_output=True, check=True)
    plan = json.loads(checked.stdout)
    if not plan['ok'] or plan['backend'] != 'strata-inkling':
        raise ValueError('Unexpected Strata launch plan')
    with local_server(args.bin, args.model, folder, 1, 65536, launcher=launcher) as base:
        models = requests.get(base + '/v1/models', timeout=10).json()
        alias = args.model.stem
        if alias not in [m['id'] for m in models['data']]:
            raise ValueError('Strata did not serve the selected model')
        response = requests.post(base + '/v1/chat/completions', timeout=(10, 240), json={
            'model': alias, 'messages': [{'role': 'user', 'content': 'What is 17 plus 25? Reply with the number only.'}],
            'temperature': 0, 'max_tokens': 96, 'reasoning_effort': 'none', 'cache_prompt': False})
        response.raise_for_status()
        chat = response.json()
        message = chat['choices'][0]['message']
        answer = (message.get('content') or '').strip()
        save(folder / 'chat.json', chat)
        engines = []
        for child in psutil.Process().children(recursive=True):
            try:
                if Path(child.exe()).resolve() == args.bin.resolve() and '--serve' in child.cmdline():
                    engines.append(dict(pid=child.pid, executable=child.exe(), command=child.cmdline()))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if len(engines)!=1 or str(args.model.resolve()).casefold() not in [x.casefold() for x in engines[0]['command']]:
            raise ValueError('Could not identify the native engine process serving this exact GGUF')
        save(folder / 'engine-process.json', engines[0])
        check = subprocess.run(python + ['connect', 'hermes', '--url', base, '--model', alias,
                               '--check', '--output', 'json'], capture_output=True, timeout=560)
        (folder / 'strata-connect.stdout').write_bytes(check.stdout)
        (folder / 'strata-connect.stderr').write_bytes(check.stderr)
        env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
        env.pop('PYTHONPATH', None)
        agent = subprocess.run([str(args.hermes / '.venv/Scripts/python.exe'), '-B',
                   str(Path(__file__).with_name('benchmark_hermes_turn.py')),
                   '--repo', str(args.hermes), '--case', str(root / 'hermes-long-context/case-512.json'),
                   '--url', base, '--model', str(args.model), '--output', str(folder / 'agent.json')],
                   capture_output=True, env=env, timeout=560)
        (folder / 'agent.log').write_bytes(agent.stdout + agent.stderr)
        agent_data = read(folder / 'agent.json') if (folder / 'agent.json').is_file() else {}
    record = dict(entry='strata launch', variant=args.variant, runtime=plan['backend'],
                  url=base, file=args.model.name, model_id=alias, context_per_slot=65536,
                  answer=answer, correct=answer == '42', visible=bool(answer), usage=chat['usage'],
                  engine_identity_verified=True,
                  strata_connect_exit=check.returncode, agent_exit=agent.returncode,
                  agent_completed=agent_data.get('completed'), agent_prompt_tokens=agent_data.get('actual_agent_prompt_tokens'),
                  agent_recall=len(agent_data.get('correct_labels',[])), evidence_dir=str(folder))
    save(work / 'latest.json', record)
    print(json.dumps(record, ensure_ascii=False), flush=True)
    if not record['visible']:
        raise ValueError('The native Strata chat returned no visible content; see latest.json')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'bin', 'model', 'hermes'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--variant', choices=('official', 'ablated'), required=True)
    run(p.parse_args())
