"""Full AIME 2025 I and II, with a fixed zero-shot protocol and integer scoring."""
import argparse
import json
from pathlib import Path
import random
import re

from benchmark_generation import ANSWER_HEADER,SEED,STOP,digest,prompt_ids,read,save
from grade_generation import paired,stats
from source import atomic_bytes,download

REPO='math-ai/aime25'
REV='563bb8404243c5f09de6ec262f2db674fe5bce9b'
INSTRUCTION=('Solve the competition problem. Show your reasoning concisely. On your last line write #### '
             'followed by the final integer from 0 to 999. Do not include units on that line.')


def prepare(root,source):
    from transformers import AutoTokenizer
    root.mkdir(parents=True,exist_ok=True)
    data=root/'test.jsonl'
    if not data.exists():
        atomic_bytes(data,download(f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/test.jsonl'))
    rows=[json.loads(x) for x in data.read_bytes().splitlines() if x]
    if len(rows)!=30 or len({r['problem'] for r in rows})!=30 or len({r['id'] for r in rows})!=30:
        raise ValueError('Expected 30 distinct AIME 2025 items')
    tok=AutoTokenizer.from_pretrained(source,local_files_only=True)
    items,gold={},{}
    for r in rows:
        key=f"aime25-{int(r['id']):02d}"
        ids=prompt_ids(tok,r['problem']+'\n\n'+INSTRUCTION)
        if not 0<=int(r['answer'])<=999:
            raise ValueError(f'Invalid item {key}')
        items[key]=dict(suite='aime25',row=int(r['id']),level=None,tokens=ids)
        gold[key]=int(r['answer'])
    keys=list(items)
    random.Random(SEED).shuffle(keys)
    save(root/'gold.json',gold)
    longest=max(len(item['tokens']) for item in items.values())
    slot_context=((longest+4096+255)//256)*256
    save(root/'protocol.json',dict(datasets={'aime25':dict(repo=REPO,revision=REV,split='test',
        population=30,file='test.jsonl',digest=digest(data))},seed=SEED,shots=0,temperature=0,
        samples=1,generation_limits={'aime25':4096},context_per_slot=slot_context,stop=STOP,
        instructions={'aime25':INSTRUCTION},output_channel=ANSWER_HEADER,reasoning_effort='none',
        tokenizer_sha256=digest(source/'tokenizer.json'),template_sha256=digest(source/'chat_template.jinja'),
        full=keys,items=items))
    print('AIME 2025:',len(keys),'items frozen; 4096 output tokens per question',flush=True)


def grade(root):
    spec,gold=read(root/'protocol.json'),read(root/'gold.json')
    scores={}
    out={'expected':len(spec['full']),'protocol_sha256':digest(root/'protocol.json'),'models':{}}
    for model in ('official','ablated'):
        data={}
        for key in spec['full']:
            p=root/model/'answers'/(key+'.json')
            if not p.exists():
                continue
            ans=read(p)
            lines=ans['content'].strip().splitlines()
            hit=re.fullmatch(r'\s*####\s*(\d{1,3})\.?\s*',lines[-1]) if lines else None
            val=int(hit[1]) if hit else None
            data[key]=dict(correct=val==gold[key],extracted=val,method='integer' if hit else 'missing-final',
                        limit=ans['stop']=='limit',empty=not lines,tokens=ans['output_tokens'])
        if data:
            scores[model]=data
            out['models'][model]=stats(list(data.values()))
            save(root/model/'full-scores.json',data)
    if len(scores)==2:
        ids=[k for k in spec['full'] if all(k in v for v in scores.values())]
        if ids:
            out['paired']=paired(ids,scores['official'],scores['ablated'],spec['items'])
    save(root/'full-summary.json',out)
    print({k:(v['correct'],v['n']) for k,v in out['models'].items()})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','grade'])
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source',type=Path)
    args=p.parse_args()
    if args.action=='prepare':
        prepare(args.root,args.source)
    else:
        grade(args.root)
