/** Refuse to package a current shell around stale GUI, Control or engine payloads. */
import {existsSync,readFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {resolve,join,relative} from 'node:path';
import {files,sha256,verifyHost,verifyTree,verifyEngine,verifyNativeBuild} from '../../host/scripts/release-integrity.mjs';
import {HARNESS_BUDGET_PATCH} from './harness-budget.mjs';
import {missingHarnessImports} from './harness-prune.mjs';
import {LOCAL_BACKENDS,findLocalBackend,verifyLocalBackend} from '../../host/server/local-backends.mjs';
const root=resolve(import.meta.dirname,'../../..');
const resources=join(root,'apps/desktop/src-tauri/resources');
const control=join(resources,'control');
const read=path=>readFileSync(path,'utf8').replace(/^\uFEFF/,'');
const json=path=>JSON.parse(read(path));
const product=read(join(root,'VERSION')).trim();
const engine=/project\(strata VERSION ([\d.]+)/.exec(read(join(root,'CMakeLists.txt')))?.[1];
verifyHost(join(root,'apps/host'));
const uiBuild=json(join(root,'apps/host/dist/release-build.json'));
if(uiBuild.recipe?.nodeVersion!=='24.22.2'||uiBuild.recipe?.publicPackage!==true||uiBuild.recipe?.publicAssetCommit!=='03f11e2d6adc319ea21e9a1d5820a99cd3767257')throw new Error('Rebuild with the public-package assets and system-font policy');
if(Object.keys(uiBuild.assets).some(name=>/gtwalsheim/i.test(name)))throw new Error('Unqualified supplied font in the release UI');
for(const name of ['icon.png','icon.ico'])if(sha256(join(root,'apps/desktop/src-tauri/icons',name))!==uiBuild.recipe.publicAssets?.[name])throw new Error('Stage the approved public shell icon before bundling');
const nsis=json(join(root,'apps/desktop/src-tauri/tauri.conf.json')).bundle?.windows?.nsis;
if(nsis?.headerImage||nsis?.sidebarImage)throw new Error('Unqualified supplied installer artwork');
const shellConfig=json(join(root,'apps/desktop/src-tauri/tauri.conf.json'));
if(JSON.stringify(shellConfig.plugins?.updater?.endpoints)!==JSON.stringify(['https://github.com/zapabob/Strata/releases/latest/download/latest.json']))throw new Error('The Hakua shell must use the fork update endpoint');
for(const name of ['apps/host/package.json','apps/desktop/package.json']) if(json(join(root,name)).version!==product) throw new Error(`Product version mismatch: ${name}`);
for(const name of ['strata_cli','strata_control','serve']) verifyTree(join(root,name),join(control,name));
for(const name of ['strata.py','requirements.txt','requirements-monitor.txt','setup.py']) if(sha256(join(root,name))!==sha256(join(control,name))) throw new Error(`Stale Control: ${name}`);
for(const path of files(join(control,'tools')).filter(path=>path.endsWith('.py'))) {
 const name=relative(control,path);
 if(!existsSync(join(root,name)) || sha256(join(root,name))!==sha256(path)) throw new Error(`Stale Control tool: ${name}`);
}
for(const name of ['hakua_hermes_memory_stack.py','strata_memory_mcp.py']) if(!existsSync(join(control,'tools',name))) throw new Error(`Missing Hakua tool: ${name}`);
const notices=join(resources,'notices'),noticeRecord=json(join(notices,'NOTICES.json'));
if(noticeRecord.schema!==1||!noticeRecord.files||!Object.keys(noticeRecord.files).length)throw new Error('Stage the third-party notices');
for(const name of ['Strata-MIT.txt','ggml-MIT.txt','NVIDIA-EULA.txt','NVIDIA-LICENSE.txt','Node-LICENSE.txt','Microsoft-VisualStudio-Community-2022.docx','Microsoft-Build-Tools-2022.docx','Microsoft-Visual-C-Runtime-2015-2022.docx'])if(!noticeRecord.files[name])throw new Error('Missing third-party notice: '+name);
const noticeNames=files(notices).map(path=>relative(notices,path).replaceAll('\\','/')).filter(name=>name!=='NOTICES.json').sort();
if(JSON.stringify(noticeNames)!==JSON.stringify(Object.keys(noticeRecord.files).sort()))throw new Error('Third-party notice membership changed');
for(const name of noticeNames)if(sha256(join(notices,name))!==noticeRecord.files[name])throw new Error('Third-party notice changed: '+name);
if(JSON.stringify(noticeRecord.microsoftSources)!==JSON.stringify(json(join(root,'packaging/microsoft-2022-notice-sources.json'))))throw new Error('Pinned Microsoft notice provenance changed');
const bundle=json(join(control,'BUNDLE.json'));
if(bundle.version!==engine || read(join(control,'VERSION')).trim()!==engine) throw new Error('Stale Control engine version');
if(bundle.installed?.['hakua-memory']!=='0.3.5') throw new Error('Missing locked Hakua-memory runtime');
const py=process.platform==='win32'?join(control,'python/python.exe'):join(control,'python/bin/python3');
const probe=spawnSync(py,['-I','-c',"import importlib.metadata as m; from hakua_memory.ebbinghaus.store import EbbinghausMemoryStore; from hakua_memory.composite import CompositeMemory; assert m.version('hakua-memory') == '0.3.5'"],{encoding:'utf8',timeout:30000,windowsHide:true});
if(probe.error || probe.status!==0) throw new Error(`Hakua runtime probe failed: ${probe.error??probe.stderr}`);
if(!existsSync(join(root,'apps/host/hakua-chatbot.enabled'))) throw new Error('Missing Hakua enable marker');
const harness=join(resources,'harness'),harnessBundle=json(join(harness,'BUNDLE.json'));
// Reviewed integration revision, documented in docs/work/IMPLEMENTATION_STATUS.md.
if(harnessBundle.commit!=='571902028a75c64c1d767f4ae5fd099485f0ddf0')throw new Error('Stage the reviewed Harness source revision');
const patch=harnessBundle.patches?.find(item=>item.id===HARNESS_BUDGET_PATCH.id);
if(!patch || patch.beforeSha256!==HARNESS_BUDGET_PATCH.beforeSha256 || patch.afterSha256!==sha256(join(harness,HARNESS_BUDGET_PATCH.file)))throw new Error('Stale Harness output-budget patch');
if(missingHarnessImports(harness).length)throw new Error('Missing Harness runtime dependencies');
if(process.platform==='win32') {
 const node=join(resources,'node/node.exe');
 if(sha256(join(resources,'node/LICENSE'))!=='ed34dd8e3f0a78dbaf00d0444ce8e285b015b765379c2e17880455f70370f8e9')throw new Error('Stage the official Node 24.22.2 licence');
 // nodejs.org/dist/v24.22.2/SHASUMS256.txt: win-x64/node.exe.
 if(sha256(node)!=='1c331340fa6cac5e4294725959070a143fa0507195a78ad77eed7943f719aac9')throw new Error('Stage the verified Node 24.22.2 Windows runtime');
 const nodeProbe=spawnSync(node,['--version'],{encoding:'utf8',timeout:15000,windowsHide:true});
 if(nodeProbe.status!==0||nodeProbe.stdout.trim()!=='v24.22.2')throw new Error('Bundled Node runtime version mismatch');
 for(const choice of Object.keys(LOCAL_BACKENDS)) {
  const binary=findLocalBackend(choice,{installRoot:resources});
  const manifest=await verifyLocalBackend(binary,choice);
  if(manifest.version!==engine)throw new Error(`Stale ${choice} runtime version`);
  if(choice==='TurboQuant' && (JSON.stringify(manifest.cacheTypesK)!==JSON.stringify(['f16','bf16','q8_0','q4_0']) || JSON.stringify(manifest.cacheTypesV)!==JSON.stringify(['f16','bf16','q8_0','q4_0','turbo2','turbo3','turbo4'])))throw new Error('Stage the TurboQuant runtime with independently qualified K/V capabilities');
  const probe=spawnSync(binary.path,['--version'],{encoding:'utf8',timeout:30000,windowsHide:true,env:{...process.env,PATH:join(process.env.SystemRoot??'C:/Windows','System32')}});
  if(probe.error||probe.status!==0||!((probe.stdout+probe.stderr).match(/\b[0-9a-f]{7,40}\b/gi)??[]).some(value=>manifest.source.commit.startsWith(value.toLowerCase())))throw new Error(`Bundled ${choice} executable does not match its source revision`);
 }
 const manifests=files(join(resources,'engine-bundle')).filter(path=>path.endsWith('engine-component.json'));
 if(manifests.length!==1) throw new Error('Stage exactly one current Windows engine package');
 const path=manifests[0],folder=resolve(path,'..');
 const manifest=verifyEngine(folder,engine);
 verifyNativeBuild(folder,root,manifest);
 const run=spawnSync(join(folder,manifest.entrypoint),['--version'],{encoding:'utf8',timeout:15000,windowsHide:true});
 if(run.error || run.status!==0 || !run.stdout.includes(engine)) throw new Error('Bundled executable version does not match engine manifest');
}
console.log(`Release payload verified: Hakua ${product}, engine ${engine}`);
