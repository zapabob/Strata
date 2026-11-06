# Spin8 CUDA 13.5 staged implementation — audit record

Date: 2026-11-06 (JST). Implementer/orchestrator: Hermes; bounded CPU implementation delegated to Codex CLI with workspace-write sandbox. This is an engineering checkpoint, not release qualification or a formal MILSPEC certification.

## Scope and preservation

The user explicitly included stages A–H of the supplied revision-2 plan and prohibited publishing intermediate work as completed. The existing v0.5.1 release, installed application, personal data and unrelated worktrees are unchanged by this checkpoint. No release, installer replacement, tag movement or model download has been performed.

Source base: `c50ca06a863a98ff121cbff30365a035a90205e2`; isolated branch `feat/spin8-cuda135-20261106`. The user's original checkout remains on `codex/windows-latest-0.4.1` with all its pre-existing untracked files preserved.

Input design SHA-256: `47214407932409d4f97bd75c2371b3a27ab0f128797c24c1a662cb0cd203c79e`. Its content was copied without numerical changes to `docs/plans/2026-11-06-spin8-cuda135-input-v2.md`. Prospective acceptance protocol is separate in `docs/plans/2026-11-06-spin8-cuda135-execution.md`.

## Independently observed starting state

- GitHub reports v0.5.1 published and Latest, target `f3fb87cd269efaca0dff149a27b9ca23a10a792d`. Release asset metadata were read. Their full anonymous downloads/signatures were NOT independently repeated in this checkpoint.
- Current fork main equals the design base. The sibling CUDA135/KV branch has unpublished work and separate audit records; it was not merged wholesale or accepted from self-report.
- `nvidia-smi`: RTX 5060 Ti, driver 621.01; 16311 MiB total and 15765 MiB used at the observed sample. Existing unrelated llama-server processes are present; they were not stopped. This is an ambient snapshot, not benchmark attribution or available-memory qualification for a model.
- CMake reports 4.4.0. Visual Studio discovery reports VS2022 Community. Ninja and cl are not on the default shell PATH.
- The attachment's example CUDA executable path under Program Files does not exist on this machine. The original combined discovery command was blocked with Security Center SCAN_ERROR; passive path verification established the missing candidate. No security control was disabled. Existing tools were then queried separately; actual CUDA135 location discovery remains open.

## Execution ledger

| Unit | State | Evidence boundary |
|---|---|---|
| A CPU baseline | IN_PROGRESS | Detached fixed source, Release, one build job; existing tests |
| A CUDA135 standalone | NOT_RUN | Discover installed compiler and check resource floor first |
| A native off/on + real model | NOT_RUN | Separate qualification from small library tests |
| B1 CPU versioned API | IN_PROGRESS | Sandboxed Codex task, behavioral TDD and independent review required |
| B CUDA reference | NOT_RUN | B1 is not the entire phase B |
| C–H | NOT_RUN | No connectivity, codec, session or learned-quality claims |
| Package / overwrite / release | HELD | User requires no incomplete-work release |

Raw outputs live in the dedicated local validation directory, outside the checkout. Record failures and reruns below without deleting earlier outcomes. Do not publish local profiles, model content, credentials or raw conversation data.
