/**
 * F06 / F07: Stop starts its deadline at click time; EOF without done/error ends the bubble.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { build } from 'esbuild';
import { fileURLToPath } from 'node:url';

const here = (p) => fileURLToPath(new URL(p, import.meta.url));

function installDom() {
  globalThis.window ??= globalThis;
  globalThis.document ??= {
    addEventListener() {},
    visibilityState: 'visible',
    documentElement: { dataset: {}, style: { setProperty() {} }, classList: { toggle() {}, add() {}, remove() {} } },
  };
  globalThis.navigator ??= { language: 'en' };
  globalThis.matchMedia ??= () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} });
  globalThis.sessionStorage ??= { getItem() { return null; }, setItem() {}, removeItem() {} };
  const memory = new Map();
  globalThis.localStorage = {
    getItem: (k) => memory.get(k) ?? null,
    setItem: (k, v) => { memory.set(k, v); },
    removeItem: (k) => { memory.delete(k); },
  };
}

async function loadStore(streamScript) {
  installDom();
  const mockClient = {
    name: 'mock-client',
    setup(b) {
      b.onResolve({ filter: /\/client$/ }, () => ({ path: 'mock-client', namespace: 'mock' }));
      b.onLoad({ filter: /.*/, namespace: 'mock' }, () => ({
        loader: 'js',
        contents: streamScript,
      }));
    },
  };
  const result = await build({
    entryPoints: [here('../src/lib/store.ts')],
    bundle: true, format: 'esm', platform: 'node', write: false, logLevel: 'silent',
    alias: { react: here('./helpers/react-stub.mjs') },
    loader: { '.json': 'json' },
    plugins: [mockClient],
  });
  return import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString('base64')}`);
}

test('F07: stream EOF without done/error clears message streaming and keeps partial text', async () => {
  const store = await loadStore(`
    export class ApiError extends Error {}
    export const api = { get: async () => ({ path: '', entries: [] }), post: async () => ({}), put: async () => ({}), patch: async () => ({}), del: async () => ({}), delete: async () => ({}) };
    export function onEvent() { return () => {}; }
    export async function streamPost(path, body, onFrame) {
      onFrame({ type: 'start', model: 'm', contextMax: 8192, requestId: 'r1' });
      onFrame({ type: 'delta', text: 'partial answer' });
      // no done / error — EOF
    }`);
  await store.sendMessage('hello');
  const msg = store.getState().sessions[0].messages.find(m => m.role === 'assistant');
  assert.equal(msg.streaming, false);
  assert.match(msg.content, /partial answer/);
  assert.match(String(msg.error ?? ''), /cut off|partial/i);
});

test('F06: Stop schedules the abort deadline before the Stop HTTP call resolves', async () => {
  let resolveStop;
  const stopPosted = new Promise((resolve) => { resolveStop = resolve; });
  const store = await loadStore(`
    export class ApiError extends Error {}
    let stopResolve;
    export const api = {
      get: async () => ({ path: '', entries: [] }),
      post: async (path, body) => {
        if (path === '/api/chat/stop') {
          globalThis.__stopCalled = true;
          await new Promise((r) => { globalThis.__releaseStop = r; });
          return { stopped: true };
        }
        return {};
      },
      put: async () => ({}), patch: async () => ({}), del: async () => ({}), delete: async () => ({}),
    };
    export function onEvent() { return () => {}; }
    export async function streamPost(path, body, onFrame, signal) {
      onFrame({ type: 'start', model: 'm', contextMax: 8192, requestId: 'r1' });
      await new Promise((resolve, reject) => {
        const onAbort = () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' }));
        if (signal?.aborted) return onAbort();
        signal?.addEventListener('abort', onAbort, { once: true });
        globalThis.__holdStream = resolve;
      });
      onFrame({ type: 'done', tokensIn: 1, tokensOut: 1, durationMs: 1, usageSource: 'reported' });
    }`);
  const send = store.sendMessage('long turn');
  for (let i = 0; i < 100 && !globalThis.__holdStream; i++) await new Promise(r => setTimeout(r, 5));
  assert.ok(globalThis.__holdStream, 'stream is held');
  assert.equal(store.getState().streaming, true);

  // Fake timers around Stop so we can see the deadline without waiting 30s.
  const realSetTimeout = globalThis.setTimeout;
  const timers = [];
  globalThis.setTimeout = (fn, ms, ...args) => {
    const handle = { fn, ms, args, cleared: false };
    timers.push(handle);
    return handle;
  };
  globalThis.clearTimeout = (handle) => { if (handle) handle.cleared = true; };

  store.stopStreaming();
  assert.equal(globalThis.__stopCalled, true);
  const deadline = timers.find(t => t.ms === 30000 && !t.cleared);
  assert.ok(deadline, '30s abort deadline armed before Stop HTTP resolves');

  // Fire the deadline: AbortError ends the held stream without waiting on Stop HTTP.
  deadline.fn();
  globalThis.setTimeout = realSetTimeout;
  globalThis.__releaseStop?.();
  await send;
  const msg = store.getState().sessions[0].messages.find(m => m.role === 'assistant');
  assert.equal(msg.streaming, false);
});
