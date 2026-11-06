/** Supplemental component regressions: actual React/ModelRun, controlled in-memory boundaries, no Host or E1 claim. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { chromium } from 'playwright-core';
import { mkdtemp, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const root = resolve(import.meta.dirname, '..');
const ui = `import React from 'react';
export const Btn=({children,onClick,disabled})=>React.createElement('button',{onClick,disabled},children);
export const Select=({ariaLabel,value,options,onChange,disabled})=>React.createElement('select',{'aria-label':ariaLabel,value,disabled,onChange:e=>onChange(e.target.value)},options.map(o=>React.createElement('option',{key:o.value,value:o.value},o.label)));
export const Screen=({children,titleDetail,actions})=>React.createElement('main',null,titleDetail,actions,children);
export const ErrorNotice=({message})=>React.createElement('p',{role:'alert'},message);
export const RunImageModel=({library})=>React.createElement('output',{'data-image':true},library?.selected??'off');
export const Dialog=()=>null,ActionError=()=>null,Icon=()=>null,DemoTest=()=>null,RunExpertEditor=()=>null,RunPreview=()=>null,RunningModels=()=>null,LocalModelImport=()=>null,GpuRoles=()=>null,FloatingMenu=()=>null,NativeModels=()=>null,NativeLocalModel=()=>null,ModelsScreen=()=>null;`;
const store = `import {useSyncExternalStore} from 'react';
const listeners=new Set();
export const getState=()=>window.__fixture;
function put(patch){window.__fixture={...window.__fixture,...patch};listeners.forEach(f=>f());}
export const useStore=select=>select(useSyncExternalStore(f=>{listeners.add(f);return()=>listeners.delete(f)},getState));
export function setConfigDraft(configDraft){put({configDraft});}
export function selectImageModel(selected){return new Promise((resolve,reject)=>window.__requests.push({selected,resolve:()=>{put({imageModels:{...window.__fixture.imageModels,selected}});resolve()},reject}));}
export const useLifecycle=()=>({allowed:true});
export const applyImageModel=async()=>{throw Error('unexpected apply')},loadRuntimeModel=applyImageModel,loadVariant=applyImageModel,restartEngine=applyImageModel,saveEngine=applyImageModel;
export const pushToast=()=>{},validateEngine=async()=>({ok:true,issues:[]});`;
const stubs = {
    store,
    native: 'export const useNative=()=>null,nativeSettled=()=>true,subscribeNative=()=>()=>{};',
    client: 'export const api={post:async()=>{throw Error("unexpected API")}};',
    i18n: 'export const tr=value=>value;',
    experience: 'export const contextTokens=value=>value==="recommended"?131072:parseFloat(value)*1024,estimate=()=>({}),execution=()=>({threads:4});',
    'run-memory': 'export const planMemory=()=>null,demoRunExperience=value=>value;',
    features: 'export const IMAGE_GENERATION_VISIBLE=true;',
};
const bundle = await build({
    stdin: { contents: `import React from 'react'; import {createRoot} from 'react-dom/client'; import {ModelRunScreen} from './src/screens/ModelRun'; window.__root=createRoot(document.getElementById('root')); window.__root.render(React.createElement(ModelRunScreen));`, resolveDir: root, loader: 'tsx' },
    bundle: true, write: false, format: 'iife', platform: 'browser', jsx: 'automatic',
    define: { 'process.env.NODE_ENV': '"test"' },
    plugins: [{ name: 'controlled-component-boundaries', setup(b) {
        b.onResolve({ filter: /\/components\/|\.\/Models$/ }, () => ({ path: 'ui', namespace: 'boundary' }));
        b.onResolve({ filter: /\/lib\/(store|native|client|i18n|experience|run-memory|features)$/ }, args => ({ path: args.path.split('/').at(-1), namespace: 'boundary' }));
        b.onLoad({ filter: /.*/, namespace: 'boundary' }, args => ({ contents: args.path === 'ui' ? ui : stubs[args.path], loader: 'jsx', resolveDir: root }));
    } }],
});

