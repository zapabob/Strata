import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { transform } from 'esbuild';

/**
 * Owner decision 12 (0.2.22): "Pause for update" is shown only when an update is waiting, from what the app already knows.
 * This fork has the pure decision API and the hook; the toolbar gating itself also needs the fork's missing /resume-agents
 * pause state (#7099), so those static UI assertions are not asserted here yet.
 */

const src = p => readFileSync(new URL(p, import.meta.url), 'utf8');

async function load() {
  const { code } = await transform(src('../src/lib/update-waiting.ts'), { loader: 'ts', format: 'esm' });
  return import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`);
}
const check = strataStatus => ({ checkedAt: '2026-11-25T08:00:00Z', strata: { status: strataStatus, canInstall: true, message: '' }, engine: { status: 'current', canInstall: false, message: '' } });

test('nothing known, or a check that found nothing, is no update waiting', async () => {
  const { strataUpdateWaiting } = await load();
  assert.equal(strataUpdateWaiting(null, null), false);
  assert.equal(strataUpdateWaiting(undefined, undefined), false);
  assert.equal(strataUpdateWaiting(check('current'), { engine: { updateAvailable: null } }), false);
  assert.equal(strataUpdateWaiting(check('error'), { engine: { updateAvailable: { engine: null, app: null } } }), false);
  assert.equal(strataUpdateWaiting(check('unavailable'), { engine: null }), false);
  assert.equal(strataUpdateWaiting(check('no-releases'), {}), false);
});

test('a kept check that found a newer Strata, or Control naming a newer app, is an update waiting', async () => {
  const { strataUpdateWaiting } = await load();
  assert.equal(strataUpdateWaiting(check('available'), null), true);
  assert.equal(strataUpdateWaiting(null, { engine: { updateAvailable: { engine: null, app: '0.2.22' } } }), true);
  assert.equal(strataUpdateWaiting(check('current'), { engine: { updateAvailable: { engine: null, app: '0.2.22' } } }), true);
});

test('a newer engine alone is not one: it does not end the app, so the agents have nothing to wait for', async () => {
  const { strataUpdateWaiting } = await load();
  assert.equal(strataUpdateWaiting(check('current'), { engine: { updateAvailable: { engine: '0.1.68', app: null } } }), false);
});

test('the hook reads only kept state: no network, no host call of its own', () => {
  const check_ = src('../src/lib/update-check.ts');
  const hook = check_.slice(check_.indexOf('export function useStrataUpdateWaiting'), check_.indexOf('/** The last known check result'));
  assert.match(hook, /useNative\(\)/);
  assert.match(hook, /useLastUpdateCheck\(useInstalledVersions\(\)\)/);
  assert.doesNotMatch(hook, /fetch\(|api\.|fetchUpdateCheck/);
});
