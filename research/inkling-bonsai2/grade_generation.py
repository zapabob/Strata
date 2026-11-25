"""Grade completed native generations and compare the two GGUFs item by item."""
import argparse
from collections import Counter
from fractions import Fraction
import math
import multiprocessing as mp
from pathlib import Path
import re
import statistics

import numpy as np

from benchmark_generation import GSM, MATH, SEED, digest, read, save


NUM = r'[-+]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:/\d+)?'
FINAL = re.compile(r'^\s*####\s*\$?\s*(' + NUM + r')\.?\s*$', re.MULTILINE)


def numeric(value):
    return Fraction(value.replace(',', ''))


def extract_gsm(text):
    last = text.rstrip().splitlines()[-1:] or ['']
    m = FINAL.fullmatch(last[0])
    return m.group(1) if m else None


def last_box(text):
    starts = list(re.finditer(r'\\(?:boxed|fbox)\s*\{', text))
    if not starts:
        return None
    start = starts[-1].end()
    depth = 1
    for i in range(start, len(text)):
        if text[i] not in '{}':
            continue
        j = i
        while j > 0 and text[j-1] == '\\':
            j -= 1
        if (i-j) % 2:
            continue
        depth += 1 if text[i] == '{' else -1
        if not depth:
            return text[start:i].strip() or None
    return None


def math_worker(pipe):
    from math_verify import LatexExtractionConfig, parse, verify
    cfg = [LatexExtractionConfig()]
    pipe.send(True)
    while True:
        try:
            gold, answer = pipe.recv()
        except EOFError:
            return
        try:
            def expr(v):
                return parse(r'$\boxed{' + v + r'}$', extraction_config=cfg,
                             fallback_mode='no_fallback', parsing_timeout=0)
            a, b = expr(gold), expr(answer)
            if not a or not b:
                pipe.send((False, 'unparsed'))
            else:
                pipe.send((bool(verify(a, b, timeout_seconds=0)), 'symbolic'))
        except Exception as exc:
            pipe.send((False, 'verifier-error-' + type(exc).__name__))


class Grader:
    def __init__(self):
        self.proc = None
        self.pipe = None

    def close(self):
        if self.pipe is not None:
            self.pipe.close()
        if self.proc is not None:
            self.proc.join(0.4)
            if self.proc.is_alive():
                self.proc.terminate()
                self.proc.join(5)
        self.proc = self.pipe = None

    def math(self, gold, answer):
        if gold.strip() == answer.strip():
            return True, 'exact'
        if self.proc is None:
            ctx = mp.get_context('spawn')
            self.pipe, child = ctx.Pipe()
            self.proc = ctx.Process(target=math_worker,args=(child,),daemon=True)
            self.proc.start()
            child.close()
            if not self.pipe.poll(60) or not self.pipe.recv():
                self.close()
                raise RuntimeError('Cannot start Math-Verify')
        self.pipe.send((gold, answer))
        if not self.pipe.poll(12):
            self.close()
            return False, 'verifier-timeout'
        return self.pipe.recv()

    def score(self, suite, expected, result):
        text = result['content']
        value = (extract_gsm if suite == GSM else last_box)(text)
        if value is None:
            correct, method = False, 'missing-final'
        elif suite == GSM:
            correct, method = numeric(value) == numeric(expected), 'numeric'
        else:
            correct, method = self.math(expected, value)
        return dict(correct=correct, extracted=value, method=method,
                    limit=result['stop']=='limit', empty=not text.strip(),
                    tokens=result['output_tokens'], seconds=result['elapsed_seconds'])


def wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    p = k/n
    d = 1 + z*z/n
    mid = (p + z*z/(2*n))/d
    span = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return [max(0.,mid-span),min(1.,mid+span)]


