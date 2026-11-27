/**
 * Skills on disk, for the app and for the agent.
 *
 * The app keeps the skills a person writes in its own folder (`<data>/skills/<id>/SKILL.md`). The agent (the Harness) finds skills by scanning
 * folders of `<name>/SKILL.md` files whose frontmatter has a kebab-case `name` and a `description`. So the app also writes the whole current
 * list (bundled, written, added, edited, switched on or off) into one folder the Harness is told to scan (`materializeSkills`), every time
 * anything changes. The Harness watches that folder, so a skill saved in the app is there for the next message without a restart.
 */
import { copyFileSync, cpSync, existsSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

const COPIED = '.strata-copied.json';
export const SKILL_EXTRAS_LIMITS = { files: 500, bytes: 64 * 1024 * 1024, depth: 6, file: 16 * 1024 * 1024 };

function extraTarget(root, relative) {
  if (typeof relative !== 'string') return null;
  const parts = relative.split('/');
  if (parts.some(part => !part || part.startsWith('.') || /[\\:\x00]/.test(part))
      || (parts.length === 1 && /^skill\.md$/i.test(parts[0]))) return null;
  let path = root;
  if (lstatSync(path, { throwIfNoEntry: false })?.isSymbolicLink()) return null;
  for (let i = 0; i < parts.length; i++) {
    path = join(path, parts[i]);
    const entry = lstatSync(path, { throwIfNoEntry: false });
    if (entry?.isSymbolicLink() || (entry && i < parts.length - 1 && !entry.isDirectory())) return null;
  }
  return path;
}

/** Materialise bounded, ordinary companion files for workspace skills on the agent's skill path. */
export function copySkillExtras(from, to, limits = SKILL_EXTRAS_LIMITS) {
  const copied = [];
  let bytes = 0;
  if (lstatSync(to, { throwIfNoEntry: false })?.isSymbolicLink()) return copied;
  const walk = (dir, prefix, depth) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      if (copied.length >= limits.files) break;
      if (entry.name.startsWith('.') || entry.name === 'node_modules') continue;
      const relative = prefix + entry.name;
      const source = join(dir, entry.name);
      if (entry.isDirectory() && depth < limits.depth) walk(source, relative + '/', depth + 1);
      if (!entry.isFile()) continue;
      const target = extraTarget(to, relative);
      if (!target) continue;
      const original = lstatSync(source, { throwIfNoEntry: false });
      if (!original?.isFile() || original.size > limits.file || bytes + original.size > limits.bytes) continue;
      const previous = lstatSync(target, { throwIfNoEntry: false });
      if (previous && !previous.isFile()) continue;
      if (!previous || previous.size !== original.size || previous.mtimeMs < original.mtimeMs) {
        mkdirSync(dirname(target), { recursive: true });
        copyFileSync(source, target);
      }
      copied.push(relative);
      bytes += original.size;
    }
  };
  walk(from, '', 0);
  const record = join(to, COPIED);
  if (lstatSync(record, { throwIfNoEntry: false })?.isSymbolicLink()) return copied;
  let previous = '';
  try { previous = readFileSync(record, 'utf8'); } catch { /* first copy */ }
  const next = JSON.stringify(copied);
  if (previous === next) return copied;
  let managed = [];
  try { managed = JSON.parse(previous); } catch { /* malformed records own no files */ }
  const kept = new Set(copied);
  for (const relative of Array.isArray(managed) ? managed : []) {
    if (kept.has(relative)) continue;
    const target = extraTarget(to, relative);
    if (target && lstatSync(target, { throwIfNoEntry: false })?.isFile()) rmSync(target);
  }
  mkdirSync(to, { recursive: true });
  writeFileSync(record, next);
  return copied;
}

/** The kebab-case name the Harness requires, from what a person typed ("Directory opener" -> "directory-opener"). */
export function skillSlug(name) {
  return String(name ?? '').toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60);
}

const yamlText = value => JSON.stringify(String(value ?? '').replace(/\s+/g, ' ').trim());

/** `SKILL.md` text: the frontmatter the Harness reads, then the instructions. */
export function skillFileText({ name, title = null, description, body, hidden = false }) {
  return `---\nname: ${skillSlug(name)}\n${title ? `title: ${yamlText(title)}\n` : ''}description: ${yamlText(description || name)}\n${hidden ? 'disable-model-invocation: true\n' : ''}---\n\n${String(body ?? '').trim()}\n`;
}