const model = (id, quant) => ({ id, name: id, label: id, family: 'Local models', quant, params: '27B', local: { architecture: 'qwen35' }, state: 'installed', contextMax: id === 'q36' ? 131072 : 32768, diskGb: 20, tags: [], kvModes: ['FP16'] });
const hardware = { host: { name: 'Test', platform: 'win32', arch: 'x64' }, cpu: { model: 'CPU', cores: 6 }, memory: { totalGb: 32 }, gpus: [], accelerator: { backend: 'cpu', unified: false } };
const qconfig = { schema: 'strata.engine/1', beginner: { contextLength: '128k' }, expert: { 'ctx.length': '128K', 'gpu.cpuMoeLayers': 28, 'runtime.backend': 'Automatic' } };
const engine = { engine: { version: 'test' }, beginner: qconfig.beginner, expert: Object.entries(qconfig.expert).map(([id, value]) => ({ id, value, recommended: id === 'gpu.cpuMoeLayers' ? 0 : value })) };
const computer = JSON.stringify({ host: 'Test', platform: 'win32', arch: 'x64', cpu: 'CPU', cores: 6, ram: 32, gpus: [], backend: 'cpu' });
const empty = { schema: 1, profiles: [], defaults: {} };
const saved = { schema: 1, defaults: { [computer+'\nq36']: 'q', [computer+'\nhikari']: 'h' }, profiles: [
    { id: 'q', name: 'Q', variantId: 'q36', hardware: computer, engineVersion: 'test', config: qconfig, imageModel: 'q6' },
    { id: 'h', name: 'H', variantId: 'hikari', hardware: computer, engineVersion: 'test', config: { ...qconfig, beginner: { contextLength: '32k' }, expert: { 'ctx.length': '32K', 'gpu.cpuMoeLayers': 0, 'runtime.backend': 'PrismML' } }, imageModel: 'off' },
] };

async function fixture(t, id, profiles = empty, draft = null) {
    const home = await mkdtemp(join(tmpdir(), 'strata-e2-component-'));
    const dirs = Object.fromEntries(['home','local','roaming','workspace','models','components','runtime','tmp'].map(name=>[name,join(home,name)]));
    await Promise.all(Object.values(dirs).map(path=>mkdir(path,{recursive:true})));
    const html = join(home,'index.html'); await writeFile(html,'<!doctype html><html><body><div id="root"></div></body></html>');
    const env = Object.fromEntries(Object.entries(process.env).filter(([key])=>!/^STRATA_|^DSH_|^WEBVIEW2_/i.test(key)));
    Object.assign(env,{LOCALAPPDATA:dirs.local,APPDATA:dirs.roaming,TEMP:dirs.tmp,TMP:dirs.tmp,STRATA_HOME:dirs.home,STRATA_WORKSPACE:dirs.workspace,STRATA_MODELS_DIR:dirs.models,STRATA_COMPONENTS_DIR:dirs.components,STRATA_RUNTIME_DIR:dirs.runtime,STRATA_SETTINGS_FILE:join(home,'settings.json'),STRATA_NO_ACQUIRE:'1',STRATA_NO_BUNDLED_ENGINE:'1',STRATA_NO_REPAIR_ACCESS:'1',STRATA_AGENT:'off'});
    const browser = await chromium.launchPersistentContext(join(home,'browser'),{ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true, env, timeout:10000,args: ['--disable-gpu','--disable-background-networking','--disable-component-update','--no-first-run'] });
    t.diagnostic('isolated browser profile: '+join(home,'browser'));
    t.after(async()=>{await browser.close();});
    const page = await browser.newPage();
    page.setDefaultTimeout(10000);
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    await page.route(/^https?:/,route=>route.abort());
    await page.goto(pathToFileURL(html).href);
    await page.evaluate(({id,profiles,engine,hardware,models,draft})=>{
        localStorage.clear();sessionStorage.clear();localStorage.setItem('strata.run-profiles.v1',JSON.stringify(profiles));
        if(id===null)localStorage.setItem('strata.run-local-variant.v1','hikari');
        if(draft)sessionStorage.setItem('strata.run-variant.v1',id);
        location.hash=id===null?'/models/local':'/models/local?variant='+id;
        window.__requests=[];
        window.__fixture={engine,hardware,library:{loaded:null,current:null,variants:models,disk:{modelsDir:'isolated'}},runtime:null,imageModels:{selected:'q6',applied:'off',generationAvailable:true,variants:[]},configDraft:draft,busy:{},connection:'offline'};
    },{id,profiles,engine,hardware,draft,models:[model('q36','Q4_K_M'),model('hikari','PQ2_0')]});
    await page.addScriptTag({content:bundle.outputFiles[0].text});
    await page.locator('select[aria-label="Model version"]').waitFor();
    t.after(()=>assert.deepEqual(errors,[]));
    return page;
}

