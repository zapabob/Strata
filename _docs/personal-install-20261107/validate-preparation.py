"""Syntax/hash receipt only. Does not import build/install entry points or execute them."""
import ast
import json
import subprocess
from common import *

files=sorted(HERE.glob('*.py'))
for path in files:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
js=sorted(HERE.glob('*.mjs'))
for path in js:subprocess.run([str(NODE),'--check',str(path)],cwd=ROOT,check=True,timeout=15)
versions=['VERSION','CONTROL_VERSION','AGENTS.md','README.md','apps/desktop/package.json','apps/desktop/package-lock.json',
          'apps/host/package.json','apps/host/package-lock.json','apps/desktop/src-tauri/Cargo.toml','apps/desktop/src-tauri/Cargo.lock',
          'strata_cli/__init__.py','packaging/full_installer.nsi']
hashes={p.relative_to(ROOT).as_posix():sha(p) for p in [*files,*js,HERE/'README.md',*(ROOT/name for name in versions)]}
record={'ok':True,'preparationOnly':True,'pythonSyntaxFiles':len(files),'nodeSyntaxFiles':len(js),'sourceFrozen':False,
        'preparedSourceHashes':hashes,'preparedSourceInventorySHA256':digest(hashes),'resourceSample':resources(),
        'processCounts':process_counts(),'releaseQualified':False,'buildExecuted':False,'signed':False,'installed':False}
write_new(OUT/'preparation-validation.json',record)
print(json.dumps({k:record[k] for k in ['ok','preparationOnly','pythonSyntaxFiles','nodeSyntaxFiles','preparedSourceInventorySHA256','processCounts','buildExecuted','signed','installed']}))
