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

const WARMING = new Set(['warmup_prefill', 'warmup_decode', 'warmup_spec']);

/** Coarse report of an accepted Q36_STARTUP stage. Names stay loading, warming, ready, and error. */
export function q36ReportPhase(event) {
  if (!event?.accepted) return null;
  if (event.state === 'error') return 'error';
  if (event.stage === 'engine_ready') return 'ready';
  if (WARMING.has(event.stage)) return 'warming';
  return 'loading';
}

/**
 * The engine writes Q36_STARTUP to its stderr. serve opens the run config's `log` as that stderr.
 * strata_control/runtime.py `_paths` returns `{profile}.host.log` (the owner host) and the server
 * process writes `{profile}.server.log` beside the state file. Neither of those is the engine log.
 */
export function q36EngineLogPath(cfg) {
  const log = cfg?.log;
  if (typeof log !== 'string') return null;
  const path = log.trim();
  if (!path || path.includes('\0')) return null;
  return path;
}

/** Feed one chunk of the engine log. Unknown stages are ignored. A later progress line does not clear an error. */
export function pushEngineLogChunk(prev, chunk) {
  const text = `${prev?.pending ?? ''}${chunk ?? ''}`;
  const parts = text.split('\n');
  const pending = parts.pop() ?? '';
  let startup = prev?.startup ?? null;
  let phase = prev?.phase ?? null;
  let sentence = prev?.sentence ?? null;
  let moved = false;
  for (const line of parts) {
    const event = parseQ36StartupLine(line);
    if (!event?.accepted) continue;
    const next = reduceQ36Startup(startup, event);
    if (next === startup) continue;
    startup = next;
    const reported = q36ReportPhase(next);
    if (reported) phase = reported;
    const said = q36StartupSentence(next);
    if (said && next === event) sentence = said;
    moved = true;
  }
  return { pending, startup, phase, sentence, moved };
}
