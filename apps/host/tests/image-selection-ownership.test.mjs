/** Actual store request ownership with controlled promises; no Host, network, filesystem or browser. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { fileURLToPath } from 'node:url';

const here = path => fileURLToPath(new URL(path, import.meta.url));
let sequence = 0;
async function fixture() {
    globalThis.window = globalThis;
    globalThis.document = { addEventListener() {}, visibilityState: 'visible', documentElement: { dataset: {}, style: { setProperty() {} }, classList: { toggle() {}, add() {}, remove() {} } } };
    globalThis.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
    globalThis.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };
    globalThis.sessionStorage = { getItem: () => null, setItem() {}, removeItem() {} };
    globalThis.__imagePatchGates = [];
    const output = await build({ entryPoints: [here('../src/lib/store.ts')], bundle: true, write: false, format: 'esm', platform: 'node', alias: { react: here('./helpers/react-stub.mjs') }, plugins: [{ name: 'controlled-client', setup(b) {
        b.onResolve({ filter: /\/client$/ }, () => ({ path: 'client', namespace: 'controlled' }));
        b.onLoad({ filter: /.*/, namespace: 'controlled' }, () => ({ contents: `
            export class ApiError extends Error {}
            const forbidden=async()=>{throw Error('unexpected non-selection API')};
            export const api={get:forbidden,post:forbidden,put:forbidden,del:forbidden,delete:forbidden,patch:(path,body)=>new Promise((resolve,reject)=>globalThis.__imagePatchGates.push({path,body,resolve,reject}))};
            export const onEvent=()=>()=>{},streamPost=forbidden;` }));
    } }] });
    const store = await import(`data:text/javascript;base64,${Buffer.from(output.outputFiles[0].text+'\n// fixture '+(++sequence)).toString('base64')}`);
    const library = selected => ({ selected, applied: 'off', variants: [], generationAvailable: false });
    const initial = store.selectImageModel('q6');
    __imagePatchGates[0].resolve(library('q6')); await initial;
    return { store, gates: __imagePatchGates, library };
}

test('actual store synchronously publishes intended selection and an older reply cannot clear current pending state', async () => {
    const { store, gates, library } = await fixture();
    const old = store.selectImageModel('off');
    const current = store.selectImageModel('q6');
    assert.equal(store.getState().imageModels.selected, 'q6');
    assert.equal(store.getState().busy['image:select'], true);
    assert.deepEqual(gates.slice(1).map(g=>[g.path,g.body.selected]), [['/api/image-models','off'],['/api/image-models','q6']]);
    gates[1].resolve(library('off')); await old;
    assert.equal(store.getState().imageModels.selected, 'q6');
    assert.equal(store.getState().busy['image:select'], true);
    gates[2].resolve(library('q6')); await current;
    assert.equal(store.getState().busy['image:select'], false);
});

test('actual store ignores stale success after the latest completion and leaves stale rejection observable to its owner', async () => {
    const { store, gates, library } = await fixture();
    const old = store.selectImageModel('off');
    const current = store.selectImageModel('q6');
    gates[2].resolve(library('q6')); await current;
    gates[1].resolve(library('off')); await old;
    assert.equal(store.getState().imageModels.selected, 'q6');
    assert.equal(store.getState().busy['image:select'], false);
    const failing = store.selectImageModel('q4');
    const rejection = assert.rejects(failing, /stale selection/);
    const latest = store.selectImageModel('off');
    gates[3].reject(new Error('stale selection')); await rejection;
    assert.equal(store.getState().imageModels.selected, 'off');
    assert.equal(store.getState().busy['image:select'], true);
    gates[4].resolve(library('off')); await latest;
    assert.equal(store.getState().imageModels.selected, 'off');
    assert.equal(store.getState().busy['image:select'], false);
});
