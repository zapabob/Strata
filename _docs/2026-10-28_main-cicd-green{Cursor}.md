# 2026-10-28 main commit/push + CI/CD green attempt {Cursor}

- **When**: 2026-10-28 00:42:18 +09:00
- **Agent**: Cursor
- **Repo**: https://github.com/zapabob/Strata
- **Workspace**: `H:\Strata\worktrees\hakua-chatbot-20261027`

## Verdict

**Push to `origin/main`: YES (FF only, no force).**  
**Cloud CI all-green on tip `91d6fb4a`: BLOCKED** — GitHub Actions refused every `workflow_dispatch` / new push run with HTTP 422 `Actions has been disabled for this repository`, even though `GET /repos/zapabob/Strata/actions/permissions` returns `{"enabled":true,"allowed_actions":"all"}`.

This is an **irreducible external blocker** from the agent side (admin API cannot flip the live runner switch). Product-side CI-equivalent checks that can run locally on this Windows host passed.

## Git / push

| Item | Value |
|------|-------|
| Before `origin/main` | `4cf0cf1ea3f0e97204d6171c6ed200236099fd7f` |
| After tip / `origin/main` | `91d6fb4aa6b633c29ee201404af9795f5d1f964b` |
| Feature branch sync | `origin/codex/strata-hakua-chatbot-20261027` → same tip |
| Push URLs | https://github.com/zapabob/Strata/commit/3c717fe6 · https://github.com/zapabob/Strata/commit/93dbc023 · https://github.com/zapabob/Strata/commit/91d6fb4a |
| Force push | **No** |

### Commits landed

1. `3c717fe6` — `[Docs] record build/release evidence and NSIS overwrite install notes`
2. `93dbc023` — `[GUI] sync desktop preview lockfiles and empty engine-bundle marker`
3. `91d6fb4a` — `[Docs] record main CI green attempt and Actions disablement blocker`

### Explicitly excluded from commit

- `dist-integrated-20261027/` (build leftovers)
- `build/` CMake artifacts / `__pycache__` / `.pytest_cache`
- line-ending-only noise on `apps/desktop/src-tauri/resources/control/.gitignore`

## CI inspection (evidence)

### Tip check status

```text
gh api repos/zapabob/Strata/commits/93dbc023…/status
→ state=pending, total_count=0, statuses=[]
```

No Actions check-runs were created for `93dbc023` (or prior tip `4cf0cf1e`).

### Dispatch attempts (all failed)

```text
gh workflow run 'Minimal serving runtime' --repo zapabob/Strata --ref main
gh workflow run 'Native preview CPU checks' --repo zapabob/Strata --ref main
gh workflow run 'Portable monitor client' --repo zapabob/Strata --ref main
gh workflow run 'Deploy GitHub Pages' --repo zapabob/Strata --ref main
→ HTTP 422: Actions has been disabled for this repository
```

Also tried `PUT …/actions/permissions` with JSON `{"enabled":true,"allowed_actions":"all"}` (accepted) and `PUT …/actions/workflows/{id}/enable` for the four workflows; dispatch still 422.

Permissions probe after PUT:

```json
{"enabled":true,"allowed_actions":"all","sha_pinning_required":false}
```

Token scopes include `repo` + `workflow`. Repo `permissions.admin=true`.

### Last known successful remote runs (when Actions still executed)

| Workflow | Run | SHA | When | Link |
|----------|-----|-----|------|------|
| Minimal serving runtime | 40246905899 | `e68f8926` | 2026-10-25 | https://github.com/zapabob/Strata/actions/runs/40246905899 |
| Native preview CPU checks | 40246904126 | `e68f8926` | 2026-10-25 | https://github.com/zapabob/Strata/actions/runs/40246904126 |
| Deploy GitHub Pages | 40246902009 | `e68f8926` | 2026-10-25 | https://github.com/zapabob/Strata/actions/runs/40246902009 |
| Portable monitor client | 40145203557 | `d6847bca` | 2026-10-25 | https://github.com/zapabob/Strata/actions/runs/40145203557 |

Historical failure previously fixed on tip (R02): `test_server_close_ends_the_sampler` — last failing remote log was run `40106051196` (2026-10-24). Local re-check on tip: **OK**.

Path filters note: docs/GUI packaging pushes would not have triggered Minimal/Native/Portable anyway; Pages only watches `docs/**` (not `_docs/**`). Green-on-tip therefore required `workflow_dispatch` or a path-matching product change — both blocked by Actions disablement.

## Local CI-equivalent matrix (this host)

| Check | Result | Notes |
|-------|--------|-------|
| `py -3 -B -m unittest discover -s tests/terminal -p test_native_preview.py` | **13 OK** | Native preview packaging boundary |
| `serve.test_responses.NoLeakedSampler.test_server_close_ends_the_sampler` | **OK** | Historical Minimal serving failure |
| `packaging/monitor_bundle.py build` + `tools/portable_monitor_smoke.py` | **passed** | Windows-11 / Python 3.12.10 |
| `tools/minimal_server_smoke.py` | **N/A on Windows** | Script requires POSIX owned-runtime venv |

## Human unblock (required for cloud green)

1. Open https://github.com/zapabob/Strata/settings/actions while signed in as `zapabob`.
2. Set **Actions permissions** to allow Actions (and confirm billing/minutes are not exhausted).
3. Re-run:

```powershell
gh workflow run 'Minimal serving runtime' --repo zapabob/Strata --ref main
gh workflow run 'Native preview CPU checks' --repo zapabob/Strata --ref main
gh workflow run 'Portable monitor client' --repo zapabob/Strata --ref main
gh workflow run 'Deploy GitHub Pages' --repo zapabob/Strata --ref main
```

4. Confirm tip `91d6fb4a` (or later) check matrix is all success.

Settings URL was opened in the system browser during this session; Cursor Computer Use sidecar was unavailable, so the UI toggle could not be actuated by the agent.

## Hypothesis checklist

1. **H1** Dirty tree has intentional docs/packaging to land on main → **adopted** (2 commits).
2. **H2** `origin/main` FF push from feature tip works → **adopted**.
3. **H3** Push alone makes Actions green → **rejected** (Actions disabled; tip has zero check-runs).
4. **H4** `workflow_dispatch` can force green matrix → **rejected** (422 disabled).
5. **H5** Product regressions explain cloud red → **rejected locally** for Native / Portable / sampler; Minimal smoke is POSIX-only here.
6. **H6** Permissions API `enabled:true` means runners accept jobs → **rejected** (dispatch still 422).