/** Name, description and instructions out of a SKILL.md (frontmatter optional). */
export function parseSkillFile(text) {
  const raw = String(text ?? '').replace(/^﻿/, '').replace(/\r\n/g, '\n');
  const m = /^---\n([\s\S]*?)\n---\n?/.exec(raw);
  if (!m) return { name: null, title: null, description: null, body: raw.trim() };
  const field = key => {
    const line = new RegExp(`^${key}:[ \t]*(.*)$`, 'mi').exec(m[1])?.[1]?.trim();
    if (line === undefined) return null;
    try { if (/^["']/.test(line)) return typeof JSON.parse(line.replace(/^'(.*)'$/, '"$1"')) === 'string' ? JSON.parse(line.replace(/^'(.*)'$/, '"$1"')) : line; } catch { /* plain scalar */ }
    return line;
  };
  return { name: field('name'), title: field('title'), description: field('description'), body: raw.slice(m[0].length).trim() };
}

/** Stage outside the discovery root, commit preferences, then publish the file.
 * A crash or cleanup failure before publication cannot expose instructions with
 * default permissions. Rollback failure leaves only inert saved preferences. */
export function writeCreatedSkill(root, { name, title = name, description, body }, { beforePublish = () => {}, rollback = () => {} } = {}) {
  const id = skillSlug(name);
  if (!id) throw new Error('Give the skill a name with letters or numbers in it.');
  const dir = join(root, id);
  if (existsSync(dir)) throw new Error(`You already have a skill called "${id}". Choose another name, or edit the one you have.`);
  mkdirSync(root, { recursive: true });
  const staged = mkdtempSync(join(dirname(root), '.skill-'));
  let prepared = false;
  try {
    writeFileSync(join(staged, 'SKILL.md'), skillFileText({ name: id, title: String(title).trim(), description, body }), { mode: 0o600, flush: true });
    beforePublish(id);
    prepared = true;
    if (existsSync(dir)) throw new Error(`You already have a skill called "${id}". Choose another name, or edit the one you have.`);
    renameSync(staged, dir);
    return id;
  } catch (error) {
    if (prepared) {
      try { rollback(id); }
      catch (rollbackError) { throw new AggregateError([error, rollbackError], 'The skill was not imported. Its unused saved preferences could not be restored.'); }
    }
    throw error;
  } finally {
    try { rmSync(staged, { recursive: true, force: true }); } catch { /* outside discovery; never remove an existing skill as rollback */ }
  }
}

/**
 * Make `root` hold exactly the skills the agent may use: one folder each, a SKILL.md with frontmatter. A skill switched off is written
 * with `disable-model-invocation` (the agent does not offer it). Folders of skills that are gone are moved to `skills-removed` next to `root`, but only
 * folders Strata wrote (named in `.strata-skills.json`, or holding `.strata-copied.json`): a folder the person put in `root` is never removed, and a
 * skill whose name it shares is written under another name (#6857). Only this folder is touched.
 * A skill that comes from a folder of its own (`folders`: skill id -> that folder) brings the rest of the folder along (`copySkillExtras`).
 * @param {string} root
 * @param {Array<{id: string, name: string, description?: string, body?: string, enabled?: boolean}>} skills
 * @param {Map<string, string>|Record<string, string>} [folders]
 */
export function materializeSkills(root, skills, folders = {}) {
  mkdirSync(root, { recursive: true });
  const manifest = readOwned(root);
  const keep = new Set();
  for (const s of skills) {
    const slug = skillSlug(s.id.replace(/^(?:ws|my)-/, '') || s.name);
    if (!slug || !s.body?.trim()) continue;
    let unique = slug, n = 2;
    // A folder the person put here by hand is theirs: a skill with the same name goes under another name instead of over it (#6857).
    while (keep.has(unique) || isForeign(root, unique, manifest)) unique = `${slug}-${n++}`;
    keep.add(unique);
    const dir = join(root, unique);
    mkdirSync(dir, { recursive: true });
    const text = skillFileText({ name: unique, description: `${s.name}. ${s.description ?? ''}`.trim(), body: s.body, hidden: s.enabled === false });
    const file = join(dir, 'SKILL.md');
    // Only a changed skill is rewritten: the agent watches this folder and treats every write as a change to its list.
    let same = false; try { same = readFileSync(file, 'utf8') === text; } catch { /* not there yet */ }
    if (!same) writeFileSync(file, text);
    const source = folders instanceof Map ? folders.get(s.id) : Object.hasOwn(folders ?? {}, s.id) ? folders[s.id] : undefined;
    if (source) {
      try { copySkillExtras(source, dir); }
      catch (error) { console.warn(`skills · could not copy companion files for ${unique}:`, error.message); }
    }
  }
  // Only a folder Strata wrote is ever taken away, and it is moved aside, not deleted (#6857). Everything else in this folder is the person's.
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory() || keep.has(entry.name) || !isOwned(root, entry.name, manifest)) continue;
    try { moveAside(root, entry.name); } catch (e) { console.warn(`skills · could not move the folder of the removed skill "${entry.name}" aside; it stays:`, e.message); }
  }
  writeOwned(root, [...keep]);
  return [...keep];
}

/** The note the agent skills folder keeps of the folders Strata wrote in it. Not a folder, so the agent's scan skips it. */
const OWNED = '.strata-skills.json';
/** Where a removed skill's folder goes: next to the agent skills folder, outside what the agent scans. */
export const SKILLS_REMOVED = 'skills-removed';
const KEEP_REMOVED = 40;

/** The folder names Strata wrote here the last time, or null when there is no note yet (a folder from 0.2.20 or older). */
function readOwned(root) {
  try {
    const note = JSON.parse(readFileSync(join(root, OWNED), 'utf8'));
    if (Array.isArray(note?.folders)) return new Set(note.folders.filter(name => typeof name === 'string' && name && !/[\\/]/.test(name) && name !== '..'));
  } catch { /* no note yet, or one that cannot be read */ }
  return null;
}

function writeOwned(root, names) {
  const note = JSON.stringify({ folders: [...names].sort() });
  let same = false; try { same = readFileSync(join(root, OWNED), 'utf8') === note; } catch { /* not there yet */ }
  if (!same) writeFileSync(join(root, OWNED), note);
}

/** A folder Strata made: named in the note, or holding the copy note of `copySkillExtras` (every folder 0.2.20 wrote for a skill that has a folder of its own). */
function isOwned(root, name, manifest) {
  return Boolean(manifest?.has(name)) || existsSync(join(root, name, COPIED));
}

/** What `skillFileText` writes: a frontmatter of name, optional title, a quoted description, optional hidden flag, then the body. */
function looksWritten(root, name) {
  try {
    const text = readFileSync(join(root, name, 'SKILL.md'), 'utf8');
    return text.startsWith(`---\nname: ${name}\n`) && /^---\nname: [^\n]*\n(?:title: "[^\n]*"\n)?description: "[^\n]*"\n(?:disable-model-invocation: true\n)?---\n\n/.test(text);
  } catch { return false; }
}

/** A folder at `name` that Strata did not make. Folders from before the note existed that look like what Strata writes are taken for its own once, so an upgrade does not leave a twin. */
function isForeign(root, name, manifest) {
  const dir = join(root, name);
  const entry = lstatSync(dir, { throwIfNoEntry: false });
  if (!entry) return false;
  if (!entry.isDirectory() || lstatSync(join(dir, 'SKILL.md'), { throwIfNoEntry: false })?.isSymbolicLink()) return true;
  if (isOwned(root, name, manifest)) return false;
  return !(manifest === null && looksWritten(root, name));
}

/** Move a folder Strata wrote out of the scanned folder into `skills-removed/<name>-<time>`, so a skill whose source went missing for a moment can be put back. */
function moveAside(root, name) {
  const from = join(root, name), bin = join(dirname(root), SKILLS_REMOVED);
  mkdirSync(bin, { recursive: true });
  const to = join(bin, `${name}-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}-${Math.random().toString(36).slice(2, 6)}`);
  try { renameSync(from, to); } catch {
    cpSync(from, to, { recursive: true });                  // a rename can fail on Windows while a watcher holds the folder
    rmSync(from, { recursive: true, force: true });
  }
  try {
    const old = readdirSync(bin, { withFileTypes: true }).filter(e => e.isDirectory()).map(e => e.name).sort();
    for (const gone of old.slice(0, Math.max(0, old.length - KEEP_REMOVED))) rmSync(join(bin, gone), { recursive: true, force: true });
  } catch { /* the backups are a convenience */ }
}
