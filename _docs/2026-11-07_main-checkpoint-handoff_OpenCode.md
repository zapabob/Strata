# Main checkpoint and personal build handoff

Updated: 2026-11-07. Owner: OpenCode. Full product/release goal remains open.

## Current request

The user requested all current work on main, commit/push, a personal build and
overwrite installation, a handoff, and removal of used worktrees after integration.
This document supersedes the working-state descriptions in the earlier C-drive
handoff. The full Spin8 A–H/public-release goal is not narrowed by this checkpoint.

## Source and installed versions

Active main: `H:/Strata/worktrees/main-integration-20261106`.
The original C-drive checkout remains on the old `codex/windows-latest-0.4.1`
branch and contains unrelated historical untracked work. Use active main.

| Item | Source/checkpoint | Installed before this build |
| --- | --- | --- |
| App/Host/shell | 0.5.2-local.2 | 0.5.2-local.1 |
| Control | 0.5.3 | 0.5.2 |
| Native CUDA | 0.5.2 | 0.5.1 |
| PrismML | 0.4.1 private candidate; 0.4.0 rollback accepted | 0.4.0 in native component |
| Metal | 0.5.0-metal, unchanged/unqualified here | Not applicable |

The current commit is the reproducible source checkpoint. The installer is not
considered updated until the guarded build, actual GUI checks, backup, NSIS exit,
installed inventory and normal startup receipts pass. Public Latest remains
v0.5.1; this checkpoint creates no release or tag.

## Integrated source

- GUI selection/async ownership, persistent profiles and actual adapter policies.
  Catalog-derived Q38/Q36/DeepSeek identity now reaches Python consistently.
  Invalid captured settings and contradictory runtime contracts fail before
  replacement or native launch.
- Verified CPU topology/readiness, with no fallback identity written as a real
  profile and no loss of drafts while hardware is being read.
- Explicit search/skill import, durable persistence and observation lifecycle.
- Screenshot fixes: registered telemetry substitution, localized recovery text,
  shared unloaded/error/unknown model status, app-event connection wording and
  ownership of reconnect/bootstrap/chat hydration.
- Bounded Q36 expert storage, capability admission and actual child-owned memory
  receipts. Readings publish after READY and are invalidated on stop/restart/error.
- Spin8 CPU/CUDA attention v2, including completion of plan initialization before
  publication to nonblocking streams. Common runtime integration is still pending.
- Qwen3.5 trunk-only GGUF diagnosis, retained first loader error, pinned private
  runtime patch and exact-version package approval.

Useful commits preceding this checkpoint: GUI 7a4eda5d, native bounded 044722d2,
Spin8 27456e2a, native source 4a171bde, memory observation 8232d672, Qwen3.5 runtime
fix be3040e6. Main includes the audited disk, small-context and watchdog ports.

## Actual verification and its limits

- Fresh combined Host/renderer/lifecycle/backend/monitor suite: **130 passed**.
- Fresh Python selection: 47 passed and one test-setup error because its explicit
  Node executable environment variable was omitted. With `STRATA_TEST_NODE_EXE`
  set to the installed private Node, that remaining test passed. No assertion was
  removed; do not describe the first command as an all-pass run.
- TypeScript and product-version consistency: passed.
- Native r3: **17 functional checks passed**, B2 **617 GPU cases**, first-use
  **32 plans**, matching Compute Sanitizer KV check **0 errors**.
- Q36 actual short bounded/legacy/restart runs passed. Context capacity4096,
  prefill512, explicit five expert slots, MTP2 and F32 KV. Inputs were **5/6 actual
  tokens**, not a full 4K/98K/131K input. All seven paired token sequences matched.
- Native resource guard retains **four failures**. Resource columns also match
  retained0.5.1. Budgets/guards were not loosened. This is a personal candidate,
  **not public-release qualification**.
- Patched Prism: **56 actual-DLL loader fixtures passed**. The reported GGUF
  loaded twice at capacity98304 with Q8 K/V and Flash Attention, answered synthetic
  arithmetic with `5` and `56`, and stopped/restarted. Each input was26 tokens.
  Full-window and general model quality are unqualified. Real-file CLI explicit-MTP
  negative attempts were aborted by other model starts; the C API negative passed.
- Monitor changes have controlled production-component/ownership evidence;
  their final installed WebView2/reconnect evidence belongs to the build below.

Native r3 source/executable:

```text
source 4a171bdeb33675963edcca51f423519863fb7127
strata.exe 13fc3b96fe71afcb98990d828d2c743f85e8b59b16174a1f7da3eb4ef9b4f8e3
strata-q36.exe 0789a8583c4409bd517357675b96f9507b7d88ae725474a70e05997cc2be5ede
```

Prism0.4.1 source/executable:

