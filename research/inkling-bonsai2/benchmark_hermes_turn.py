"""Exercise an actual Hermes AIAgent Windows turn against the local GGUF server."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlparse

import requests


def run(args):
    if urlparse(args.url).hostname!='127.0.0.1':
        raise ValueError('A loopback model endpoint is required')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    home=(args.output.parent/'isolated-profile').resolve()
    home.mkdir(exist_ok=True)
    os.environ.update(HERMES_HOME=str(home),TERMINAL_CWD=str(home),PYTHONDONTWRITEBYTECODE='1',
                      HERMES_API_TIMEOUT='14400',NO_PROXY='127.0.0.1,localhost')
    os.chdir(home)
    sys.path.insert(0,str(args.repo))
    props=requests.get(args.url+'/props',timeout=10).json()
    model=requests.get(args.url+'/v1/models',timeout=10).json()['data'][0]['id']
    health=requests.get(args.url+'/health',timeout=10).json()
    if health.get('service')=='strata':
        if health['model']!=args.model.stem or model!=args.model.stem:
            raise ValueError('Unexpected native Strata model behind agent endpoint')
        context=int(health['max_context'])
    else:
        if Path(props['model_path']).resolve()!=args.model.resolve():
            raise ValueError('Unexpected model behind local agent endpoint')
        context=props['default_generation_settings']['n_ctx']
    config=dict(model=dict(default=model,provider='custom',base_url=args.url+'/v1',context_length=context),
        compression=dict(enabled=False),memory=dict(memory_enabled=False,user_profile_enabled=False),
        providers={'custom':{'request_timeout_seconds':14400}},
        agent=dict(max_turns=1),display=dict(streaming=True))
    (home/'config.yaml').write_text(json.dumps(config,indent=2),encoding='utf8')
    from run_agent import AIAgent
    from benchmark_hermes_context import measure_recall
    case=json.loads(args.case.read_bytes())
    first=None
    def on_delta(*values,**kwargs):
        nonlocal first
        if first is None and any(isinstance(v,str) and v for v in values):
            first=time.monotonic()
    agent=AIAgent(base_url=args.url+'/v1',api_key='local-hermes-benchmark',provider='custom',
        api_mode='chat_completions',model=model,max_iterations=1,enabled_toolsets=[],
        skip_context_files=True,load_soul_identity=False,skip_memory=True,skip_background_review=True,
        save_trajectories=False,max_tokens=512,quiet_mode=True,platform='cli',
        reasoning_config={'enabled':False,'effort':'none'},stream_delta_callback=on_delta,
        request_overrides={'temperature':0},session_id='inkling-gguf-context-trial')
    start=time.monotonic()
    started=datetime.now(timezone.utc).isoformat()
    try:
        response=agent.run_conversation(case['messages'][-1]['content'],
                                      system_message=case['messages'][0]['content'],conversation_history=[])
        answer=response.get('final_response') or ''
        record=dict(backend='hermes-agent-windows AIAgent.run_conversation',started_utc=started,
            source_case=case['target'],model=model,finished_utc=datetime.now(timezone.utc).isoformat(),
            seconds=time.monotonic()-start,first_delta_seconds=(first-start) if first is not None else None,
            actual_agent_prompt_tokens=getattr(agent,'last_prompt_tokens',None),
            api_calls=response.get('api_calls'),completed=response.get('completed'),
            error=response.get('error'),final_answer=answer,**measure_recall(answer,case['expected']))
        args.output.write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf8')
        print(json.dumps({k:record[k] for k in ('source_case','api_calls','actual_agent_prompt_tokens','completed','correct_labels')}),flush=True)
        if record['error'] or not record['api_calls']:
            raise RuntimeError(f'The agent turn failed; see {args.output}')
    finally:
        agent.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True)
    for k in ['repo','model','case','output']:
        p.add_argument('--'+k,type=Path,required=True)
    run(p.parse_args())
