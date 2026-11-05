/** Qwen3.6 launch contract.

 * The native Qwen3.6 engine (strata-q36) accepts a short flag list and, in --serve,
 * skips anything else with a warning. A skipped flag still looks like a successful
 * setting in the UI. This module keeps the launch argv inside the flags the engine
 * actually reads, and refuses a start when the person, or a private-cache policy,
 * asked for something this engine cannot do.
 *
 * Capability list is the `a == "--..."` options in src/qwen35/q36_engine.cu::run.
 * Q36_SOURCE_BASELINE is the reviewed public commit. The live flag list is
 * Q36_CAPABILITY_REVISION. --q36-expert-store mapped-pack is not put on the
 * command line unless that engine binary's digest is allowlisted, so an older
 * binary cannot ignore the flag and still allocate the full host arena.
 */
import { createHash } from 'node:crypto';
import { closeSync, fstatSync, openSync, readFileSync, realpathSync } from 'node:fs';
import { basename } from 'node:path';
import { flagOf, groups } from './native-user-args.mjs';

export const Q36_SOURCE_BASELINE = '170e0d330edd9c03b5dcddfc64b77e498387ff86';
export const Q36_CAPABILITY_REVISION = 'q36-argv-private-cache-1';
// Private-cache support is negotiated with the running engine's INFO response
// by serve/server.py, before requests are accepted. It is not a binary allowlist.
/** Release strata.exe files that contain --q36-expert-store. A digest
 * written in model settings is not consulted. The first entry is the
 * 2026-11-03 sm_120 link of hakua040-nsis-native-20261102. The second is
 * H:\Strata\releases\hakua040-native-sync-20261103\Release\strata.exe.
 * An older binary is not listed. Legacy placement stays the default. */
export const Q36_MAPPED_PACK_DIGESTS = new Set([
  // Same mapped layout, with final-prefill STOP acknowledgement fixed; 0.4.1 sm_120.
  '2dd5dbcd2874767096b9c1eb4ac4132a96f7979bcd019ec6b779f23c9dbacc0f',
  // 0.4.1 sm_120: verified mapped pack, 131072-cell READY and real requests on RTX 5060 Ti 16 GB.
  '3797f2d368360b184b055c2130ed300645a1ece20d0bdef05dd6a3ceecf7e608',
  '512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046',
  'dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5',
  // 2026-11-03 mapped-pack host pin-pool wire-up (sm_120), unsigned; kept allowed after .6
  '6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29',
  // 2026-11-04 help-honesty rebuild (--q36-expert-store in --help); .6 unsigned Q36 component / live-proven
  '64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7',
  // 2026-11-05 opt-in STRATA_Q36_HOTSPOT_PROFILE (T07 capture path); unsigned q36 side-by-side
  '907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150',
]);
export const Q36_ENGINE_DEFAULT_CONTEXT = 32768;
export const Q36_KV_BYTES_PER_CELL_PER_SEQ = 45056n;

/** Options that take one following value. */
export const Q36_VALUE_FLAGS = new Set([
  '--model', '--native', '--max-new', '--pool-workers', '--gpu', '--max-context', '--ctx',
  '--chunk', '--prefill', '--tokens', '--n', '--force', '--emb', '--dump-full-logits',
  '--bench-pp', '--bench-tg', '--mtp', '--draft-vocab', '--batch', '--slots',
  '--expert-vram', '--cpu-threads', '--expert-slots', '--hybrid-rows', '--q36-expert-store',
  '--prompt-cache', '--conversation-cache-mib',
]);
/** Options that stand alone. */
export const Q36_SWITCH_FLAGS = new Set([
  '--no-token-graph', '--greedy', '--serve', '--no-graph', '--no-warmup', '--vision', '--batch-mtp', '--private-conversation-cache',
]);
export const Q36_SUPPORTED_FLAGS = new Set([...Q36_VALUE_FLAGS, ...Q36_SWITCH_FLAGS]);

const PRIVATE_CACHE_FLAGS = new Set(['--prompt-cache', '--conversation-cache-mib']);

/** SHA-256 of a file on disk. Null when it cannot be read. A digest written in model settings is not this. */
export function q36FileSha256(path) {
  try {
    return createHash('sha256').update(readFileSync(path)).digest('hex');
  } catch {
    return null;
  }
}

export function q36MappedPackAllowed(input = {}) {
  const sha = String(input.binarySha256 ?? '').toLowerCase();
  if (!/^[0-9a-f]{64}$/.test(sha)) return false;
  const listed = new Set([...Q36_MAPPED_PACK_DIGESTS].map(item => String(item).toLowerCase()));
  for (const item of input.mappedPackDigests ?? []) listed.add(String(item).toLowerCase());
  return listed.has(sha);
}

