import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createServer } from 'node:net';

test('a backend that exits before health reports its error promptly', async t => {
  const home=mkdtempSync(join(tmpdir(),'strata-early-exit-'));
  const previous={ home:process.env.STRATA_HOME, binary:process.env.STRATA_LLAMA_SERVER };
  process.env.STRATA_HOME=home;
  process.env.STRATA_LLAMA_SERVER=process.execPath; // Node exits on llama-server's -m option.
  const supervisor=await import('../server/supervisor.mjs');
  const model=join(home,'dummy.gguf');writeFileSync(model,'fixture');
  const listener=createServer();await new Promise(resolve=>listener.listen(0,'127.0.0.1',resolve));
  const port=listener.address().port;await new Promise(resolve=>listener.close(resolve));
  t.after(async()=>{
    await supervisor.stop();
    if(previous.home===undefined)delete process.env.STRATA_HOME;else process.env.STRATA_HOME=previous.home;
    if(previous.binary===undefined)delete process.env.STRATA_LLAMA_SERVER;else process.env.STRATA_LLAMA_SERVER=previous.binary;
    rmSync(home,{recursive:true,force:true});
  });
  const started=Date.now();
  await assert.rejects(supervisor.start({modelId:'fixture',modelPath:model,port,config:{beginner:{contextLength:'2k'},expert:[]},hardware:{cpu:{cores:4}},timeoutMs:10_000}),/Engine exited early with code \d+.*bad option: -m/);
  assert.ok(Date.now()-started<5_000,'did not wait for the health timeout');
});
