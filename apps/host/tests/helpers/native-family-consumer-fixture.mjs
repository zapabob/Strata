/** Feed the actual Host builder's run configs to the Python consumer regression. No real engine. */
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {nativeFixture,finishJob} from './native-fixture.mjs';

process.env.STRATA_HAKUA_CHATBOT='1';
const cap={schema:1,family:'qwen35moe',layoutVersion:1,scaleSchema:'none',cacheTypesK:['f32','f16'],cacheTypesV:['f32'],
 flags:['--cache-type-k','--cache-type-v'],quality:'experimental-unqualified',binarySha256:'ab'.repeat(32)};
const result={};
for(const family of ['qwen','qwen36']){
 const f=nativeFixture({packaged:true,q36CapabilityProbe:async()=>cap});
 try{
  f.catalog.families[0].family=family;
  const path=join(f.repo,'strata-iq2_xs.json');
  writeFileSync(path,JSON.stringify({parallel:1,args:['--max-context','256'],
   ...(family==='qwen'?{arch:'qwen4exp',exe:'C:/fixture/strata-q36-lookalike/strata.exe',model_name:'Qwen3.6-looking label'}
     :{exe:'C:/fixture/neutral-runtime.exe',model_name:'Neutral model'})}));
  await f.control.refresh(true);
  if(family==='qwen36')await f.control.saveChecked('iq2_xs',{values:{cache_type_k:'f16',cache_type_v:'f32'}});
  const job=await finishJob(f.control,f.control.operation('load',{model:'iq2_xs'}).id);
  if(job.state!=='done')throw new Error(job.error);
  const run=JSON.parse(readFileSync(f.launchConfigs.at(-1),'utf8'));
  // Export only the real family's launch inputs. Keys and task-local memory paths are not evidence.
  result[family]=Object.fromEntries(['arch','exe','model_name','args','parallel','cache_type_k','cache_type_v','q36_run']
   .filter(key=>key in run).map(key=>[key,run[key]]));
 }finally{await f.cleanup();}
}
console.log(JSON.stringify(result));
