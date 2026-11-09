/** Real-Q36 negative acceptance only. Inlined into both isolated WebView2 recipes. */
import assert from 'node:assert/strict';

const feature='refusal_direction_removal';
const japaneseLabel='拒否方向ベクトルの除去';
const negativeStates=new Set(['unobserved','off']);

/** Saved intent and API health never count as actual vector observation. */
export function validateQ36ProjectionSettings(settings){
 const field=settings.fields?.find(item=>item.id===feature);
 assert.ok(field,'Actual native settings must expose refusal_direction_removal');
 assert.equal(field.supported,false,'Q36 must not advertise control-vector support');
 assert.equal(typeof field.unavailableReason,'string');assert.ok(field.unavailableReason.trim());
 assert.equal(settings.refusalProjection?.supported,false);
 assert.equal(typeof settings.refusalProjection.reason,'string');assert.ok(settings.refusalProjection.reason.trim());
 assert.match(settings.refusalProjection.reason,/Qwen3\.6|Q36/i);
 assert.equal(settings.refusalProjection.requested,false,'Fresh Q36 config must keep projection off');
 assert.notEqual(settings.values?.[feature],true);
 return {supported:false,reason:settings.refusalProjection.reason};
}

/** Reject positive/stale UI badges unless this real current child can justify OFF. */
export function validateQ36ProjectionObservation(instance,state,{unloaded=false}={}){
 assert.ok(negativeStates.has(state),`Unsupported Q36 must not display projection state ${state}`);
 const info=instance?.metrics?.engine,child=info?.native_child;
 assert.ok(info?.cvec===undefined||info.cvec===null||info.cvec===0||info.cvec==='0','Q36 must not report a loaded control vector');
 if(unloaded||instance?.status!=='ready')assert.equal(state,'unobserved','An unloaded/stopped child must not retain an observation');
 if(state==='off'){
  assert.equal(instance?.status,'ready');assert.equal(child?.alive,true);assert.equal(child?.admitted,true);
  assert.ok(info.cvec===0||info.cvec==='0','OFF needs real cvec=0 INFO');
  const observed=instance.q36Run?.observed;assert.equal(observed?.status,'observed');
  assert.equal(child.generation,observed.generation,'OFF belongs to a stale child generation');
  assert.equal(child.process_id,observed.processId,'OFF belongs to a stale child process');
 }
 return {state,cvec:info?.cvec??null};
}

