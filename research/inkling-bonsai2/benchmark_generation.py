"""Reproducible zero-shot GSM8K and MATH-500 generation on a local Inkling GGUF."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import socket
import subprocess
import tempfile
import threading
import time

import requests

from source import atomic_bytes, download


GSM = 'gsm8k'
MATH = 'math500'
DATA = {
    GSM: ('openai/gsm8k', '740312add88f781978c0658806c59bc2815b9866',
          'main/test-00000-of-00001.parquet', 'gsm8k.parquet', 1319),
    MATH: ('HuggingFaceH4/MATH-500', '6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be',
           'test.jsonl', 'math-500.jsonl', 500),
}
LIMIT = {GSM: 512, MATH: 1024}
INSTRUCTION = {
    GSM: 'Solve the problem, showing your calculation briefly. On the last line write #### followed by the final numeric answer, without units.',
    MATH: r'Solve the problem, giving a concise mathematical justification. Put your final answer in a single \boxed{...} at the end.',
}
ANSWER_HEADER = '<|message_model|><|content_text|>'
STOP = ['<|end_message|>', '<|content_model_end_sampling|>', '<|message_user|>']
SEED = 20261125


def save(path, value):
    atomic_bytes(path, json.dumps(value, ensure_ascii=False, allow_nan=False,
                                 indent=2).encode('utf-8'))


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def now():
    return datetime.now(timezone.utc).isoformat()


def prompt_ids(tokenizer, user_text):
    chat = tokenizer.apply_chat_template([{'role': 'user', 'content': user_text}],
        tokenize=False, add_generation_prompt=True, reasoning_effort='none')
    if not chat.endswith('<|end_message|>'):
        raise ValueError('Unexpected official generation boundary')
    return tokenizer.encode(chat + ANSWER_HEADER, add_special_tokens=False)


def prepare(root, source):
    import pyarrow.parquet as pq
    from transformers import AutoTokenizer

    data = root / 'data'
    data.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(source, local_files_only=True)
    special = [tokenizer.convert_tokens_to_ids(t) for t in ('<|message_model|>', '<|content_text|>')]
    if tokenizer.encode(ANSWER_HEADER, add_special_tokens=False) != special:
        raise ValueError('Incorrect assistant special token IDs')
    items, gold, datasets, pilot = {}, {}, {}, []
    for suite, (repo, rev, remote, local, population) in DATA.items():
        asset = data / local
        if not asset.is_file():
            atomic_bytes(asset, download(f'https://huggingface.co/datasets/{repo}/resolve/{rev}/{remote}'))
        rows = (pq.read_table(asset).to_pylist() if suite == GSM else
                [json.loads(line) for line in asset.read_bytes().splitlines() if line])
        if len(rows) != population:
            raise ValueError(f'{suite} has {len(rows)} items, expected {population}')
        datasets[suite] = dict(repo=repo, revision=rev, file=remote, split='test',
                               population=population, digest=digest(asset))
        strata = {}
        for index, row in enumerate(rows):
            key = f'{suite}-{index:04}'
            question = row['question' if suite == GSM else 'problem']
            level = None if suite == GSM else int(row['level'])
            tokens = prompt_ids(tokenizer, question + '\n\n' + INSTRUCTION[suite])
            if len(tokens) + LIMIT[suite] > 2048:
                raise ValueError(f'Insufficient slot context for {key}')
            items[key] = dict(suite=suite, row=index, id=row.get('unique_id', key),
                              level=level, subject=row.get('subject'), tokens=tokens)
            gold[key] = row['answer'].rsplit('####', 1)[-1].strip() if suite == GSM else row['answer']
            strata.setdefault(level, []).append(key)
        rng = random.Random(SEED)
        for level, keys in sorted(strata.items()):
            pilot.extend(rng.sample(keys, 64 if suite == GSM else 10))
    rng = random.Random(SEED)
    rng.shuffle(pilot)
    rest = sorted(set(items) - set(pilot))
    rng.shuffle(rest)
    specification = dict(datasets=datasets, seed=SEED, shots=0, temperature=0, samples=1,
        instructions=INSTRUCTION, generation_limits=LIMIT, stop=STOP, reasoning_effort='none',
        output_channel=ANSWER_HEADER, tokenizer_sha256=digest(source/'tokenizer.json'),
        template_sha256=digest(source/'chat_template.jinja'), pilot=pilot, full=pilot+rest, items=items)
    # Keep evaluator labels outside the generation manifest.
    save(root/'gold.json', gold)
    save(root/'protocol.json', specification)
    print('Frozen protocol:', len(pilot), 'pilot,', len(items), 'full, largest prompt',
          max(len(row['tokens']) for row in items.values()), 'tokens', flush=True)


@contextmanager
def local_server(binary, model, folder, slots, context, batch=512, ubatch=128, extra=(), admission=12000, launcher=None):
    from filelock import FileLock

    lock = FileLock(str(Path(tempfile.gettempdir()) / 'strata-inkling-benchmark-gpu0.lock'))
    with lock, _local_server(binary, model, folder, slots, context, batch, ubatch, extra, admission, launcher) as base:
        yield base


@contextmanager
def _local_server(binary, model, folder, slots, context, batch, ubatch, extra, admission, launcher):
    from sm120_native import MemoryPolicy, Nvml, available_memory

    folder.mkdir(parents=True, exist_ok=False)
    gpu = Nvml()
    pressure = MemoryPolicy(physical_floor_bytes=3*2**30, commit_floor_bytes=4*2**30,
                            physical_grace_seconds=0)
    def sample():
        return dict(utc=now(), **available_memory(), **gpu.memory(),
                    destination_free_bytes=shutil.disk_usage(folder).free,
                    system_free_bytes=shutil.disk_usage(Path(os.environ['SystemRoot']).anchor).free)
    def check_capacity():
        headroom = sample()
        return headroom['device_free_bytes'] >= admission*2**20 and not pressure.observe(headroom, time.monotonic())

    until = time.monotonic()+1800
    while not check_capacity():
        if time.monotonic() > until:
            raise TimeoutError(f'GPU admission timed out. See {folder}')
        time.sleep(5)
    baseline = sample()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    cmd = [str(binary), '-m', str(model), '--host', '127.0.0.1', '--port', str(port),
           '-ngl', '99', '-np', str(slots), '-c', str(context), '-t', '5', '-b', str(batch),
           '-ub', str(ubatch), '--no-warmup', '--no-webui', '--cache-ram', '0',
           '--no-context-shift', *extra]
    if launcher is not None:
        cmd = launcher(port)
    started = now()
    finished = threading.Event()
    events = []
    peak = baseline['device_used_bytes']
    minimum = baseline['device_free_bytes']
    count = 0
    with (folder/'server.log').open('x', encoding='utf8') as log:
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        def monitor():
            nonlocal peak, minimum, count
            try:
                with (folder/'resources.jsonl').open('x', encoding='utf8', buffering=1) as trace:
                    while not finished.is_set():
                        snap = sample()
                        trace.write(json.dumps(snap)+'\n')
                        count += 1
                        peak = max(peak, snap['device_used_bytes'])
                        minimum = min(minimum, snap['device_free_bytes'])
                        reason = pressure.observe(snap, time.monotonic())
                        if reason:
                            events.append(reason)
                            break
                        finished.wait(1)
            except Exception as exc:
                events.append(repr(exc))
            if events and proc.poll() is None:
                proc.terminate()
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{port}'
        ready = False
        succeeded = False
        try:
            deadline = time.monotonic()+420
            while proc.poll() is None and time.monotonic() < deadline:
                try:
                    status = requests.get(base+'/health', timeout=3)
                    if status.ok and status.json().get('status') == 'ok':
                        ready = True
                        break
                except requests.RequestException:
                    pass
                time.sleep(1)
            if not ready:
                raise RuntimeError(f'Local server did not start (code {proc.poll()}, {events}). See {folder}/server.log')
            props = requests.get(base+'/props', timeout=10)
            props.raise_for_status()
            info = props.json()
            if launcher is None:
                if Path(info['model_path']).resolve() != model.resolve() or info['total_slots'] != slots:
                    raise ValueError('Unexpected model or slot count on the local endpoint')
                identity = dict(model_path=info['model_path'], total_slots=info['total_slots'],
                                context=info.get('default_generation_settings',{}).get('n_ctx'))
            else:
                health = status.json()
                if health.get('service') != 'strata' or health.get('model') != model.stem:
                    raise ValueError(f'Unexpected native Strata service or model: {health}')
                identity = dict(service='strata', model=health['model'], context=health['max_context'])
            save(folder/'server-identity.json', identity)
            yield base
            if events or proc.poll() is not None:
                raise RuntimeError(f'Local server stopped unexpectedly: {events} {proc.poll()}')
            succeeded = True
        finally:
            finished.set()
            thread.join(5)
            if proc.poll() is None:
                proc.terminate()
            proc.wait(timeout=30)
            save(folder/'measurement.json', dict(gpu=gpu.name, cmd=cmd, pid=proc.pid, started=started,
                finished=now(), became_ready=ready, workload_completed=succeeded,
                protection_events=events, samples=count, sample_seconds=1,
                baseline_device_used_bytes=baseline['device_used_bytes'], peak_device_used_bytes=peak,
                min_device_free_bytes=minimum))


def complete(base, tokens, limit):
    body = dict(prompt=tokens, temperature=0, seed=SEED, n_predict=limit, stop=STOP, return_tokens=True,
                repeat_penalty=1.0, cache_prompt=False, stream=False)
    started = time.monotonic()
    response = requests.post(base+'/completion', json=body, timeout=(10,900))
    response.raise_for_status()
    result = response.json()
    if (result.get('truncated') or result['tokens_evaluated'] != len(tokens)
            or result['stop_type'] not in ('eos','word','limit')):
        raise ValueError(f"Native token accounting failed: {len(tokens)}, {result.get('tokens_evaluated')}, {result.get('stop_type')}, {result.get('truncated')}")
    raw_ids = result.get('tokens')
    if not isinstance(raw_ids, list) or any(type(t) is not int or t < 0 for t in raw_ids):
        raise ValueError('The raw completion endpoint did not supply generated token IDs')
    return dict(content=result['content'], output_ids=raw_ids, stop=result['stop_type'], stopping_word=result.get('stopping_word'),
                input_tokens=len(tokens), output_tokens=result['tokens_predicted'],
                timings=result['timings'], elapsed_seconds=time.monotonic()-started, utc=now())


def generate(args):
    protocol = read(args.root/'protocol.json')
    selection = protocol[args.stage]
    items = protocol['items']
    folder = args.root/args.variant
    answers = folder/'answers'
    answers.mkdir(parents=True,exist_ok=True)
    manifest = read(args.manifest)
    if manifest['bytes'] != args.model.stat().st_size:
        raise ValueError('Manifest and GGUF extent differ')
    slot_context=protocol.get('context_per_slot',2048)
    identifier = dict(model=str(args.model.resolve()), manifest=digest(args.manifest),
                      protocol=digest(args.root/'protocol.json'), slots=args.slots,
                      context_per_slot=slot_context, temperature=0, seed=SEED, backend=digest(args.bin))
    identity = folder/'identity.json'
    if identity.exists() and read(identity)!=identifier:
        raise ValueError('Existing results use a different model or protocol')
    save(identity, identifier)
    pending = [key for key in selection if not (answers/(key+'.json')).exists()]
    if not pending:
        return
    completed = len(selection)-len(pending)
    # Release the single SM120 between groups so that calibration and parity jobs can run.
    for start in range(0,len(pending),2*args.slots):
        group=pending[start:start+2*args.slots]
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        using=local_server(args.bin,args.model,folder/('server-'+stamp),args.slots,slot_context*args.slots)
        with using as base:
            run_group(base,group,args.slots,items,protocol,answers)
        completed+=len(group)
        print(f'{args.variant} {args.stage} {completed}/{len(selection)}',flush=True)
        if completed < len(selection):
            time.sleep(.5)


def run_group(base, group, slots, items, protocol, answers):
    def one(key):
        row = items[key]
        for retry in range(3):
            try:
                answer = complete(base, row['tokens'], protocol['generation_limits'][row['suite']])
                break
            except requests.RequestException:
                if retry == 2:
                    raise
                time.sleep(2**retry)
        save(answers/(key+'.json'), dict(key=key, **answer))
        return key
    print(f'Generating {len(group)} items',flush=True)
    with ThreadPoolExecutor(max_workers=slots) as pool:
        iterator = iter(group)
        running = {pool.submit(one,key) for _,key in zip(range(slots),iterator)}
        while running:
            job = next(as_completed(running))
            running.remove(job)
            job.result()
            key = next(iterator,None)
            if key is not None:
                running.add(pool.submit(one,key))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare','generate'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--variant', choices=['official','ablated'])
    parser.add_argument('--stage', choices=['pilot','full'], default='pilot')
    parser.add_argument('--model', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--bin', type=Path)
    parser.add_argument('--slots',type=int,default=8)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.root,args.source)
    else:
        generate(args)
