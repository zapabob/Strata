/**
 * Architecture-aware hybrid memory estimator (PR-B).
 *
 * Separates Full-Attention KV (context-growing) from Recurrent/SSM state
 * (fixed-size). GGUF disk bytes are never treated as GPU weight allocation.
 * Unknown layouts stay null / confidence=low; fits is never claimed from
 * optimistic arithmetic alone.
 */
import { createHash } from 'node:crypto';

export const GiB = 1024 ** 3;

/** GGML block element sizes used by KV cache rows (Prism ggml-common.h). */
const GGML_BLOCK = Object.freeze({
  f32: { typeSize: 4, blockSize: 1 },
  f16: { typeSize: 2, blockSize: 1 },
  bf16: { typeSize: 2, blockSize: 1 },
  q8_0: { typeSize: 34, blockSize: 32 },
  q4_0: { typeSize: 18, blockSize: 32 },
});

const HYBRID_ARCH = new Set(['qwen35', 'qwen35moe', 'qwen3next']);

function positiveInt(value, max = Number.MAX_SAFE_INTEGER) {
  return Number.isInteger(value) && value >= 1 && value <= max ? value : null;
}

function asIntArray(value) {
  if (Array.isArray(value) && value.every(v => Number.isInteger(v))) return value;
  if (value && typeof value === 'object' && Array.isArray(value.values)
    && value.values.every(v => Number.isInteger(v))) return value.values;
  return null;
}

/** Bytes for one contiguous GGML-typed row of `elements` values. */
export function ggmlRowBytes(type, elements) {
  const key = String(type ?? '').toLowerCase();
  const block = GGML_BLOCK[key];
  if (!block) {
    const error = new Error(`Unsupported cache type: ${String(type)}`);
    error.code = 'KV_UNSUPPORTED_TYPE';
    throw error;
  }
  const n = Number(elements);
  if (!Number.isFinite(n) || n <= 0) throw new Error('row element count must be a positive number');
  if (n % block.blockSize !== 0) {
    // KV heads×dim that are not block-aligned still round up to whole blocks.
    const blocks = Math.ceil(n / block.blockSize);
    return blocks * block.typeSize;
  }
  return (n / block.blockSize) * block.typeSize;
}

/**
 * Classify Full-Attention vs Recurrent layers.
 * Prefer `attention.recurrent_layers` when present and consistent; otherwise
 * use `full_attention_interval` with Prism/Strata indexing
 * (`layer % interval === interval - 1`).
 */
export function classifyHybridLayers({ nLayerAll, fullAttentionInterval = null, recurrentLayers = null } = {}) {
  const n = positiveInt(nLayerAll, 4096);
  if (n === null) {
    return { nFullAttention: null, nRecurrent: null, confidence: 'low', source: 'invalid', reason: 'block_count missing or invalid' };
  }

  const recurrent = asIntArray(recurrentLayers);
  if (recurrent) {
    const unique = [...new Set(recurrent)];
    const inRange = unique.every(i => i >= 0 && i < n);
    if (!inRange || unique.length !== recurrent.length) {
      return {
        nFullAttention: null,
        nRecurrent: null,
        confidence: 'low',
        source: 'attention.recurrent_layers',
        reason: 'recurrent_layers has duplicates or out-of-range indices',
      };
    }
    if (unique.length >= n) {
      return {
        nFullAttention: null,
        nRecurrent: null,
        confidence: 'low',
        source: 'attention.recurrent_layers',
        reason: 'recurrent_layers covers every layer (no attention KV layers)',
      };
    }
    // Size mismatch against interval-derived expectation → unknown, do not invent.
    const interval = positiveInt(fullAttentionInterval, 4096);
    if (interval !== null && n % interval === 0) {
      const expectedRecurrent = n - Math.floor(n / interval);
      if (unique.length !== expectedRecurrent) {
        return {
          nFullAttention: null,
          nRecurrent: null,
          confidence: 'low',
          source: 'attention.recurrent_layers',
          reason: `recurrent_layers length ${unique.length} disagrees with full_attention_interval expectation ${expectedRecurrent}`,
        };
      }
    }
    return {
      nFullAttention: n - unique.length,
      nRecurrent: unique.length,
      confidence: 'high',
      source: 'attention.recurrent_layers',
      reason: null,
      recurrentIndices: unique.slice().sort((a, b) => a - b),
    };
  }

  const interval = positiveInt(fullAttentionInterval, 4096);
  if (interval !== null && interval >= 2 && n % interval === 0) {
    let nFull = 0;
    for (let layer = 0; layer < n; layer++) {
      if (layer % interval === interval - 1) nFull += 1;
    }
    return {
      nFullAttention: nFull,
      nRecurrent: n - nFull,
      confidence: 'high',
      source: 'full_attention_interval',
      reason: null,
    };
  }

  if (interval !== null) {
    return {
      nFullAttention: null,
      nRecurrent: null,
      confidence: 'low',
      source: 'full_attention_interval',
      reason: 'block_count is not a multiple of full_attention_interval',
    };
  }

  // Non-hybrid / unknown: treat every layer as attention (legacy upper bound).
  return {
    nFullAttention: n,
    nRecurrent: 0,
    confidence: 'low',
    source: 'legacy_all_layers',
    reason: 'no hybrid layer map; counting every layer as attention KV (upper bound)',
  };
}

