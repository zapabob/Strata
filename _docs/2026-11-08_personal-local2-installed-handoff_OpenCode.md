# Personal local.2 installed — parent handoff

Local installation is successful. App is open normally, unloaded, with remote
debugging disabled. Do not stop an active user conversation during cleanup.

## Delivered source and artifact

- Compiled app/Control source: `52048324c235e15ad34b95ec84a80dbad7e2c492`.
- Product-fix commits: `4e63f338` (native FP32 projection), `52048324` (native
  chat crypto import and generated reserve persistence on reload).
- Previously pushed source: `7cacaf5949937b438eaedb452d26724904a1bc9e`.
- Installer:
  `H:/Strata/releases/personal-052-local2-20261107/app/Strata-0.5.2-local.2-windows-x64-setup.exe`.
- Installer bytes: **112,090,046**.
- SHA-256: `be423e6955943f5f5689160a20e9e9a897e1b22b5eff38e13fa7d01179dad9cd`.

Installed: app/shell/Host **0.5.2-local.2**, Control **0.5.3**, native **0.5.2**
(unchanged r3 `13fc3b96...`), exact private PrismML **0.4.1**. New signed component
manifest SHA-256 `9ec246e323d956049be5de0d64df45a789cc057f0127280bc2ac8860c7e3e455`,
built-in trusted key **1daf8588d50b1049**. All 141 new files match the signed copy;
all 139 original 0.5.1 fallback files remain unchanged and available.

## Fresh actual gates

- Focused source tests: **44/44 PASS**; TypeScript PASS.
- Exact package payload **29,476 files**, real production self-tests **13/13 PASS**.
- Actual Q36 WebView2/native E2E: **8 acceptance groups PASS**, no mocks, zero
  page exceptions; load/nonempty chat/unload/reload, settings/reselection/process
  restart, invalid-choice refusal, live child INFO and Japanese screenshots.
- Actual reported-GGUF Prism WebView2 E2E: **two cycles PASS**, arithmetic 5/56,
  98,304 capacity with observed Q8 K/V and flash attention, saved-profile restart
  and GUI unload. Short prompts only; not full-window qualification.
- Backup: **926 files / 4,400,671 bytes**, no weights copied.
- One NSIS `/S /D=C:\Users\downl\AppData\Local\Programs\Strata`: **exit 0**.
- Before first launch: **29,476 payload files equal**, **926 user files unchanged**;
  real C: uninstall registration and both shortcuts correct.
- Component activation: built-in signatures/full payload, real model/generation
  test start enabled, selected native 0.5.2 usable.
- Normal startup/handoff: settings retained, manual/unloaded, no debug endpoint.
- One exact reported-file saved profile now uses **PrismML** and survives an
  actual normal-profile restart. Unrelated profile/defaults/library/current
  different model preserved; global Automatic environment and generic pointer
  unchanged. Profile count 1→2. No normal-profile model load was requested.

## Evidence / preservation

Receipts: `H:/Strata/releases/personal-052-local2-20261107/app`.
Final authoritative receipts: `app-build.json`, `app-qualification.json`,
`functional-e2e.json`, `prism-e2e.json`, `backup.json`, `nsis-result.json`,
`installed-payload.json`, `native-activated.json`, `normal-target-prism-r2.json`,
`normal-target-profile-restart-qualified.json`, `user-handoff-final.json`,
`final-sanity.json`.

Private backup:
`H:/Strata/private-backups/personal-052-local2-20261107`.
Preflight hash `b0615cde24599e71b26ca0b96890ea4eeb057f4422c2bf309ae4b6f74a3782ba`.
Prior failed candidates are retained under `candidate-before-fp32-fix` and
`candidate-before-chat-fix`; original r3, unsigned r4, published assets, old C:
build/staging and unrelated worktrees were not deleted. No absent Hermes server
was started. The authorized PowerShell cache was preserved privately earlier.

Failures and exact scope are in `_docs/2026-11-07_personal-overwrite-2_OpenCode.md`.
All unsuccessful GUI/activation attempts have unique retained receipts. The
update's automatic test initially found an old unsupported native config; the
successful retry used the actually qualified config through `--model-config`
and kept full generation testing. Optional desktop principal credentials were
excluded only from the protected update-probe copy, not user configs.

## Parent next actions / limits

Parent owns final push of the two product-fix commits and this evidence, remote
SHA verification, broader handoff and used-worktree cleanup. No tags or public
release/feed changes occurred. Do not rebuild unless source changes require it.
Evidence-only HEAD is not the compiled app source; the binary is from 52048324.

Native generic CUDA resource guard still has four pre-existing failures;
**releaseQualified=false** remains explicit. No native speed/full-window/general
quality/total-process-memory-bound or real-file explicit-MTP negative claim.
The parent's remaining Spin8 A–H/publication goal is not complete. This is a
Windows-code-unsigned personal installer with signed component integrity.
