import test from 'node:test';
import assert from 'node:assert/strict';
import { parseQ36StartupLine, q36StartupSentence, reduceQ36Startup, pushEngineLogChunk, q36EngineLogPath } from '../server/q36-startup-events.mjs';
import { admitQ36LegacyPhysical, Q36_UD_Q4_K_XL_HOST_EXPERT_BYTES } from '../server/q36-run-contract.mjs';

test('startup events keep order, drop unknown stages, and do not clear an error', () => {
  const begin = parseQ36StartupLine('Q36_STARTUP schema=1 stage=warmup_prefill state=begin elapsed_ms=0 stage_elapsed_ms=0 error_code=null');
  assert.equal(begin.accepted, true);
  assert.equal(parseQ36StartupLine('not a startup line'), null);
  assert.equal(parseQ36StartupLine('Q36_STARTUP schema=1 stage=nope state=begin elapsed_ms=0 stage_elapsed_ms=0 error_code=null').accepted, false);
  const failed = parseQ36StartupLine('Q36_STARTUP schema=1 stage=expert_host_alloc state=error elapsed_ms=10 stage_elapsed_ms=10 error_code=host_allocation_failure');
  const later = parseQ36StartupLine('Q36_STARTUP schema=1 stage=warmup_prefill state=progress elapsed_ms=11 stage_elapsed_ms=1 error_code=null');
  assert.equal(reduceQ36Startup(failed, later), failed);
  assert.match(q36StartupSentence(failed), /Allocating expert memory failed: host_allocation_failure/);
  const otherGen = parseQ36StartupLine('Q36_STARTUP schema=1 stage=dense_load state=end elapsed_ms=1 stage_elapsed_ms=1 error_code=null generation=other');
  const mine = { ...begin, generation: 'mine' };
  assert.equal(reduceQ36Startup(mine, otherGen), mine);
  const done = parseQ36StartupLine('Q36_STARTUP schema=1 stage=expert_repack state=end elapsed_ms=266000 stage_elapsed_ms=266000 error_code=null');
  assert.match(q36StartupSentence(done), /266\.0 s/);
});

test('an engine-log chunk moves loading to warming to ready, and an error stays', () => {
  const line = (stage, state, error = 'null') => `Q36_STARTUP schema=1 stage=${stage} state=${state} elapsed_ms=4 stage_elapsed_ms=1 error_code=${error}\n`;
  assert.equal(q36EngineLogPath({ log: '  C:\\strata\\strata-qwen.log  ' }), 'C:\\strata\\strata-qwen.log');
  assert.equal(q36EngineLogPath({ log: 'app-1.host.log\0' }), null);
  assert.equal(q36EngineLogPath({}), null);
  const split = pushEngineLogChunk({ pending: '', startup: null, phase: null, sentence: null }, line('dense_load', 'begin').slice(0, 24));
  assert.equal(split.moved, false);
  const loading = pushEngineLogChunk(split, line('dense_load', 'begin').slice(24));
  assert.equal(loading.phase, 'loading');
  assert.match(loading.sentence, /Loading weights onto the GPU/);
  const warming = pushEngineLogChunk(loading, line('warmup_prefill', 'begin'));
  assert.equal(warming.phase, 'warming');
  const unknown = pushEngineLogChunk(warming, line('nope', 'begin'));
  assert.equal(unknown.phase, 'warming');
  assert.equal(unknown.moved, false);
  const ready = pushEngineLogChunk(unknown, line('engine_ready', 'end'));
  assert.equal(ready.phase, 'ready');
  const failed = pushEngineLogChunk(loading, `${line('expert_host_alloc', 'error', 'host_allocation_failure')}${line('warmup_prefill', 'progress')}`);
  assert.equal(failed.phase, 'error');
  assert.equal(failed.startup.state, 'error');
  assert.match(failed.sentence, /host_allocation_failure/);
  assert.doesNotMatch(failed.sentence, /Warming/);
});

test('full-file verification remains visible as loading before expert allocation', () => {
  let state = null;
  for (const [stage, label] of [['expert_model_verify', 'model file'], ['expert_pack_verify', 'expert cache']]) {
    const line = `Q36_STARTUP schema=1 stage=${stage} state=progress elapsed_ms=2500 stage_elapsed_ms=2500 error_code=null\n`;
    state = pushEngineLogChunk(state ?? { pending: '', startup: null, phase: null, sentence: null }, line);
    assert.equal(state.phase, 'loading');
    assert.equal(state.startup.stage, stage);
    assert.match(state.sentence, new RegExp(label));
  }
});

test('UD-Q4_K_XL legacy placement is refused when free RAM cannot hold the measured arena', () => {
  const low = admitQ36LegacyPhysical({
    modelName: 'Qwen3.6-35B-A3B-UD-Q4_K_XL',
    availablePhysicalBytes: 10n << 30n,
    ramBytes: 32n << 30n,
  });
  assert.equal(low.decision, 'rejected');
  assert.equal(low.fits, false);
  assert.match(low.message, /not started/);
  const unknown = admitQ36LegacyPhysical({ modelName: 'Qwen3.6-35B-A3B', availablePhysicalBytes: 1n, ramBytes: 32n << 30n });
  assert.equal(unknown.decision, 'unknown');
  assert.equal(unknown.fits, null);
  const huge = admitQ36LegacyPhysical({
    modelName: 'ud-q4_k_xl',
    availablePhysicalBytes: Q36_UD_Q4_K_XL_HOST_EXPERT_BYTES + (8n << 30n),
    ramBytes: 32n << 30n,
  });
  assert.equal(huge.decision, 'allowed');
  assert.equal(admitQ36LegacyPhysical({ modelName: 'ud-q4_k_xl' }).fits, null);
});