export function extractHybridGeometry(metadata = {}) {
  const m = metadata && typeof metadata === 'object' ? metadata : {};
  const arch = typeof m['general.architecture'] === 'string' ? m['general.architecture'] : null;
  const prefix = arch ?? '';
  const nLayerAll = positiveInt(m[`${prefix}.block_count`], 4096);
  const interval = positiveInt(m[`${prefix}.full_attention_interval`], 4096);
  const recurrentLayers = asIntArray(m[`${prefix}.attention.recurrent_layers`])
    ?? asIntArray(m['attention.recurrent_layers']);
  const layers = classifyHybridLayers({
    nLayerAll,
    fullAttentionInterval: interval,
    recurrentLayers,
  });
  const heads = positiveInt(m[`${prefix}.attention.head_count`], 8192);
  const nKvHeads = m[`${prefix}.attention.head_count_kv`] === undefined
    ? heads
    : positiveInt(m[`${prefix}.attention.head_count_kv`], 8192);
  const keyLength = positiveInt(m[`${prefix}.attention.key_length`], 1_000_000);
  const valueLength = m[`${prefix}.attention.value_length`] === undefined
    ? keyLength
    : positiveInt(m[`${prefix}.attention.value_length`], 1_000_000);
  const contextLimit = positiveInt(m[`${prefix}.context_length`], 100_000_000);
  const hybrid = HYBRID_ARCH.has(arch) || interval !== null || recurrentLayers !== null;
  let confidence = layers.confidence;
  if (!arch || nLayerAll === null || nKvHeads === null || keyLength === null || valueLength === null) {
    confidence = 'low';
  } else if (hybrid && confidence === 'high') {
    confidence = 'high';
  } else if (!hybrid) {
    confidence = 'low';
  }
  return {
    architecture: arch,
    nLayerAll,
    nFullAttention: layers.nFullAttention,
    nRecurrent: layers.nRecurrent,
    fullAttentionInterval: interval,
    nKvHeads,
    keyLength,
    valueLength,
    contextLimit,
    ssm: {
      stateSize: positiveInt(m[`${prefix}.ssm.state_size`], 1_000_000),
      groupCount: positiveInt(m[`${prefix}.ssm.group_count`], 1_000_000),
      timeStepRank: positiveInt(m[`${prefix}.ssm.time_step_rank`], 1_000_000),
      innerSize: positiveInt(m[`${prefix}.ssm.inner_size`], 10_000_000),
    },
    confidence,
    layerSource: layers.source,
    layerReason: layers.reason,
    metadataSignature: createHash('sha256').update(JSON.stringify(m)).digest('hex'),
  };
}

