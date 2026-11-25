"""Measure the Strata-owned Inkling engine against real GGUF and source-reference logits."""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import statistics
import tempfile

from filelock import FileLock
import numpy as np
from tokenizers import Tokenizer

from benchmark_generation import save
from benchmark_inkling2 import score
from sm120_native import run


def evaluate(args):
    evidence = args.root / 'evaluation'
    folder = evidence / ('sm120-' + args.variant) / 'strata-native-kernels'
    folder.mkdir(exist_ok=True, parents=True)
    attempt = folder / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    attempt.mkdir()
    tokenizer = Tokenizer.from_file(str(args.root / 'official' / 'tokenizer.json'))
    text = 'The capital of France is'
    ids = tokenizer.encode(text, add_special_tokens=False).ids
    model_flags = ['--native', str(args.model), '--gpu', '0', '--parallel', '1', '--max-context', '2048',
                   '--kv', 'k8v4', '--draft', 'off', '--cpu-threads', '5', '--vram-reserve-mib', '1536']
    lock = FileLock(str(Path(tempfile.gettempdir()) / 'strata-inkling-benchmark-gpu0.lock'))
    def invoke(name, flags):
        dest = attempt / name
        with lock:
            receipt = run(dest, [str(args.engine), *flags, *model_flags], 12000, 1800, 1800)
        return (dest / 'stdout.txt').read_text(encoding='utf8', errors='replace'), receipt
    generated, receipt = invoke('generation', ['--prompt-ids', ','.join(map(str, ids)), '--gen', '16'])
    lines = [line for line in generated.splitlines() if re.fullmatch(r'\d+(,\d+)*', line.strip())]
    if not lines:
        raise ValueError(f'No generated token IDs in {attempt}')
    generated_ids = [int(t) for t in lines[-1].split(',')]
    result = dict(engine='strata-inkling', model=args.model.name, variant=args.variant, input_text=text,
                  input_ids=ids, output_ids=generated_ids, output_text=tokenizer.decode(generated_ids, skip_special_tokens=False),
                  peak_generation_vram_bytes=receipt['peak_device_used_bytes'], attempts_directory=str(attempt))
    save(attempt / 'generation.json', result)
    speeds = []
    for trial in range(3):
        out, receipt = invoke(f'bench-{trial+1}', ['--bench', '--prompt-len', '128', '--gen', '32'])
        m = re.search(r'\[bench\] backend=(\S+).*?prefill=([\d.]+) ppts.*?decode=([\d.]+) tps', out)
        if not m or 'cuda' not in m[1].lower():
            raise ValueError(f'Expected a native CUDA benchmark in {attempt}')
        speeds.append(dict(backend=m[1], prefill=float(m[2]), decode=float(m[3]),
                           peak_vram_bytes=receipt['peak_device_used_bytes']))
    result.update(throughput=speeds, prefill_mean=statistics.mean(s['prefill'] for s in speeds),
                  decode_mean=statistics.mean(s['decode'] for s in speeds))
    save(folder/'performance.json', result)
    references = evidence / ('official-dynamic' if args.variant=='official' else 'ablated-bf16-heldout')
    seqs = sorted(references.glob('holdout-*.npz'))
    comparisons = {}
    for ref in seqs:
        with np.load(ref) as saved:
            tokens = saved['input_ids'][0]
            output = attempt / (ref.stem + '.bin')
            native_out, _ = invoke(ref.stem, ['--dump-ref', str(output), '--prompt-ids', ','.join(map(str,tokens))])
            if 'cuda' not in native_out.lower():
                raise ValueError('Logit dump did not attest to CUDA')
            with output.open('rb') as fh:
                n, vocab = map(int, np.fromfile(fh, dtype='<i4', count=2))
                check = np.fromfile(fh, dtype='<i4', count=n)
            if not np.array_equal(check, tokens) or output.stat().st_size != 8+4*n+4*n*vocab:
                raise ValueError('Native logits have an invalid token trajectory or extent')
            logits = np.memmap(output, dtype='<f4', mode='r', offset=8+4*n, shape=(n,vocab))
            comparisons[ref.stem] = score(saved['logits'], logits, tokens)
    if comparisons:
        n = sum(r['tokens'] for r in comparisons.values())
        result['source_comparison'] = dict(sequences=comparisons, tokens=n,
            mean_kl=sum(r['sum_kl'] for r in comparisons.values())/n,
            top1=sum(r['argmax_matches'] for r in comparisons.values())/n,
            reference_ppl=math.exp(sum(r['sum_reference_nll'] for r in comparisons.values())/n),
            candidate_ppl=math.exp(sum(r['sum_candidate_nll'] for r in comparisons.values())/n))
    save(folder/'results.json',result)
    print(json.dumps({k:result[k] for k in ('model','output_text','prefill_mean','decode_mean')},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','engine','model'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--variant',choices=('official','ablated'),required=True)
    evaluate(p.parse_args())
