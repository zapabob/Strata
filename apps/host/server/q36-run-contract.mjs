/** Qwen3.6 launch contract.

 * The native Qwen3.6 engine (strata-q36) accepts a short flag list and, in --serve,
 * skips anything else with a warning. A skipped flag still looks like a successful
 * setting in the UI. This module keeps the launch argv inside the flags the engine
 * actually reads, and refuses a start when the person, or a private-cache policy,
 * asked for something this engine cannot do.
 *
 * Capability list is the `a == "--..."` options in src/qwen35/q36_engine.cu::run
 * at source baseline 170e0d330edd9c03b5dcddfc64b77e498387ff86.
 */
import { createHash } from 'node:crypto';
import { closeSync, fstatSync, openSync, realpathSync } from 'node:fs';
import { basename } from 'node:path';
import { flagOf, groups } from './native-user-args.mjs';

export const Q36_SOURCE_BASELINE = '170e0d330edd9c03b5dcddfc64b77e498387ff86';
export const Q36_CAPABILITY_REVISION = 'q36-argv-170e0d33';
export const Q36_ENGINE_DEFAULT_CONTEXT = 32768;
export const Q36_KV_BYTES_PER_CELL_PER_SEQ = 45056n;

/** Options that take one following value. */
export const Q36_VALUE_FLAGS = new Set([
  '--model', '--native', '--max-new', '--pool-workers', '--gpu', '--max-context', '--ctx',
  '--chunk', '--prefill', '--tokens', '--n', '--force', '--emb', '--dump-full-logits',
  '--bench-pp', '--bench-tg', '--mtp', '--draft-vocab', '--batch', '--slots',
  '--expert-vram', '--cpu-threads', '--expert-slots', '--hybrid-rows',
]);
/** Options that stand alone. */
export const Q36_SWITCH_FLAGS = new Set([
  '--no-token-graph', '--greedy', '--serve', '--no-graph', '--no-warmup', '--vision', '--batch-mtp',
]);
export const Q36_SUPPORTED_FLAGS = new Set([...Q36_VALUE_FLAGS, ...Q36_SWITCH_FLAGS]);

const PRIVATE_CACHE_FLAGS = new Set(['--prompt-cache', '--conversation-cache-mib']);
const isFlag = text => typeof text === 'string' && text.startsWith('--');

export function isQwen36Config(config = {}) {
  if (!config || typeof config !== 'object') return false;
  if (config.arch === 'qwen35moe') return true;
  if (/strata-q36/i.test(String(config.exe ?? ''))) return true;
  const name = `${config.model_name ?? ''} ${config.family ?? ''}`;
  return /qwen3\.6|qwen36|35b-a3b/i.test(name);
}

function valueSpan(list, at) {
  return at + 1 < list.length && !isFlag(list[at + 1]) ? 1 : 0;
}

function fail(code, message) {
  return { ok: false, error: { code, message } };
}

/** Persistent FP32 K+V bytes for Qwen3.6: 45056 * cells * sequences. Not a Hikari layer map. */
export function q36PersistentKvBytes(cells, sequences = 1) {
  if (!Number.isInteger(cells) || !Number.isInteger(sequences) || cells < 0 || sequences < 0) {
    return { ok: false, error: { code: 'kv_invalid', message: 'Qwen3.6 KV capacity must be a non-negative integer.' } };
  }
  const bytes = Q36_KV_BYTES_PER_CELL_PER_SEQ * BigInt(cells) * BigInt(sequences);
  return { ok: true, bytes, bytesDecimal: bytes.toString() };
}

/** Decimal GiB (up to 2 places) to bytes. 18.75 and 11.89 stay exact at hundredths of a GiB. */
export function gibToBytes(gib) {
  const text = String(gib);
  if (!/^\d+(\.\d{1,2})?$/.test(text)) {
    return { ok: false, error: { code: 'bytes_invalid', message: 'A memory quantity must be a non-negative GiB value.' } };
  }
  const [whole, frac = ''] = text.split('.');
  const hundredths = BigInt(whole) * 100n + BigInt((frac + '00').slice(0, 2));
  const bytes = hundredths * (1n << 30n) / 100n;
  return { ok: true, bytes, bytesDecimal: bytes.toString() };
}

/** Legacy expert arena versus commit headroom. Missing inputs stay unknown. Shared GPU memory is not an input. */
export function admitLegacyExperts({ expertBytes = null, commitHeadroomBytes = null } = {}) {
  if (expertBytes == null || commitHeadroomBytes == null) return { ok: true, fits: null, reason: 'unknown' };
  let expert, head;
  try {
    expert = BigInt(expertBytes);
    head = BigInt(commitHeadroomBytes);
  } catch {
    return { ok: false, fits: null, reason: 'invalid' };
  }
  if (expert < 0n || head < 0n) return { ok: false, fits: null, reason: 'invalid' };
  const fits = head >= expert;
  return { ok: true, fits, reason: fits ? 'ok' : 'commit_headroom' };
}

