import {spawnSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'../..');
const exe='H:/Strata/releases/personal-052-local2-20261107/native-build/Release/strata.exe';
const version=/project\(strata VERSION ([\d.]+)/.exec(readFileSync(resolve(root,'CMakeLists.txt'),'utf8'))?.[1];
const start=Date.now();
const probe=spawnSync(exe,['--version'],{encoding:'utf8',windowsHide:true,timeout:15000});
const matched=new RegExp('(^|\\s)'+version.replaceAll('.','\\.')+'(\\s|$)').test(probe.stdout??'');
console.log(JSON.stringify({version,status:probe.status,error:probe.error?.message,signal:probe.signal,
  stdout:probe.stdout,stderr:probe.stderr,matched,ms:Date.now()-start}));
if(probe.status!==0||!matched)process.exitCode=1;
