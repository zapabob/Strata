import { createHash } from 'node:crypto';
import { once } from 'node:events';
import { readFile, writeFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';

const require = createRequire(new URL('../../app/host/package.json', import.meta.url));
const { chromium } = require('playwright-core');
const three = 'https://unpkg.com/three@0.160.0/';
const shim = 'https://unpkg.com/es-module-shims@1.8.0/dist/es-module-shims.js';
const declaredImports = {
  three: three + 'build/three.module.js',
  'three/addons/': three + 'examples/jsm/',
};
const allowed = new Set([
  shim, declaredImports.three,
  ...[
    'controls/OrbitControls.js', 'postprocessing/EffectComposer.js',
    'postprocessing/UnrealBloomPass.js', 'postprocessing/Pass.js',
    'postprocessing/MaskPass.js', 'postprocessing/ShaderPass.js',
    'shaders/CopyShader.js', 'shaders/LuminosityHighPassShader.js',
  ].map((path) => declaredImports['three/addons/'] + path),
]);
const csp = [
  'sandbox allow-scripts', "default-src 'none'", "script-src 'unsafe-inline' https://unpkg.com blob:",
  "style-src 'unsafe-inline'", 'img-src data: blob:', "connect-src 'none'", "form-action 'none'",
  "base-uri 'none'", "worker-src 'none'", "frame-src 'none'",
].join('; ');

function instrumentWebGL() {
  const contexts = new WeakSet();
  const stats = { contexts: [], draws: 0, instancedDraws: 0, instances: 0 };
  Object.defineProperty(window, '__pagodaObservation', { value: stats });
  const getContext = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function observeContext(type, ...args) {
    const result = getContext.call(this, type, ...args);
    if (!result || !/^(webgl2?|experimental-webgl)$/.test(type) || contexts.has(result)) {
      return result;
    }
    contexts.add(result);
    const debug = result.getExtension('WEBGL_debug_renderer_info');
    stats.contexts.push({ type, renderer: debug ? result.getParameter(debug.UNMASKED_RENDERER_WEBGL) : null });
    for (const [name, instanced] of [
      ['drawArrays', false], ['drawElements', false], ['drawArraysInstanced', true], ['drawElementsInstanced', true],
    ]) {
      const draw = result[name];
      if (typeof draw !== 'function') continue;
      result[name] = function observeDraw(...parameters) {
        stats.draws += 1;
        if (instanced) {
          stats.instancedDraws += 1;
          stats.instances += parameters.at(-1);
        }
        return draw.apply(this, parameters);
      };
    }
    return result;
  };
}

function state() {
  const read = (value) => Object.fromEntries(
    ['voxelCount', 'pagodaFloors', 'fps', 'timeOfDay'].map((key) => {
      const field = value?.[key];
      return [key, typeof field === 'number' && Number.isFinite(field) ? field : null];
    }),
  );
  const observed = window.__pagodaObservation;
  return {
    counters: { draws: observed.draws, instancedDraws: observed.instancedDraws, instances: observed.instances },
    contexts: observed.contexts,
    canvas: [...document.querySelectorAll('canvas')].map(({ width, height }) => ({ width, height })),
    telemetry: window.__VOXEL__ === undefined ? null : read(window.__VOXEL__),
    aliasTelemetry: window.VOXEL === undefined ? null : read(window.VOXEL),
    bodyText: document.body?.innerText.slice(0, 1000) ?? '',
  };
}

function measureFrameIntervals() {
  return new Promise((done) => {
    const times = [];
    function sample(timestamp) {
      times.push(timestamp);
      if (times.length > 1 && timestamp - times[0] >= 3000) {
        const elapsedMs = timestamp - times[0];
        done({ intervals: times.length - 1, elapsedMs, fps: 1000 * (times.length - 1) / elapsedMs });
      } else {
        requestAnimationFrame(sample);
      }
    }
    requestAnimationFrame(sample);
  });
}

async function capture(page, path) {
  const bytes = await page.screenshot({ path, timeout: 15000 });
  return createHash('sha256').update(bytes).digest('hex');
}

async function evaluate(page, fn) {
  let timer;
  try {
    return await Promise.race([
      page.evaluate(fn),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('Timed out observing the generated page')), 12000);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

async function inspect(htmlPath, executablePath) {
  const html = await readFile(htmlPath);
  const folder = dirname(htmlPath);
  const server = createServer((req, res) => {
    if (req.url !== '/index.html' || req.method !== 'GET') {
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8', 'Content-Security-Policy': csp,
      'Referrer-Policy': 'no-referrer', 'X-Content-Type-Options': 'nosniff',
      'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), fullscreen=()',
    }).end(html);
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const url = 'http://127.0.0.1:' + server.address().port + '/index.html';
  const evidence = {
    htmlBytes: html.length,
    htmlSha256: createHash('sha256').update(html).digest('hex'),
    viewport: [1280, 800], errors: [], failedRequests: [], requests: [],
  };
  let browser;
  try {
    // Do not turn Chromium's OS sandbox off for generated JavaScript.
    browser = await chromium.launch({ executablePath, chromiumSandbox: true, timeout: 20000 });
    evidence.browser = browser.version();
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1,
      serviceWorkers: 'block', acceptDownloads: false });
    await context.routeWebSocket('**/*', (socket) => socket.close());
    await context.route('**/*', async (route) => {
      const request = route.request();
      const target = request.url();
      if (target === url && request.isNavigationRequest() && evidence.requests.length === 0) {
        evidence.requests.push({ url: target, status: 200 });
        await route.continue();
      } else if (request.method() === 'GET' && request.resourceType() === 'script' && allowed.has(target)) {
        try {
          const response = await route.fetch({ maxRedirects: 0, timeout: 15000 });
          evidence.requests.push({ url: target, status: response.status() });
          await route.fulfill({ response, headers: { ...response.headers(), 'access-control-allow-origin': '*' } });
        } catch (error) {
          evidence.failedRequests.push({ url: target, error: String(error) });
          await route.abort().catch(() => {});
        }
      } else {
        evidence.requests.push({ url: target, status: 'blocked' });
        await route.abort();
      }
    });
    await context.addInitScript(instrumentWebGL);
    const page = await context.newPage();
    page.on('pageerror', (error) => evidence.errors.push(String(error)));
    page.on('console', (entry) => {
      if (entry.type() === 'error') evidence.errors.push(entry.text());
    });
    page.on('requestfailed', (request) => {
      evidence.failedRequests.push({ url: request.url(), error: request.failure()?.errorText });
    });
    await page.goto(url, { waitUntil: 'load', timeout: 25000 });
    const format = await evaluate(page, () => ({
      maps: [...document.querySelectorAll('script[type=importmap]')].map((script) => script.textContent),
      modules: [...document.querySelectorAll('script[type=module]')].map((script) => !script.hasAttribute('src')),
      externalScripts: [...document.querySelectorAll('script[src]')].map((script) => script.getAttribute('src')),
    }));
    let imports;
    try {
      imports = format.maps.length === 1 ? JSON.parse(format.maps[0]).imports : null;
    } catch {
      imports = null;
    }
    evidence.format = {
      under700kB: html.length < 700000,
      lockedImports: !!imports && Object.keys(imports).length === 2
        && Object.entries(declaredImports).every(([key, value]) => imports[key] === value),
      oneInlineModule: format.modules.length === 1 && format.modules[0],
      lockedShim: format.externalScripts.length === 1 && format.externalScripts[0] === shim,
    };
    const drawing = await page.waitForFunction(() => window.__pagodaObservation.draws > 0, null, { timeout: 12000 })
      .then(() => true, () => false);
    if (drawing) await page.waitForTimeout(3500);
    evidence.start = await evaluate(page, state);
    if (drawing) evidence.frameSample = await evaluate(page, measureFrameIntervals);
    evidence.end = await evaluate(page, state);
    evidence.firstScreenshot = await capture(page, resolve(folder, 'preview.png'));
    evidence.drawing = drawing;
    if (drawing) {
      await page.mouse.move(740, 380);
      await page.mouse.down();
      await page.mouse.move(1000, 430, { steps: 12 });
      await page.mouse.up();
      await page.mouse.wheel(0, -285);
      await page.waitForTimeout(650);
      evidence.afterDrag = await capture(page, resolve(folder, 'after-drag.png'));
      await page.setViewportSize({ width: 1024, height: 640 });
      await page.waitForTimeout(450);
      evidence.resized = await evaluate(page, state);
    }
  } catch (error) {
    evidence.harnessError = String(error);
  } finally {
    if (browser) await browser.close();
    server.closeAllConnections();
    await new Promise((done) => server.close(done));
    await writeFile(resolve(folder, 'render.json'), JSON.stringify(evidence, null, 2) + '\n');
    console.log(JSON.stringify({ model: folder, drawing: evidence.drawing, errors: evidence.errors.length,
      harnessError: evidence.harnessError, telemetry: evidence.end?.telemetry }));
  }
}

const [executable, ...files] = process.argv.slice(2);
if (!executable || !files.length) throw new Error('Usage: node inspect_pagoda.mjs chrome.exe [index.html ...]');
for (const path of files) await inspect(resolve(path), executable);
