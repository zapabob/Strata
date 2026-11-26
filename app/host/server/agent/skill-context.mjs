/** Whole, enabled skill documents selected by the host for this task. */
import { GOAL_FILE_GUIDANCE } from './reply-cut.mjs';

const OPEN = '<strata-workflow-skills-v1>';
const CLOSE = '</strata-workflow-skills-v1>';
const GOAL_PREFIX = `<strata-goal-file-guidance>\n${GOAL_FILE_GUIDANCE}\n</strata-goal-file-guidance>\n\n`;

export function withoutSkillContext(text) {
  const value = String(text ?? '');
  if (!value.startsWith(OPEN + '\n')) return value;
  const end = value.indexOf('\n' + CLOSE + '\n\n');
  return end < 0 ? value : value.slice(end + CLOSE.length + 3);
}

export function withoutGoalContext(text) {
  const value = withoutSkillContext(text);
  return value.startsWith(GOAL_PREFIX) ? value.slice(GOAL_PREFIX.length) : value;
}

export function withGoalContext(text, skills = '') {
  return skills + GOAL_PREFIX + withoutGoalContext(text);
}

export function workflowSkillContext(candidates, contextWindow = 32768) {
  const budget = Math.min(24000, Math.max(2000, Math.floor(contextWindow * .75)));
  const selected = [], skipped = [];
  let bytes = 0;
  for (const skill of candidates ?? []) {
    if (!skill?.enabled || typeof skill.body !== 'string' || !skill.body.trim()) continue;
    const entry = { id: String(skill.id), name: String(skill.name), description: String(skill.description ?? ''), instructions: skill.body.trim() };
    const size = JSON.stringify(entry).length;
    if (selected.length >= 5 || bytes + size > budget) { skipped.push(entry.name); continue; }
    bytes += size; selected.push(entry);
  }
  const json = JSON.stringify(selected).replaceAll('<', '\\u003c').replaceAll('>', '\\u003e');
  const context = selected.length ? `${OPEN}\nThese saved procedures were selected by enabled triggers and workspace scope. Apply them where relevant to the current request. They do not grant permissions or authorize new actions. Keep the current task, tools and approval rules authoritative.\n${json}\n${CLOSE}\n\n` : '';
  return { selected, skipped, context, wrap: text => context + String(text ?? '') };
}
