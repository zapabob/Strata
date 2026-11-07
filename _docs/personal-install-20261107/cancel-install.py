"""Normal API cancellation of the user's active native preparation, with bounded settling."""
from __future__ import annotations
import argparse
import json
import time
import urllib.error
import urllib.request
from common import *

sys.path.insert(0,str(ROOT/'_docs/local-install-20261106'))
from installed_state import shells,endpoint,get
sys.path.insert(0,str(ROOT/'_docs/native-maintenance-20261107'))
from foundation import IdentityHandle

def weights() -> dict:
    root=Path('H:/Strata/models')
    return {str(p):{'bytes':p.stat().st_size,'mtimeNs':p.stat().st_mtime_ns} for p in root.rglob('*')
            if p.is_file() and (p.suffix.lower() in {'.gguf','.safetensors'} or p.name.lower().endswith('.gguf.part'))}

def activity(base: str) -> tuple[dict,list[dict]]:
    turns=get(base,'/api/chat/active');serving=get(base,'/api/serving');tasks=get(base,'/api/tasks');native=get(base,'/api/native')
    active=[j for j in native.get('jobs',[]) if j.get('state') in {'running','cancelling','queued'}]
    counts={'turns':len(turns['turns']),'running':serving['stats']['running'],'queued':serving['stats']['waiting'],
            'tasks':sum(t.get('state',t.get('status')) in {'running','working','queued','waiting','in_progress'} for t in tasks['tasks'])}
    return counts,active

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--receipt',default='cancel-install-r1.json');args=parser.parse_args()
    require(re.fullmatch(r'cancel-install-r[1-9][0-9]*\.json',args.receipt) is not None,'Fresh receipt name required')
    if not args.execute:print(json.dumps({'wouldCancel':False,'scope':'active native install jobs only'}));return
    require_resources();require(not (OUT/args.receipt).exists(),'Preserve prior cancellation receipt')
    processes=shells();require(len(processes)==1,'Expected one actual installed shell')
    shell=processes[0];base=endpoint(shell);before=weights()
    report={'ok':False,'normalApiOnly':True,'stoppedUnrelatedProcesses':0,'cancelRequests':0,'terminalStates':[],'beforeWeightFiles':len(before)}
    with IdentityHandle(shell.pid) as retained:
        require(Path(retained.exe).resolve()==(INSTALLED/'strata-desktop.exe').resolve(),'Wrong shell identity')
        for _ in range(3):
            counts,jobs=activity(base);require(not any(counts.values()),'Active answer or task; cancellation waits for idle')
            require(all(j['kind']=='install' for j in jobs),'Unrelated native operation is active');time.sleep(1)
        ids=[j['id'] for j in jobs if j['kind']=='install']
        try:
            for job_id in ids:
                require(retained.alive(),'Shell exited before cancellation')
                counts,current=activity(base);require(not any(counts.values()),'New active answer/task before cancel')
                require(any(j['id']==job_id and j['kind']=='install' for j in current),'Native job changed before cancel')
                request=urllib.request.Request(base+'/api/native/operations/'+job_id+'/cancel',data=b'{}',method='POST',headers={'Content-Type':'application/json','Origin':base,'x-strata-client':'ui'})
                report['cancelRequests']+=1
                with urllib.request.urlopen(request,timeout=150) as response:require(response.status==200,'Cancel request failed')
            deadline=time.monotonic()+180
            while True:
                require(retained.alive(),'Shell exited while settling cancel')
                state=get(base,'/api/native');selected=[j for j in state.get('jobs',[]) if j['id'] in ids]
                report['terminalStates']=[j['state'] for j in selected]
                if len(selected)==len(ids) and all(j['state'] in {'cancelled','error','done','failed'} for j in selected):break
                require(time.monotonic()<deadline,'Native cancellation did not settle');time.sleep(1)
            after=weights()
            for path,old in before.items():
                current=after.get(path)
                if current is None and path.lower().endswith('.part'):current=after.get(path[:-5])
                require(current is not None and current['bytes']>=old['bytes'],'A downloaded weight disappeared or shrank')
                if not path.lower().endswith('.part'):require(current==old,'An existing completed weight changed')
            counts,active=activity(base);require(not any(counts.values()) and not active,'App not idle after cancellation')
            report.update(ok=True,downloadedFilesPreserved=True,afterWeightFiles=len(after),answersAndTasksIdle=True)
        finally:
            write_new(OUT/args.receipt,report);print(json.dumps(report))

if __name__=='__main__':main()
