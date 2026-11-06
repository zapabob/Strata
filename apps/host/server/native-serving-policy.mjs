/** Ordinary serving contracts. Weight names, compiler/GPU features and capsules are not capabilities. */
import { capture, merge, setFlag, USER_KEY } from './native-user-args.mjs';
import { q36KvFields, parseQ36KvCapabilities } from './q36-kv-capabilities.mjs';

const Q38_FAMILIES = new Set(['qwen', 'swift', 'coder', 'unsloth', 'gyro']);
export const ORDINARY_KV = ['fp16', 'int8', 'q4_0', 'k8v4'];
export const SERVING_FLAGS = {
  cache_type_k: ['--cache-type-k', '-ctk'], cache_type_v: ['--cache-type-v', '-ctv'],
  spin8_mode: ['--spin8-mode'], spin8_native_config: ['--spin8-native-config'], spin8_native_sha256: ['--spin8-native-sha256'],
};
const present = value => value !== undefined && value !== null && value !== '';
export function nativeServingPolicy(config = {}, family = null, capability = null) {
  // The saved architecture wins over the catalog; neither executable nor model filename is consulted.
  const identity = config.arch || config.family || family;
  const id = identity === 'qwen35moe' || identity === 'qwen36' ? 'q36' : identity === 'deepseek41' ? 'deepseek41'
    : identity === 'qwen4exp' || Q38_FAMILIES.has(identity) ? 'q38' : 'unknown';
  const { binarySha256, ...marker } = capability ?? {};
  const kvCapability = id === 'q36' && /^[a-f0-9]{64}$/.test(binarySha256 ?? '') &&
    parseQ36KvCapabilities(`Q36_KV_CAPABILITIES ${JSON.stringify(marker)}`) ? capability : null;
  const note = id === 'q38' ? 'Ordinary Qwen3.8 serving uses --kv. Independent K/V formats and Spin(8) capsules cannot serve requests.'
    : id === 'q36' ? 'Qwen3.6 uses negotiated FP32/FP16 storage. Unknown engines retain the legacy FP32 path. Spin(8) serving is unavailable.'
    : id === 'deepseek41' ? 'DeepSeek uses its own packed FP8 window and FP4 latent/index cache, not generic Qwen KV or Spin(8) controls.'
    : 'The serving adapter is unknown. Generic KV and Spin(8) choices are unavailable.';
  return { id, ordinaryKv: id === 'q38' ? [...ORDINARY_KV] : [], note, kvCapability };
}

