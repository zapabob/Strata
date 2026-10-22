import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveKvSettings, explicitKvEnvironment } from '../server/kv-settings.mjs';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { buildArgs, restart, status } from '../server/supervisor.mjs';
const entry = (id, value) => ({ id, value });

test('manual K/V survives conflicting fork environment without modifying its parent', () => {
  const base = { ...process.env, LLAMA_ARG_CACHE_TYPE_K:'turbo3', llama_arg_cache_type_v:'turbo2',
    TURBO_AUTO_ASYMMETRIC:'1', turbo_layer_adaptive:'7', STRATA_KV_FIXTURE:'retained' };
  const env = explicitKvEnvironment(base);
  assert.equal(base.LLAMA_ARG_CACHE_TYPE_K, 'turbo3');
  assert.equal(base.TURBO_AUTO_ASYMMETRIC, '1');
  const child = spawnSync(process.execPath, ['-e', `
    for (const k of Object.keys(process.env)) {
      if (/^LLAMA_ARG_CACHE_TYPE_[KV]$/i.test(k)) process.exit(3);
    }
    if (process.env.TURBO_AUTO_ASYMMETRIC!=='0' || process.env.TURBO_LAYER_ADAPTIVE!=='0') process.exit(4);
    process.stdout.write(process.env.STRATA_KV_FIXTURE);
  `], { env, encoding:'utf8', windowsHide:true });
  assert.equal(child.status, 0, child.stderr);
  assert.equal(child.stdout, 'retained');
  for (const file of ['supervisor.mjs','spin8-backend.mjs']) {
    assert.match(readFileSync(new URL(`../server/${file}`,import.meta.url),'utf8'), /env:\s*(?:\{\s*\.\.\.)?explicitKvEnvironment\(\)/);
  }
});
test('legacy cache choice and inherited values keep existing defaults', () => {
  assert.deepEqual(resolveKvSettings(), { k: 'q8_0', v: 'q8_0' });
  assert.deepEqual(resolveKvSettings([entry('ctx.kvMode','FP16'),entry('ctx.kType','Inherit')]), {k:'f16',v:'f16'});
});
test('K and V can be selected independently in the real launch arguments', () => {
  const args = buildArgs({modelPath:'fixture.gguf',config:{expert:[entry('ctx.kType','FP16'),entry('ctx.vType','Q4_0')]}});
  assert.equal(args[args.indexOf('-ctk')+1],'f16');
  assert.equal(args[args.indexOf('-ctv')+1],'q4_0');
});
test('invalid precision and incompatible flash settings reject before restart mutates state', async () => {
  const before = status();
  for(const expert of [[entry('ctx.kType','turbo99')],[entry('ctx.vType','Q4_0'),entry('perf.flashAttn',false)]]) {
    await assert.rejects(restart({modelPath:'fixture.gguf',config:{expert}}));
    assert.deepEqual(status(),before);
  }
});
