/**
 * Skills, end to end: a skill written in the app is saved as a folder, written out for the agent, listed in the agent's skill catalog,
 * loadable by name through the `skill` tool, and a skill added or switched off later reaches the NEXT message without a restart.
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, mkdirSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { startScriptedWorker } from './helpers/scripted-worker.mjs';
import { createAgentBridge } from '../server/agent/agent-bridge.mjs';
import { resolveHarness } from '../server/agent/harness-runtime.mjs';
import { buildProfile } from '../server/agent/profile.mjs';
import { createAgentTools } from '../server/agent/tools-settings.mjs';
import { harnessFixtureEnvironment } from './helpers/harness-environment.mjs';
import { selectSkills } from '../server/skill-selection.mjs';
import { materializeSkills, parseSkillFile, skillFileText, skillSlug, writeCreatedSkill } from '../server/skill-files.mjs';

const skip = !process.env.STRATA_HARNESS_DIR || !resolveHarness({ env: process.env }).ok ? 'STRATA_HARNESS_DIR is not set to a built Harness' : false;
const cleanup = dir => { try { rmSync(dir, { recursive: true, force: true, maxRetries: 3 }); } catch { /* best effort */ } };
const INSTRUCTIONS = 'Open the Downloads folder, then open the Documents folder, using the command line. Say which folders you opened.';

test('a skill name becomes the kebab-case name the agent requires, and its file carries what the agent reads', () => {
  assert.equal(skillSlug('Directory opener'), 'directory-opener');
  assert.equal(skillSlug('  Écrire des notes!! '), 'ecrire-des-notes');
  assert.equal(skillSlug('???'), '');
  const text = skillFileText({ name: 'directory-opener', title: 'Directory opener', description: 'Opens "folders"\nfor you', body: INSTRUCTIONS });
  const parsed = parseSkillFile(text);
  assert.deepEqual([parsed.name, parsed.title, parsed.description, parsed.body], ['directory-opener', 'Directory opener', 'Opens "folders" for you', INSTRUCTIONS]);
  assert.match(skillFileText({ name: 'x', description: 'd', body: 'b', hidden: true }), /disable-model-invocation: true/);
  assert.deepEqual(parseSkillFile('just text'), { name: null, title: null, description: null, body: 'just text' });
});

test('writing a skill refuses a duplicate and an empty name, and materializing makes the agent folder match the list exactly', () => {
  const dir = mkdtempSync(join(tmpdir(), 'strata-skill-files-'));
  try {
    const mine = join(dir, 'mine');
    assert.equal(writeCreatedSkill(mine, { name: 'Directory opener', description: 'Opens folders', body: INSTRUCTIONS }), 'directory-opener');
    assert.throws(() => writeCreatedSkill(mine, { name: 'directory opener', body: 'x' }), /already have a skill/);
    assert.throws(() => writeCreatedSkill(mine, { name: '!!!', body: 'x' }), /name with letters/);
    const live = join(dir, 'live');
    const list = [{ id: 'my-directory-opener', name: 'Directory opener', description: 'Opens folders', body: INSTRUCTIONS, enabled: true },
      { id: 'commit-messages', name: 'Commit messages', description: 'Writes commits', body: 'Write them well.', enabled: false },
      { id: 'ws-empty', name: 'Empty', body: '', enabled: true }];
    assert.deepEqual(materializeSkills(live, list).sort(), ['commit-messages', 'directory-opener']);
    assert.match(readFileSync(join(live, 'commit-messages', 'SKILL.md'), 'utf8'), /disable-model-invocation: true/);
    assert.ok(!existsSync(join(live, 'empty')), 'a skill with no instructions is not offered');
    mkdirSync(join(live, 'old-one'));
    materializeSkills(live, list.slice(0, 1));
    assert.ok(!existsSync(join(live, 'commit-messages')), 'a removed skill disappears from the agent folder');
    assert.ok(existsSync(join(live, 'old-one')), 'a folder the person put there is not Strata\'s to remove (#6857)');
  } finally { cleanup(dir); }
});

