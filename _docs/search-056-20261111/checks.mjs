import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
const cwd=resolve(import.meta.dirname,'../../apps/host');
for(const args of [
  ['node_modules/typescript/bin/tsc','--noEmit'],
  ['--test','tests/btw-deepresearch.test.mjs','tests/web-search-rustxng.test.mjs','tests/chat-web-search.test.mjs','tests/chat-stream-terminal.test.mjs','tests/agent-tools-settings.test.mjs','tests/agent-search-policy.test.mjs','tests/tools-locales.test.mjs','tests/ux-web-search.test.mjs'],
]) {
  const result=spawnSync(process.execPath,args,{cwd,stdio:'inherit',windowsHide:true});
  if(result.error)throw result.error;
  if(result.status!==0)process.exit(result.status??1);
}
