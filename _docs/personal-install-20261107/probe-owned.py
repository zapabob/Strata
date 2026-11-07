"""Read only process identity/ancestry for the isolated Q36 GUI acceptance test."""
import argparse
import json
from common import *
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--shell',type=int);parser.add_argument('--child',type=int)
args=parser.parse_args()
if args.shell is None:
    print(json.dumps({'processCounts':process_counts(),'resourceBlockers':blockers(resources())}))
else:
    shell=psutil.Process(args.shell);child=psutil.Process(args.child)
    require(shell in child.parents(),'Observed engine is not owned by this QA shell')
    exe=Path(child.exe());require(sha(exe)==ENGINE_SHA,'Observed child is not r3 strata.exe')
    command=child.cmdline()
    def flag(name: str, value: str) -> bool:
        return name in command and command.index(name)+1<len(command) and command[command.index(name)+1]==value
    require(all(flag(k,v) for k,v in [('--max-context','4096'),('--prefill','512'),('--expert-slots','5'),('--mtp','2'),('--cache-type-k','f32'),('--cache-type-v','f32'),('--q36-memory','bounded-experts-v1')]),'Actual child settings differ')
    require('--private-conversation-cache' in command,'Private-owner cache mode missing')
    print(json.dumps({'owned':True,'engineSHA256':ENGINE_SHA,'actualSettingsMatched':True,'privateOwnerMode':True}))
