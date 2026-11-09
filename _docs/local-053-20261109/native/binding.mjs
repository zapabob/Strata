/** Verify the current helper's record. Never manufactures or repairs a build identity. */
import {readFileSync} from 'node:fs';
import {resolve, join} from 'node:path';
import {pathToFileURL} from 'node:url';

if (process.argv.includes('--help')) {
  console.log('node binding.mjs <frozen-source-root> <Release-or-native-directory>');
} else {
  if (process.argv.length !== 4) throw Error('Expected source root and binary directory');
  const root = resolve(process.argv[2]), folder = resolve(process.argv[3]);
  const {nativeSources, sha256} = await import(pathToFileURL(join(root, 'apps/host/scripts/release-integrity.mjs')));
  const record = JSON.parse(readFileSync(join(folder, 'native-build.json'), 'utf8'));
  const fail = message => { throw Error(message); };
  if (record.schema !== 1 || record.version !== '0.5.3' || record.entrypoint !== 'strata.exe') fail('Wrong build identity');
  if (record.sha256 !== sha256(join(folder, 'strata.exe'))) fail('Executable hash mismatch');
  const sources = nativeSources(root);
  if (JSON.stringify(sources) !== JSON.stringify(record.sources)) fail('Native source membership/bytes changed');
  const recipe = record.recipe;
  if (!recipe?.portable || recipe.cudaArchs !== '120' || recipe.spin8 !== 'ON' ||
      recipe.ggmlCommit !== '3cf03257f219afbe7334045ff7c6a06ac68c627d' || recipe.cudaSpillBaseline !== undefined)
    fail('Unexpected recipe/baseline; reviewed default allowances required');
  console.log(JSON.stringify({nativeSourceCount: Object.keys(sources).length,
    nativeBuildSHA256: sha256(join(folder, 'native-build.json')),
    strataSHA256: sha256(join(folder, 'strata.exe')), q36SHA256: sha256(join(folder, 'strata-q36.exe')),
    recipe, version: record.version}));
}
