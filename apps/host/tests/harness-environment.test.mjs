import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { HarnessProcess } from '../server/agent/harness-runtime.mjs';
import { harnessFixtureEnvironment } from './helpers/harness-environment.mjs';

test('the spawned Harness uses the explicit fixture home and filtered environment, with only named credentials', async t => {
  const tempRoot = resolve(tmpdir());
  const parentProfile = process.env.USERPROFILE;
  const directory = mkdtempSync(join(tempRoot, 'strata-harness-env-'));
  const home = join(directory, 'home');
  const output = join(directory, 'environment.json');
  const bin = join(directory, 'probe.mjs');
  const baseEnv = harnessFixtureEnvironment(directory, { ...process.env, AMBIENT_TEST_TOKEN: 'synthetic-ambient' });
  writeFileSync(bin, `import {writeFileSync} from 'node:fs'; import {homedir} from 'node:os';
writeFileSync(${JSON.stringify(output)},JSON.stringify({home:homedir(),profile:process.env.USERPROFILE,harness:process.env.DSH_HOME,ambient:process.env.AMBIENT_TEST_TOKEN??null,explicit:process.env.EXPLICIT_TEST_TOKEN}));
console.log('http://127.0.0.1:12345/?token=synthetic_fixture_token'); setInterval(()=>{},1000);`);
  const runtime = new HarnessProcess({ harness: { bin }, home, patchFile: join(directory, 'unused.patch.yml'),
    cwd: join(directory, 'run'), baseEnv, env: { EXPLICIT_TEST_TOKEN: 'synthetic-explicit' } });
  t.after(async () => {
    await runtime.stop();
    assert.equal(dirname(resolve(directory)), tempRoot, 'cleanup stays inside this fixture temp root');
    rmSync(directory, { recursive: true, force: true, maxRetries: 3 });
  });
  await runtime.start({ timeoutMs: 10_000 });
  assert.deepEqual(JSON.parse(readFileSync(output, 'utf8')), {
    home: directory, profile: directory, harness: home, ambient: null, explicit: 'synthetic-explicit',
  });
  assert.equal(process.env.USERPROFILE, parentProfile, 'the parent profile is unchanged');
});