test('mounted fresh explicit target without a saved default matches picker restoration, not global Q36 settings', async t => {
    const direct=await fixture(t,'hikari');
    const picked=await fixture(t,'q36');
    await picked.locator('select[aria-label="Model version"]').selectOption('hikari');
    await picked.waitForFunction(()=>new URLSearchParams(location.hash.split('?')[1]).get('variant')==='hikari');
    await picked.waitForFunction(()=>window.__fixture.configDraft!==null);
    const a=await direct.evaluate(()=>JSON.parse(window.__fixture.configDraft??JSON.stringify({beginner:window.__fixture.engine.beginner,expert:Object.fromEntries(window.__fixture.engine.expert.map(p=>[p.id,p.value]))})));
    const b=await picked.evaluate(()=>JSON.parse(window.__fixture.configDraft));
    assert.deepEqual(a,b);
    assert.equal(a.beginner.contextLength,'32k');
    assert.equal(a.expert['gpu.cpuMoeLayers'],0);
    assert.equal(a.expert['runtime.backend'],'PrismML');
});

test('mounted bare-route restoration initializes the durable target while an established own session draft survives', async t => {
    const restored=await fixture(t,null);
    await restored.waitForFunction(()=>new URLSearchParams(location.hash.split('?')[1]).get('variant')==='hikari');
    const config=await restored.evaluate(()=>JSON.parse(window.__fixture.configDraft));
    assert.equal(config.beginner.contextLength,'32k');
    assert.equal(config.expert['gpu.cpuMoeLayers'],0);
    const own={...qconfig,expert:{...qconfig.expert,'gpu.cpuMoeLayers':17}};
    const editing=await fixture(t,'q36',saved,JSON.stringify(own));
    assert.equal(await editing.evaluate(()=>JSON.parse(window.__fixture.configDraft).expert['gpu.cpuMoeLayers']),17);
});

test('mounted rapid Back/Forward binds intended images before delayed replies and ignores stale completions', async t => {
    const page=await fixture(t,'q36',saved);
    await page.waitForFunction(()=>JSON.parse(window.__fixture.configDraft??'{}').beginner?.contextLength==='128k');
    const initial=await page.evaluate(()=>window.__requests.length);
    await page.evaluate(()=>{location.hash='/models/local?variant=hikari';});
    await page.waitForFunction(n=>window.__requests.length>n,initial);
    await page.goBack();
    await page.waitForFunction(n=>window.__requests.length>n+1,initial);
    await page.goForward();
    await page.waitForFunction(n=>window.__requests.length>n+2,initial);
    const transitions=await page.evaluate(n=>window.__requests.slice(n).map(r=>r.selected),initial);
    assert.deepEqual(transitions,['off','q6','off']);
    await page.evaluate(n=>window.__requests[n+2].resolve(),initial);
    await page.evaluate(n=>window.__requests[n+1].resolve(),initial);
    assert.equal(await page.locator('[data-image]').textContent(),'off');
    if(initial) {
        await page.evaluate(()=>window.__requests[0].reject(new Error('obsolete model image failure')));
        await page.evaluate(()=>new Promise(resolve=>queueMicrotask(resolve)));
        assert.equal(await page.getByRole('alert').count(),0);
    }
    await page.evaluate(n=>window.__requests[n].resolve(),initial);
    await page.goBack();
    await page.waitForFunction(n=>window.__requests.length>n+3,initial);
    assert.equal(await page.locator('[data-image]').textContent(),'q6');
});
