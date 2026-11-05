/** Build the separate GPU component from verified, already-qualified runtime bytes. */
import {readFileSync,writeFileSync,existsSync,mkdirSync,copyFileSync,statSync} from 'node:fs';
import {resolve,join,dirname,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {files,sha256,verifyEngine,verifyNativeBuild} from '../../host/scripts/release-integrity.mjs';
import {LOCAL_BACKENDS,findLocalBackend,verifyLocalBackend} from '../../host/server/local-backends.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const resources=join(root,'apps/desktop/src-tauri/resources');
const output=process.argv[2]&&resolve(process.argv[2]);
if(!output||existsSync(output))throw new Error('Pass a fresh output directory outside the source checkout');
const inside=relative(root,output);
if(!isAbsolute(inside)&&inside!=='..'&&!inside.startsWith('..'+(process.platform==='win32'?'\\':'/')))throw new Error('Release component output must stay outside the checkout');
const version=/project\(strata VERSION ([\d.]+)/.exec(readFileSync(join(root,'CMakeLists.txt'),'utf8'))?.[1];
const manifests=files(join(resources,'engine-bundle')).filter(path=>path.endsWith('engine-component.json'));
if(manifests.length!==1)throw new Error('Stage exactly one qualified native engine');
const native=dirname(manifests[0]),base=verifyEngine(native,version);verifyNativeBuild(native,root,base);
if(base.platform!=='windows-x86_64'||base.backend!=='cuda'||!base.archs?.includes('sm_120'))throw new Error('This release recipe is Windows CUDA sm_120 only');
const runtimes=[];
for(const choice of Object.keys(LOCAL_BACKENDS)){
 const binary=findLocalBackend(choice,{installRoot:resources});
 const manifest=await verifyLocalBackend(binary,choice);
 if(manifest.version!==LOCAL_BACKENDS[choice].packageVersion)throw new Error('Stale local runtime: '+choice);
 runtimes.push({choice,root:dirname(binary.manifestPath),id:manifest.backend,manifest});
}
const notices=join(resources,'notices'),noticeRecord=JSON.parse(readFileSync(join(notices,'NOTICES.json'),'utf8'));
const noticeFiles=files(notices);
if(JSON.stringify(noticeFiles.map(path=>relative(notices,path).replaceAll('\\','/')).filter(name=>name!=='NOTICES.json').sort())!==JSON.stringify(Object.keys(noticeRecord.files).sort()))throw new Error('Notice membership changed');
for(const [name,hash] of Object.entries(noticeRecord.files))if(sha256(join(notices,name))!==hash)throw new Error('Notice changed: '+name);
mkdirSync(output,{recursive:true});
const folder=join(output,version+'-windows-x86_64-cuda-cuda13');mkdirSync(folder);
function copy(source,target){mkdirSync(dirname(target),{recursive:true});copyFileSync(source,target);if(sha256(source)!==sha256(target))throw new Error('Component copy changed: '+target);}
for(const entry of base.files)copy(join(native,entry.path),join(folder,entry.path));
for(const runtime of runtimes)for(const path of files(runtime.root))copy(path,join(folder,'local-backends',runtime.id,relative(runtime.root,path)));
for(const path of noticeFiles)copy(path,join(folder,'notices',relative(notices,path)));
const manifest={...base,variant:'cuda13',build_id:base.build_id+'-hakua-runtimes-v1',signature:null,
 files:files(folder).map(path=>({path:relative(folder,path).replaceAll('\\','/'),bytes:statSync(path).size,sha256:sha256(path)}))};
writeFileSync(join(folder,'engine-component.json'),JSON.stringify(manifest,null,2)+'\n');
verifyEngine(folder,version);verifyNativeBuild(folder,root,manifest);
for(const choice of Object.keys(LOCAL_BACKENDS))await verifyLocalBackend(findLocalBackend(choice,{installRoot:folder}),choice);
const report={ok:true,folder,version,variant:manifest.variant,files:manifest.files.length,installedBytes:manifest.files.reduce((sum,file)=>sum+file.bytes,0),nativeSHA256:sha256(join(folder,manifest.entrypoint)),backends:runtimes.map(runtime=>({name:runtime.choice,source:runtime.manifest.source,entrypointSHA256:sha256(join(folder,'local-backends',runtime.id,'llama-server.exe'))})),notices:Object.keys(noticeRecord.files).length};
writeFileSync(join(output,'STAGED.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
