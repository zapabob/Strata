/** Supplemental mounted React component tests, with controlled API promises. No Host or engine E2E. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { chromium } from 'playwright-core';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = resolve(import.meta.dirname, '..');
const controls = `import React from 'react';
export const Btn=({children,onClick,disabled})=>React.createElement('button',{onClick,disabled},children);
export const Select=({ariaLabel,value,options,onChange,disabled})=>React.createElement('select',{'aria-label':ariaLabel,value,disabled,onChange:e=>onChange(e.target.value)},options.map(o=>React.createElement('option',{key:o.value,value:o.value},o.label)));
export const Screen=({children})=>React.createElement('main',null,children);
export const ErrorNotice=({message})=>React.createElement('p',{role:'alert'},message);
export const Dialog=()=>null,Icon=()=>null,VersionPicker=()=>null,FamilySwitch=()=>null,PcComputer=()=>null,GpuRoles=()=>null,DownloadParts=()=>null,EngineWarning=()=>null,EngineUpdateCard=()=>null,EngineUpdateDialog=()=>null,NativeDeleteDialog=()=>null,NativeSettingsFile=()=>null,NativeTune=()=>null,NativeTuneBadge=()=>null,NativePresets=()=>null,NativeMcpEditor=()=>null,RunImageModel=()=>null;`;
const boundaries = {
    ui: controls,
    native: `import {useSyncExternalStore} from 'react';export * from './src/lib/native.ts';
const listeners=new Set();export const useNative=()=>useSyncExternalStore(f=>{listeners.add(f);return()=>listeners.delete(f)},()=>window.__native);
window.__putNative=value=>{window.__native=value;listeners.forEach(f=>f())};export const refreshNative=async()=>{};
export const nativeAction=async(path,body)=>{window.__actions.push({path,body});if(path==='operations')return {id:'job-A'};};`,
    client: `const request=(method,path,body)=>new Promise((resolve,reject)=>window.__requests.push({method,path,body,resolve,reject}));export const api={get:path=>request('get',path),post:(path,body)=>request('post',path,body),patch:(path,body)=>request('patch',path,body)};`,
    store: `export const go=()=>{},setSettingsSection=()=>{},selectRemoteModel=()=>{},pushToast=()=>{},useStore=select=>select({imageModels:null,hardware:null});`,
    i18n: 'export const tr=value=>value;',
    features: 'export const IMAGE_GENERATION_VISIBLE=false;',
};
const bundle = await build({
    stdin: { contents: `import React from 'react';import {createRoot} from 'react-dom/client';import {NativeSettings} from './src/components/NativeSettings';import {NativeLocalModel} from './src/components/NativeLocalModel';import {NativeModels,NativeProgress} from './src/components/NativeModels';import {nativePollDelay} from './src/lib/native.ts';
window.__root=createRoot(document.getElementById('root'));window.__pollDelay=nativePollDelay;window.__render=(kind,model='A')=>window.__root.render(kind==='settings'?<NativeSettings model={model}/>:kind==='local'?<NativeLocalModel onBack={()=>{}} onAlternative={()=>{}}/>:kind==='models'?<NativeModels onOtherModels={()=>{}}/>:<NativeProgress job={window.__native.jobs[0]}/>);`, resolveDir: root, loader: 'tsx' },
    bundle:true,write:false,format:'iife',platform:'browser',jsx:'automatic',define:{'process.env.NODE_ENV':'"test"'},
    plugins:[{name:'controlled-boundaries',setup(b){
        b.onResolve({filter:/\/lib\/(native|client|store|i18n|features)$/},a=>({path:a.path.split('/').at(-1),namespace:'boundary'}));
        b.onResolve({filter:/\/components\/|^\.\/(ui|layout|VersionPicker|FamilySwitch|PcComputer|GpuRoles|DownloadParts|EngineWarning|EngineUpdateCard|EngineUpdateDialog|NativeDelete|NativeSettingsFile|NativeTune|NativeTuneBadge|NativePresets|NativeMcpEditor|RunImageModel)$/},a=> /\/(NativeSettings|NativeLocalModel|NativeModels|DecimalInput)$/.test(a.path)?undefined:({path:'ui',namespace:'boundary'}));
        b.onLoad({filter:/.*/,namespace:'boundary'},a=>({contents:boundaries[a.path],loader:'jsx',resolveDir:root}));
    }}],
});
const job = (state,summary='Operation A')=>({id:'job-A',kind:'load',model:'A',state,summary,error:state==='error'?'A failed':null,result:null,startedAt:'2026-11-06T00:00:00Z'});
const state = jobs=>({available:true,jobs,instances:[],fields:[],catalog:{families:[],contexts:[32768]},installed:{models:[]},hardware:{ram_gb:32,gpus:[]}});
async function fixture(t,kind='settings',jobs=[]) {
    const home=await mkdtemp(join(tmpdir(),'strata-e3c-component-'));
    const dirs=Object.fromEntries(['home','local','roaming','workspace','models','components','runtime','tmp'].map(n=>[n,join(home,n)]));
    await Promise.all(Object.values(dirs).map(p=>mkdir(p,{recursive:true})));
    const html=join(home,'index.html');await writeFile(html,'<!doctype html><div id="root"></div>');
    const env=Object.fromEntries(Object.entries(process.env).filter(([k])=>!/^STRATA_|^DSH_|^WEBVIEW2_/i.test(k)));
    Object.assign(env,{LOCALAPPDATA:dirs.local,APPDATA:dirs.roaming,TEMP:dirs.tmp,TMP:dirs.tmp,STRATA_HOME:dirs.home,STRATA_WORKSPACE:dirs.workspace,STRATA_MODELS_DIR:dirs.models,STRATA_COMPONENTS_DIR:dirs.components,STRATA_RUNTIME_DIR:dirs.runtime,STRATA_SETTINGS_FILE:join(home,'settings.json'),STRATA_NO_ACQUIRE:'1',STRATA_NO_BUNDLED_ENGINE:'1',STRATA_NO_REPAIR_ACCESS:'1',STRATA_AGENT:'off'});
    const browser=await chromium.launchPersistentContext(join(home,'browser'),{executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true,env,timeout:10000,args:['--disable-gpu','--disable-background-networking','--disable-component-update','--no-first-run']});
    t.after(()=>browser.close());t.diagnostic('isolated browser profile: '+join(home,'browser'));
    const page=await browser.newPage();page.setDefaultTimeout(5000);const errors=[];page.on('pageerror',e=>errors.push(e.message));t.after(()=>assert.deepEqual(errors,[]));
    await page.route(/^https?:/,r=>r.abort());await page.goto(pathToFileURL(html).href);
    await page.evaluate(s=>{window.__native=s;window.__requests=[];window.__actions=[]},state(jobs));await page.addScriptTag({content:bundle.outputFiles[0].text});await page.evaluate(k=>window.__render(k),kind);
    return page;
}
const values = n=>({values:{sampling:{temperature:n}},mcp:{},fields:[]});
async function settle(page,index,value,error=false){await page.evaluate(({index,value,error})=>{const r=window.__requests[index];error?r.reject(Error(value)):r.resolve(value)}, {index,value,error});await page.evaluate(()=>new Promise(r=>setTimeout(r,0)));}
async function settingsReady(page,index,n){await page.waitForFunction(i=>window.__requests.length>i,index);await settle(page,index,values(n));await page.locator('details.native-settings').evaluate(el=>el.open=true);await page.getByRole('tab',{name:'JSON',exact:true}).click();}

