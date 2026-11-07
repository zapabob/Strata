"""Prepare unsigned r4 composite and managed staging only; never sign or activate."""
from __future__ import annotations
import argparse
import json
import subprocess
from common import *

WORK=OUT/'prism041-r4'

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if not args.execute:
        print(json.dumps({'wouldStage':False,'wouldSign':False,'wouldActivate':False,'resourceBlockers':blockers(resources()),'prismVersion':'0.4.1','releaseQualified':False}));return
    require_resources();require(not WORK.exists() and not COMPOSITE.parent.exists(),'Fresh r4 output required');WORK.mkdir()
    require(sha(UNSIGNED/'engine-component.json')==UNSIGNED_MANIFEST,'r3 manifest changed')
    require(sha(PRISM_ROOT/'runtime.json')==PRISM_MANIFEST_SHA,'Exact Prism manifest changed')
    require(sha(PRISM_ROOT/'llama-server.exe')==PRISM_EXE_SHA,'Exact Prism binary changed')
    handoff=load(PRISM_HANDOFF);require(handoff['manifestSHA256']==PRISM_MANIFEST_SHA and handoff['source']['commit']==PRISM_SOURCE,'Wrong Prism handoff')
    require(handoff['ordinaryModelUseQualified'] is True and handoff['fullWindowQualified'] is False and handoff['generalQualityQualified'] is False,'Prism qualification scope changed')
    env=build_env()
    subprocess.run([str(NODE),str(HERE/'verify-prism.mjs'),str(PRISM_ROOT),str(RESOURCES/'local-backends/prism'),str(WORK/'runtime-readonly.json')],cwd=ROOT,env=env,check=True,timeout=180)
    subprocess.run([str(NODE),str(HERE/'verify-native.mjs'),str(UNSIGNED)],cwd=ROOT,env=env,check=True,timeout=180)
    originals={'r3':inventory(UNSIGNED),'prism041':inventory(PRISM_ROOT),'stagedBackends':inventory(RESOURCES/'local-backends')}
    write_new(WORK/'original-inputs.json',originals)
    backups=WORK/'backups';backups.mkdir()
    prism=RESOURCES/'local-backends/prism';old_prism=inventory(prism)
    # Move the managed old staging in the same H: volume; the rollback bytes remain intact.
    shutil.move(str(prism),str(backups/'prism-0.4.0'))
    require(inventory(backups/'prism-0.4.0')==old_prism,'Legacy Prism backup changed')
    copied=preserved_copy(PRISM_ROOT,prism);require(copied['inventory']==originals['prism041'],'Prism stage mismatch')
    subprocess.run([str(NODE),'apps/desktop/scripts/stage-engine-components.mjs',str(COMPOSITE.parent),'--native-component',str(UNSIGNED),'--private-candidate'],cwd=ROOT,env=env,check=True,timeout=360)
    staged=load(COMPOSITE.parent/'STAGED.json');require(staged['ok'] and staged['nativeSHA256']==ENGINE_SHA and staged['releaseQualified'] is False,'Composite identity differs')
    require(sha(COMPOSITE/'local-backends/prism/runtime.json')==PRISM_MANIFEST_SHA,'Composite Prism manifest differs')
    for name in ['native-build.json','strata.exe','strata-q36.exe','strata_kq.dll']:
        require(sha(COMPOSITE/name)==sha(UNSIGNED/name),'Native r3 bytes changed')
    old_engine,=list((RESOURCES/'engine-bundle').glob('*/engine-component.json'))
    old_engine=old_engine.parent;old_tree=inventory(old_engine)
    require(load(old_engine/'engine-component.json')['version']=='0.5.1','Unexpected old staged engine')
    shutil.move(str(old_engine),str(backups/'engine-0.5.1'))
    require(inventory(backups/'engine-0.5.1')==old_tree,'Old staged native backup changed')
    component=preserved_copy(COMPOSITE,RESOURCES/'engine-bundle'/COMPOSITE.name)
    require(inventory(UNSIGNED)==originals['r3'] and inventory(PRISM_ROOT)==originals['prism041'],'Original payload changed')
    subprocess.run([str(NODE),str(HERE/'verify-prism.mjs'),str(RESOURCES/'local-backends/prism'),str(backups/'prism-0.4.0'),str(WORK/'staged-runtime-readonly.json')],cwd=ROOT,env=env,check=True,timeout=180)
    subprocess.run([str(NODE),str(HERE/'verify-native.mjs'),str(RESOURCES/'engine-bundle'/COMPOSITE.name)],cwd=ROOT,env=env,check=True,timeout=180)
    final_resources={name:inventory(RESOURCES/name) for name in ['local-backends','engine-bundle']}
    write_new(WORK/'staged-inventories.json',final_resources)
    write_new(COMPOSITE_RECEIPT,{'ok':True,'unsigned':True,'signed':False,'activated':False,'installed':False,'releaseQualified':False,
        'folder':str(COMPOSITE),'manifestSHA256':sha(COMPOSITE/'engine-component.json'),'nativeSourceCommit':NATIVE_COMMIT,'nativeSHA256':ENGINE_SHA,
        'prismManifestSHA256':PRISM_MANIFEST_SHA,'prismExeSHA256':PRISM_EXE_SHA,'prismSourceCommit':PRISM_SOURCE,
        'componentFiles':len(component['inventory']),'componentInventorySHA256':component['inventorySHA256'],
        'installedBytes':staged['installedBytes'],'cFreeRequiredForActivationBytes':5*1024**3+staged['installedBytes'],
        'originalR3ManifestSHA256':UNSIGNED_MANIFEST,'handoffSHA256':sha(PRISM_HANDOFF),'quality':quality_record(),
        'legacyPrismBackupInventorySHA256':digest(old_prism),'oldEngineBackupInventorySHA256':digest(old_tree),
        'stagedResourceInventorySHA256':{name:digest(tree) for name,tree in final_resources.items()}})
    print(json.dumps({'ok':True,'prismVersion':'0.4.1','componentVersion':'0.5.2','nativeBytesUnchanged':True,'componentFiles':len(component['inventory']),'signed':False,'activated':False,'releaseQualified':False}))

if __name__=='__main__':main()
