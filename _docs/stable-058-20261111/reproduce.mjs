import { spawn } from 'node:child_process';
import { resolve } from 'node:path';
import { mkdirSync } from 'node:fs';
const root = resolve(import.meta.dirname, '../../apps/host');
const isolated = process.argv[2] === 'isolated';
const home = 'H:/Strata/releases/stable-058-20261111-codex/reproduce-isolated-home';
if (isolated) mkdirSync(home);
const child = spawn(process.execPath, ['--test', '--test-concurrency=2',
  '--test-name-pattern=dense text compacts|a message that fits only|/compact summarises|a search-heavy /plan',
  'tests/agent-context.test.mjs', 'tests/agent-turn-guard.test.mjs'], {
  cwd: root, stdio: 'inherit', windowsHide: true,
  env: { ...process.env, ...(isolated ? { HOME: home, USERPROFILE: home, HOMEDRIVE: 'H:', HOMEPATH: home.slice(2) } : {}), STRATA_HARNESS_DIR: resolve(root, '../desktop/src-tauri/resources/harness'), STRATA_NO_ACQUIRE: '1' },
});
child.once('error', error => { console.error(error); process.exitCode = 1; });
child.once('exit', code => { process.exitCode = code ?? 1; });