```text
source 1965755ceee6738b9a04ceaf5d30e6305d6ccd00 (base73bfe6cc plus recorded patches)
runtime.json 9c729c73eb050dc466203fe149a27acd5be48763a33ea2c5d2b89f78e4ddcbaa
llama-server.exe 5ca5d8bfdfcb6fe46a96a06b71eaf45aedfbd1c6673bda2a10eb6412613be777
```

## Reported GGUF and runtime selection

The [publisher's file list](https://huggingface.co/mradermacher/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-i1-GGUF/tree/main)
matches the measured file: 5,629,111,584 bytes, SHA256
`8cf793a36e62fb078ac05c2e1bdb2121ff94736dccbede7cf81b76346e868949`.
Architecture is `qwen35`: 32 trunk blocks, one absent predictor in metadata, and
the original 33-entry recurrent map. Neither GGUF bytes nor that map were changed.

Its path moved externally during work. Both locations have been observed:
`H:/Strata/models/新しいフォルダー/` and
`H:/Strata/models/models/新しいフォルダー/`. Recheck the exact file/hash and the two
registered references before choosing the user's intended profile. The old
Automatic User environment selects an older generic runtime. Preserve that
explicit global choice; use the reviewed PrismML candidate for this model through
normal per-model settings after backup and actual GUI verification.

## Personal build: exact next actions

Read `_docs/personal-install-20261107/README.md`. Its phases are separate and
guarded: verify inputs, stage/sign the local component, build fresh Control,
build NSIS, check every payload file and13 production self-tests, run real isolated
WebView2 Q36 and reported-GGUF flows, back up, install to C:, verify before first
launch, activate the signed component, and verify normal startup.

The prepared unsigned r4 composite is:

```text
H:/Strata/releases/personal-052-local2-20261107/component-copy-r4/0.5.2-windows-x86_64-cuda-cuda13
manifest SHA256 df94ca9c8260e002896b1fe8c26d5e5948358eaf3b83191ad7a0c28cc7f97206
```

It contains native r3 and exact Prism0.4.1. Preserve the older unsigned r3 and
public assets. Signing uses the existing private key only through the package
tool; no key content enters Git. No public feed publication is part of this build.
The old local.1 installer remains the rollback artifact:
`H:/Strata/releases/local-052-20261106-opencode/Strata-0.5.2-local.1-windows-x64-setup.exe`.

## Runtime and resource conditions

The user approved temporary model-server pauses **after active answers finish**
with exact restoration. Recheck the real state: user shell/model processes have
started and exited independently during the session. Never act on recorded PIDs.
The prepared maintenance helper snapshots with missing servers or unknown admission
are non-executable; absence is not evidence of an idle/restorable server.

RAM floor3GiB, commit4GiB, H:10GiB and C:5GiB remain. Component activation needs
its additional bytes above the C: floor (about7.05GiB plus overhead for r4).
One compile job; H: TMP/TEMP; owned Job containment. Do not alter the system
pagefile to manufacture headroom. C: free space has varied substantially.

Recorded inactive synthetic test profiles were copied with full byte/time
inventories and verified before removing their C: copies. Preserved destination:
`H:/Strata/validation/retired-test-profiles-20261107/relocation.json`.
Two linked trees were retained. Subsequent focused tests use
`STRATA_TEST_SCRATCH_ROOT=H:/Strata/validation` to avoid growing C: profiles.

## Evidence and cleanup

Primary logs under `_docs`: `2026-11-07_personal-native-build_OpenCode.md`,
`2026-11-07_bounded-memory-gui_OpenCode.md`,
`2026-11-07_qwen35-mtp-load_OpenCode.md`,
`2026-11-07_monitor-state-consistency_OpenCode.md`,
`2026-11-07_personal-overwrite-2_OpenCode.md`, and
`2026-11-07_resume-e2e-regression_OpenCode.md`.
Raw qualification is under `H:/Strata/releases/personal-052-local2-20261107/`
and `H:/Strata/validation/qwen35-mtp-load-20261107/`.

After push verification, remove the clean integrated GUI/native/hybrid/Spin8 and
baseline worktrees. First preserve ignored native `_docs/native-32gb16gb` raw
logs, receipts and tested binaries. Keep active main and original C: checkout.
Keep the frozen upstream resource donor and old CUDA-KV evidence worktree until
their untracked/private artifacts and dependency junctions are explicitly preserved.
The external Prism source bundle is retained under `freeze-r1/source-1965755.bundle`.
Worktree removal has not happened at this checkpoint.

Full Spin8 A/C–H, comprehensive long-context/model-quality qualification, final
public installer README/release/tag/anonymous readback remain future gates.
The current source/personal-build checkpoint is not full-goal completion.
