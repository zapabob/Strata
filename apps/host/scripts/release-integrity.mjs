import {createHash} from 'node:crypto';
import {existsSync, readFileSync, readdirSync, statSync} from 'node:fs';
import {join, relative, resolve, isAbsolute} from 'node:path';

export const sha256 = path => createHash('sha256').update(readFileSync(path)).digest('hex');
export function files(root) {
  if (!existsSync(root)) throw new Error(`Missing build input: ${root}`);
  return readdirSync(root, {withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name)).flatMap(entry => {
    if (entry.name === '__pycache__' || entry.name.endsWith('.pyc')) return [];
    const path=join(root,entry.name);
    if (entry.isSymbolicLink()) throw new Error(`Linked build input: ${path}`);
    return entry.isDirectory() ? files(path) : [path];
  });
}
export function hostSources(root) {
  const paths=['src','public','server'].flatMap(name=>files(join(root,name)));
  for (const name of ['package.json','package-lock.json','vite.config.ts','vite.config.mjs','index.html','scripts/build.mjs','scripts/release-integrity.mjs']) {
    if (existsSync(join(root,name))) paths.push(join(root,name));
  }
  return Object.fromEntries(paths.map(path=>[relative(root,path).replaceAll('\\','/'),sha256(path)]).sort(([a],[b])=>a.localeCompare(b)));
}
export function nativeSources(root) {
  const paths=['src','include','cmake','spin8/src','spin8/include','spin8/third_party','tqcodec/src','tqcodec/include'].filter(name=>existsSync(join(root,name))).flatMap(name=>files(join(root,name)));
  for(const name of ['CMakeLists.txt','spin8/CMakeLists.txt','tqcodec/CMakeLists.txt']) if(existsSync(join(root,name)))paths.push(join(root,name));
  return Object.fromEntries(paths.map(path=>[relative(root,path).replaceAll('\\','/'),sha256(path)]).sort(([a],[b])=>a.localeCompare(b)));
}
export function verifyTree(source, staged, {pythonOnly=false}={}) {
  const select=root=>files(root).filter(path=>!pythonOnly || path.endsWith('.py'));
  const expected=select(source).map(path=>relative(source,path).replaceAll('\\','/')).sort();
  const actual=select(staged).map(path=>relative(staged,path).replaceAll('\\','/')).sort();
  if (JSON.stringify(expected)!==JSON.stringify(actual)) throw new Error(`Stale staged membership: ${staged}`);
  for (const name of expected) if (sha256(join(source,name))!==sha256(join(staged,name))) throw new Error(`Stale staged source: ${staged}/${name}`);
}
/** Check the package against its manifest before probing the actual executable. */
export function verifyEngine(folder, version) {
  const manifest=JSON.parse(readFileSync(join(folder,'engine-component.json'),'utf8'));
  if(manifest.id!=='strata-engine' || manifest.version!==version || !Array.isArray(manifest.files) || !manifest.files.length) throw new Error('Stale or invalid bundled engine');
  if(!manifest.files.some(entry=>entry.path===manifest.entrypoint)) throw new Error('Engine entrypoint is not in the manifest');
  for(const entry of manifest.files) {
    if(typeof entry.path!=='string' || isAbsolute(entry.path) || entry.path.split(/[\\\\/]/).some(part=>!part || part==='..' || part==='.')) throw new Error('Unsafe engine manifest path');
    const target=resolve(folder,entry.path);
    const rel=relative(resolve(folder),target);
    if(isAbsolute(rel) || rel.startsWith('..')) throw new Error('Unsafe engine manifest path');
    if(statSync(target).size!==entry.bytes || sha256(target)!==entry.sha256) throw new Error('Changed engine payload: '+entry.path);
  }
  const actual=files(folder).map(path=>relative(folder,path).replaceAll('\\','/')).filter(name=>name!=='engine-component.json').sort();
  const expected=manifest.files.map(entry=>entry.path).sort();
  if(JSON.stringify(actual)!==JSON.stringify(expected))throw new Error('Unexpected engine package membership');
  return manifest;
}
export function verifyNativeBuild(folder,root,manifest) {
  const record=JSON.parse(readFileSync(join(folder,'native-build.json'),'utf8'));
  if(record.version!==manifest.version || record.entrypoint!==manifest.entrypoint || record.sha256!==sha256(join(folder,manifest.entrypoint)))throw new Error('Stale native build identity');
  if(JSON.stringify(record.sources)!==JSON.stringify(nativeSources(root)))throw new Error('Native engine sources changed: rebuild the engine');
  const baseline=record.recipe?.cudaSpillBaseline;
  if(baseline!==undefined) {
    if(!baseline||typeof baseline.path!=='string'||isAbsolute(baseline.path)||baseline.path.split(/[\\/]/).some(part=>!part||part==='.'||part==='..')||!/^[a-f0-9]{64}$/.test(baseline.sha256??''))throw new Error('Unsafe CUDA resource baseline identity');
    const path=resolve(root,baseline.path),name=relative(resolve(root),path);
    if(isAbsolute(name)||name.startsWith('..')||sha256(path)!==baseline.sha256)throw new Error('CUDA resource baseline changed: rebuild and qualify the engine');
  }
}
export const PUBLIC_ASSET_COMMIT='03f11e2d6adc319ea21e9a1d5820a99cd3767257';
export function verifyPublicAssets(root,record) {
 if(record?.lucide_commit!==PUBLIC_ASSET_COMMIT||!record.files||!Object.keys(record.files).length)throw new Error('Prepare the pinned public assets first');
 const actual=files(root).map(path=>relative(root,path).replaceAll('\\','/')).sort();
 const expected=Object.keys(record.files).sort();
 if(JSON.stringify(actual)!==JSON.stringify(expected))throw new Error('Public asset membership changed');
 for(const name of expected) {
  if(/gtwalsheim/i.test(name)||name.split('/').some(part=>!part||part==='.'||part==='..')||isAbsolute(name))throw new Error('Unapproved public asset');
  if(sha256(join(root,name))!==record.files[name])throw new Error('Public asset payload changed: '+name);
 }
}
export function verifyHost(host) {
  const dist=join(host,'dist');
  const record=JSON.parse(readFileSync(join(dist,'release-build.json'),'utf8'));
  if (JSON.stringify(record.sources)!==JSON.stringify(hostSources(host))) throw new Error('Stale GUI/Host: rebuild apps/host');
  const actual=files(dist).filter(path=>relative(dist,path)!=='release-build.json');
  const assets=Object.fromEntries(actual.map(path=>[relative(dist,path).replaceAll('\\','/'),sha256(path)]).sort(([a],[b])=>a.localeCompare(b)));
  if (JSON.stringify(record.assets)!==JSON.stringify(assets)) throw new Error('Changed GUI build assets');
}
