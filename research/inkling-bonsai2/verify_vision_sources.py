"""Compare every source vision tensor from the two locally verified safetensors."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from source import atomic_bytes


def header(stream):
    size, = struct.unpack('<Q',stream.read(8))
    return json.loads(stream.read(size)), size+8


def compare(root, output):
    filename='model-00001-of-00001.safetensors'
    matched=0
    bytes_compared=0
    differences=[]
    with (root/'official'/filename).open('rb') as a, (root/'source'/filename).open('rb') as b:
        ha, abase = header(a)
        hb, bbase = header(b)
        keys=sorted({k for k in ha.keys() | hb.keys() if k.startswith('model.visual.')})
        if not keys:
            raise ValueError('No source vision tensors')
        for k in keys:
            x,y=ha.get(k),hb.get(k)
            if not x or not y or (x['shape'],x['dtype'])!=(y['shape'],y['dtype']):
                differences.append(k)
                continue
            ab,ae=x['data_offsets']
            bb,be=y['data_offsets']
            if ae-ab!=be-bb:
                differences.append(k)
                continue
            a.seek(abase+ab)
            b.seek(bbase+bb)
            left=ae-ab
            equal=True
            while left:
                size=min(2**20,left)
                first,second=a.read(size),b.read(size)
                if len(first)!=size or len(second)!=size:
                    raise EOFError(k)
                equal &= first==second
                bytes_compared+=size
                left-=size
            if equal:
                matched+=1
            else:
                differences.append(k)
    configs={}
    for file in ['config.json','processor_config.json']:
        first=json.loads((root/'official'/file).read_bytes())
        second=json.loads((root/'source'/file).read_bytes())
        if file=='config.json':
            first,second=first['vision_config'],second['vision_config']
        configs[file]=first==second
    with (root/'official-models/mmproj-Inkling-2-Mini-F16.gguf').open('rb') as f:
        projector=hashlib.file_digest(f,'sha256').hexdigest()
    result=dict(tensors=len(keys),matched=matched,compared_bytes_per_checkpoint=bytes_compared,
                differing_tensors=differences,configurations_equal=configs,projector_sha256=projector)
    atomic_bytes(output,json.dumps(result,indent=2).encode())
    print('Vision tensors',matched,'/',len(keys),'matching configuration',configs,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    compare(args.root,args.output)
