/** Explicit, self-contained llama-server runtimes. Each fork keeps its own libraries. */
import {createHash} from 'node:crypto';
import {readFileSync,existsSync,realpathSync,createReadStream,readdirSync} from 'node:fs';
import {dirname,join,resolve,relative,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';

export const LOCAL_BACKENDS=Object.freeze({
 PrismML:{id:'prism',repository:'https://github.com/PrismML-Eng/llama.cpp.git',commit:'73bfe6cc485554822f80c473a3c0c4f25e80f41b'},
 TurboQuant:{id:'turboquant',repository:'https://github.com/TheTom/llama-cpp-turboquant.git',commit:'643956891dfdf51aecdbd05ca508dd21e21e8195'},
});
export function localBackendChoice(expert=[]) {
 const selected=expert.find(item=>item.id==='runtime.backend')?.value??'Automatic';
 if(selected!=='Automatic'&&!LOCAL_BACKENDS[selected])throw new Error('Unknown local llama-server backend: '+selected);
 return selected;
}
export function findLocalBackend(choice,{componentsDir,installRoot=resolve(dirname(fileURLToPath(import.meta.url)),'../..'),platform=process.platform}={}) {
 const definition=LOCAL_BACKENDS[choice];
 if(!definition)throw new Error('Choose PrismML or TurboQuant explicitly.');
 const roots=[join(installRoot,'local-backends',definition.id),componentsDir&&join(componentsDir,'local-backends',definition.id)].filter(Boolean);
 const candidates=[];
 for(const root of roots) {
  const binary=join(root,platform==='win32'?'llama-server.exe':'llama-server');
  if(existsSync(binary)&&existsSync(join(root,'runtime.json'))) {
   try {const version=JSON.parse(readFileSync(join(root,'runtime.json'),'utf8')).version;
    if(/^\d+\.\d+\.\d+$/.test(version))candidates.push({path:binary,source:choice,manifestPath:join(root,'runtime.json'),backend:definition.id,version});
   } catch { /* an incomplete package is not usable */ }
  }
 }
 candidates.sort((a,b)=>{const left=a.version.split('.').map(Number),right=b.version.split('.').map(Number);for(let i=0;i<3;i++)if(left[i]!==right[i])return right[i]-left[i];return 0;});
 return candidates[0]??null;
}
async function hash(path) {const digest=createHash('sha256');for await(const chunk of createReadStream(path))digest.update(chunk);return digest.digest('hex');}
export async function verifyLocalBackend(binary,choice) {
 const expected=LOCAL_BACKENDS[choice];
 if(!expected||!binary?.manifestPath)throw new Error('A verified local '+choice+' runtime is required.');
 const root=dirname(resolve(binary.manifestPath));
 const manifest=JSON.parse(readFileSync(binary.manifestPath,'utf8'));
 if(manifest.schema!==1||manifest.backend!==expected.id||manifest.source?.repository!==expected.repository||manifest.source?.commit!==expected.commit)throw new Error('The selected local runtime has an unknown source identity.');
 const patches=manifest.source.patches??[];
 const approvedHash=expected.id==='prism'?'a291a22cd8915edee441e39b08b1c948e5ecc18b41060529c120701bfcf26ddd':'41301159b543700425038d569926ed68b131d5f0692d89ab8e1efd1488399144';
 const approvedPatch=manifest.source.dirty===true&&patches.length===1&&patches[0].id===expected.id+'-standard-sm120-v1'&&patches[0].sha256===approvedHash;
 if(!(manifest.source.dirty===false&&patches.length===0)&&!approvedPatch)throw new Error('The local runtime has unreviewed source changes.');
 if(!Array.isArray(manifest.files)||!manifest.files.length||!Array.isArray(manifest.cacheTypes))throw new Error('The local runtime manifest is incomplete.');
 let entry=false;const seen=new Set();
 for(const file of manifest.files) {
  if(typeof file?.path!=='string'||isAbsolute(file.path)||file.path.split(/[\\/]/).some(part=>!part||part==='.'||part==='..'))throw new Error('Unsafe local runtime payload path');
  const target=resolve(root,file.path),rel=relative(root,realpathSync(target));
  if(isAbsolute(rel)||rel==='..'||rel.startsWith('..'+(process.platform==='win32'?'\\':'/'))||seen.has(file.path.toLowerCase()))throw new Error('Invalid local runtime payload membership');
  seen.add(file.path.toLowerCase());
  if(await hash(target)!==file.sha256)throw new Error('Local runtime payload changed: '+file.path);
  if(target===resolve(binary.path))entry=true;
 }
 if(!entry)throw new Error('The selected llama-server is not in its runtime manifest.');
 if(approvedPatch&&!manifest.files.some(file=>file.path==='source-patch.diff'&&file.sha256===patches[0].sha256))throw new Error('The approved runtime source patch is missing or changed.');
 const inventory=(folder,prefix='')=>readdirSync(folder,{withFileTypes:true}).flatMap(item=>{
  if(item.isSymbolicLink())throw new Error('Linked local runtime payload');
  const name=prefix+item.name;return item.isDirectory()?inventory(join(folder,item.name),name+'/'):[name];
 });
 const actual=inventory(root).filter(name=>name!=='runtime.json').sort();
 if(JSON.stringify(actual)!==JSON.stringify(manifest.files.map(item=>item.path).sort()))throw new Error('Unexpected local runtime package membership');
 return manifest;
}
export function requireRuntimeKv(manifest,{k,v}) {
 for(const [side,type] of [['K',k],['V',v]])if(!(manifest['cacheTypes'+side]??manifest.cacheTypes).includes(type))throw new Error('This '+manifest.backend+' runtime cannot use '+type+' '+side+' cache. Choose a supported precision or another backend.');
}
