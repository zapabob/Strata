/** Read-only reproduction against the already retained pre-feature baseline. */
import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
const cwd='H:/Strata/worktrees/search-056-baseline-20261111/apps/host';
const harness=resolve(import.meta.dirname,'../../apps/desktop/src-tauri/resources/harness');
const child=spawn(process.execPath,['--test','--test-name-pattern=dense text compacts|a message that fits only after a summary|/compact summarises','tests/agent-context.test.mjs'],{cwd,stdio:'inherit',windowsHide:true,env:{...process.env,STRATA_HARNESS_DIR:harness,STRATA_NO_ACQUIRE:'1'}});
child.once('error',error=>{console.error(error);process.exitCode=1;});child.once('exit',code=>{process.exitCode=code??1;});
