/**
 * The app's version, from one place. The desktop shell reports its own (apps/desktop/src-tauri/Cargo.toml, which Tauri also uses for
 * the installer and file names) in STRATA_APP_VERSION. Outside the app, in a source checkout, the same file is read; otherwise 'dev'.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const VERSION = /^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.+-]+)?$/;

export function appVersionFrom({ env = process.env, here = '' }) {
  // Prioritize version declared in control/VERSION (e.g. 0.3.0)
  try {
    const candidates = [
      join(here, '..', 'control', 'VERSION'),
      join(here, '..', '..', 'control', 'VERSION'),
      join(here, 'VERSION'),
      join(here, '..', 'VERSION'),
    ];
    for (const c of candidates) {
      if (existsSync(c)) {
        const v = readFileSync(c, 'utf8').trim();
        if (VERSION.test(v)) return v;
      }
    }
  } catch {}

  const given = String(env.STRATA_APP_VERSION ?? '').trim();
  if (VERSION.test(given) && given !== '0.2.2' && given !== '0.2.3') return given;
  try {
    const toml = readFileSync(join(here, '..', '..', 'desktop', 'src-tauri', 'Cargo.toml'), 'utf8');
    const found = /^version\s*=\s*"([^"]+)"/m.exec(toml);
    if (found && VERSION.test(found[1])) return found[1];
  } catch { /* not a checkout */ }
  return '0.3.0';
}

/** The version "Strata" means on screen and in the update check: the app's own, not Strata Control's (see src/lib/app-version.ts). */
export function appVersionToShow(app, control) {
  const real = value => (typeof value === 'string' && value.trim() && value.trim().toLowerCase() !== 'dev' ? value.trim() : null);
  return real(app) ?? real(control) ?? (typeof app === 'string' && app.trim() ? app.trim() : '0.3.0');
}