for(const fail of [false,true]) test(`settings model B ignores model A PATCH ${fail?'failure':'success'} and finally`,async t=>{
    const p=await fixture(t);await settingsReady(p,0,0.1);await p.getByRole('textbox',{name:'Native configuration JSON'}).fill(JSON.stringify({sampling:{temperature:0.2}}));await p.getByRole('button',{name:'Save settings',exact:true}).click();
    await p.waitForFunction(()=>window.__requests.length===2);await p.evaluate(()=>window.__render('settings','B'));await settingsReady(p,2,0.7);
    await p.getByRole('textbox',{name:'Native configuration JSON'}).fill(JSON.stringify({sampling:{temperature:0.8}}));
    // Current model is free to save while A's disk write finishes.
    const save=p.locator('.native-settings-actions button').first();
    const enabled=await save.isEnabled();
    assert.equal(enabled,true);
    await save.click();await p.waitForFunction(()=>window.__requests.length===4);
    await settle(p,1,fail?'obsolete A save failed':values(0.2),fail);
    assert.equal(JSON.parse(await p.getByRole('textbox',{name:'Native configuration JSON'}).inputValue()).sampling.temperature,0.8);
    assert.equal(await p.getByRole('alert').count(),0);assert.equal(await p.getByText(/^Saved\. Load/).count(),0);assert.equal(enabled,true);
    assert.equal(await p.getByRole('button',{name:'Saving…',exact:true}).isDisabled(),true);
    await settle(p,3,values(0.8));assert.equal(await p.getByRole('button',{name:'Save settings',exact:true}).isDisabled(),true);
});