export function driveLetter(filePath) {
  const match = String(filePath ?? '').match(/^([A-Za-z]):[\\/]/);
  return match ? match[1].toUpperCase() : null;
}

/** A requested C: model must not be launched from an H: path. Same-file proof does not authorise the swap. */
export function bindLaunchPath({ requestedPath, resolvedPath }) {
  const requested = driveLetter(requestedPath);
  const resolved = driveLetter(resolvedPath);
  if (requested && resolved && requested !== resolved) {
    return fail(
      'path_drive_substituted',
      `The selected model is on ${requested}: and the resolved file is on ${resolved}:. Qwen3.6 will not start from the other drive.`,
    );
  }
  return { ok: true, launchPath: requestedPath };
}

export function fileIdentitySync(filePath) {
  const fd = openSync(filePath, 'r');
  try {
    const st = fstatSync(fd);
    let resolvedPath = filePath;
    try { resolvedPath = realpathSync.native(filePath); } catch { resolvedPath = filePath; }
    return {
      requestedPath: filePath,
      resolvedPath,
      fileId: `${st.dev}:${st.ino}`,
      volumeId: String(st.dev),
      sizeBytes: String(st.size),
      basename: basename(filePath),
    };
  } finally {
    closeSync(fd);
  }
}

/** Same file index, or the same content hash. The file name is not an identity. */
export function sameModelIdentity(a, b) {
  if (!a || !b) return false;
  if (a.fileId && b.fileId) return a.fileId === b.fileId;
  if (a.contentSha256 && b.contentSha256) return a.contentSha256 === b.contentSha256;
  return false;
}

function canonical(value) {
  return JSON.stringify(value, (_, item) => {
    if (item && typeof item === 'object' && !Array.isArray(item)) {
      return Object.fromEntries(Object.entries(item).sort(([p], [q]) => (p < q ? -1 : p > q ? 1 : 0)));
    }
    return item;
  });
}

function sha256Text(text) {
  return createHash('sha256').update(text).digest('hex');
}

function readNumberFlag(argv, flags) {
  for (const flag of flags) {
    const at = argv.indexOf(flag);
    if (at >= 0 && at + 1 < argv.length) return argv[at + 1];
  }
  return null;
}

/**
 * Build the argv and contract for one Qwen3.6 launch.
 * `input` is copied immediately. Later edits to the caller's object do not enter the argv.
 * `userArgs` are the person's flags. Any other unsupported flag is removed from the launch
 * and reported. It is not deleted from `userArgs`.
 */
