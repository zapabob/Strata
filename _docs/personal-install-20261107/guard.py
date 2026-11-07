"""Bound only a parent-approved owned child; never stop or restore other servers."""
from __future__ import annotations
import argparse
import json
import subprocess
import time
from common import *

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name',required=True)
    parser.add_argument('--seconds',type=int,required=True)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    require(re.fullmatch('[a-z0-9-]+',args.name) is not None and 1<=args.seconds<=3600,'Invalid guard identity/deadline')
    command=args.command[1:] if args.command[:1]==['--'] else args.command
    require(bool(command),'Command required')
    if not args.execute:
        print(json.dumps({'wouldExecute':False,'deadlineSeconds':args.seconds,'resourceBlockers':blockers(resources())}));return 0
    require_resources();receipts=OUT/'receipts';receipts.mkdir(exist_ok=True)
    path=receipts/f'job-{args.name}.json';require(not path.exists(),'Fresh guard receipt required')
    sys.path.insert(0,str(ROOT));from serve import winjob
    report={'ok':False,'abort':None,'deadlineSeconds':args.seconds,'ownedOnly':True,'restorationPerformed':False}
    child=None;started=time.monotonic()
    try:
        with (receipts/f'job-{args.name}.txt').open('x',encoding='utf-8') as log, (receipts/f'job-{args.name}-memory.jsonl').open('x') as samples:
            worker='import json,subprocess,sys; assert sys.stdin.readline().strip()=="GO"; raise SystemExit(subprocess.call(json.loads(sys.argv[1])))'
            child=subprocess.Popen([str(PYTHON),'-B','-c',worker,json.dumps(command)],cwd=ROOT,env=build_env(),stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
            require(winjob.contain(child),'Owned child containment failed')
            child.stdin.write('GO\n');child.stdin.flush();child.stdin.close()
            while child.poll() is None:
                sample=resources();failures=blockers(sample)
                if time.monotonic()-started>args.seconds:failures.append('deadline')
                samples.write(json.dumps(dict(sample,elapsedSeconds=time.monotonic()-started,blockers=failures))+'\n');samples.flush()
                if failures:report['abort']=failures;winjob.terminate();break
                time.sleep(1)
            report['exitCode']=child.wait(timeout=15);report['ok']=report['exitCode']==0 and report['abort'] is None
    finally:
        winjob.terminate()
        if child and child.poll() is None:child.kill();child.wait(timeout=10)
        report['seconds']=round(time.monotonic()-started,3);write_new(path,report);print(json.dumps(report))
    return 0 if report['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
