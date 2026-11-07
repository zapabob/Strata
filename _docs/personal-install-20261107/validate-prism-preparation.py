"""Final syntax/source/staging/selection receipt; no signing, activation or model execution."""
import ast
import argparse
import json
import subprocess
from common import *

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--receipt',default='preparation-validation-r2.json');args=parser.parse_args()
require(re.fullmatch(r'preparation-validation-r[2-9][0-9]*\.json',args.receipt) is not None,'Fresh validation receipt required')

for path in HERE.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
js=[*HERE.glob('*.mjs'),ROOT/'apps/host/server/local-backends.mjs',ROOT/'apps/desktop/scripts/stage-engine-components.mjs']
for path in js:subprocess.run([str(NODE),'--check',str(path)],cwd=ROOT,check=True,timeout=15)
stage=load(COMPOSITE_RECEIPT);selection=load(OUT/'prism041-r4/selection-plan.json')
require(stage['ok'] and stage['unsigned'] and not stage['signed'] and not stage['activated'],'Preparation state changed')
require(sha(COMPOSITE/'engine-component.json')==stage['manifestSHA256'],'r4 manifest changed')
require(sha(RESOURCES/'engine-bundle'/COMPOSITE.name/'engine-component.json')==stage['manifestSHA256'],'Staged composite mismatch')
require(sha(RESOURCES/'local-backends/prism/runtime.json')==PRISM_MANIFEST_SHA,'Staged Prism mismatch')
require(sha(UNSIGNED/'engine-component.json')==UNSIGNED_MANIFEST,'Original r3 manifest changed')
require(selection['ok'] and not selection['applied'] and selection['normalProfileFieldsChanged']==0,'User plan must stay unapplied')
files=[*HERE.glob('*.py'),*HERE.glob('*.mjs'),HERE/'README.md',ROOT/'apps/host/server/local-backends.mjs',ROOT/'apps/desktop/scripts/stage-engine-components.mjs',ROOT/'apps/host/tests/local-backends.test.mjs',ROOT/'apps/host/tests/hakua-distribution.test.mjs',ROOT/'apps/host/tests/fixtures/prism-0.4.1-runtime.json']
hashes={p.relative_to(ROOT).as_posix():sha(p) for p in files}
result={'ok':True,'preparationOnly':True,'sourceFrozen':False,'observedHead':git('rev-parse','HEAD'),'sourceHashes':hashes,'sourceInventorySHA256':digest(hashes),
        'unsignedCompositeSHA256':stage['manifestSHA256'],'prismManifestSHA256':PRISM_MANIFEST_SHA,'prismExeSHA256':PRISM_EXE_SHA,
        'nativeSHA256':ENGINE_SHA,'selectionPlanSHA256':selection['privatePlanSHA256'],'normalProfileFieldsChanged':0,
        'signed':False,'activated':False,'installed':False,'releaseQualified':False,'resourceSample':resources(),'processCounts':process_counts()}
write_new(OUT/'prism041-r4'/args.receipt,result)
print(json.dumps({k:result[k] for k in ['ok','preparationOnly','sourceInventorySHA256','unsignedCompositeSHA256','normalProfileFieldsChanged','signed','activated','installed','releaseQualified']}))
