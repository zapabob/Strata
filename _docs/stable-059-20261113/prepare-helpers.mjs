/** Retain original recipes; generate only new-version helpers, never old receipts. */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
const here = import.meta.dirname, prior = resolve(here, '../stable-058-20261111');
const names = ['build.py', 'delivery.py', 'publish.py', 'components.py', 'finalize-native.py', 'source-binding.mjs', 'control-binding.mjs', 'nsis-check.mjs', 'normal-start.py', 'normal-unload.py', 'qa-installed.mjs', 'snapshot.py', 'ci.py', 'runtime-equivalence.py'];
for (const name of names) {
  const target = resolve(here, name);
  if (existsSync(target)) throw Error('Preserve existing helper: ' + name);
  let text = readFileSync(resolve(prior, name), 'utf8').replaceAll('stable-058-20261111', 'stable-059-20261113').replaceAll('native-058-source-20261111', 'native-059-source-20261113').replaceAll('0.5.8', '0.5.9').replaceAll('app-058-', 'app-059-');
  if (name === 'publish.py') text = text.replace("latest['tag_name'] == 'v0.5.7'", "latest['tag_name'] == 'v0.5.8'").replace('context isolation and CI repair', 'local memory protection and reliable workflows');
  if (name === 'components.py') text = text.replace("Path('H:/Strata/releases/public-055-20261111-opencode/assets/strata-feed.json')", "Path('H:/Strata/releases/stable-058-20261111-codex/assets/strata-feed.json')");
  if (name === 'runtime-equivalence.py') text = text.replace("'c629ee37dde049b09bc42bdc00b076906f44fa27'", "json.loads((OUT / 'frozen-source.json').read_text())['sourceCommit']");
  if (name === 'delivery.py') text = text.replace("'passed': 43", "'passed': 44").replace("'receipts/harness-group-r1.json'", "'receipts/harness-group-final.json'");
  writeFileSync(target, text, { flag: 'wx' });
}
