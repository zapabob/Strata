/** Execute the real NSIS cleanup macros against disposable, bounded fixture trees. */
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {existsSync,readFileSync,writeFileSync,mkdtempSync,mkdirSync,symlinkSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,relative,isAbsolute} from 'node:path';

if(process.platform!=='win32')throw new Error('This integration check requires Windows and NSIS');
const root=resolve(import.meta.dirname,'..');
const compiler=process.env.MAKENSIS??join(process.env.LOCALAPPDATA,'tauri','NSIS','makensis.exe');
const baseline=process.argv.includes('--baseline');
const file='apps/desktop/src-tauri/nsis/installer.nsi';
const source=baseline?spawnSync('git',['show','HEAD:'+file],{cwd:root,encoding:'utf8',windowsHide:true}).stdout:readFileSync(join(root,file),'utf8');
const macros=source.match(/; STRATA-CLEAN-BEGIN([\s\S]*?); STRATA-CLEAN-END/)?.[1];
assert.ok(macros,'installer cleanup macros must exist');
const scratch=mkdtempSync(join(tmpdir(),'strata-nsis-regression-'));
const safe=path=>{const rel=relative(scratch,resolve(path));assert.ok(rel&&!isAbsolute(rel)&&rel!=='..'&&!rel.startsWith('..\\'));return path;};
const managed=['control','host','node','harness','engine-bundle','local-backends','notices'];
const outcomes=[];
for(const name of ['missing','empty','existing','junction']){
 const target=safe(join(scratch,name));mkdirSync(target);
 writeFileSync(join(target,'keep.txt'),'unrelated user file');
 if(name==='empty')for(const folder of managed)mkdirSync(join(target,folder));
 if(name==='existing'||name==='junction'){
  mkdirSync(join(target,'control','cache'),{recursive:true});
  writeFileSync(join(target,'control','cache','old.txt'),'managed file');
 }
 let sentinel;
 if(name==='junction'){
  const outside=safe(join(scratch,'outside'));mkdirSync(outside);
  sentinel=join(outside,'keep.txt');writeFileSync(sentinel,'junction target must survive');
  symlinkSync(outside,join(target,'host'),'junction');
 }
 const exe=safe(join(scratch,name+'.exe')),script=safe(join(scratch,name+'.nsi'));
 const quoted=value=>value.replaceAll('$','$$').replaceAll('"','$\\"');
 writeFileSync(script,`Unicode true\nRequestExecutionLevel user\nSilentInstall silent\n!include "LogicLib.nsh"\n!include "FileFunc.nsh"\nName "Strata cleanup regression"\nOutFile "${quoted(exe)}"\n${macros}\nSection\n!insertmacro StrataRemoveAppFolders "${quoted(target)}" ""\nSetErrorLevel 0\nSectionEnd\n`);
 const build=spawnSync(compiler,['/V2',script],{encoding:'utf8',windowsHide:true,timeout:30000});
 assert.equal(build.status,0,build.stdout+build.stderr);
 const run=spawnSync(exe,['/S'],{windowsHide:true,timeout:30000});
 const expected=name==='junction'?2:0;
 const protectedFiles=readFileSync(join(target,'keep.txt'),'utf8')==='unrelated user file'
  &&(!sentinel||existsSync(sentinel))
  &&(name!=='junction'||existsSync(join(target,'control','cache','old.txt')));
 const removed=name==='junction'||managed.every(folder=>!existsSync(join(target,folder)));
 outcomes.push({name,exit:run.status,expected,protectedFiles,removed,passed:run.status===expected&&protectedFiles&&removed});
}
console.log(JSON.stringify({baseline,scratch,outcomes},null,2));
assert.ok(outcomes.every(row=>row.passed),'NSIS fixture failed');