/** Inject only live lifecycle accessors; never intercept an HTTP route or fabricate INFO. */
export function createQ36ProjectionAcceptance({getPage,request,until,language,modelScreen,modelId,modelPath,hashFile,getBase,home,result}){
 const checks=[],observations=[];
 const current=async()=>{
  const native=await request('/api/native');
  return {native,instance:native.instances.find(item=>item.model===modelId&&item.status==='ready')??native.instances.find(item=>item.model===modelId)};
 };
 async function settings(){const value=await request(`/api/native/models/${modelId}/settings`);validateQ36ProjectionSettings(value);return value;}
 function record(name){checks.push(name);result.checks.push('q36-projection-'+name);}
 async function status(stage,unloaded=false){
  await settings();
  const page=getPage(),panel=page.locator('details.native-settings');await panel.evaluate(element=>element.open=true);
  const badge=panel.locator('[data-refusal-projection]');await badge.waitFor({state:'visible'});assert.equal(await badge.count(),1);
  assert.equal(await badge.getAttribute('role'),'status');assert.ok((await badge.innerText()).trim());
  if(unloaded)await until(async()=>await badge.getAttribute('data-refusal-projection')==='unobserved',15);
  const {instance}=await current(),state=await badge.getAttribute('data-refusal-projection');
  observations.push({stage,...validateQ36ProjectionObservation(instance,state,{unloaded}),processId:instance?.q36Run?.observed?.processId??null,generation:instance?.q36Run?.observed?.generation??null});
  assert.equal(await page.locator('[data-refusal-projection="applied"]:visible').count(),0,'Saving/request history must not invent application');
  record(stage);
 }
 async function japaneseSettings(){
  await language('ja');
  const page=getPage(),panel=page.locator('details.native-settings');await panel.waitFor();await panel.evaluate(element=>element.open=true);
  const region=panel.getByRole('region',{name:japaneseLabel,exact:true});await region.waitFor({state:'visible'});
  await region.getByText(japaneseLabel,{exact:true}).waitFor({state:'visible'});
  assert.equal(await region.getByRole('combobox',{name:japaneseLabel,exact:true}).count(),0,'Unsupported Q36 must not offer enable');
  const actual=await settings();
  const reason=region.locator('p').filter({hasText:/Qwen3\.6|Q36/i});assert.ok(await reason.count()>0,'Japanese Q36 unavailability reason missing');
  const reasonText=await reason.first().innerText();assert.match(reasonText,/[\u3040-\u30ff\u3400-\u9fff]/,'Unsupported reason must be localised');
  const badge=region.locator('[data-refusal-projection]');await badge.waitFor({state:'visible'});assert.equal(await badge.getAttribute('role'),'status');
  assert.match(await badge.innerText(),/[\u3040-\u30ff\u3400-\u9fff]/,'Actual status must be Japanese');
  const {instance}=await current();validateQ36ProjectionObservation(instance,await badge.getAttribute('data-refusal-projection'),{unloaded:true});
  await region.screenshot({path:home+'/screenshots/q36-projection-japanese.png'});
  observations.push({stage:'japanese-label-and-reason',state:await badge.getAttribute('data-refusal-projection'),supported:actual.refusalProjection.supported});
  record('japanese-label-and-reason');
  await language('en');await modelScreen();
 }
 async function rejectedEnable(live){
  for(const kind of ['settings-patch','load-operation']){
   const beforeSettings=await settings(),before=await current(),beforeHash=hashFile(modelPath);
   const identity=before.instance?.q36Run?.observed;
   assert.equal(before.instance?.status,'ready');assert.equal(identity?.processId,live.processId);assert.equal(identity.generation,live.generation);
   const path=kind==='settings-patch'?`/api/native/models/${modelId}/settings`:'/api/native/operations';
   const body=kind==='settings-patch'?{values:{...beforeSettings.values,[feature]:true},mcp:beforeSettings.mcp??{}}:{kind:'load',args:{model:modelId,values:{[feature]:true}}};
   const response=await fetch(getBase()+path,{method:kind==='settings-patch'?'PATCH':'POST',headers:{'content-type':'application/json','x-strata-client':'ui',Origin:getBase()},body:JSON.stringify(body),signal:AbortSignal.timeout(30000)});
   assert.ok([400,422].includes(response.status),`Unsupported enable must fail admission (${response.status})`);
   const error=await response.text();assert.match(error,/refusal|projection|Qwen3\.6|Q36/i,'Error must describe feature refusal');
   const afterSettings=await settings(),after=await current();
   assert.equal(hashFile(modelPath),beforeHash,'Rejected enable changed persisted config');
   assert.deepEqual(afterSettings.values,beforeSettings.values);assert.deepEqual(afterSettings.mcp,beforeSettings.mcp);
   assert.deepEqual(afterSettings.refusalProjection,beforeSettings.refusalProjection);
   assert.deepEqual(after.native.jobs.map(job=>job.id).sort(),before.native.jobs.map(job=>job.id).sort(),'Rejected enable created a job');
   assert.equal(after.instance?.id,before.instance.id);assert.equal(after.instance?.status,'ready');
   assert.equal(after.instance.q36Run.observed.processId,live.processId);assert.equal(after.instance.q36Run.observed.generation,live.generation,'Rejected enable replaced/unloaded the real child');
   record(kind+'-rejected-before-job-unload-persistence');
  }
  await status('rejected-enable-stays-unapplied');
 }
 async function sampling(){
  const page=getPage();
  // Ordinary chat settings, not a native load-setting editor. Discover only accessible controls.
  const opener=page.getByRole('button',{name:/Response settings/i});assert.equal(await opener.count(),1,'Ordinary Response settings opener missing');await opener.click();
  const toggle=page.getByRole('switch',{name:/refusal.direction removal.*request|request.*refusal.direction removal/i});
  if(!await toggle.isVisible()){
   const advanced=page.getByRole('button',{name:'Advanced',exact:true}).or(page.getByRole('tab',{name:'Advanced',exact:true})).or(page.locator('summary').filter({hasText:/^Advanced$/}));
   assert.equal(await advanced.count(),1,'Advanced sampling disclosure missing');await advanced.click();
  }
  await toggle.waitFor({state:'visible'});assert.equal(await toggle.count(),1);
  assert.equal(await toggle.isEnabled(),false,'Request switch must be disabled without a verified loaded vector');
  assert.equal(await toggle.isChecked(),false,'Request-only intent must stay OFF');
  assert.equal(await page.getByRole('switch',{name:/experimental speed projection/i}).count(),0,'Old speed/projection switch label remains');
  const drawerText=await toggle.evaluate(element=>{let node=element;while(node.parentElement&&!node.querySelector('[data-refusal-projection]'))node=node.parentElement;return node.textContent??'';});
  assert.match(drawerText,/request/i);assert.match(drawerText,/vector/i);
  assert.match(drawerText,/does not load.*vector|load.*native.*first|loaded.*vector/is,'Sampling help must distinguish requests from vector loading');
  const badges=page.locator('[data-refusal-projection]:visible');assert.ok(await badges.count()>0,'Sampling projection status is missing');
  const {instance}=await current();
  for(const badge of await badges.all()){assert.equal(await badge.getAttribute('role'),'status');validateQ36ProjectionObservation(instance,await badge.getAttribute('data-refusal-projection'));}
  await toggle.screenshot({path:home+'/screenshots/q36-projection-request-switch.png'});
  record('ordinary-request-switch-accessible-disabled-off');
  // Navigation back uses the same lifecycle as the original recipe and closes the drawer.
  await page.keyboard.press('Escape');await modelScreen();
 }
 function receipt(){
  for(const required of ['japanese-label-and-reason','save-only','after-profile-restart','settings-patch-rejected-before-job-unload-persistence','load-operation-rejected-before-job-unload-persistence','ordinary-request-switch-accessible-disabled-off','after-unload','reloaded-child'])assert.ok(checks.includes(required),'Missing projection acceptance: '+required);
  return {ok:true,supported:false,positiveProjectionRuntimeTested:false,q38RuntimeQualified:false,noMocks:true,checks,observations};
 }
 return {japaneseSettings,status,rejectedEnable,sampling,receipt};
}
