"""Read-only input verification with sanitized receipts; no builds, signing or activation."""
from __future__ import annotations
import argparse
import json
import subprocess
from common import *

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',default='prep-audit-r1.json')
    args=parser.parse_args()
    require(re.fullmatch(r'prep-audit-r[1-9][0-9]*\.json',args.receipt) is not None,'Use a fresh preparation receipt name')
    require(BASE.is_dir(),'Candidate parent missing');OUT.mkdir(exist_ok=True)
    audit_dir=OUT/args.receipt.removesuffix('.json');require(not audit_dir.exists(),'Fresh audit inventory directory required');audit_dir.mkdir()
    require(sha(UNSIGNED/'engine-component.json')==UNSIGNED_MANIFEST,'Unsigned r3 manifest changed')
    require(load(UNSIGNED/'engine-component.json').get('signature') is None,'Original r3 must remain unsigned')
    require(sha(NODE)==NODE_SHA,'Private Node differs')
    env={k:v for k,v in os.environ.items() if not k.upper().startswith('STRATA_')}
    native=subprocess.run([str(NODE),'--max-old-space-size=512',str(HERE/'verify-native.mjs'),str(UNSIGNED)],cwd=ROOT,env=env,capture_output=True,text=True,check=True,timeout=180)
    result={'ok':True,'preparationOnly':True,'observedHead':git('rev-parse','HEAD'),'sourceFrozen':False,
        'installedHostVersion':load(INSTALLED/'host/package.json')['version'],'installedControlVersion':load(INSTALLED/'control/BUNDLE.json')['version'],
        'nodeSHA256':sha(NODE),'nodeVersion':subprocess.check_output([str(NODE),'--version'],text=True).strip(),
        'signingKeyExists':KEY.is_file(),'uvExists':UV.is_file(),'cargoCacheExists':CARGO_TARGET.is_dir(),
        'processCounts':process_counts(),'resourceSample':resources(),'native':json.loads(native.stdout),'quality':quality_record(),'resources':{}}
    old=Path('H:/Strata/releases/local-052-20261106-opencode')
    original=load(old/'resources.json')
    for name in ['node','harness','notices','local-backends']:
        tree=inventory(RESOURCES/name)
        # Prior receipt used the pretty JSON digest recipe, preserve that exact comparison.
        legacy_digest=hashlib.sha256(json.dumps(tree,sort_keys=True).encode()).hexdigest()
        if name=='local-backends' and COMPOSITE_RECEIPT.exists():
            require(digest(tree)==load(COMPOSITE_RECEIPT)['stagedResourceInventorySHA256']['local-backends'],'r4 staged backends have drifted')
            require(sha(RESOURCES/'local-backends/prism/runtime.json')==PRISM_MANIFEST_SHA,'Exact Prism 0.4.1 staging changed')
        else:
            require(legacy_digest==original['trees'][name]['inventorySHA256'],'Reusable staged resources have drifted')
        result['resources'][name]={'files':len(tree),'inventorySHA256':digest(tree)}
        write_new(audit_dir/('input-'+name+'-inventory.json'),tree)
    if COMPOSITE_RECEIPT.exists():
        composite=load(COMPOSITE_RECEIPT)
        require(sha(COMPOSITE/'engine-component.json')==composite['manifestSHA256'],'Unsigned r4 composite drift')
        result['preparedPrismVersion']='0.4.1'
        result['unsignedCompositeManifestSHA256']=composite['manifestSHA256']
    installed_engine=Path('C:/Users/downl/AppData/Local/Strata/components/engine/0.5.1-windows-x86_64-cuda-cuda13')
    require(sha(installed_engine/'strata.exe')=='e75716a9d5deb6289e87741d42e7003ba82b7696f6121d5203e615d9fe596a96','Installed native changed')
    result['installedNativeVersion']=load(installed_engine/'engine-component.json')['version']
    result['executionBlockers']=blockers(result['resourceSample'])+['parent-review-and-source-freeze']
    write_new(OUT/args.receipt,result)
    print(json.dumps({k:result[k] for k in ['ok','preparationOnly','installedHostVersion','installedControlVersion','installedNativeVersion','processCounts','executionBlockers']}))

if __name__=='__main__':
    main()
