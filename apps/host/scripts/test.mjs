#!/usr/bin/env node
/** Enumerate test files explicitly so npm test works without shell glob expansion. */
import {readdirSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'..');
const files=readdirSync(resolve(root,'tests')).filter(name=>name.endsWith('.test.mjs')).sort().map(name=>resolve(root,'tests',name));
/* Every test file runs against scratch copies of the per-user places the host writes to (the owner's real profile is never touched). */
import {mkdtempSync,mkdirSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const scratch=mkdtempSync(join(tmpdir(),'strata-host-suite-profile-'));
const testTemp=join(scratch,'tmp');mkdirSync(testTemp);
const guard=pathToFileURL(join(root,'scripts/test-fs-guard.mjs')).href;
const env={...process.env,STRATA_TEST_SCRATCH:scratch,TEMP:testTemp,TMP:testTemp,TMPDIR:testTemp,HOME:join(scratch,'home'),USERPROFILE:join(scratch,'home'),STRATA_HOME:join(scratch,'home'),STRATA_SETTINGS_FILE:join(scratch,'app-settings.json'),STRATA_COMPONENTS_DIR:join(scratch,'components'),LOCALAPPDATA:join(scratch,'Local'),APPDATA:join(scratch,'Roaming'),XDG_DATA_HOME:join(scratch,'xdg-data'),XDG_STATE_HOME:join(scratch,'xdg-state'),XDG_CONFIG_HOME:join(scratch,'xdg-config')};
// Each fixture selects its own Control and settings through its scratch HOME.
// A caller's packaged Control/settings override would silently switch test routes
// and share state between otherwise independent fixture homes.
delete env.STRATA_CONTROL_DIR;
delete env.STRATA_SETTINGS_FILE;
const requested=process.env.STRATA_TEST_CONCURRENCY;
const concurrency=requested===undefined?null:Number(requested);
if(concurrency!==null&&(!Number.isSafeInteger(concurrency)||concurrency<1||concurrency>16))throw new Error('STRATA_TEST_CONCURRENCY must be an integer from 1 to 16');
const requestedTimeout=process.env.STRATA_TEST_TIMEOUT_MS;
const timeout=requestedTimeout===undefined?null:Number(requestedTimeout);
if(timeout!==null&&(!Number.isSafeInteger(timeout)||timeout<1000||timeout>3600000))throw new Error('STRATA_TEST_TIMEOUT_MS must be an integer from 1000 to 3600000');
const child=spawn(process.execPath,['--import',guard,'--test',...(concurrency===null?[]:[`--test-concurrency=${concurrency}`]),...(timeout===null?[]:[`--test-timeout=${timeout}`]),...files],{cwd:root,stdio:'inherit',env});
child.on('error',error=>{console.error(error.message);process.exitCode=1;});
child.on('exit',(code,signal)=>{process.exitCode=code??(signal?1:0);});
