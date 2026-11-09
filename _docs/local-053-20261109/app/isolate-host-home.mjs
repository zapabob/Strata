/** Test-only preload: isolate Node homedir, keep the shell's Windows identity intact. */
import assert from 'node:assert/strict';
const home=process.env.STRATA_HOME;
assert.ok(home&&/^H:[\\/]Strata[\\/]releases[\\/]local-053-20261109-opencode[\\/]app[\\/]qa[\\/](candidate|installed)-(q36|prism)-r[1-9][0-9]*[\\/](e2e-profile|prism-e2e-profile)$/.test(home));
process.env.USERPROFILE=home;
process.env.HOME=home;