export function estimateAttentionKvBytes({
  context,
  sequences = 1,
  nFullAttention,
  nKvHeads,
  keyLength,
  valueLength,
  kType,
  vType,
} = {}) {
  const ctx = positiveInt(context, 100_000_000);
  const seq = positiveInt(sequences, 1024);
  const layers = positiveInt(nFullAttention, 4096);
  const kvh = positiveInt(nKvHeads, 8192);
  const kd = positiveInt(keyLength, 1_000_000);
  const vd = positiveInt(valueLength, 1_000_000);
  if ([ctx, seq, layers, kvh, kd, vd].some(v => v === null)) return null;
  // Guard absurd dimensions that would overflow safe integers.
  const perToken = layers * (
    ggmlRowBytes(kType, kvh * kd) + ggmlRowBytes(vType, kvh * vd)
  );
  const total = ctx * seq * perToken;
  if (!Number.isFinite(total) || total < 0 || total > Number.MAX_SAFE_INTEGER) return null;
  return total;
}

/**
 * Full estimate plan. `fits` stays null unless a future planner supplies a
 * measured VRAM budget and explicit safety margin (PR-D).
 */
export function estimateModelMemory({
  metadata,
  diskBytes = null,
  context,
  sequences = 1,
  kType = 'q8_0',
  vType = 'q8_0',
} = {}) {
  const geo = extractHybridGeometry(metadata);
  const attentionKvBytes = (geo.nFullAttention !== null && geo.nKvHeads && geo.keyLength && geo.valueLength)
    ? estimateAttentionKvBytes({
      context,
      sequences,
      nFullAttention: geo.nFullAttention,
      nKvHeads: geo.nKvHeads,
      keyLength: geo.keyLength,
      valueLength: geo.valueLength,
      kType,
      vType,
    })
    : null;

  const notes = [];
  if (geo.layerReason) notes.push(geo.layerReason);
  if (attentionKvBytes !== null) {
    notes.push(`Attention KV theoretical ${Number((attentionKvBytes / GiB).toFixed(3))} GiB `
      + `(${geo.nFullAttention} full-attention layers; recurrent excluded)`);
  } else {
    notes.push('Attention KV could not be computed from metadata');
  }
  notes.push('GGUF disk bytes are not GPU weight allocation');
  notes.push('Recurrent/SSM state requires backend-specific layout; left null');

  const disk = Number.isFinite(diskBytes) && diskBytes >= 0 ? diskBytes : null;

  return {
    architecture: geo.architecture,
    metadataSignature: geo.metadataSignature,
    nLayerAll: geo.nLayerAll,
    nFullAttention: geo.nFullAttention,
    nRecurrent: geo.nRecurrent,
    nKvHeads: geo.nKvHeads,
    keyLength: geo.keyLength,
    valueLength: geo.valueLength,
    contextLimit: geo.contextLimit,
    contextRequested: positiveInt(context, 100_000_000),
    kType,
    vType,
    diskBytes: disk,
    weightsAllocatedBytes: null,
    attentionKvBytes,
    attentionKvGiB: attentionKvBytes === null ? null : Number((attentionKvBytes / GiB).toFixed(3)),
    recurrentBytes: null,
    workspaceBytes: null,
    reserveBytes: null,
    confidence: geo.confidence,
    layerSource: geo.layerSource,
    fits: null,
    notes,
  };
}

/** KiB per token for Attention-only KV at FP16 element width (legacy field shape). */
export function hybridKvKbPerToken(geometry) {
  if (!geometry || geometry.nFullAttention === null || !geometry.nKvHeads
    || !geometry.keyLength || !geometry.valueLength) return null;
  // Legacy local-models field assumed FP16 element size (= 2 bytes) without block format.
  // Keep that unit so existing UI math stays comparable; prefer estimateAttentionKvBytes for budgets.
  return geometry.nFullAttention * geometry.nKvHeads
    * (geometry.keyLength + geometry.valueLength) / 1024;
}
