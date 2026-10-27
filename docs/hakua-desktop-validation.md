# Hakua desktop validation notes

This file records how T7–T9 measurements are defined on this PC. Numbers here are
only those taken on the machine that wrote them. Missing values stay `null` with a
reason; they are not filled with guesses.

## Build identity (fill per run)

| Field | Value |
|---|---|
| repoCommit | see `_docs` implementation logs |
| hostVersion | `apps/host/package.json` |
| modelId | operator choice; do not invent |
| sanitizedConfigHash | hash of run-config without keys |

## Timing fields

| Field | Meaning |
|---|---|
| `ttftMs` | Time to first model output token (reasoning or answer). Existing meaning kept. |
| `firstVisibleAnswerMs` | Time to first answer **body** (`text-delta`). Separate from reasoning. |
| `answerDone` | Turn `done` / terminal frame. |
| `writebackDone` | Memory store completion when Hakua store_summary is on. Success / fail / unknown. |

Do not subtract clocks from different processes without a shared correlation id.

## Resource sampling

Use live sensors. On failure, record `unknown` — never invent 16 GiB free or a fixed
commit cap as proof the machine can load.

Example snapshot (2026-10-27, RTX 5060 Ti, after Cursor idle):

| Sensor | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Ti |
| VRAM total / used / free | 16311 / 1157 / 14894 MiB (nvidia-smi) |
| CPU | AMD Ryzen 5 4500, 6c/12t |

## T8 profile comparison

Opt-in only. Change one factor at a time. Do not promote a profile without same-day
paired runs on the same Japanese task set. If free VRAM or RAM is too low for a fair
load, mark the comparison **未実行** with the sensor reading.

## T9 long-run gate

32 turns and 2 hours on the **installed** app are required for a stability pass.
Fixture cancel cycles (mock Control) are evidence for F03 only; they are not a
substitute for the installed GUI endurance run.
