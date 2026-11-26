# Hakua 0.8.3 — release notes

## Scope
A local, unsigned Windows NSIS build of the Hakua fork. It carries the app shell and staged
Control 0.6.3. The GPU engine is rebuilt from the committed source for this release and is bound
to it by digest (no signing key). Product and engine use the unified semantic version 0.8.3;
Control remains independently versioned at 0.6.3. Hakua-memory, web search, PrismML auto-adapter
and Inkling-2 support are retained.

## Integrated upstream work (v0.2.21 → v0.2.22, one change at a time)
- Security and host hardening (#7130 browser /api restriction and SVG/HTML sandbox follow-up),
  setup and engine fixes (#7119, #7090, #7089, #7093), serve fixes (#7044, #7051, #7092,
  #7043, #7060), thinking-budget fixes (#7133, #7132, #7084).
- Pause/resume for updates (#7099) and toolbar gating (#7101), plus the 0.2.22 Hebrew wording.
- Three previously dropped upstream tests adapted and passing: image cap (#7043), conversation
  cache budget (#7044), model-card sampling (#7092).
- Integration bugs found and repaired while adapting: misplaced `q36_kv_receipt_matches` body,
  missing `inkling_dialect` import, shadowed model-card table, and the answered-reply finish
  reason after a budget wrap.

## Verification recorded in `_docs/2026-11-26_upstream-0222-and-q4k_Codex.md`
- Python targeted suite: 120 passed.
- Node pause/keepalive/branch/sandbox suites: all passing (20 pause tests in the final batch).
- TypeScript typecheck: clean.
- GUI/API E2E before the app went offline: host health, engine health, chat, `memory_recall`
  and `search` tool calls all HTTP 200.

## Limits
`releaseQualified=false` is unchanged. The installer has no Windows Authenticode signature.
The staged engine is a rebuilt local unsigned component (0.8.3, CUDA 13.5 / sm_120) bound to
the committed native sources by `native-build.json` digest; the Windows EXE itself has no code
signature. The app starts unloaded.

Full-window generation, general/low-precision model quality, public search quality and GPU
concurrency are not qualified by these checks. The system RAM/commit/disk floors are unchanged.
The app starts unloaded; the model is loaded manually.


## Publication and local overwrite (2026-11-27)
- Installer: `H:\Strata\releases\Strata-0.8.3-windows-x64-setup.exe`, 127,397,661 bytes,
  SHA-256 `16d1b5652b6d23f1ceb806354cad78922aecb4938fef511f0b2adb61c73f1282`.
- GitHub release: https://github.com/zapabob/Strata/releases/tag/v0.8.3 with the installer and
  `SHA256SUMS-v083.txt`. Immutable tag points to `b15f12d3e`; mutable `latest` alias was moved
  to the same commit.
- Anonymous download readback: HTTP 200, 127,397,661 bytes, matching local SHA-256.
- Local silent overwrite with `/S /UPDATE` completed; installed `strata-desktop.exe` ProductVersion
  is 0.8.3 and installed Control reports 0.6.3. The app was not running afterward, so a
  post-install E2E was not executed; the earlier green GUI/API E2E remains the verification record.
- Old build outputs except evidence were removed (about 17 GB of release/build directories, old
  installer and obsolete worktrees). Text/log evidence was archived under
  `H:\Strata\evidence\cleanup-20261127-old-build-artifacts` (9,057 files, including the aborted
  upstream merge diff). Models, current targets and published GitHub assets were not deleted.
