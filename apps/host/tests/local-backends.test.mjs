import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {LOCAL_BACKENDS,localBackendChoice,findLocalBackend,verifyLocalBackend,requireRuntimeKv} from '../server/local-backends.mjs';
import {findBinary,restart,status,buildArgs} from '../server/supervisor.mjs';
import {resolveKvSettings,requireModelKvCompatible} from '../server/kv-settings.mjs';
const setting=(id,value)=>({id,value});

test('explicit backends use their own payload and never pick an old generic engine',async t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-runtimes-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 const options={componentsDir:root,installRoot:join(root,'empty'),platform:process.platform};
 const exe=process.platform==='win32'?'llama-server.exe':'llama-server';
 const generic=join(root,'generic-gguf');mkdirSync(generic);writeFileSync(join(generic,exe),'old generic');
 assert.equal(localBackendChoice(),'Automatic');assert.throws(()=>localBackendChoice([setting('runtime.backend','other')]));
 assert.equal(findBinary({...options,backend:'TurboQuant'}),null);
 for(const choice of Object.keys(LOCAL_BACKENDS)) {
  const definition=LOCAL_BACKENDS[choice],folder=join(root,'local-backends',definition.id);mkdirSync(folder,{recursive:true});
  const path=join(folder,exe),payload=Buffer.from(choice);writeFileSync(path,payload);
  const manifest={schema:1,version:'0.3.3',backend:definition.id,source:{repository:definition.repository,commit:definition.commit,dirty:false,patches:[]},cacheTypes:choice==='TurboQuant'?['f16','q8_0','turbo3']:['f16','q8_0'],files:[{path:exe,sha256:createHash('sha256').update(payload).digest('hex')}]};
  const save=()=>writeFileSync(join(folder,'runtime.json'),JSON.stringify(manifest));save();
  const selected=findLocalBackend(choice,options);assert.equal(selected.path,path);
  assert.equal(findBinary({...options,backend:choice}).path,path);
  assert.equal((await verifyLocalBackend(selected,choice)).backend,definition.id);
  writeFileSync(join(folder,'unexpected.dll'),'stale payload');
  await assert.rejects(verifyLocalBackend(selected,choice),/Unexpected local runtime package membership/);
  rmSync(join(folder,'unexpected.dll'));
  const bundled=join(options.installRoot,'local-backends',definition.id);mkdirSync(bundled,{recursive:true});
  writeFileSync(join(bundled,exe),payload);
  writeFileSync(join(bundled,'runtime.json'),JSON.stringify(manifest));
  assert.equal(findLocalBackend(choice,options).path,join(bundled,exe),'the current bundle takes precedence over a same-version installed component');
  writeFileSync(join(bundled,'runtime.json'),JSON.stringify({...manifest,version:'0.3.4'}));
  assert.equal(findLocalBackend(choice,options).path,join(bundled,exe),'a newer bundled runtime replaces an older installed component');
  writeFileSync(join(bundled,'runtime.json'),JSON.stringify({...manifest,version:'0.3.2'}));
  assert.equal(findLocalBackend(choice,options).path,path,'a newer installed runtime remains selected');
  if(choice==='PrismML')assert.throws(()=>requireRuntimeKv(manifest,{k:'turbo3',v:'q8_0'}),/cannot use turbo3/);
  else assert.doesNotThrow(()=>requireRuntimeKv(manifest,{k:'turbo3',v:'f16'}));
  writeFileSync(path,'substituted');await assert.rejects(verifyLocalBackend(selected,choice),/payload changed/);
  writeFileSync(path,payload);manifest.source.dirty=true;save();await assert.rejects(verifyLocalBackend(selected,choice),/unreviewed/);
 }
});

