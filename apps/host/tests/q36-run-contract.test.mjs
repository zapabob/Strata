import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { finishJob, nativeFixture } from './helpers/native-fixture.mjs';
import {
  admitLegacyExperts,
  bindLaunchPath,
  fileIdentitySync,
  gibToBytes,
  prepareQ36Launch,
  Q36_MAPPED_PACK_DIGESTS,
  q36FileSha256,
  q36PersistentKvBytes,
  sameModelIdentity,
} from '../server/q36-run-contract.mjs';

test('a C: selection is not launched from H:, and the file name is not the model identity', () => {
  const swapped = bindLaunchPath({ requestedPath: 'C:\\models\\model.gguf', resolvedPath: 'H:\\models\\model.gguf' });
  assert.equal(swapped.ok, false);
  assert.equal(swapped.error.code, 'path_drive_substituted');
  const root = mkdtempSync(join(tmpdir(), 'q36-id-'));
  try {
    const realDir = join(root, 'real');
    const otherDir = join(root, 'other');
    mkdirSync(realDir);
    mkdirSync(otherDir);
    const real = join(realDir, 'model.gguf');
    const twin = join(otherDir, 'model.gguf');
    writeFileSync(real, 'same-name-a');
    writeFileSync(twin, 'same-name-b');
    const a = fileIdentitySync(real);
    const b = fileIdentitySync(twin);
    assert.equal(a.basename, b.basename);
    assert.equal(sameModelIdentity(a, b), false);
    const spaced = join(root, 'my models');
    mkdirSync(spaced);
    const jp = join(spaced, 'モデル.gguf');
    writeFileSync(jp, 'unicode-path');
    const opened = fileIdentitySync(jp);
    assert.equal(opened.sizeBytes, String(Buffer.byteLength('unicode-path')));
    const link = join(root, 'link');
    execFileSync('cmd.exe', ['/d', '/c', 'mklink', '/J', link, realDir], { windowsHide: true });
    const via = fileIdentitySync(join(link, 'model.gguf'));
    assert.equal(sameModelIdentity(a, via), true);
    assert.equal(sameModelIdentity({ fileId: null, contentSha256: 'abc', basename: 'model.gguf' }, { fileId: null, contentSha256: 'abc', basename: 'other.gguf' }), true);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('the launch contract is frozen from the snapshot that was checked', () => {
  const input = { args: ['--max-context', '65536', '--prefill', 'auto', '--mtp', '2'], userArgs: [], binarySha256: 'abc' };
  const out = prepareQ36Launch(input);
  input.args.push('--cache-type-v', 'turbo3');
  assert.equal(out.ok, true);
  assert.deepEqual(out.argv, ['--max-context', '65536', '--prefill', 'auto', '--mtp', '2']);
  assert.equal(out.contract.effective.prefill, null);
  assert.equal(out.contract.requested.prefill, 'auto');
  assert.equal(out.contract.effective.persistentKv, 'fp32');
  assert.equal(out.contract.effective.expertStoreMode, 'legacy');
  assert.equal(out.contract.effective.mtp, 2);
  assert.equal(out.preservedUserArgs.includes('--cache-type-v'), false);
});

test('an explicit unsupported setting stops the launch and is not called applied', () => {
  for (const [flag, value] of [['--cache-type-k', 'q8_0'], ['--cache-type-v', 'turbo3'], ['--spin8-mode', 'consensus']]) {
    const denied = prepareQ36Launch({
      args: ['--max-context', '65536', flag, value],
      userArgs: [flag, value],
    });
    assert.equal(denied.ok, false, flag);
    assert.equal(denied.error.code, 'unsupported_setting');
    assert.match(denied.error.message, /not applied/);
    assert.equal(denied.argv, undefined);
  }
  const store = prepareQ36Launch({ args: ['--max-context', '65536'], requested: { expertStoreMode: 'mapped-pack' } });
  assert.equal(store.ok, false);
  assert.equal(store.error.code, 'expert_store_not_available');
  const bounded = prepareQ36Launch({ args: ['--max-context', '65536'], requested: { warmupMode: 'bounded' } });
  assert.equal(bounded.ok, false);
  assert.equal(bounded.error.code, 'unsupported_setting');
});

test('the engine digest is read from the file, and a missing file is not an allowlisted digest', () => {
  const dir = mkdtempSync(join(tmpdir(), 'q36-sha-'));
  try {
    const file = join(dir, 'strata.exe');
    writeFileSync(file, 'q36-engine');
    assert.equal(q36FileSha256(file), createHash('sha256').update('q36-engine').digest('hex'));
    assert.equal(q36FileSha256(join(dir, 'missing.exe')), null);
    const forged = prepareQ36Launch({
      args: ['--model', 'm.gguf', '--max-context', '65536'],
      requested: { expertStoreMode: 'mapped-pack' },
      binarySha256: q36FileSha256(file),
    });
    assert.equal(forged.ok, false);
    assert.equal(forged.error.code, 'expert_store_not_available');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('the recorded sm_120 engine digests are the mapped-pack allowlist, and legacy stays the default', () => {
  const listed = [...Q36_MAPPED_PACK_DIGESTS].sort();
  assert.deepEqual(listed, [
    '512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046',
    '6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29',
    'dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5',
  ].sort());
  for (const sha of listed) assert.match(sha, /^[0-9a-f]{64}$/);
  for (const sha of listed) {
    const bound = prepareQ36Launch({
      args: ['--model', 'm.gguf', '--max-context', '65536'],
      requested: { expertStoreMode: 'mapped-pack' },
      binarySha256: sha,
    });
    assert.equal(bound.ok, true, sha);
    assert.equal(bound.contract.effective.expertStoreMode, 'mapped-pack');
  }
  const settingsDigest = { binarySha256: listed[1], expertStoreMode: 'mapped-pack' };
  const untouched = prepareQ36Launch({
    args: ['--model', 'm.gguf', '--max-context', '65536'],
    binarySha256: listed[1],
    modelSettings: settingsDigest,
  });
  assert.equal(untouched.ok, true);
  assert.equal(untouched.contract.effective.expertStoreMode, 'legacy');
  assert.equal(untouched.argv.includes('--q36-expert-store'), false);
});

test('mapped-pack stays off the command line unless this engine digest is allowlisted', () => {
  const sha = 'ab'.repeat(32);
  const other = 'cd'.repeat(32);
  const allowed = prepareQ36Launch({
    args: ['--model', 'm.gguf', '--max-context', '65536'],
    requested: { expertStoreMode: 'mapped-pack' },
    binarySha256: sha,
    mappedPackDigests: [sha],
  });
  assert.equal(allowed.ok, true);
  assert.equal(allowed.argv[allowed.argv.indexOf('--q36-expert-store') + 1], 'mapped-pack');
  assert.equal(allowed.contract.effective.expertStoreMode, 'mapped-pack');
  const denied = prepareQ36Launch({
    args: ['--model', 'm.gguf', '--q36-expert-store', 'mapped-pack'],
    binarySha256: other,
    mappedPackDigests: [sha],
  });
  assert.equal(denied.ok, false);
  assert.equal(denied.error.code, 'expert_store_not_available');
  assert.equal(denied.argv, undefined);
  const junk = prepareQ36Launch({
    args: ['--model', 'm.gguf', '--q36-expert-store', 'spin'],
    userArgs: ['--q36-expert-store', 'spin'],
    binarySha256: sha,
    mappedPackDigests: [sha],
  });
  assert.equal(junk.ok, false);
  assert.equal(junk.error.code, 'unsupported_setting');
});

test('app-owned flags that this engine ignores are left out of argv and kept in the saved user list', () => {
  const userArgs = ['--pool-workers', '4'];
  const out = prepareQ36Launch({
    args: ['--max-context', '65536', '--vram-reserve-mib', '1536', '--resident-budget-gib', '12', '--pool-workers', '4'],
    userArgs,
  });
  assert.equal(out.ok, true);
  assert.equal(out.argv.includes('--vram-reserve-mib'), false);
  assert.equal(out.argv.includes('--resident-budget-gib'), false);
  assert.deepEqual(out.argv, ['--max-context', '65536', '--pool-workers', '4']);
  assert.match(out.note, /not applied/);
  assert.match(out.note, /Saved settings were kept/);
  assert.deepEqual(out.preservedUserArgs, userArgs);
});

test('a private-cache demand is refused instead of being deleted', () => {
  const required = prepareQ36Launch({ args: ['--max-context', '65536'], privacyRequired: true });
  assert.equal(required.error.code, 'q36_private_cache_unsupported');
  const present = prepareQ36Launch({ args: ['--max-context', '65536', '--prompt-cache', '0', '--conversation-cache-mib', '0'], userArgs: [] });
  assert.equal(present.error.code, 'q36_private_cache_unsupported');
  assert.match(present.error.message, /not removed to force a start/);
});

test('FP32 KV bytes and the legacy 18.75 GiB arena use commit headroom, not a shared-VRAM sum', () => {
  assert.equal(q36PersistentKvBytes(65536, 1).bytesDecimal, '2952790016');
  assert.equal(q36PersistentKvBytes(65536, 2).bytesDecimal, '5905580032');
  assert.equal(q36PersistentKvBytes(131072, 1).bytesDecimal, '5905580032');
  assert.equal(q36PersistentKvBytes(16384, 1).bytesDecimal, String(45056n * 16384n));
  assert.equal(q36PersistentKvBytes(Number.NaN, 1).ok, false);
  const expert = gibToBytes('18.75');
  const head = gibToBytes('11.89');
  assert.equal(admitLegacyExperts({ expertBytes: expert.bytesDecimal, commitHeadroomBytes: head.bytesDecimal }).fits, false);
  assert.equal(admitLegacyExperts({ expertBytes: null, commitHeadroomBytes: head.bytesDecimal }).fits, null);
  assert.notEqual(q36PersistentKvBytes(131072, 1).bytes, 4563402752n);
});

test('loading Qwen3.6 drops ignored memory flags and refuses an explicit cache flag before spawn', async () => {
  const f = nativeFixture();
  try {
    await f.control.refresh(true);
    const path = join(f.repo, 'strata-iq3_s.json');
    const config = JSON.parse(readFileSync(path, 'utf8'));
    config.arch = 'qwen35moe';
    config.model_name = 'Qwen3.6-35B-A3B';
    config.args = ['--max-context', '65536', '--prefill', '2048', '--mtp', '2', '--resident-budget-gib', '8'];
    writeFileSync(path, JSON.stringify(config));
    const loaded = await finishJob(f.control, f.control.operation('load', { model: 'iq3_s', resourceProfile: 'performance' }).id);
    assert.equal(loaded.state, 'done', loaded.error);
    const spawn = f.calls.find(call => call.args?.some(arg => String(arg).endsWith('server.py')));
    const configPath = spawn.args[spawn.args.indexOf('--config') + 1];
    const launched = JSON.parse(readFileSync(configPath, 'utf8'));
    assert.equal(launched.args.includes('--vram-reserve-mib'), false);
    assert.equal(launched.args.includes('--resident-budget-gib'), false);
    assert.ok(launched.args.includes('--max-context'));
    assert.equal(launched.q36_run.effective.context, 65536);
    assert.equal(launched.q36_run.effective.prefill, 2048);
    assert.equal(launched.q36_run.effective.persistentKv, 'fp32');
    await f.control.unload(loaded.result.instanceId);
    const handwritten = JSON.parse(readFileSync(path, 'utf8'));
    handwritten.args = ['--max-context', '65536', '--vram-reserve-mib', '1536'];
    writeFileSync(path, JSON.stringify(handwritten));
    const reserve = await finishJob(f.control, f.control.operation('load', { model: 'iq3_s' }).id);
    assert.equal(reserve.state, 'error');
    assert.match(reserve.error, /--vram-reserve-mib 1536/);
    assert.match(reserve.error, /not applied/);
    config.user_args = ['--cache-type-k', 'q8_0'];
    config.args = ['--max-context', '65536', '--cache-type-k', 'q8_0'];
    writeFileSync(path, JSON.stringify(config));
    const denied = await finishJob(f.control, f.control.operation('load', { model: 'iq3_s' }).id);
    assert.equal(denied.state, 'error');
    assert.match(denied.error, /--cache-type-k q8_0/);
    assert.match(denied.error, /not applied/);
  } finally {
    await f.cleanup();
  }
});