def stats(rows):
    n = len(rows)
    k = sum(row['correct'] for row in rows)
    unparseable=sum(row['extracted'] is None or row['method']=='unparsed' for row in rows)
    verifier_failures=sum(row['method'].startswith('verifier-') for row in rows)
    return dict(n=n, generated=n, scored=n, correct=k, truncated=sum(row['limit'] for row in rows),
                unparseable=unparseable, verifier_failures=verifier_failures,
                accuracy=k/n if n else None, wilson95=wilson(k,n),
                missing_final=sum(row['extracted'] is None for row in rows),
                empty=sum(row['empty'] for row in rows), at_limit=sum(row['limit'] for row in rows),
                incorrect_at_limit=sum(row['limit'] and not row['correct'] for row in rows),
                mean_tokens=statistics.mean(row['tokens'] for row in rows) if n else None,
                methods=dict(Counter(row['method'] for row in rows)))


def paired(keys, a, b, items):
    cells = Counter((a[k]['correct'], b[k]['correct']) for k in keys)
    # Paired resampling within each difficulty stratum preserves the sampling design.
    levels = sorted({str(items[k]['level']) for k in keys})
    rng = np.random.default_rng(SEED)
    draws = np.zeros(10000)
    for level in levels:
        d = np.array([int(b[k]['correct'])-int(a[k]['correct'])
                      for k in keys if str(items[k]['level'])==level])
        probs = np.array([(d==-1).mean(), (d==0).mean(), (d==1).mean()])
        samples = rng.multinomial(len(d),probs,size=draws.size)
        draws += samples[:,2]-samples[:,0]
    return dict(n=len(keys), both_correct=cells[True,True], official_only=cells[True,False],
                ablated_only=cells[False,True], both_incorrect=cells[False,False],
                ablated_minus_official=(cells[False,True]-cells[True,False])/len(keys),
                paired_bootstrap95=np.quantile(draws/len(keys),[.025,.975]).tolist())


def run(root, stage):
    from importlib.metadata import version
    results = {}
    spec, gold = read(root/'protocol.json'), read(root/'gold.json')
    keys, items = spec[stage], spec['items']
    out = dict(stage=stage, protocol_sha256=digest(root/'protocol.json'),
               grading_version='strict-final-v1', math_verify=version('math-verify'), models={}, paired={})
    grader = Grader()
    try:
        # Explicit regression checks run before touching model scores.
        assert numeric(extract_gsm('42 is intermediate.\n#### -2,014.50')) == Fraction(-4029,2)
        assert extract_gsm('A total of 9') is None
        assert last_box(r'\boxed{\frac{1}{2}}') == r'\frac{1}{2}'
        assert last_box(r'\boxed{3} then \boxed{4') is None
        assert grader.math(r'\frac{1}{2}','0.5')[0]
        assert not grader.math('3','-3')[0]
        for name in ('official','ablated'):
            location = root/name/'answers'
            if not location.is_dir():
                continue
            scored = {}
            for k in keys:
                file = location/(k+'.json')
                if file.is_file():
                    ans = read(file)
                    if ans['key'] != k:
                        raise ValueError(f'Answer identity mismatch for {k}')
                    scored[k] = grader.score(items[k]['suite'], gold[k], ans)
            results[name] = scored
            save(root/name/(stage+'-scores.json'), scored)
            suites = {}
            for suite in (GSM,MATH):
                selected = [k for k in keys if items[k]['suite']==suite]
                valid = [k for k in selected if k in scored]
                suites[suite] = dict(expected=len(selected), **stats([scored[k] for k in valid]))
                if suite==MATH:
                    suites[suite]['levels'] = {str(level): stats([scored[k] for k in valid
                        if items[k]['level']==level]) for level in range(1,6)}
            out['models'][name] = suites
        if len(results)==2:
            a,b = results['official'],results['ablated']
            for suite in (GSM,MATH):
                both = [k for k in keys if items[k]['suite']==suite and k in a and k in b]
                if both:
                    out['paired'][suite] = paired(both,a,b,items)
    finally:
        grader.close()
    save(root/(stage+'-summary.json'),out)
    for name,suites in out['models'].items():
        print(name, {s:(r['correct'],r['n'],r['expected']) for s,r in suites.items()})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--stage',choices=['pilot','full'],required=True)
    args = parser.parse_args()
    run(args.root,args.stage)