export function prepareQ36Launch(input = {}) {
  const args = [...(input.args ?? [])].map(String);
  const userArgs = [...(input.userArgs ?? [])].map(String);
  const requested = { ...(input.requested ?? {}) };
  const userFlags = new Set(groups(userArgs).map(flagOf).filter(Boolean));
  const warnings = [];

  if (input.privacyRequired === true || args.some(a => PRIVATE_CACHE_FLAGS.has(a)) || [...userFlags].some(f => PRIVATE_CACHE_FLAGS.has(f))) {
    return fail(
      'q36_private_cache_unsupported',
      'Qwen3.6 has no tested prompt-cache isolation. Private cache flags were not removed to force a start.',
    );
  }
  if (requested.persistentKv && requested.persistentKv !== 'fp32') {
    return fail('unsupported_setting', 'Qwen3.6 keeps FP32 KV for this launch. Another KV storage was not applied.');
  }
  if (requested.expertStoreMode && requested.expertStoreMode !== 'legacy') {
    return fail('expert_store_not_available', 'The mapped expert store is not part of this engine. The legacy placement stays available and this launch was not switched.');
  }
  if (requested.warmupMode && !['legacy', 'off'].includes(requested.warmupMode)) {
    return fail('unsupported_setting', `Qwen3.6 warmup mode "${requested.warmupMode}" is not in capability ${Q36_CAPABILITY_REVISION}.`);
  }
  for (const [key, flag] of [['cacheTypeK', '--cache-type-k'], ['cacheTypeV', '--cache-type-v'], ['spin8Mode', '--spin8-mode']]) {
    if (requested[key]) {
      return fail('unsupported_setting', `${flag} ${requested[key]} is not a Qwen3.6 option. It was not applied and the model was not started.`);
    }
  }

  const argv = [];
  const dropped = [];
  for (let i = 0; i < args.length; i++) {
    const item = args[i];
    if (!isFlag(item)) { argv.push(item); continue; }
    const takes = Q36_VALUE_FLAGS.has(item);
    const alone = Q36_SWITCH_FLAGS.has(item);
    const n = valueSpan(args, i);
    const value = n ? args[i + 1] : null;
    if (item === '--mtp' && value != null && !/^\d+$/.test(value)) {
      if (userFlags.has(item)) {
        return fail('unsupported_setting', `--mtp ${value} is not a draft count. Qwen3.6 was not started.`);
      }
      dropped.push({ flag: item, value });
      i += n;
      continue;
    }
    if (takes) {
      if (!n) return fail('unsupported_setting', `${item} needs a value. The model was not started.`);
      if ((item === '--max-context' || item === '--ctx' || item === '--mtp' || item === '--batch' || item === '--slots') && !/^\d+$/.test(value)) {
        return fail('unsupported_setting', `${item} needs an integer. The model was not started.`);
      }
      if ((item === '--prefill' || item === '--chunk') && value !== 'auto' && !/^\d+$/.test(value)) {
        return fail('unsupported_setting', `${item} needs auto or an integer. The model was not started.`);
      }
      argv.push(item, value);
      i += 1;
      continue;
    }
    if (alone) { argv.push(item); continue; }
    if (userFlags.has(item) || PRIVATE_CACHE_FLAGS.has(item)) {
      const shown = [item, value].filter(v => v != null).join(' ');
      return fail('unsupported_setting', `${shown} is not a Qwen3.6 option. It was not applied and the model was not started.`);
    }
    dropped.push({ flag: item, value });
    i += n;
  }

  const nativeAt = argv.indexOf('--native');
  const modelAt = argv.indexOf('--model');
  const pathAt = nativeAt >= 0 ? nativeAt : modelAt;
  if (pathAt >= 0) {
    const requestedPath = argv[pathAt + 1];
    const resolvedPath = input.modelIdentity?.resolvedPath ?? requestedPath;
    const bound = bindLaunchPath({ requestedPath, resolvedPath });
    if (!bound.ok) return bound;
    if (input.modelIdentity?.fileId && input.expectedFileId && input.modelIdentity.fileId !== input.expectedFileId) {
      return fail('model_identity_mismatch', 'The opened model file is not the file that was checked. The launch was stopped.');
    }
  }

  const contextText = readNumberFlag(argv, ['--max-context', '--ctx']);
  const context = contextText != null ? Number(contextText) : Q36_ENGINE_DEFAULT_CONTEXT;
  if (contextText == null) warnings.push({ code: 'engine_default_context', message: 'No --max-context was set. The engine default is 32768.' });
  const prefillText = readNumberFlag(argv, ['--prefill', '--chunk']);
  let prefill = null;
  if (prefillText == null) warnings.push({ code: 'effective_prefill_unobserved', message: 'Prefill was not set on the command line. The engine chooses it after VRAM is known.' });
  else if (prefillText === 'auto') warnings.push({ code: 'effective_prefill_unobserved', message: 'Prefill is auto. The effective chunk is known only after the engine measures VRAM.' });
  else prefill = Number(prefillText);
  const mtpText = readNumberFlag(argv, ['--mtp']);
  const mtp = mtpText != null ? Number(mtpText) : 0;
  const batchText = readNumberFlag(argv, ['--batch', '--slots']);
  const parallel = Number.isInteger(requested.parallel) ? requested.parallel : (batchText != null ? Number(batchText) : 1);
  const warmupMode = argv.includes('--no-warmup') || requested.warmupMode === 'off' ? 'off' : 'legacy';

  if (!input.binarySha256) {
    warnings.push({ code: 'binary_digest_unbound', message: 'The engine binary digest is not bound. Only the legacy expert placement is allowed.' });
  }

  const identity = input.modelIdentity ?? {};
  const contract = {
    schemaVersion: 1,
    runId: input.runId ?? null,
    generation: input.generation ?? null,
    backend: { family: 'qwen36', binarySha256: input.binarySha256 ?? null, capabilityRevision: Q36_CAPABILITY_REVISION },
    model: {
      requestedPath: identity.requestedPath ?? (pathAt >= 0 ? argv[pathAt + 1] : null),
      resolvedPath: identity.resolvedPath ?? null,
      fileId: identity.fileId ?? null,
      volumeId: identity.volumeId ?? null,
      sizeBytes: identity.sizeBytes ?? null,
      contentSha256: identity.contentSha256 ?? null,
      geometryDigest: identity.geometryDigest ?? null,
      tokenizerDigest: identity.tokenizerDigest ?? null,
    },
    requested: {
      context: requested.context ?? context,
      prefill: requested.prefill ?? (prefillText === 'auto' ? 'auto' : prefill),
      mtp: requested.mtp ?? mtp,
      parallel,
    },
    effective: {
      context,
      prefill,
      mtp,
      parallel,
      persistentKv: 'fp32',
      warmupMode,
      expertStoreMode: 'legacy',
    },
    securityPolicyDigest: input.securityPolicyDigest ?? null,
    argv,
    warnings,
  };
  contract.configDigest = sha256Text(canonical({
    capabilityRevision: Q36_CAPABILITY_REVISION,
    argv,
    effective: contract.effective,
    fileId: contract.model.fileId,
    contentSha256: contract.model.contentSha256,
  }));

  const note = dropped.length
    ? `Left out because this Qwen3.6 engine does not take them (not applied): ${dropped.map(d => [d.flag, d.value].filter(v => v != null).join(' ')).join(', ')}. Saved settings were kept.`
    : '';
  return { ok: true, argv, note, warnings, dropped, preservedUserArgs: userArgs, contract };
}