const MAPPED_PACK_REFUSAL = 'This engine binary is not on the mapped expert-store allowlist. The launch was not switched, and the full host arena was not requested.';
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

  const privateCache = input.privacyRequired === true || [...args, ...userArgs].some(a => PRIVATE_CACHE_FLAGS.has(a.split('=')[0]) || a === '--private-conversation-cache');
  if (privateCache) {
    for (const flag of PRIVATE_CACHE_FLAGS) {
      for (const list of [args, userArgs]) {
        const occurrences = list.filter(a => a.split('=')[0] === flag);
        const at = list.indexOf(flag);
        if (occurrences.length > 1 || (occurrences.length && (at < 0 || list[at + 1] !== '0'))) {
          return fail('unsupported_setting', `${flag} must occur once with value 0 for private Qwen3.6 requests.`);
        }
      }
      if (!args.includes(flag)) {
        if (!input.privacyRequired) return fail('unsupported_setting', 'Private Qwen3.6 requests require both --prompt-cache 0 and --conversation-cache-mib 0.');
        args.push(flag, '0');
      }
    }
    if (input.privacyRequired && !args.includes('--private-conversation-cache')) args.push('--private-conversation-cache');
  }
  if (requested.persistentKv && requested.persistentKv !== 'fp32') {
    return fail('unsupported_setting', 'Qwen3.6 keeps FP32 KV for this launch. Another KV storage was not applied.');
  }
  if (requested.expertStoreMode && !['legacy', 'mapped-pack'].includes(requested.expertStoreMode)) {
    return fail('expert_store_not_available', 'The requested expert store is not part of this engine. The launch was not switched.');
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
      if (item === '--q36-expert-store' && value !== 'legacy' && value !== 'mapped-pack') {
        return fail('unsupported_setting', `${item} ${value} is not a Qwen3.6 expert store. It was not applied and the model was not started.`);
      }
      if (item === '--q36-expert-store' && value === 'mapped-pack' && !q36MappedPackAllowed(input)) {
        return fail('expert_store_not_available', MAPPED_PACK_REFUSAL);
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
  if (privateCache && (parallel > 1 || Number(batchText) > 1 || argv.includes('--batch-mtp'))) {
    return fail('q36_private_cache_parallel', 'Private Qwen3.6 requests currently run one at a time. Set parallel requests to 1.');
  }
  const warmupMode = argv.includes('--no-warmup') || requested.warmupMode === 'off' ? 'off' : 'legacy';
  let expertStoreMode = 'legacy';
  const storeAt = argv.indexOf('--q36-expert-store');
  if (storeAt >= 0) expertStoreMode = argv[storeAt + 1];
  if (requested.expertStoreMode === 'mapped-pack' && expertStoreMode === 'legacy') {
    if (!q36MappedPackAllowed(input)) return fail('expert_store_not_available', MAPPED_PACK_REFUSAL);
    argv.push('--q36-expert-store', 'mapped-pack');
    expertStoreMode = 'mapped-pack';
  } else if (requested.expertStoreMode === 'legacy' && expertStoreMode === 'mapped-pack') {
    return fail('unsupported_setting', 'The launch asked for mapped-pack and also for the legacy store. It was not started.');
  }

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
      expertStoreMode,
      privateCache,
      scopedConversationCache: argv.includes('--private-conversation-cache'),
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

/** Host arena measured for UD-Q4_K_XL on 2026-11-02: "no host memory for the experts (19195 MiB)". Not a size for every Qwen3.6 file. */
export const Q36_UD_Q4_K_XL_HOST_EXPERT_BYTES = 19195n << 20n;

function gibPhrase(bytes) {
  const gib = Number(bytes) / 1024 / 1024 / 1024;
  return (Math.round(gib * 10) / 10).toFixed(1);
}

/**
 * Legacy placement copies every expert into a private arena. For the measured UD-Q4_K_XL file,
 * refuse to start when free physical RAM cannot hold that arena plus a reserve (the larger of 4 GiB and 20% of RAM).
 * Other Qwen3.6 files stay unknown: their expert bytes are not invented.
 */
export function admitQ36LegacyPhysical({ modelName = '', availablePhysicalBytes = null, ramBytes = null } = {}) {
  if (!/q4_k_xl/i.test(String(modelName))) return { decision: 'unknown', fits: null, reason: 'expert_bytes_unknown' };
  if (availablePhysicalBytes == null || ramBytes == null) return { decision: 'unknown', fits: null, reason: 'memory_unknown' };
  let free, ram;
  try {
    free = BigInt(availablePhysicalBytes);
    ram = BigInt(ramBytes);
  } catch {
    return { decision: 'unknown', fits: null, reason: 'memory_unknown' };
  }
  if (free < 0n || ram < 0n) return { decision: 'unknown', fits: null, reason: 'memory_unknown' };
  const floor = 4n << 30n;
  const fifth = ram / 5n;
  const reserve = fifth > floor ? fifth : floor;
  const need = Q36_UD_Q4_K_XL_HOST_EXPERT_BYTES + reserve;
  if (free < need) {
    return {
      decision: 'rejected',
      fits: false,
      reason: 'physical_reserve',
      needBytes: need.toString(),
      reserveBytes: reserve.toString(),
      availableBytes: free.toString(),
      message: `Qwen3.6 UD-Q4_K_XL places about 18.7 GiB of experts in RAM with the current engine. ${gibPhrase(free)} GiB is free and ${gibPhrase(reserve)} GiB stays aside for the rest of the PC. The model was not started.`,
    };
  }
  return { decision: 'allowed', fits: true, reason: 'ok', needBytes: need.toString(), reserveBytes: reserve.toString(), availableBytes: free.toString() };
}
