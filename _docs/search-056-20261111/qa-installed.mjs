/** Actual installed shell/WebView2 and real RustXNG; the language-model API is an explicit local test fixture. */
import assert from 'node:assert/strict';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { setTimeout as delay } from 'node:timers/promises';

const root='C:/Users/downl/Documents/ChatGPT/Strata';
const out='H:/Strata/releases/search-056-20261111-codex';
const target=process.argv[3]??'installed';assert.ok(['candidate','installed'].includes(target));
const app=target==='installed'?'C:/Users/downl/AppData/Local/Programs/Strata':join(out,'extracted');
const attempt=process.argv[2]??'r1'; assert.match(attempt,/^r[1-9][0-9]*$/);
const home=join(out,'qa-'+target+'-'+attempt);mkdirSync(home);
for(const name of ['data','workspace','models','components','profiles','runtime','desktop','Local','Roaming','temp','screenshots'])mkdirSync(join(home,name));
writeFileSync(join(home,'data/state.json'),JSON.stringify({version:1,setup:{complete:true,flowVersion:2,step:4,history:[]},installed:{},current:null,loaded:null,expert:{'sample.maxTokens':64}}));
writeFileSync(join(home,'shell-prefs.json'),JSON.stringify({port:0,tray:false,language:'en'}));
const digest=path=>createHash('sha256').update(readFileSync(path)).digest('hex');
const build=JSON.parse(readFileSync(join(out,'app-build.json'),'utf8'));
assert.equal(digest(join(app,'strata-desktop.exe')),JSON.parse(readFileSync(join(out,'nsis-shell-binding.json'),'utf8')).nsisSHA256);
const requests=[];let mainResponse=null,mainClosed=false,mainReleased=false;
const model=http.createServer(async(req,res)=>{
  const parts=[];for await(const part of req)parts.push(part);
  const body=parts.length?JSON.parse(Buffer.concat(parts)):null;
  if(req.url.includes('/models')){res.setHeader('content-type','application/json');res.end(JSON.stringify({data:[{id:'qa-model',name:'QA model',context_length:8192,input_modalities:['text']}]}));return;}
  if(req.url==='/props'){res.setHeader('content-type','application/json');res.end(JSON.stringify({modalities:{vision:false}}));return;}
  requests.push(body);
  res.writeHead(200,{'content-type':'text/event-stream'});
  const send=value=>res.write('data: '+JSON.stringify(value)+'\n\n');
  const text=(body?.messages??[]).filter(row=>row.role==='user').at(-1)?.content??'';
  if(String(text).includes('MAIN_PENDING_056')){
    mainResponse=res;
    res.on('close',()=>{if(!mainReleased)mainClosed=true;});
    send({choices:[{index:0,delta:{content:'Main task running.\n'}}]});
    const heartbeat=setInterval(()=>res.write(': keepalive\n\n'),1000);res.on('close',()=>clearInterval(heartbeat));return;
  }
  const answer=String(text).includes('Side question:')?'SIDE_ANSWER_056':'FOLLOW_UP_ANSWER_056';
  send({choices:[{index:0,delta:{content:answer}}]});
  send({choices:[{index:0,delta:{},finish_reason:'stop'}],usage:{prompt_tokens:20,completion_tokens:8}});
  res.end('data: [DONE]\n\n');
});
await new Promise(resolve=>model.listen(0,'127.0.0.1',resolve));
const portProbe=http.createServer();await new Promise(resolve=>portProbe.listen(0,'127.0.0.1',resolve));const debugPort=portProbe.address().port;await new Promise(resolve=>portProbe.close(resolve));
const env=Object.fromEntries(Object.entries(process.env).filter(([key])=>!/^(STRATA_|DSH_|WEBVIEW2_)/i.test(key)&&!/(API_KEY|TOKEN|SECRET|PASSWORD)$/i.test(key)));
Object.assign(env,{STRATA_HOME:home,STRATA_INSTALL_DIR:join(home,'install'),STRATA_COMPONENTS_DIR:join(home,'components'),STRATA_PROFILE_DIR:join(home,'profiles'),STRATA_RUNTIME_DIR:join(home,'runtime'),STRATA_SETTINGS_FILE:join(home,'settings.json'),STRATA_MODELS_DIR:join(home,'models'),STRATA_WORKSPACE:join(home,'workspace'),STRATA_DESKTOP_DATA_DIR:join(home,'desktop'),STRATA_AGENT:'off',STRATA_NO_ACQUIRE:'1',STRATA_NO_BUNDLED_ENGINE:'1',STRATA_NO_REPAIR_ACCESS:'1',STRATA_NO_DIALOG:'1',DSH_HOME:join(home,'harness'),APPDATA:join(home,'Roaming'),LOCALAPPDATA:join(home,'Local'),TEMP:join(home,'temp'),TMP:join(home,'temp'),WEBVIEW2_USER_DATA_FOLDER:join(home,'webview'),WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-address=127.0.0.1 --remote-debugging-port=${debugPort}`});
const child=spawn(join(app,'strata-desktop.exe'),[],{env,windowsHide:true,stdio:'ignore'});
const {chromium}=createRequire(join(root,'apps/host/package.json'))('playwright-core');
let browser,page,base;const errors=[],sideBodies=[];
const until=async(fn,ms=30_000)=>{const end=Date.now()+ms;while(Date.now()<end){const value=await fn();if(value)return value;await delay(150);}throw new Error('QA condition timed out');};
const call=async(path,method='GET',body)=>{const response=await fetch(base+path,{method,headers:{origin:base,'content-type':'application/json','x-strata-client':'isolated-feature-qa'},...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(60_000)});assert.equal(response.status,200,`${path}: ${response.status}`);return response.json();};
const report={ok:false,target,actualInstalledExe:target==='installed',actualWebView2:true,isolatedHome:true,mockModelOnly:true,realRustxng:true,checks:[]};
try{
  await until(async()=>{try{return (await fetch(`http://127.0.0.1:${debugPort}/json/version`,{signal:AbortSignal.timeout(700)})).ok;}catch{return false;}},60_000);
  browser=await chromium.connectOverCDP(`http://127.0.0.1:${debugPort}`);
  page=await until(()=>browser.contexts().flatMap(context=>context.pages()).find(page=>/^http:\/\/127\.0\.0\.1:\d+/.test(page.url())));
  base=new URL(page.url()).origin;
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
  page.on('request',request=>{if(new URL(request.url()).pathname==='/api/chat/btw')sideBodies.push(JSON.parse(request.postData()));});
  const identity=await call('/api/app/build');assert.deepEqual(identity,{host:'0.5.6-local.1',shell:'0.5.6-local.1'});report.checks.push('installed-host-shell-renderer-identity');
  const provider=await call('/api/model-providers','POST',{kind:'custom',name:'Isolated QA model fixture',baseUrl:`http://127.0.0.1:${model.address().port}/v1`,protocol:'openai-chat',models:[{id:'qa-model',name:'QA model',vision:false,reasoning:false,contextMax:8192}]});
  const connectionId=provider.connections.find(row=>row.name==='Isolated QA model fixture').id;
  const id='qa-side-056';
  await call('/api/chats/import','POST',{sessions:[{id,title:'Isolated side-question QA',workspace:join(home,'workspace'),messages:[],tokensIn:0,tokensOut:0,createdAt:new Date().toISOString(),updatedAt:new Date().toISOString(),preferences:{agent:false,useTools:false,remoteModel:{connectionId,modelId:'qa-model'}}}]});
  await page.goto(base+'/#/chat/'+id);await page.reload();
  const input=page.getByRole('textbox',{name:/Message Strata|Strataにメッセージを送信/});await input.waitFor({timeout:60_000});
  await input.fill('MAIN_PENDING_056');await input.press('Enter');
  await until(()=>mainResponse);
  await page.getByText('Main task running.',{exact:true}).waitFor();
  await input.fill('/btw Explain the current status.');await input.press('Enter');
  await page.getByText('SIDE_ANSWER_056',{exact:true}).waitFor({timeout:30_000});
  assert.equal(mainClosed,false);assert.equal(mainReleased,false);assert.equal(sideBodies.length,1);
  const stored=await until(async()=>{const row=await call('/api/chats/'+id);return row.session.asides?.[0]?.answer==='SIDE_ANSWER_056'?row.session:null;});
  assert.equal(stored.messages.length,2);assert.equal(stored.messages.some(row=>row.content.includes('SIDE_ANSWER_056')),false);
  const sideRequest=requests.find(body=>JSON.stringify(body.messages).includes('Side question:'));
  assert.ok(sideRequest);assert.equal(sideRequest.tools,undefined);
  report.checks.push('btw-typed-during-main-stream','main-not-cancelled-or-queued','btw-tool-free-api','separate-durable-aside');
  await page.screenshot({path:join(home,'screenshots/btw-desktop.png'),fullPage:true});
  mainReleased=true;
  mainResponse.write('data: '+JSON.stringify({choices:[{index:0,delta:{content:'Main task finished.'}}]})+'\n\n');
  mainResponse.write('data: '+JSON.stringify({choices:[{index:0,delta:{},finish_reason:'stop'}],usage:{prompt_tokens:20,completion_tokens:12}})+'\n\n');mainResponse.end('data: [DONE]\n\n');
  await until(async()=>{const row=await call('/api/chats/'+id);return row.session.messages.at(-1)?.streaming===false;});
  await input.fill('/deep');await page.getByRole('option').filter({hasText:'/deepresearch'}).waitFor();
  await input.press('Escape');await input.fill('');report.checks.push('deepresearch-slash-menu');
  await call('/api/agent/tools','PUT',{groups:{search:true},search:{provider:'rustxng'}});
  const search=await call('/api/chat/web-search','POST',{sessionId:id,query:'Tauri NSIS Windows installer documentation',confirmed:true});
  assert.ok(search.sources.length>0);report.rustxngSources=search.sources.map(({title,url})=>({title,url}));report.checks.push('installed-rustxng-full-real-search');
  await page.reload();await page.getByText('SIDE_ANSWER_056',{exact:true}).waitFor();report.checks.push('aside-survives-page-reload');
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:join(home,'screenshots/btw-mobile.png'),fullPage:true});
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1);assert.equal(overflow,false);report.checks.push('mobile-no-horizontal-overflow');
  assert.deepEqual(errors,[]);report.consoleErrors=0;report.ok=true;
}finally{
  if(child.exitCode===null)child.kill();
  await browser?.close().catch(()=>{});
  model.closeAllConnections();await new Promise(resolve=>model.close(resolve));
  writeFileSync(join(home,'result.json'),JSON.stringify({...report,errors},null,2)+'\n',{flag:'wx'});
}
console.log(JSON.stringify(report,null,2));
