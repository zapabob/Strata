"""Check only the isolated GUI's actual Prism child, executable and bound loopback port."""
import argparse
import json
from common import *
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--shell',type=int,required=True);parser.add_argument('--child',type=int,required=True)
parser.add_argument('--port',type=int,required=True);parser.add_argument('--model',type=Path,required=True)
args=parser.parse_args()
shell=psutil.Process(args.shell);child=psutil.Process(args.child)
require(shell in child.parents(),'Prism process is not owned by the isolated shell')
require(sha(Path(child.exe()))==PRISM_EXE_SHA,'Prism executable differs')
command=child.cmdline()
def value(flag: str) -> str | None:
    return command[command.index(flag)+1] if flag in command and command.index(flag)+1<len(command) else None
require(Path(value('-m') or '').resolve()==args.model.resolve(),'Prism model path differs')
require(all(value(k)==v for k,v in [('-c','98304'),('-ctk','q8_0'),('-ctv','q8_0'),('-fa','on'),('-np','1')]),'Actual Prism settings differ')
require(value('--spec-type') in (None,'none'),'Unexpected explicit speculative mode')
require(any(c.status==psutil.CONN_LISTEN and c.laddr.ip=='127.0.0.1' and c.laddr.port==args.port for c in child.net_connections(kind='tcp')),'Prism listener is not owned by this child')
print(json.dumps({'owned':True,'runtimeVersion':'0.4.1','executableSHA256':PRISM_EXE_SHA,'context':98304,'q8Kv':True,'flashAttentionOn':True,'modelPathMatched':True}))
