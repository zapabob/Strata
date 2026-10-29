/** Targeted mutation checks. Only temporary copies of modules are changed. */
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const repo=resolve(import.meta.dirname,'..');
const scratch=mkdtempSync(join(tmpdir(),'hakua-mutations-'));
let serial=0;
const results=[];
async function moduleOf(source) {
  const path=join(scratch,'module-'+serial+++'.mjs');
  writeFileSync(path,source);
  return import(pathToFileURL(path).href);
}
function fixture(name,version) {
 const dir=join(scratch,name);
 mkdirSync(join(dir,'python'),{recursive:true});mkdirSync(join(dir,'strata_control'));
 writeFileSync(join(dir,'python','python.exe'),'fixture');writeFileSync(join(dir,'strata.py'),'fixture');
 writeFileSync(join(dir,'BUNDLE.json'),JSON.stringify({version}));
 return dir;
}
const old=fixture('old','0.1.47'),fresh=fixture('fresh','0.3.3'),same=fixture('same','0.3.3');
const host=join(scratch,'product','host','server');
mkdirSync(host,{recursive:true});mkdirSync(join(scratch,'product','control'));
writeFileSync(join(scratch,'product','control','VERSION'),'0.1.47');
const sourceDir=join(scratch,'source'),staged=join(scratch,'staged');
mkdirSync(sourceDir);mkdirSync(staged);
writeFileSync(join(sourceDir,'run.py'),'new');writeFileSync(join(staged,'run.py'),'old');
const app=readFileSync(join(repo,'apps/host/server/app-version.mjs'),'utf8').replaceAll('\r\n','\n');
const control=readFileSync(join(repo,'apps/host/server/control-runtime.mjs'),'utf8').replaceAll('\r\n','\n');
const integrity=readFileSync(join(repo,'apps/host/scripts/release-integrity.mjs'),'utf8').replaceAll('\r\n','\n');
const appContract=m=>{
 assert.equal(m.appVersionFrom({env:{STRATA_APP_VERSION:'0.3.3-preview.20261030.1'},here:host}),'0.3.3-preview.20261030.1');
 assert.equal(m.appVersionFrom({env:{STRATA_APP_VERSION:'invalid'},here:host}),'dev');
 assert.equal(m.appVersionToShow(undefined,null),null);
};
const controlContract=m=>{
 const select=(a,b)=>m.findControl({env:{STRATA_CONTROL_DIR:a},platform:'win32',hostDir:join(scratch,'none'),components:join(scratch,'none'),exists:path=>path.startsWith(a)||path.startsWith(b)});
 // An updated candidate is introduced through the normal active.json pointer.
 const components=join(scratch,'components');
 mkdirSync(join(components,'control'),{recursive:true});
 writeFileSync(join(components,'control','active.json'),JSON.stringify({folder:'fresh',version:'0.3.3'}));
 const choose=(a,b)=>m.findControl({env:{STRATA_CONTROL_DIR:a},platform:'win32',hostDir:join(scratch,'none'),components,exists:path=>path.startsWith(a)||path.startsWith(b)});
 const installed=join(components,'control','fresh');
 mkdirSync(join(installed,'python'),{recursive:true});mkdirSync(join(installed,'strata_control'),{recursive:true});
 writeFileSync(join(installed,'BUNDLE.json'),JSON.stringify({version:'0.3.3'}));
 assert.equal(choose(old,installed).dir,installed);
 assert.equal(choose(fresh,installed).dir,fresh,'equal version keeps first candidate');
 // Incomplete newer packages cannot displace a complete candidate.
 assert.equal(select(fresh,same).dir,fresh);
};
const integrityContract=m=>{
 assert.throws(()=>m.verifyTree(sourceDir,staged,{pythonOnly:true}),/Stale staged source/);
 writeFileSync(join(staged,'run.py'),'new');
 assert.doesNotThrow(()=>m.verifyTree(sourceDir,staged,{pythonOnly:true}));
 writeFileSync(join(staged,'leftover.py'),'obsolete');
 try {assert.throws(()=>m.verifyTree(sourceDir,staged,{pythonOnly:true}),/membership/);}
 finally {rmSync(join(staged,'leftover.py'));writeFileSync(join(staged,'run.py'),'old');}
};
const engineDir=join(scratch,'engine');mkdirSync(engineDir);
const engineFile=join(engineDir,'strata.exe');writeFileSync(engineFile,'same-length');
const engineHash=createHash('sha256').update('same-length').digest('hex');
writeFileSync(join(engineDir,'engine-component.json'),JSON.stringify({id:'strata-engine',version:'0.3.3',entrypoint:'strata.exe',files:[{path:'strata.exe',bytes:11,sha256:engineHash}]}));
const engineContract=m=>{
 assert.doesNotThrow(()=>m.verifyEngine(engineDir,'0.3.3'));
 writeFileSync(engineFile,'wrong-bytes');
 try {assert.throws(()=>m.verifyEngine(engineDir,'0.3.3'),/Changed engine payload/);}
 finally {writeFileSync(engineFile,'same-length');}
};
async function verify(name,source,contract,from,to) {
 contract(await moduleOf(source));
 assert.equal(source.split(from).length-1,1,'mutation anchor must be unique: '+name);
 const mutated=source.replace(from,to);
 const module=await moduleOf(mutated); // Import failures do not count as detected behaviour.
 let killed=false;
 try {contract(module);} catch(error) {
  if(!(error instanceof assert.AssertionError)) throw error;
  killed=true;
 }
 assert.ok(killed,'surviving mutation: '+name);
 results.push({name,baseline:'passed',mutation:'detected'});
}
try {
 await verify('fixed 0.3.0 fallback',app,appContract,"return 'dev';","return '0.3.0';");
 await verify('ignore running shell version',app,appContract,'if (VERSION.test(given)) return given;','if (false) return given;');
 await verify('prefer stale Control over GUI',app,appContract,"  const given=String(env.STRATA_APP_VERSION??'').trim();","  try {return readFileSync(join(here,'..','..','control','VERSION'),'utf8').trim();} catch {}\n  const given=String(env.STRATA_APP_VERSION??'').trim();");
 await verify('reverse Control version comparison',control,controlContract,'return (a[i] ?? 0) > (b[i] ?? 0);','return (a[i] ?? 0) < (b[i] ?? 0);');
 await verify('replace equal-version first preference',control,controlContract,'  return false;\n}','  return true;\n}');
 await verify('remove staged-source hash comparison',integrity,integrityContract,'if (sha256(join(source,name))!==sha256(join(staged,name)))','if (false)');
 await verify('remove exact staged membership check',integrity,integrityContract,'if (JSON.stringify(expected)!==JSON.stringify(actual))','if (false)');
 await verify('remove bundled-engine hash validation',integrity,engineContract,'sha256(target)!==entry.sha256','false');
 const report={scope:'targeted product identity, numeric Control selection and staged-source integrity',total:results.length,detected:results.length,results};
 if(process.argv[2])writeFileSync(resolve(process.argv[2]),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report,null,2));
} finally {
 rmSync(scratch,{recursive:true,force:true});
}
