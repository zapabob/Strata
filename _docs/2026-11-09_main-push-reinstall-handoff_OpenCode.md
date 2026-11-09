# Main push and verified local.2 overwrite — 2026-11-09

Owner: OpenCode. Requested checkpoint/overwrite complete; full native/Spin8 goal remains open.

## Main and artifact identity

The diagnostic/research/actual-input QA checkpoint was committed and pushed as
`5a026a9863bcab7c7ba71f3540bbe800e5de0e96`. Remote main was read back and matched.
It includes49 passing CPU behavior cases and the DFlash compiler-resource research
patch. The patch is not selected by production CMake and is not installed.

There has been no new production application/kernel source change since the
qualified personal local.2 build. The user's requested overwrite therefore used
the exact same tested installer, not a newly qualified CUDA candidate:

```text
Compiled app/Control source: 52048324c235e15ad34b95ec84a80dbad7e2c492
Installer: H:/Strata/releases/personal-052-local2-20261107/app/Strata-0.5.2-local.2-windows-x64-setup.exe
Bytes: 112090046
SHA256: be423e6955943f5f5689160a20e9e9a897e1b22b5eff38e13fa7d01179dad9cd
```

The final documentation/helper commit following this record does not change that
compiled source or imply the new compiler experiments passed numerical parity.
Published releases/tags/feeds remain unchanged.

## Actual overwrite results

| Item | Fresh observed result |
| --- | --- |
| NSIS | One explicit `/S /D=C:\Users\downl\AppData\Local\Programs\Strata`, exit0 |
| App/Host/shell | 0.5.2-local.2 |
| Control | 0.5.3 |
| Native/Prism | Existing signed0.5.2 / exact reviewed Prism0.4.1 retained |
| Payload | 29,476 files match the qualified archive |
| User data | 957 files unchanged before first launch |
| Native component | All141 files unchanged; built-in signature reverified |
| Registration/shortcuts | Explicit C: target and both shortcuts correct |
| Normal startup | Opened normally, no debugging, initially unloaded, saved settings/registrations retained |
| Outer installation guard | Exit0, no resource abort, 254.36 seconds |

User-data backup: `H:/Strata/private-backups/reinstall-local2-20261109`.
957 files /4,726,139 bytes; no weights copied or deleted.
Preflight SHA256: `353834cced177697f112e0435fc205b0fd5963796bdeaeb1c7d1ffc932b1bb7f`.

Fresh receipts:
`H:/Strata/releases/personal-052-local2-20261107/reinstall-20261109/result.json`,
`install-complete.json`, `installed-payload.json`, `backup.json`, `nsis-result.json`,
`normal-startup.json`, `native-activated.json` (verified existing, no repeated activation).
Outer guard: original app output's `receipts/job-reinstall-local2-20261109.json`.

The exact installer had already passed13 production self-tests, eight actual Q36
GUI/native acceptance groups, and two reported-GGUF Prism GUI chat/restart cycles.
Those earlier tests are bound to these same artifact bytes; they were not rerun
and are not reported as fresh full E2E for this same-version reinstall.

## Stop/unload and restoration

The user explicitly approved normal Stop/unload of the current Swift response to
prioritize diagnosis. The first normal pause succeeded. A later, separate Swift
instance appeared through normal application/workflow activity; it was not the
diagnostic engine. The user then prioritized push/overwrite.

The fresh update snapshot is protected at
`H:/Strata/private-backups/native-diagnostics-20261109-update-r2`.
One normal Stop completed. Initial unload returned `server_stop_deadline_expired`.
Read-only reconciliation confirmed zero turns, requests and native processes;
only then did another normal unload clear the stale error instance successfully.
Both the failure and successful reconciliation receipts remain. No blanket
process termination or configuration repair was used to hide the failed stop.

The idle installed Host was asked to shut down through its authenticated normal
shutdown API, allowed to finish, then only its exact idle shell handle was closed
for NSIS. The application and user data were backed up after shutdown.

Following the verified initially-unloaded startup, the normal app/workflow loaded
Swift again. The restore helper refused to create a duplicate. It then observed
the current instance become ready and verified the same model, context131072,
parallel1, GPU/vision choices, exact runtime argument vector and unchanged saved
configuration hash. The operator sent zero new load requests and did not resubmit
the interrupted private prompt. This is observed external restoration, not an
operator-initiated successful reload. `restored.json` records that distinction.

## Remaining engineering work

- DFlash candidate B removes the two selected stack frames in an isolated object;
  GPU parity/timing and production review are NOT_RUN. Default kernels unchanged.
- EXPDEC/QSA trial changes worsened spill use and were rejected. The four native
  resource findings remain FAIL; no baseline/allowance was increased.
- The3071-token Q36 fixture and49 CPU cases are ready as a checkpoint. Actual native
  input consumption/retrieval/cache/cancel/restart execution remains NOT_RUN.
  An external-engine/Host-activity guard prevents overlapping user workloads.
- Full native long-window quality, remaining Spin8 stages and public release
  qualification remain open. `releaseQualified=false` is retained.

See `_docs/2026-11-09_cuda-resource-investigation_OpenCode.md`,
`_docs/2026-11-09_q36-actual-input_OpenCode.md` and the original installed handoff
for exact source/artifact evidence. The five earlier used worktrees remain
removed; this continuation created no new worktree.

## Verification and self-review

Applied the existing PC/project/canonical-compatible context and engineering,
Security, Application, LLMOps, Python/CPP/QA controls. No formal compliance claim.
The reinstall helper uses the existing package verifier, backup, explicit NSIS
and prelaunch inventory functions; only the exact qualified installer is allowed.
RAM3GiB /commit4GiB /C:5GiB /H:10GiB floors stayed enabled in the installation guard.
Normal user handoff ran outside that owned child guard to preserve app lifetime.

Self-review-event: qa_defect, ticket_completed (push/reinstall unit only), review-only.
The helper's missing public configPath assumption, actual Control stop timeout,
and externally restored model were kept distinct from successful update gates.
Rejected: duplicate load, replaying stale instance IDs, deleting user state,
claiming new CUDA qualification from same-version installation, or modifying
installed binaries outside the qualified installer. No governance weakening.
