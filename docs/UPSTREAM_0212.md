# Official 0.2.12 source integration

This source candidate incorporates official
[`v0.2.12`](https://github.com/Niko1221/Strata/releases/tag/v0.2.12) and main at
[`146df3c4`](https://github.com/Niko1221/Strata/commit/146df3c468739147f520ac3816de806f71232571),
checked on 2026-11-09. It is not a newly built or installed release. The public
stable download remains 0.5.1. The installed personal local.2 payload was built
from earlier source `52048324` / native `4a171bde` and has its own measured limits.

## What is being integrated

The official changes cover tuned DFlash2 distribution/planning, backend-specific
drafter choices, file-tier accounting, native transfer ordering, a prompt MMQ
row-table over-read margin, tool-name/opener recovery, Anthropic result ordering
and model-name compatibility, honest request statistics, Mac model preparation,
old-GPU build fixes and optional kernel paths. Official performance figures are
upstream measurements, not new measurements on this fork's PC.

## Combining the two implementations

| Official path | Retained fork advantage |
| --- | --- |
| Anthropic single-loaded-model resolver | The gateway keeps inferenceFetch deadlines/cancellation and refuses memory consent on its shared backend key. |
| Prefill/admission accounting | Private requests retain debug-output suppression and authenticated, per-conversation memory isolation. |
| Drafting/Feed APIs, including tuned packs | GUI and Terminal call the same Control API; the fork's signed feed/key policy remains in place. Missing tuned files keep the supported stock/MTP fallback. |
| Run-config options | The GUI recognises `undeclared_tool_calls`, validates `text` / `call` and leaves the official default at `text`. |
| Architecture-based settings | Unsupported controls stay unavailable; retained invalid settings remain visible and clearable. A misleading filename does not select a different architecture. |
| Native kernel/transfer changes | Q36 bounded/mapped expert storage, verified capabilities, private cache ownership, native-cache opt-ins and Windows resource/job gates remain in the source. |

Hakua/Hermes memory, GGUF reuse, PrismML Qwen3.5 loading, reconnect/state settings,
Spin8/TurboQuant research and independent package versions remain separate fork
contracts. The original weights and installed user data are not rewritten.

## Verification status

Python performed the actual merge and the reviewed conflict resolution.
Server regression groups: 553 passed, 4 skipped. Focused Host protocol/settings/
drafting/inference tests: 45 passed. The Q36/settings group passed 78 cases; its
3 durable-route fixtures passed on rerun after configuring the required scratch
guard. The first Terminal/Control group had 426 pass, 3 failures from an
upstream-specific feed URL expectation and 2 skips. That expectation was adapted
to the existing fork feed; all 100 tuned-drafter cases
passed on rerun. These are CPU/mock/local-HTTP results, not native-model or GPU tests.
Further checks are recorded in the [implementation log](../_docs/2026-11-09_upstream-0212-integration_OpenCode.md).

TypeScript checking failed at the bounded 256 MiB V8 heap limit and remains
unverified. Twenty-one bounded-run fixtures failed their H:-volume precondition
when started under C: scratch. Their production guard is unchanged; a correctly
located rerun still needs its existing memory floor. Other Q36/version/setup
checks had 161 pass and 24 skips, plus one outdated startup-fixture failure.
The fixture was connected to the actual admission helpers and all 10 startup-log
cases then passed. These failed attempts remain in the work record.

Native CUDA/HIP/SYCL/Metal compilation and hardware/model regression remain
pending. Existing low-memory gates are retained. Earlier four CUDA resource
failures and `releaseQualified=false` are not cleared by this source merge or
by successful CPU tests. Full-window/general-quality/Spin8 A–H qualification is open.

The maintainer's public advisory API returned an empty list on 2026-11-09.
This is not proof that no vulnerability exists. The listed upstream bug fixes
are incorporated as source; no new CVE, exploitation or audit claim is made.

## 日本語

公式v0.2.12と最新mainをソースへ取り込み、重複する処理は公式APIへ合わせた統合候補です。
独自の認証・同意付きメモリー、Qwen3.6の省メモリーとキャッシュ所有、GGUF再利用、
PrismML修正、設定・再接続の保持を組み合わせています。
新しいネイティブのビルド・実機認定・配布は未完了です。以前のlocal.2の成功結果を、
今回の実行ファイルの検証結果として扱いません。
