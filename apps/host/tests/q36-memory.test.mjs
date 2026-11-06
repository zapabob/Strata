/** Actual policy/PATCH/load boundaries; fake executable bytes, never native execution. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import * as probes from '../server/q36-kv-capabilities.mjs';
import {prepareQ36Launch,q36FileSha256} from '../server/q36-run-contract.mjs';
import {nativeFixture,finishJob} from './helpers/native-fixture.mjs';
import {NATIVE_FIELDS} from '../server/native-settings.mjs';

export const memory={schema:1,family:'qwen35moe',modes:['bounded-experts-v1'],flag:'--q36-memory',requiresExpertStore:'mapped-pack',requiresExplicitSlots:true,scope:'expert-working-storage',totalProcessBound:false,qualification:'experimental-unqualified'};
const marker=`Q36_MEMORY_CAPABILITIES ${JSON.stringify(memory)}`;
const args=['--max-context','256','--prefill','128','--mtp','0','--q36-expert-store','mapped-pack','--expert-slots','5'];

test('every memory label/help/receipt string has all nine catalogs, including translated Japanese',()=>{
  const read=language=>JSON.parse(readFileSync(new URL(`../src/locales/fix-${language}.json`,import.meta.url)));
  const en=read('en'),field=NATIVE_FIELDS.find(f=>f.id==='q36_memory');
  for(const text of [field.label,field.hint,field.defaultLabel,...Object.values(field.choiceLabels)])assert.ok(Object.values(en).includes(text));
  for(const language of ['zh','ja','de','es','ru','pt','ko','fr']){
    const catalog=read(language);
    for(let i=1;i<=7;i++){
      const key=`q36m${i}`;assert.ok(catalog[key]);assert.notEqual(catalog[key],en[key]);
      assert.deepEqual(catalog[key].match(/\{\d+\}/g)??[],en[key].match(/\{\d+\}/g)??[]);
    }
  }
});

test('one digest-bound bounded help query discovers memory separately from the public KV schema',async()=>{
  const sha='ab'.repeat(32),calls=[];
  const kv={schema:1,family:'qwen35moe',layoutVersion:1,scaleSchema:'none',cacheTypesK:['f32'],cacheTypesV:['f32'],flags:['--cache-type-k','--cache-type-v'],quality:'experimental-unqualified'};
  const output=`Q36_KV_CAPABILITIES ${JSON.stringify(kv)}\n${marker}`;
  assert.equal(typeof probes.probeQ36Capabilities,'function');
  const run=(exe,argv,options,done)=>{calls.push({exe,argv,options});done(null,output,'');};
  assert.deepEqual(await probes.probeQ36Capabilities('fake',{run,hash:()=>sha}),{kvCapability:{...kv,binarySha256:sha},memoryCapability:{...memory,binarySha256:sha}});
  assert.equal(calls.length,1);assert.deepEqual(calls[0].argv,['--help']);
  assert.equal(calls[0].options.timeout,3000);assert.equal(calls[0].options.maxBuffer,65536);
  assert.deepEqual(await probes.probeQ36KvCapabilities('fake',{run,hash:()=>sha}),{...kv,binarySha256:sha});
  for(const text of ['',marker+'\n'+marker,marker+'x','x'.repeat(65536)+marker,
    marker.replace('"schema":1','"schema":true'),marker.replace('"totalProcessBound":false','"totalProcessBound":true'),
    marker.replace('"requiresExplicitSlots":true','"requiresExplicitSlots":1'),marker.replace('qwen35moe','qwen4exp'),
    marker.replace('bounded-experts-v1','future'),marker.replace('"scope":','"extra":1,"scope":')])
    assert.equal(probes.parseQ36MemoryCapabilities(text),null,text.slice(0,100));
  assert.deepEqual(probes.parseQ36MemoryCapabilities(marker.replace('["bounded-experts-v1"]','[]')),{...memory,modes:[]});
  let reads=0;
  assert.equal((await probes.probeQ36Capabilities('fake',{run,hash:()=>reads++?'cd'.repeat(32):sha})).memoryCapability,null);
});

test('bounded launch freezes memory expectations; explicit legacy has no new flag',()=>{
  const sha='ab'.repeat(32),cap=structuredClone({...memory,binarySha256:sha});
  const result=prepareQ36Launch({args,requested:{memoryMode:'bounded-experts-v1'},memoryCapability:cap,binarySha256:sha});
  assert.equal(result.ok,true,result.error?.message);
  assert.deepEqual(result.argv,[...args,'--q36-memory','bounded-experts-v1']);
  assert.equal(result.contract.requested.q36_memory,'bounded-experts-v1');
  assert.deepEqual(result.contract.backend.memoryCapability,cap);
  cap.modes.length=0;assert.deepEqual(result.contract.backend.memoryCapability.modes,['bounded-experts-v1']);
  for(const input of [{}, {args:['--q36-memory','legacy']},{requested:{memoryMode:'legacy'}}]){
    const out=prepareQ36Launch(input);assert.equal(out.ok,true);assert.deepEqual(out.argv,[]);
    assert.equal(out.contract.backend.memoryCapability,null);
  }
  for(const patch of [{memoryCapability:null},{binarySha256:'cd'.repeat(32)},{memoryCapability:{...memory,modes:[],binarySha256:sha}},
    {args:[]},{args:args.slice(0,-2)},{args:[...args.slice(0,-1),'0']},{args:[...args,'--q36-memory','legacy']},
    {args:[...args,'--q36-memory=bounded-experts-v1']}])
    assert.equal(prepareQ36Launch({args,requested:{memoryMode:'bounded-experts-v1'},memoryCapability:{...memory,binarySha256:sha},binarySha256:sha,...patch}).ok,false,JSON.stringify(patch));
});

async function fixture(capability=true){
  let f;f=nativeFixture({packaged:true,q36CapabilityProbe:async()=>({kvCapability:null,memoryCapability:capability===true?{...memory,binarySha256:q36FileSha256(join(f.repo,'strata.exe'))}:capability})});
  f.catalog.families[0].family='qwen36';
  writeFileSync(join(f.repo,'strata.exe'),'inert memory capability fixture');
  writeFileSync(join(f.repo,'strata-iq2_xs.json'),JSON.stringify({parallel:1,args}));
  const cleanup=f.cleanup;f.cleanup=async()=>{for(const job of f.control.state().jobs.filter(j=>j.state==='running'))await finishJob(f.control,job.id);await cleanup();};
  await f.control.refresh(true);return f;
}
test('real PATCH service and buildConfig preserve canonical adapter and explicit bounded mode',async()=>{
  const f=await fixture();try{
    const view=await f.control.settingsKv('iq2_xs');
    assert.deepEqual(view.fields.find(f=>f.id==='q36_memory')?.choices,['legacy','bounded-experts-v1']);
    await f.control.saveChecked('iq2_xs',{values:{q36_memory:'bounded-experts-v1'}});
    const done=await finishJob(f.control,f.control.operation('load',{model:'iq2_xs'}).id);assert.equal(done.state,'done',done.error);
    const run=JSON.parse(readFileSync(f.launchConfigs.at(-1)));
    assert.equal(run.arch,'qwen35moe');assert.equal(run.args[run.args.indexOf('--q36-memory')+1],'bounded-experts-v1');
    for(const flag of ['--max-context','--prefill','--mtp','--expert-slots'])assert.equal(run.args[run.args.indexOf(flag)+1],args[args.indexOf(flag)+1]);
    assert.equal(run.q36_run.backend.memoryCapability.binarySha256,q36FileSha256(join(f.repo,'strata.exe')));
    assert.equal(run.q36_run.observed.status,'unobserved');
    assert.equal(JSON.parse(readFileSync(join(f.repo,'strata-iq2_xs.json'))).arch,undefined);
  }finally{await f.cleanup();}
});
for(const kind of ['unknown','wronghash','wrongfamily','missing-store','missing-slots','zero-slots','malformed'])test(`bounded ${kind} fails before persistence/replacement and known job creation`,async()=>{
  const f=await fixture(kind==='unknown'?null:kind==='wronghash'?{...memory,binarySha256:'ab'.repeat(32)}:true);try{
    const path=join(f.repo,'strata-iq2_xs.json');
    const cfg=JSON.parse(readFileSync(path));
    if(kind==='wrongfamily')cfg.arch='qwen4exp';
    if(kind==='missing-store')cfg.args=args.filter((_,i)=>i!==6&&i!==7);
    if(kind==='missing-slots')cfg.args=args.slice(0,-2);
    if(kind==='zero-slots')cfg.args=[...args.slice(0,-1),'0'];
    if(kind==='malformed')cfg.args=[...args,'--q36-memory=bounded-experts-v1'];
    writeFileSync(path,JSON.stringify(cfg));await f.control.settingsKv('iq2_xs');
    const before=readFileSync(path,'utf8'),effects=[...f.effects],jobs=f.control.state().jobs.length;
    await assert.rejects(f.control.saveChecked('iq2_xs',{values:{q36_memory:'bounded-experts-v1'}}),/memory|mapped|slots/i);
    assert.throws(()=>f.control.operation('load',{model:'iq2_xs',values:{q36_memory:'bounded-experts-v1'}}),/memory|mapped|slots/i);
    assert.equal(readFileSync(path,'utf8'),before);assert.deepEqual(f.effects,effects);assert.equal(f.control.state().jobs.length,jobs);
  }finally{await f.cleanup();}
});
test('stored incompatible mode stays visible until all representations are explicitly cleared',async()=>{
  const f=await fixture(null);try{
    const path=join(f.repo,'strata-iq2_xs.json');writeFileSync(path,JSON.stringify({arch:'qwen4exp',args:['--q36-memory','bounded-experts-v1'],user_args:['--q36-memory','bounded-experts-v1']}));
    assert.equal(f.control.settings('iq2_xs').values.q36_memory,'bounded-experts-v1');
    const view=await f.control.settingsKv('iq2_xs');assert.equal(view.fields.find(f=>f.id==='q36_memory').supported,false);assert.ok(view.settingsIssues.some(i=>i.field==='q36_memory'));
    await f.control.saveChecked('iq2_xs',{values:{q36_memory:null}});
    assert.equal(f.control.settings('iq2_xs').values.q36_memory,null);
  }finally{await f.cleanup();}
});

test('unsupported bounded replacement preserves a ready model and rejects a raw-argv request before a new job',async()=>{
  const f=await fixture(null);try{
    writeFileSync(join(f.repo,'strata-iq3_s.json'),JSON.stringify({arch:'qwen4exp',args:['--max-context','256']}));
    const ready=await finishJob(f.control,f.control.operation('load',{model:'iq3_s'}).id);assert.equal(ready.state,'done',ready.error);
    await f.control.settingsKv('iq2_xs');
    const before=f.control.state(),effects=[...f.effects],calls=f.calls.length;
    assert.throws(()=>f.control.operation('load',{model:'iq2_xs',values:{args:[...args,'--q36-memory','bounded-experts-v1']}}),/memory/);
    assert.equal(f.control.state().jobs.length,before.jobs.length);assert.deepEqual(f.effects,effects);assert.equal(f.calls.length,calls);
    assert.equal(f.control.state().instances[0].id,before.instances[0].id);assert.equal(f.control.state().instances[0].status,'ready');
  }finally{await f.cleanup();}
});

test('a changed binary invalidates known memory support before job creation',async()=>{
  const f=await fixture();try{
    await f.control.settingsKv('iq2_xs');writeFileSync(join(f.repo,'strata.exe'),'different inert binary');
    assert.throws(()=>f.control.operation('load',{model:'iq2_xs',values:{q36_memory:'bounded-experts-v1'}}),/memory/);
    assert.equal(f.control.state().jobs.length,0);assert.deepEqual(f.effects,[]);
  }finally{await f.cleanup();}
});

test('bounded slots use the native positive decimal int range before job creation',async()=>{
  const f=await fixture();try{
    await f.control.settingsKv('iq2_xs');
    assert.throws(()=>f.control.operation('load',{model:'iq2_xs',values:{q36_memory:'bounded-experts-v1',args:[...args.slice(0,-1),'2147483648']}}),/slots/);
    assert.equal(f.control.state().jobs.length,0);
    assert.equal((await f.control.saveChecked('iq2_xs',{values:{q36_memory:'bounded-experts-v1',args:[...args.slice(0,-1),'05']}})).values.q36_memory,'bounded-experts-v1');
  }finally{await f.cleanup();}
});
