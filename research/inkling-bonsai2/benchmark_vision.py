"""Two native CUDA image-conditioned colour controls for the prepared projector."""
import argparse
import base64
from datetime import datetime,timezone
from io import BytesIO
from pathlib import Path
import re
import time

from PIL import Image
import requests

from benchmark_generation import local_server,read,save


def run(args):
    folder=args.root/'evaluation'/('sm120-'+args.variant)
    summary=folder/'vision-summary.json'
    if summary.is_file():
        return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    server=folder/('vision-server-'+stamp)
    projector=args.root/'official-models/mmproj-Inkling-2-Mini-F16.gguf'
    rows=[]
    with local_server(args.bin/'llama-server.exe',args.model,server,1,2048,extra=('--mmproj',str(projector))) as url:
        for expected,rgb in [('red',(225,14,14)),('blue',(12,34,225))]:
            png=BytesIO()
            Image.new('RGB',(224,224),rgb).save(png,format='PNG')
            data=base64.b64encode(png.getvalue()).decode()
            parts=[{'type':'image_url','image_url':{'url':'data:image/png;base64,'+data}},
                   {'type':'text','text':'Name the colour of the square in this image. Reply with the single English colour word.'}]
            body=dict(model=args.model.stem,messages=[{'role':'user','content':parts}],
                      max_tokens=48,temperature=0,seed=20261125,cache_prompt=False,
                      logit_bias={'200008':-100},chat_template_kwargs={'reasoning_effort':'none'})
            start=time.monotonic()
            r=requests.post(url+'/v1/chat/completions',json=body,timeout=(10,300))
            r.raise_for_status()
            out=r.json()
            text=out['choices'][0]['message'].get('content') or ''
            colours=set(re.findall(r'\b(red|blue|green|yellow|black|white|grey|gray|orange|purple|pink|brown)\b',text.lower()))
            rows.append(dict(expected=expected,rgb=rgb,answer=text,correct=colours=={expected},
                         elapsed_seconds=time.monotonic()-start,usage=out['usage'],timings=out.get('timings'),
                         finish_reason=out['choices'][0]['finish_reason']))
    correct=sum(r['correct'] for r in rows)
    info=dict(results=rows,projector=projector.name,model=args.model.name,
              server=server.name,measurement=read(server/'measurement.json'),
              card_sentence=f'An end-to-end CUDA test answered {correct}/2 solid-colour controls correctly. General visual ability remains unmeasured.')
    save(summary,info)
    print(info['card_sentence'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['root','bin','model']:
        p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--variant',required=True,choices=['official','ablated'])
    run(p.parse_args())