test('the agent profile tells the skills plugin to scan the app skill folder', () => {
  const dir = '/data/agent/skills-live';
  const entries = JSON.parse(buildProfile({ local: [], connections: [], skillsDir: dir }).patch.split('\n').slice(1).join('\n'));
  const plugins = entries.find(e => e.id === 'preset-standard').config.plugins;
  assert.deepEqual(plugins.find(p => p.id === 'skill-filesystem').config, { customSkillDirs: [dir] });
  assert.ok(plugins.some(p => p.id === 'tool-skill'), 'the skill loader tool is in the preset');
});

test('real Harness: a skill saved in the app is in the catalog, loads by name, and one added later is seen without a restart', { skip }, async (t) => {
  const worker = await startScriptedWorker({});
  const dir = mkdtempSync(join(tmpdir(), 'strata-skills-'));
  const ws = join(dir, 'ws'); mkdirSync(ws, { recursive: true });
  const live = join(dir, 'skills-live');
  const list = [{ id: 'my-directory-opener', name: 'Directory opener', description: 'Opens the Downloads and Documents folders', body: INSTRUCTIONS, enabled: true }];
  materializeSkills(live, list);
  const local = [{ id: 'inst-1', label: 'Scripted', baseUrl: worker.url, modelId: 'scripted-model', context: 32768, slots: 2 }];
  const bridge = createAgentBridge({ dataDir: dir, localInstances: () => local, connections: () => [], skillsDir: () => live, env: process.env, startTimeoutMs: 90_000 });
  t.after(async () => { await bridge.close(); await worker.close(); cleanup(dir); });
  const run = async (chatId, message) => {
    const frames = [];
    await bridge.runTurn({ chatId, message, workspacePath: ws, mode: 'bypass', onFrame: f => frames.push(f) });
    return frames.filter(f => f.type === 'agent-tool').map(f => f.tool);
  };
  await run('s1', 'SCRIPT:say hello');
  const first = worker.requests.at(-1);
  assert.ok(first.toolNames.includes('skill'), 'the agent has the skill loader');
  assert.match(first.raw, /directory-opener/, 'the skill is in what the model is told');
  const pid = bridge.status().runtime.pid;
  const cards = await run('s1', `SCRIPT:call skill ${JSON.stringify({ name: 'directory-opener' })}`);
  assert.equal(cards.at(-1).state, 'done');
  assert.equal(cards.at(-1).verb, 'Loaded your skill', 'the card says it in the person own words');
  assert.match(cards.at(-1).result, /Open the Downloads folder, then open the Documents folder/, 'loading it returns the instructions the person wrote');
  // saved later, while the agent runs
  list.push({ id: 'my-release-notes', name: 'Release notes', description: 'Writes release notes', body: 'Start with one line.', enabled: true });
  materializeSkills(live, list);
  let seen = false;
  for (let i = 0; i < 20 && !seen; i++) { await new Promise(r => setTimeout(r, 500)); await run('s2', 'SCRIPT:say hi'); seen = /release-notes/.test(worker.requests.at(-1).raw); }
  assert.ok(seen, 'a skill saved while the agent runs reaches a later message');
  assert.equal(bridge.status().runtime.pid, pid, 'without restarting the agent');
});