test('each runtime admits only its exact reviewed standard-sm120 patch',async t=>{
 const root=mkdtempSync(join(tmpdir(),'hakua-patched-runtimes-'));t.after(()=>rmSync(root,{recursive:true,force:true}));
 for(const [choice,definition] of Object.entries(LOCAL_BACKENDS)) {
  const folder=join(root,'local-backends',definition.id);mkdirSync(folder,{recursive:true});
  const exe=process.platform==='win32'?'llama-server.exe':'llama-server',payload=Buffer.from('fixture executable');
  const patch=readFileSync(new URL('../../../tools/'+(choice==='PrismML'?'spin8_backend_sm120.patch':'turboquant_backend_sm120.patch'),import.meta.url));
  const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
  writeFileSync(join(folder,exe),payload);writeFileSync(join(folder,'source-patch.diff'),patch);
  const manifest={schema:1,version:'0.3.3',backend:definition.id,source:{repository:definition.repository,commit:definition.commit,dirty:true,patches:[{id:definition.id+'-standard-sm120-v1',sha256:hash(patch)}]},cacheTypes:['f16'],files:[{path:exe,sha256:hash(payload)},{path:'source-patch.diff',sha256:hash(patch)}]};
  const save=()=>writeFileSync(join(folder,'runtime.json'),JSON.stringify(manifest));save();
  const binary=findLocalBackend(choice,{componentsDir:root,installRoot:join(root,'absent')});
  await verifyLocalBackend(binary,choice);
  manifest.source.patches[0].id+='-unknown';save();await assert.rejects(verifyLocalBackend(binary,choice),/unreviewed/);
  manifest.source.patches[0].id=definition.id+'-standard-sm120-v1';save();
  writeFileSync(join(folder,'source-patch.diff'),'unreviewed change');await assert.rejects(verifyLocalBackend(binary,choice),/payload changed/);
 }
});

test('TurboQuant settings produce real independent K/V flags and reject incompatible geometry',()=>{
 const expert=[setting('runtime.backend','TurboQuant'),setting('ctx.kType','TURBO3'),setting('ctx.vType','TURBO4')];
 assert.deepEqual(resolveKvSettings(expert),{k:'turbo3',v:'turbo4'});
 const args=buildArgs({modelPath:'fixture.gguf',config:{expert}});
 assert.equal(args[args.indexOf('-ctk')+1],'turbo3');assert.equal(args[args.indexOf('-ctv')+1],'turbo4');
 assert.throws(()=>requireModelKvCompatible({local:{keyLength:null,valueLength:128},kvModes:['INT8']},expert),/geometry/);
 for(const width of [64,128,256])assert.doesNotThrow(()=>requireModelKvCompatible({local:{keyLength:width,valueLength:width},kvModes:['INT8']},expert));
 assert.throws(()=>resolveKvSettings([...expert,setting('perf.flashAttn',false)]),/flash attention/);
});

test('the bundled TurboQuant policy rejects failed K modes while allowing qualified V modes',()=>{
 const manifest={backend:'turboquant',cacheTypes:['f16','turbo2','turbo3','turbo4'],cacheTypesK:['f16'],cacheTypesV:['f16','turbo2','turbo3','turbo4']};
 for(const v of ['turbo2','turbo3','turbo4']) {
  assert.doesNotThrow(()=>requireRuntimeKv(manifest,{k:'f16',v}));
  assert.throws(()=>requireRuntimeKv(manifest,{k:v,v:'f16'}),new RegExp(v+' K cache'));
 }
});

test('a missing selected runtime rejects before restart changes process state',async()=>{
 const previous=process.env.STRATA_COMPONENTS_DIR;
 process.env.STRATA_COMPONENTS_DIR=join(tmpdir(),'nonexistent-hakua-component-test');
 const before=status();
 try {await assert.rejects(restart({modelPath:'missing-model.gguf',config:{expert:[setting('runtime.backend','TurboQuant')]}}),/TurboQuant runtime/);assert.deepEqual(status(),before);}
 finally {if(previous===undefined)delete process.env.STRATA_COMPONENTS_DIR;else process.env.STRATA_COMPONENTS_DIR=previous;}
});