const effectiveArgs = config => merge(config.args ?? [], capture(config));
export function servingValue(config, field) {
  return config[field] ?? (field in SERVING_FLAGS ? options(effectiveArgs(config), SERVING_FLAGS[field]).at(-1)?.value : null) ?? null;
}
function options(args, flags) {
  return args.flatMap((arg, i) => {
    const flag = flags.find(f => arg === f || arg.startsWith(f + '='));
    return flag ? [{ flag, value: arg === flag ? args[i + 1] : arg.slice(flag.length + 1), malformed: arg !== flag || !args[i + 1] || args[i + 1].startsWith('-') }] : [];
  });
}
export function servingSettingsIssues(config, policy, { negotiating = false } = {}) {
  const issues = [], args = effectiveArgs(config);
  const reject = (field, detail) => issues.push({ field, code: 'unsupported_serving_setting', message: `${field}: ${detail} Clear this setting before loading. ${policy.note}` });
  for (const [field, flags] of Object.entries(SERVING_FLAGS)) {
    const found = options(args, flags), value = config[field];
    if (!present(value) && !found.length) continue;
    if (policy.id !== 'q36' || field.startsWith('spin8_')) { reject(field, 'not supported by this serving adapter.'); continue; }
    // Q36's native contract uses long flags once, with matching top-level settings.
    const values = [...found.map(o => o.value), ...(present(value) ? [value] : [])];
    const choices = policy.kvCapability?.[field === 'cache_type_k' ? 'cacheTypesK' : 'cacheTypesV'] ?? (negotiating ? ['f32', 'f16'] : ['f32']);
    if (found.length > 1 || found.some(o => o.malformed || o.flag !== flags[0]) || new Set(values).size > 1 || values.some(v => !choices.includes(v)))
      reject(field, 'the format is conflicting, malformed or not verified for this engine.');
  }
  const combined = options(args, ['--kv']);
  if (combined.length && (policy.id !== 'q38' || combined.some(o => o.malformed) || !ORDINARY_KV.includes(combined.at(-1).value)))
    reject('kv', 'ordinary --kv is unsupported or has an unknown format.');
  if (policy.id === 'deepseek41') {
    for (const field of ['mtp', 'batchMtp', 'drafting']) if (present(config[field])) reject(field, 'this is a Qwen serving control.');
  } else if (present(config.ds_experts)) reject('ds_experts', 'this is a DeepSeek routing control.');
  return issues;
}
export function assertServingSettings(config, policy, options) {
  const issues = servingSettingsIssues(config, policy, options);
  if (issues.length) throw Object.assign(new Error(issues.map(i => i.message).join(' ')), { code: issues[0].code, issues });
}
export function servingSettingsView(config, policy, fields) {
  const projected = policy.id === 'q36' ? q36KvFields(fields, policy.kvCapability) : fields;
  return {
    servingPolicy: { id: policy.id, ordinaryKv: policy.ordinaryKv, note: policy.note },
    settingsIssues: servingSettingsIssues(config, policy),
    fields: projected.map(field => {
      const blocked = field.id in SERVING_FLAGS && (policy.id !== 'q36' || field.id.startsWith('spin8_')) ||
        policy.id === 'deepseek41' && ['mtp', 'batchMtp', 'drafting'].includes(field.id) || field.id === 'ds_experts' && policy.id !== 'deepseek41';
      // UI uses this actual adapter decision, not forModel's historical filename test.
      const { forModel, notForModel, ...row } = field;
      return blocked ? { ...row, supported: false, choices: [], unavailableReason: policy.note } : row;
    }),
  };
}

/** Clear all representations together, including legacy aliases; unrelated GGUF/path arguments are untouched. */
function removeFlags(args, flags) {
  const list = Array.isArray(args) ? args : [], out = [];
  for (let i = 0; i < list.length; i++) {
    const flag = flags.find(f => list[i] === f || list[i].startsWith(f + '='));
    if (!flag) out.push(list[i]);
    else if (list[i] === flag && i + 1 < list.length && !list[i + 1].startsWith('-')) i++;
  }
  return out;
}
export function applyServingPatch(config, patch) {
  const next = { ...config, ...patch };
  for (const [key, value] of Object.entries(patch)) if (value === null || value === '') {
    delete next[key];
    if (key in SERVING_FLAGS) for (const list of ['args', USER_KEY, 'args_written'])
      if (Array.isArray(next[list])) next[list] = removeFlags(next[list], SERVING_FLAGS[key]);
  }
  return next;
}
export function applyOrdinaryKv(config, kv, policy) {
  if (kv === undefined) return config;
  if (!policy.ordinaryKv.includes(kv)) throw Object.assign(new Error(`kv: choose a supported ordinary serving format. ${policy.note}`), { code: 'unsupported_serving_setting' });
  const next = { ...config, args: setFlag(config.args, '--kv', kv) };
  // An explicit current choice replaces an older explicit choice, not unrelated user arguments.
  if (Array.isArray(config[USER_KEY])) next[USER_KEY] = setFlag(removeFlags(config[USER_KEY], ['--kv']), '--kv', kv);
  if (Array.isArray(config.args_written)) next.args_written = setFlag(config.args_written, '--kv', kv);
  return next;
}

export function persistOrdinaryKv(current, original, kv, policy) {
  if (kv === undefined) return current;
  const selection = cfg => JSON.stringify(options(effectiveArgs(cfg), ['--kv']));
  // A later explicit file edit owns its KV, just as it owns its other future settings.
  return selection(current) === selection(original) ? applyOrdinaryKv(current, kv, policy) : current;
}
