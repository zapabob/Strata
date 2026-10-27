# v0.3.2-preview.20261027.2 — release notes draft (unsigned / not published)

Date: 2026-10-27 23:20+09:00 (Tokyo). Worktree: `H:/Strata/worktrees/hakua-chatbot-20261027`.

## What “release” means on this fork (from packaging/)

Per `packaging/UPDATES.md` and `packaging/README.md`, a **real release** is **not** just a git tag:

1. **Build boxes** produce installers / engine packages **without** private keys (`createUpdaterArtifacts: false`).
2. **Release PC** holds secrets never in git:
   - feed key (`feed-key.json`) — Ed25519 for `strata-feed.json` + engine package manifests
   - Tauri updater key (`tauri-updater.key`) — minisign for app installers
3. Owner runs `feed_tool.py sign-package` / `pack-engine` / `pack-control` / `tauri signer sign` / `build-feed` / `verify-feed`.
4. Assets go on a **normal** (non-prerelease) GitHub Release so `…/releases/latest/download` works for installers and `strata update`.
5. A **git tag alone** does not update the signed feed or ship installers.

Unsigned local NSIS / local tag / draft notes are **preview packaging**, not a signed feed release.

## This preview

| Item | Status |
|------|--------|
| Merge | `7e79763f` — upstream `4b9e05a2` (v0.2.6) into Hakua fork |
| App / tag version | `0.3.2-preview.20261027.2` |
| Local annotated tag | `v0.3.2-preview.20261027.2` → merge commit (**not pushed**) |
| README | Rewritten (fork notes + measured preview only) |
| Proprietary surfaces | Present (see verify section in impl log) |
| Signed feed / Tauri `.sig` | **Not done** — no `feed-key.json` / `tauri-updater.key` on this PC |
| `git push` / `gh release create` | **Not done** — user historically forbids auto-push; needs explicit OK |

## Blockers (concrete)

1. **Missing signing credentials on this machine**
   - Searched: worktree, `H:\Strata` depth-3, `D:\strata-keys`, `%USERPROFILE%\strata-keys` → no private feed/Tauri keys.
   - Public updater pubkey is in `tauri.conf.json`; private half is required to produce `.sig` and a verifiable feed.

2. **Network publish needs explicit user OK** (no auto-push policy)
   ```powershell
   git -C H:\Strata\worktrees\hakua-chatbot-20261027 push -u origin HEAD
   git -C H:\Strata\worktrees\hakua-chatbot-20261027 push origin v0.3.2-preview.20261027.2
   ```
   Only after keys + built artifacts exist on a release PC:
   ```powershell
   # example shape only — do not run without keys + artifacts + user OK
   gh release create v0.3.2-preview.20261027.2 --title "…" --notes-file _docs\2026-10-27_v032-preview-release-notes-draft{Cursor}.md --draft
   ```
   Note: packaging says a **prerelease/draft is not** what `latest/download` consumers use. A draft is allowed as a **holding area** only if the user wants an unpublished asset dump; it is **not** a signed feed release.

3. **Unsigned draft GitHub Release**
   - Technically possible with `gh release create … --draft` after push+tag, **without** signing keys.
   - That still requires `git push` / `gh` auth and does **not** satisfy `packaging/UPDATES.md` “release”.
   - Not created in this session (push policy).

## Suggested notes body (when publish is allowed)

### Summary
- Sync Hakua fork with upstream Strata **v0.2.6** (`4b9e05a2`) while keeping proprietary cancel-path, Hakua chat open, harness auth, and run-config keys.
- Preview version `0.3.2-preview.20261027.2` (not upstream app `0.2.6`).

### Kept (fork)
- `stopCancelledLoad` cancel path (F03/F03b)
- `openHakuaChat` host API
- `hakua_harness` principal-key handling + `checkRunConfig` known key
- Spin8 / Prism / native fork surfaces as previously inventoried

### From upstream
- Engine / Control / docs / installer matrix for 0.2.6
- Host settled skeleton and DeepSeek experts settings gates where merged

### Limits
- Signed update feed not published from this worktree.
- Full CUDA/CMake and full `npm test` evidence recorded separately in the impl log for this date.

## Exact next commands (owner)

On release PC with keys:

```powershell
# 1) after engine/control/app artifacts exist in RELEASE/
py -3 packaging/feed_tool.py sign-package <engine-folder> --key <feed-key.json>
py -3 packaging/feed_tool.py pack-engine <engine-folder> --out RELEASE/engine --url-prefix=
py -3 packaging/feed_tool.py pack-control <control-folder> --version <CONTROL_VER> --platform windows-x86_64 --format zip --out RELEASE/control --url-prefix=
npx tauri signer sign -f <tauri-updater.key> <installer.exe>
py -3 packaging/feed_tool.py build-feed --out RELEASE --sequence <N> --key <feed-key.json> --engine RELEASE/engine --control RELEASE/control --app-json RELEASE/tauri-latest.json
py -3 packaging/feed_tool.py verify-feed RELEASE --pub <feed-key.pub.json>
```

Then, only with explicit network allow:

```powershell
git push origin HEAD ; git push origin v0.3.2-preview.20261027.2
# upload RELEASE/* as GitHub Release assets (latest, not prerelease, for feed consumers)
```
