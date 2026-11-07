/** Bounded synthetic checks for one already-staged private runtime. Run under the owned job guard. */
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {createHash,randomBytes} from 'node:crypto';
import {createReadStream,mkdirSync,readFileSync,statSync,writeFileSync} from 'node:fs';
import {createServer} from 'node:net';
import {join,resolve} from 'node:path';
import {readGGUF,qwen35MissingMtp} from '../apps/host/server/gguf.mjs';
import {explicitKvEnvironment} from '../apps/host/server/kv-settings.mjs';

const [runtimeArg,manifestHash,modelArg,mode='chat']=process.argv.slice(2);
assert.ok(process.env.QWEN35_TEST_OUT,'Run under the resource/job guard');
assert.ok(['chat','explicit-mtp'].includes(mode));
const runtime=resolve(runtimeArg),model=resolve(modelArg),out=process.env.QWEN35_TEST_OUT;
const hash=async path=>{const h=createHash('sha256');for await(const chunk of createReadStream(path))h.update(chunk);return h.digest('hex');};
assert.equal(await hash(join(runtime,'runtime.json')),manifestHash);
const manifest=JSON.parse(readFileSync(join(runtime,'runtime.json'),'utf8'));
assert.equal(manifest.version,'0.4.1');assert.equal(manifest.privateCandidate,true);
for(const file of manifest.files){
 assert.match(file.path,/^[a-zA-Z0-9_.+-]+$/);assert.ok(!['.','..'].includes(file.path));
 assert.equal(await hash(join(runtime,file.path)),file.sha256,file.path);
}
const modelHash='8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949';
const before=statSync(model);assert.equal(before.size,5629111584);assert.equal(await hash(model),modelHash);
const info=readGGUF(model,{includeTensors:true}),proof=qwen35MissingMtp(info);
assert.ok(proof);assert.equal(info.tensorCount,427);
assert.equal(info.metadata['qwen35.block_count'],33);assert.equal(info.metadata['qwen35.attention.recurrent_layers'].length,33);
const result={mode,model,modelSHA256:modelHash,modelBefore:{size:before.size,mtimeMs:before.mtimeMs,ctimeMs:before.ctimeMs},
 sourceCommit:manifest.source.commit,runtimeManifestSHA256:manifestHash,cases:[],fullWindowQualified:false,passed:false};
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function freePort(){const server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));const port=server.address().port;await new Promise(r=>server.close(r));return port;}
async function run(index,prompt,expected){
 const profile=join(out,`cycle-${index}`);mkdirSync(profile);
 const port=await freePort(),key=randomBytes(32).toString('hex'),base=`http://127.0.0.1:${port}`;
 const args=['-m',model,'--host','127.0.0.1','--port',String(port),'-c','98304','--metrics','--slots','--jinja','--no-webui',
  '-ngl','999','-t','12','-ctk','q8_0','-ctv','q8_0','-b','2048','-ub','512','-fa','on','-np','1',
  '--temp','0.6','--top-p','0.95','--top-k','40','--repeat-penalty','1.05','--offline','-lv','4','--spec-type',mode==='explicit-mtp'?'draft-mtp':'none'];
 const started=Date.now(),entry={args,profile,port,startedAt:new Date(started).toISOString(),ready:false,stopped:false};result.cases.push(entry);
 let log='',proc,closed;
 const call=async(path,body)=>{
  const response=await fetch(base+path,{method:body?'POST':'GET',headers:{authorization:`Bearer ${key}`,...(body?{'content-type':'application/json'}:{})},
   body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(body?90000:1500)});
  const data=await response.json();return {status:response.status,data};
 };
 try{
  proc=spawn(join(runtime,'llama-server.exe'),args,{windowsHide:true,cwd:profile,env:{...explicitKvEnvironment(),
   PATH:join(process.env.SystemRoot??'C:/Windows','System32'),LLAMA_CACHE:join(profile,'cache'),LLAMA_API_KEY:key},stdio:['ignore','pipe','pipe']});
  entry.pid=proc.pid;
  closed=new Promise((resolveClosed,reject)=>{proc.on('error',reject);proc.on('close',(code,signal)=>resolveClosed({code,signal}));});
  const consume=chunk=>{log+=chunk.toString();if(log.length>16*1024**2){entry.logLimitExceeded=true;log=log.slice(0,16*1024**2);proc.kill('SIGTERM');}};
  proc.stdout.on('data',consume);proc.stderr.on('data',consume);
  while(proc.exitCode===null&&proc.signalCode===null&&Date.now()-started<180000){
   try{const health=await call('/health');if(health.status===200&&health.data.status==='ok'){entry.ready=true;break;}}catch{}
   await pause(300);
  }
  entry.readySeconds=(Date.now()-started)/1000;
  if(mode==='explicit-mtp'){
   if(proc.exitCode!==null||proc.signalCode!==null)await closed;
   assert.equal(entry.ready,false,'An explicit MTP request must not silently become ordinary inference');
   assert.notEqual(proc.exitCode,null,'Explicit MTP rejection must exit promptly');
   assert.match(log,/blk\.32\.attn_norm\.weight.*not found/);
  }else{
   assert.equal(entry.ready,true,'Runtime did not become healthy');
   assert.match(log,/trunk-only export: 32 trunk layers, no MTP tensors; MTP not requested/);
   assert.match(log,/K \(q8_0\).*V \(q8_0\)/,'Effective K/V must remain Q8_0');
   assert.match(log,/flash_attn\s*=\s*enabled/);
   assert.match(log,/offloaded [1-9][0-9]*\/[0-9]+ layers to GPU/);
   entry.observedAllocation=log.split('\n').filter(line=>/K \(q8_0\).*V \(q8_0\)|flash_attn\s*=|offloaded [0-9]+\/[0-9]+ layers to GPU/.test(line));
   const props=await call('/props');assert.equal(props.status,200);
   entry.effectiveContext=props.data.default_generation_settings?.n_ctx;
   assert.equal(entry.effectiveContext,98304,'Requested capacity must remain intact');
   const response=await call('/v1/chat/completions',{messages:[{role:'user',content:prompt}],max_tokens:64,
    temperature:0,seed:42,chat_template_kwargs:{enable_thinking:false},stream:false});
   entry.httpStatus=response.status;entry.response=response.data;
   assert.equal(response.status,200);
   const text=response.data.choices?.[0]?.message?.content;
   assert.equal(typeof text,'string');assert.ok(text.trim().length>0);
   assert.equal(text.trim(),expected,'Synthetic arithmetic response');
   entry.prompt=prompt;entry.expected=expected;entry.arithmeticPassed=true;
  }
 }finally{
  if(proc&&proc.exitCode===null&&proc.signalCode===null)proc.kill('SIGTERM');
  if(closed)entry.exit=await closed;
  entry.elapsedSeconds=(Date.now()-started)/1000;
  entry.stopped=!!proc&&(proc.exitCode!==null||proc.signalCode!==null);
  writeFileSync(join(profile,'engine.log'),log.replaceAll(key,'[redacted]'));
  writeFileSync(join(profile,'case.json'),JSON.stringify(entry,null,2));
 }
 assert.ok(entry.stopped);
 await pause(500);
 let reachable=false;
 try{await fetch(base+'/health',{signal:AbortSignal.timeout(700)});reachable=true;}catch{}
 assert.equal(reachable,false,'Owned server must release its port before restart');
}
try{
 await run(1,'What is 2 + 3? Reply with only the number.','5');
 if(mode==='chat')await run(2,'What is 7 * 8? Reply with only the number.','56');
 result.passed=true;
}finally{
 const after=statSync(model);result.modelAfter={size:after.size,mtimeMs:after.mtimeMs,ctimeMs:after.ctimeMs};
 result.modelUnchanged=before.size===after.size&&before.mtimeMs===after.mtimeMs&&before.ctimeMs===after.ctimeMs&&await hash(model)===modelHash;
 result.passed=result.passed&&result.modelUnchanged;
 writeFileSync(join(out,'qualification.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
 assert.ok(result.modelUnchanged,'Original GGUF identity must remain unchanged');
}
