/**
 * Local models the agent can drive: native Strata instances and a running
 * Prism/TurboQuant llama-server (supervisor). Hikari-style local GGUFs live on
 * the supervisor path — without them, web_search never reaches the model.
 */

/** @param {{status:string, modelId?:string|null, port?:number|null}} engine */
export function supervisorIsReady(engine) {
  return !!engine && engine.status === 'running'
    && typeof engine.modelId === 'string' && engine.modelId
    && Number.isInteger(engine.port) && engine.port > 0;
}

/**
 * Shape one supervisor-backed instance for the agent profile.
 * @param {{status:string, modelId:string, port:number}} engine
 * @param {{authenticationKey?:()=>string|null, servingApiKey?:string|null, label?:string|null, context?:number|null, vision?:boolean}} [opts]
 */
export function supervisorLocalInstance(engine, opts = {}) {
  if (!supervisorIsReady(engine)) return null;
  const key = opts.authenticationKey?.() || opts.servingApiKey || null;
  return {
    id: `supervisor:${engine.modelId}`,
    label: opts.label || engine.modelId,
    baseUrl: `http://127.0.0.1:${engine.port}/v1`,
    // llama-server accepts any model id; inference uses "local" for this path.
    modelId: 'local',
    // Serving/unload accounting consumes the native instance shape too. A
    // supervisor route has no measured per-GPU attribution; do not invent one.
    apiModelId: 'local',
    gpus: [],
    context: Number.isFinite(opts.context) ? opts.context : undefined,
    key,
    vision: opts.vision === true,
    slots: 1,
    mcpServers: undefined,
    source: 'supervisor',
    variantId: engine.modelId,
  };
}

/** Native ready rows already shaped for the agent, plus an optional supervisor row. */
export function mergeAgentLocalInstances(nativeRows = [], supervisorRow = null) {
  const out = [];
  const seen = new Set();
  for (const row of nativeRows) {
    if (!row?.id || seen.has(row.id)) continue;
    seen.add(row.id);
    out.push(row);
  }
  if (supervisorRow?.id && !seen.has(supervisorRow.id)) out.push(supervisorRow);
  return out;
}

/** True when the agent has a local model or an API model to talk to. */
export function agentHasLocalModel({ remoteModel = false, nativeLive = false, supervisorLive = false } = {}) {
  return !!(remoteModel || nativeLive || supervisorLive);
}

export function agentSkipReason({
  agentOff = false,
  plainChat = false,
  chatId = null,
  remoteModel = false,
  nativeLive = false,
  supervisorLive = false,
} = {}) {
  if (agentOff) return 'The agent is turned off (STRATA_AGENT=off).';
  if (plainChat) return 'This chat runs without the agent.';
  if (!chatId) return 'This request did not name a chat.';
  if (!agentHasLocalModel({ remoteModel, nativeLive, supervisorLive })) {
    return 'The agent needs a loaded Strata model, a local GGUF (Prism/TurboQuant), or an API model.';
  }
  return null;
}
