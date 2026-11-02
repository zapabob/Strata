/** Q36_STARTUP lines from strata-q36. A later progress line does not clear an error. */

const STAGES = new Set([
  'identity', 'dense_load', 'buffers', 'expert_host_alloc', 'expert_repack', 'expert_upload',
  'warmup_prefill', 'warmup_decode', 'warmup_spec', 'engine_ready',
]);
const STATES = new Set(['begin', 'progress', 'end', 'error', 'cancelled']);

const SENTENCE = {
  dense_load: 'Loading weights onto the GPU',
  buffers: 'Preparing the context',
  expert_host_alloc: 'Allocating expert memory',
  expert_repack: 'Arranging experts',
  expert_upload: 'Copying experts to the GPU',
  warmup_prefill: 'Warming the prompt path',
  warmup_decode: 'Warming decode',
  warmup_spec: 'Warming speculative decode',
  engine_ready: 'Engine ready',
};

export function parseQ36StartupLine(line) {
  const text = String(line ?? '');
  const at = text.indexOf('Q36_STARTUP');
  if (at < 0) return null;
  const fields = {};
  for (const part of text.slice(at).split(/\s+/)) {
    const eq = part.indexOf('=');
    if (eq <= 0) continue;
    fields[part.slice(0, eq)] = part.slice(eq + 1);
  }
  if (fields.schema !== '1') return null;
  const stage = fields.stage ?? null;
  const state = fields.state ?? null;
  const accepted = STAGES.has(stage) && STATES.has(state);
  const num = key => {
    if (fields[key] == null || fields[key] === 'null') return null;
    const n = Number(fields[key]);
    return Number.isFinite(n) ? n : null;
  };
  return {
    accepted,
    schema: 1,
    stage,
    state,
    elapsed_ms: num('elapsed_ms'),
    stage_elapsed_ms: num('stage_elapsed_ms'),
    error_code: fields.error_code && fields.error_code !== 'null' ? fields.error_code : null,
    generation: fields.generation && fields.generation !== 'null' ? fields.generation : null,
  };
}

/** Keep the error. Ignore a different generation. Unknown events do not move the previous one. */
export function reduceQ36Startup(prev, event) {
  if (!event?.accepted) return prev ?? null;
  if (prev?.accepted && prev.state === 'error' && event.state !== 'error') return prev;
  if (prev?.generation && event.generation && prev.generation !== event.generation) return prev;
  return event;
}

export function q36StartupSentence(event) {
  if (!event?.accepted) return null;
  const label = SENTENCE[event.stage] ?? event.stage;
  if (event.state === 'error') {
    const why = event.error_code ? `: ${event.error_code}` : '';
    return `${label} failed${why}.`;
  }
  if (event.state === 'end' && event.stage_elapsed_ms != null) return `${label} finished in ${(event.stage_elapsed_ms / 1000).toFixed(1)} s.`;
  if (event.state === 'begin' || event.state === 'progress') return `${label}…`;
  if (event.state === 'cancelled') return `${label} was cancelled.`;
  return `${label}.`;
}
