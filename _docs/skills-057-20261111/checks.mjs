import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
const cwd=resolve(import.meta.dirname,'../../apps/host');
for(const args of [
  ['node_modules/typescript/bin/tsc','--noEmit'],
  ['--test','--test-concurrency=2','tests/skill-learning.test.mjs','tests/skill-import.test.mjs','tests/skill-import-routes.test.mjs','tests/split-qa2-skills.test.mjs','tests/skills-used.test.mjs','tests/tools-locales.test.mjs','tests/btw-deepresearch.test.mjs','tests/chat-stream-terminal.test.mjs','tests/agent-events.test.mjs','tests/agent-tools-settings.test.mjs','tests/ux-skill-import.test.mjs','tests/skill-context.test.mjs'],
]){
  const result=spawnSync(process.execPath,args,{cwd,stdio:'inherit',windowsHide:true});
  if(result.error)throw result.error;
  if(result.status!==0)process.exit(result.status??1);
}
