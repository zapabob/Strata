"""Create isolated real-component/model fixtures after parent source review; starts nothing."""
from __future__ import annotations
import argparse
import json
from common import *

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--reviewed-commit')
    args=parser.parse_args()
    if not args.execute:
        print(json.dumps({'wouldCreateFixture':False,'wouldStartModel':False,'context':4096,'prefill':512,'expertSlots':5,'mtp':2,'kvF32':True,'requiresParentReview':True}));return
    commit=approved_source(args.reviewed_commit);require_resources()
    qa=load(OUT/'app-qualification.json');require(qa['ok'] and qa['sourceCommit']==commit,'Qualify the reviewed package first')
    home=OUT/'e2e-profile';require(not home.exists(),'Fresh isolated E2E profile required');home.mkdir()
    for name in ['data','install','profiles','runtime','models','Local','Roaming','webview','desktop','temp','screenshots']:(home/name).mkdir()
    components=home/'components/engine'/SIGNED.name
    staged=load(OUT/'staged-native.json')
    require(staged['signatureVerified'] and staged['prismVersion']=='0.4.1' and staged['prismManifestSHA256']==PRISM_MANIFEST_SHA,'Signed r4 with exact Prism 0.4.1 required')
    component=preserved_copy(SIGNED,components)
    require(sha(components/'strata.exe')==ENGINE_SHA,'Wrong isolated engine')
    tokenizer=Path('H:/Strata/models/packs/qwen36-ud-q4_k_xl/tokenizer')
    require((tokenizer/'tokenizer.json').is_file(),'Existing tokenizer required; never download one')
    model_files=[MODEL,Path(str(MODEL)+'.q36epk'),Path(str(MODEL)+'.q36epk.verified')]
    require(all(p.is_file() for p in model_files),'Existing model, expert pack and verification receipt required')
    before={str(p):{'bytes':p.stat().st_size,'mtimeNs':p.stat().st_mtime_ns} for p in model_files}
    model_id='qwen36-ud-q4_k_xl'
    cfg={'exe':'component:strata-engine','tokenizer':str(tokenizer),'cwd':str(home/'install'),'arch':'qwen35moe','backend':'cuda',
         'model_name':'Personal QA Qwen3.6','host':'127.0.0.1','parallel':1,'ui_context_chosen':True,'ui_vision_enabled':False,'ui_resource_profile':'performance',
         'args':['--native',str(MODEL),'--q36-expert-store','mapped-pack','--max-context','4096','--prefill','512','--expert-slots','5','--mtp','2',
                 '--no-warmup','--greedy','--prompt-cache','0','--conversation-cache-mib','0','--private-conversation-cache','--cache-type-k','f32','--cache-type-v','f32'],
         'cache_type_k':'f32','cache_type_v':'f32','open_browser':False,'experimental_speed_projection':False}
    write_new(home/'install'/f'strata-{model_id}.json',cfg)
    write_new(home/'data/native-host.json',{'installDir':str(home/'install'),'downloadDirectory':str(home/'models')})
    write_new(home/'data/state.json',{'version':1,'setup':{'complete':True,'flowVersion':2,'step':4,'history':[]},'installed':{},'current':None,'loaded':None,
        'beginner':{'priority':'balanced','contextLength':'4k','readImages':False,'gpuIdle':'never'},'expert':{'sample.maxTokens':32,'sample.temp':0,'sample.speedProjection':False}})
    write_new(OUT/'e2e-fixture.json',{'prepared':True,'sourceCommit':commit,'home':str(home),'app':qa['app'],'modelId':model_id,
        'modelFilesBefore':before,'tokenizerInventorySHA256':digest(inventory(tokenizer)),'componentInventorySHA256':component['inventorySHA256'],
        'engineSHA256':ENGINE_SHA,'shellSHA256':qa['shellSHA256'],'executed':False,'releaseQualified':False})
    print(json.dumps({'prepared':True,'startedModel':False,'modelFilesCopied':0,'sourceCommit':commit}))

if __name__=='__main__':main()
