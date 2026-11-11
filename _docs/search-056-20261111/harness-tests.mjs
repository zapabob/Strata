import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
const root=resolve(import.meta.dirname,'../../apps/host');
const child=spawn(process.execPath,['--test','--test-name-pattern=research','tests/agent-plan-run.test.mjs'],{cwd:root,stdio:'inherit',windowsHide:true,env:{...process.env,STRATA_HARNESS_DIR:resolve(root,'../desktop/src-tauri/resources/harness'),STRATA_NO_ACQUIRE:'1'}});
child.once('error',error=>{console.error(error);process.exitCode=1;});
child.once('exit',code=>{process.exitCode=code??1;});