const preview=path=>({path,preview:{file_count:1,total_bytes:1,file_set_status:'plausible',issues:[],candidate_selection:{family:'qwen',model:'B'}}});
for(const terminal of ['error','done']) test(`new file check detaches A ${terminal} result while keeping diagnostics`,async t=>{
    const p=await fixture(t,'local');const input=p.getByPlaceholder('Full path to the folder or the file');await input.fill('A.gguf');await p.getByRole('button',{name:'Check files',exact:true}).click();await settle(p,0,preview('A.gguf'));await p.getByRole('button',{name:'Prepare and load',exact:true}).click();await p.waitForFunction(()=>window.__actions.length===1);
    await p.evaluate(s=>window.__putNative(s),state([job(terminal)]));await p.getByText(terminal==='error'?'A failed':'Operation A',{exact:true}).waitFor();
    await input.fill('B.gguf');await p.getByRole('button',{name:'Check files',exact:true}).click();await settle(p,1,preview('B.gguf'));
    assert.equal(await p.getByText(terminal==='error'?'A failed':'Operation A',{exact:true}).count(),0);assert.equal(await p.evaluate(()=>window.__native.jobs[0].state),terminal);assert.equal(await p.getByRole('button',{name:'Prepare and load',exact:true}).isEnabled(),true);
});
test('running and cancelling remain visible and busy through another file preview until a terminal state',async t=>{
    const p=await fixture(t,'local',[job('running')]);const input=p.getByPlaceholder('Full path to the folder or the file');await input.fill('B.gguf');await p.getByRole('button',{name:'Check files',exact:true}).click();await settle(p,0,preview('B.gguf'));
    const prepare=p.getByRole('button',{name:'Prepare and load',exact:true});assert.equal(await prepare.isDisabled(),true);
    await p.evaluate(s=>window.__putNative(s),state([job('cancelling')]));
    assert.equal(await prepare.isDisabled(),true);assert.equal(await p.locator('.native-progress[data-state="cancelling"]').count(),1);assert.match(await p.locator('.native-progress').textContent(),/Stopping…/);assert.equal(await p.getByRole('button',{name:'Stopping…',exact:true}).isDisabled(),true);
    assert.equal(await p.evaluate(()=>window.__pollDelay(window.__native)),1000);
    for(const terminal of ['cancelled','error','done']){await p.evaluate(s=>window.__putNative(s),state([job(terminal)]));assert.equal(await prepare.isEnabled(),true);assert.equal(await p.locator('.native-progress').count(),0);assert.equal(await p.evaluate(()=>window.__pollDelay(window.__native)),2500);}
});
test('NativeModels keeps Load disabled and progress visible while cancellation is pending',async t=>{
    const p=await fixture(t,'models');
    const ready=state([]);ready.catalog.families=[{family:'qwen',title:'Qwen',images:false,sizes:[{id:'B',model:'B',download_gb:1,ram_needed_gb:1,experts_gb:1}]}];ready.installed.models=[{model:'B',ready:true,context:32768,contextChosen:true,kv:'int8'}];
    await p.evaluate(s=>window.__putNative(s),ready);
    const load=p.getByRole('button',{name:'Load model',exact:true});await load.waitFor();assert.equal(await load.isEnabled(),true);
    await p.evaluate(s=>window.__putNative(s),{...ready,jobs:[job('cancelling')]});
    assert.equal(await p.locator('.native-progress[data-state="cancelling"]').count(),1);assert.equal(await load.isDisabled(),true);
    await p.evaluate(s=>window.__putNative(s),{...ready,jobs:[job('cancelled')]});assert.equal(await load.isEnabled(),true);
});

test('returning to A performs a fresh read and ignores the previous visit save reply',async t=>{
    const p=await fixture(t);await settingsReady(p,0,0.1);await p.getByRole('textbox',{name:'Native configuration JSON'}).fill(JSON.stringify({sampling:{temperature:0.2}}));await p.getByRole('button',{name:'Save settings',exact:true}).click();await p.waitForFunction(()=>window.__requests.length===2);
    await p.evaluate(()=>window.__render('settings','B'));await settingsReady(p,2,0.7);
    await p.evaluate(()=>window.__render('settings','A'));await settingsReady(p,3,0.4);
    assert.deepEqual(await p.evaluate(()=>window.__requests.filter(r=>r.method==='get').map(r=>r.path)),['/api/native/models/A/settings','/api/native/models/B/settings','/api/native/models/A/settings']);
    await settle(p,1,values(0.2));assert.equal(JSON.parse(await p.getByRole('textbox',{name:'Native configuration JSON'}).inputValue()).sampling.temperature,0.4);assert.equal(await p.getByText(/^Saved\. Load/).count(),0);
});
