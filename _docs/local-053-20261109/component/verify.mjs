/** Read-only production guards, including independent frozen native bindings. No executable probes. */
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

if (process.argv.includes('--help')) {
  console.log('node verify.mjs <app-root> <package> <version> <native-source-root|-> <native-commit|->');
} else {
  const [app, folder, version, sourceRoot, sourceCommit] = process.argv.slice(2);
  assert.ok(app && folder && version && sourceRoot && sourceCommit);
  const root = resolve(app);
  const {verifyEngine, verifyNativeBuild, nativeSources, sha256, verifyPublicAssets} =
    await import(pathToFileURL(join(root, 'apps/host/scripts/release-integrity.mjs')));
  const {verifyLocalBackend} = await import(pathToFileURL(join(root, 'apps/host/server/local-backends.mjs')));
  const manifest = version === 'siblings' ? null : verifyEngine(folder, version);
  let binding = null, nativeSourceCount = null;
  if (sourceRoot !== '-') {
    binding = verifyNativeBuild(folder, root, manifest, {
      sourceRoot, sourceCommit, manifestSHA256: sha256(join(folder, 'engine-component.json')),
    });
    nativeSourceCount = Object.keys(nativeSources(sourceRoot)).length;
    assert.ok(nativeSourceCount > 0);
    const record = JSON.parse(readFileSync(join(folder, 'native-build.json'), 'utf8'));
    assert.equal(record.schema, 1);
    assert.equal(record.recipe?.portable, true);
    assert.equal(record.recipe.cudaArchs, '120');
    assert.equal(record.recipe.spin8, 'ON');
    assert.equal(record.recipe.ggmlCommit, '3cf03257f219afbe7334045ff7c6a06ac68c627d');
    assert.equal(record.recipe.cudaSpillBaseline, undefined);
  }
  // Native-only inputs have no local backends; composites and sibling resources must pass both.
  const backends = {};
  if (sourceRoot === '-' || manifest.files.some(row => row.path.startsWith('local-backends/'))) {
    for (const [choice, id, version, hash] of [
      ['PrismML', 'prism', '0.4.1', '9c729c73eb050dc466203fe149a27acd5be48763a33ea2c5d2b89f78e4ddcbaa'],
      ['TurboQuant', 'turboquant', '0.4.0', '85a6fea57bf766f7ebbb98ff62ee0ff8c83330f99b770e68031f662dae93ae14'],
    ]) {
      const dir = join(folder, 'local-backends', id);
      const runtime = await verifyLocalBackend({path: join(dir, 'llama-server.exe'), manifestPath: join(dir, 'runtime.json')}, choice);
      assert.equal(runtime.version, version);
      assert.equal(sha256(join(dir, 'runtime.json')), hash);
      backends[id] = {version, manifestSHA256: hash};
    }
    assert.equal(sha256(join(folder, 'local-backends/prism/llama-server.exe')),
      '5ca5d8bfdfcb6fe46a96a06b71eaf45aedfbd1c6673bda2a10eb6412613be777');
    const notices = join(folder, 'notices');
    const record = JSON.parse(readFileSync(join(notices, 'NOTICES.json'), 'utf8'));
    const {files} = await import(pathToFileURL(join(root, 'apps/host/scripts/release-integrity.mjs')));
    const {relative} = await import('node:path');
    const actual = files(notices).map(p => relative(notices, p).replaceAll('\\', '/'))
      .filter(p => p !== 'NOTICES.json' && p !== '.gitignore').sort();
    assert.deepEqual(actual, Object.keys(record.files).sort());
    for (const [name, hash] of Object.entries(record.files)) assert.equal(sha256(join(notices, name)), hash);
  }
  verifyPublicAssets('H:/Strata/releases/hakua033-public-assets',
    JSON.parse(readFileSync('H:/Strata/releases/hakua033-public-assets.receipt.json', 'utf8')));
  console.log(JSON.stringify({ok: true, binding, nativeSourceCount, backends, publicAssetsVerified: true}));
}
