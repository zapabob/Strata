# Implementation Log: Defer Windows repair-access until after host listen

- **Date**: 2026-11-28
- **AI**: Antigravity
- **Target**: Prevent desktop startup `/api/health` timeout caused by early `control.repairAccess()` disk scan

## Overview

Moved Windows `control.repairAccess()` invocation in `app/host/server/index.mjs` from module-load time (before `server.listen`) into a 2-second unref'd timer inside the `server.listen` callback so `/api/health` becomes ready before the 4,963-file ownership scan starts. Applied the same change to the locally installed `0.8.7` host.

## Background / Requirements

- Desktop startup log `desktop-20261127-204501.log` showed `[host] control #1 begin repair-access --output` followed by a 60s `/api/health` connection timeout before `strata host · http://127.0.0.1:47831` was logged.
- Direct measurement of `strata.py repair-access --output json` took 43.7 s across 4,963 files (and 53.0 s in prior startup logs).

## Changed Files

- `app/host/server/index.mjs`
- Local installed copy: `C:\Users\downl\AppData\Local\Programs\Strata\host\server\index.mjs`

## Verification

- Syntax check with bundled Node 24.22.3 (`node --check app/host/server/index.mjs`) and host tests (`tests/packaged-control.test.mjs`).
- Live `/api/health` probe on installed `strata-desktop.exe` confirmed healthy response in 13.4 s.

## Residual Risks

- The already-published `v0.8.7` installer archive does not include this post-release fix; it will be included in the next installer build (`0.8.8` or next patch).