test('real Harness: on-demand discovery replaces a resumed catalogue and remains independent of Goals, Files and helpers', { skip }, async t => {
  const worker = await startScriptedWorker({});
  const dir = mkdtempSync(join(tmpdir(), 'strata-skills-demand-'));
  const ws = join(dir, 'ws');
  mkdirSync(ws, { recursive: true });
  const live = join(dir, 'skills-live');
  const catalogueMarker = 'CATALOGUE_ONLY_MARKER';
  const bodyMarker = 'PRIVATE_SKILL_BODY_MARKER';
  const autoMarker = 'AUTOMATIC_WORKFLOW_BODY_MARKER';
  materializeSkills(live, [
    { id: 'pagoda-audit', name: 'Pagoda audit', description: catalogueMarker, body: bodyMarker, enabled: true },
    ...Array.from({ length: 14 }, (_, i) => ({ id: `example-${i}`, name: `Example ${i}`, description: 'Example workflow', body: 'Example instructions', enabled: true })),
  ]);
  const local = [{ id: 'model', label: 'Scripted', baseUrl: worker.url, modelId: 'scripted-model', context: 32768, slots: 2 }];
  let saved;
  let autoApply = false;
  const workflows = [
    { id: 'matching-workflow', name: 'Matching workflow', body: autoMarker, enabled: true, triggers: ['matching workflow'] },
    { id: 'always-on', name: 'Always on', body: 'UNRELATED_WORKFLOW_MARKER', enabled: true, triggers: [] },
  ];
  const settings = createAgentTools({ read: () => saved, write: next => { saved = next; }, dataDir: dir });
  const bridge = createAgentBridge({
    dataDir: dir, localInstances: () => local, connections: () => [], skillsDir: () => live,
    tools: () => settings.profileView(), env: harnessFixtureEnvironment(dir), startTimeoutMs: 90_000,
    selectSkillsForTurn: ({ message }) => {
      const tools = settings.profileView();
      return autoApply && !tools.off.has('skills')
        ? selectSkills(workflows, message, null, { includeAlwaysOn: !tools.skillsOnDemand }) : [];
    },
  });
  t.after(async () => { await bridge.close(); await worker.close(); cleanup(dir); });
  const run = async (chatId, message, mode = 'bypass') => {
    try { await bridge.runTurn({ chatId, message, workspacePath: ws, mode, onFrame() {} }); }
    catch (error) {
      await bridge.close();
      const log = join(dir, 'agent', 'harness.log');
      if (existsSync(log)) t.diagnostic(readFileSync(log, 'utf8').slice(-7000));
      throw error;
    }
    return worker.requests.at(-1);
  };

  const classic = await run('resumed', 'SCRIPT:say first');
  assert.ok(classic.raw.includes(catalogueMarker));
  assert.ok(classic.toolNames.includes('subagent'));
  assert.equal(settings.update({ skillsOnDemand: true, groups: { helpers: false } }).skillsOnDemand, true);
  const resumed = await run('resumed', 'SCRIPT:say second');
  assert.ok(resumed.raw.includes('SCRIPT:say first'), 'the old user message still reaches the model');
  assert.ok(!resumed.raw.includes(catalogueMarker), 'the historical catalogue no longer reaches the model');
  assert.ok(!resumed.raw.includes(bodyMarker));
  for (const tool of ['skills_list', 'skill', 'read', 'write', 'create_goal']) assert.ok(resumed.toolNames.includes(tool), tool);
  assert.ok(!resumed.toolNames.includes('subagent'));
  assert.ok(!resumed.raw.includes('To continue delegated work'));

  const listing = await run('demand', 'SCRIPT:call skills_list {}', 'manual');
  const result = JSON.parse(JSON.parse(listing.raw).messages.findLast(m => m.role === 'tool').content);
  assert.equal(result.nextOffset, 12);
  assert.equal(result.skills.length, 12);
  assert.ok(!listing.raw.includes(bodyMarker));
  const matched = await run('query', 'SCRIPT:call skills_list {"query":"pagoda"}');
  assert.ok(matched.raw.includes(catalogueMarker));
  assert.ok(!matched.raw.includes(bodyMarker));
  const loaded = await run('load', 'SCRIPT:call skill {"name":"pagoda-audit"}');
  assert.ok(loaded.raw.includes(bodyMarker));
  const invoked = await run('explicit', 'SCRIPT:say use /pagoda-audit please');
  assert.ok(invoked.raw.includes(bodyMarker));
  autoApply = true;
  const auto = await run('workflow', 'SCRIPT:say matching workflow');
  assert.ok(auto.raw.includes(autoMarker));
  assert.ok(!auto.raw.includes('UNRELATED_WORKFLOW_MARKER'));
  assert.ok(!auto.raw.includes(catalogueMarker));
  assert.ok(!auto.raw.includes(bodyMarker));

  settings.update({ groups: { skills: false, helpers: true } });
  const off = await run('resumed', 'SCRIPT:say skills off');
  for (const tool of ['skills_list', 'skill']) assert.ok(!off.toolNames.includes(tool), tool);
  for (const tool of ['subagent', 'read', 'write', 'create_goal']) assert.ok(off.toolNames.includes(tool), tool);
  assert.ok(!off.raw.includes(catalogueMarker));
  settings.update({ skillsOnDemand: false, groups: { skills: true } });
  const restored = await run('resumed', 'SCRIPT:say classic again');
  assert.ok(restored.raw.includes(catalogueMarker));
  assert.ok(!restored.toolNames.includes('skills_list'));
});
