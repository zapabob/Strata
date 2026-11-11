# BTW, deep research and RustXNG delivery

## Requirements and decisions

The user requested `/btw`, `/deepresearch`, RustXNG search, an overwrite install,
a rewritten README, a tar.7z bundle and an installer following upstream's Windows
layout. The subsequent instruction explicitly selects RustXNG's Full profile.
Work starts from clean main at d9207991. Existing native source, engine artifacts,
resource floors, settings, model files, memories and release assets are preserved.

R1: `/btw` answers in a separate, cancellable, tool-free request using a snapshot
of the current conversation. It does not interrupt, queue into or modify the main
agent conversation. A single-slot engine can schedule its request behind active
inference; no concurrent GPU execution is promised.

R2: `/deepresearch` extends the existing research workflow with multiple searches,
page reads, source attribution and an explicit statement when evidence is limited.
Existing `/research` remains available. Search and tool approval choices apply.

R3: RustXNG v0.31.1 is pinned to official Windows bytes with SHA-256
a509798f040722db4a3df9eebb3551437c69189ed0003bb2a0b62bf749cf6775.
The app owns a loopback-only Full-profile process. No runtime download or update
is allowed. Existing other providers remain selectable. Distribution retains
LICENSE, NOTICE, source identity and corresponding source access.

R4: Deliver a distinct preview using Tauri's current-user NSIS recipe and the
same installer inside tar.7z. Verify archive members, artifact hashes and actual
installation. Preserve older published releases and stable Latest unless new
qualification supports changing them.

## Standards and verification plan

Read PC and project AGENTS, canonical CLAUDE-FABLE-5.md and applicable SOPs:
Common, Implementation Start Gate, Skill Selection, DeepResearch, Security,
Application, WebApp, Frontend Design, Internet Connectivity, LLMOps, TypeScript,
Rust. Skills: codex-session-style-and-standards, deepresearch-defense-standard,
milspec-codex-standard, frontend-ui-engineering, documentation-and-adrs.
The canonical prompt is supplementary; conflicting identity, environment, tool,
date and product assertions do not override the actual runtime instructions.

Use host unit/integration tests, TypeScript checks, production UI build, browser
checks, RustXNG health/config and real searches, NSIS cleanup regression, installed
payload comparison, and full streamed tar.7z readback. Five compiler jobs apply.
Record actual results below before making completion claims.

## Primary sources checked

2026-11-11 JST: https://github.com/sahenjp/RustXNG/releases/tag/v0.31.1
and its pinned README and docs/AGENT-SETUP.md. Release source:
a8ba33d8c9ceed91236f3abf029254d0f84995bb.
Full is the user's explicit choice; optional paid providers still require their
own key and authorization. No key is invented or copied into release artifacts.

## Implementation and evidence

RustXNG Full was verified with the actual pinned binary: /config identity,
/healthz, shared concurrent start, two real searches returning five public
results each (1783 ms and 902 ms), explicit close and rejection after close.
Receipt: H:/Strata/releases/search-056-20261111-codex/rustxng-live.json.
The first guarded attempt was refused before execution at the unchanged 3 GiB
available-RAM floor. With the user's explicit authorization, the active Strata
chat was normally stopped and its model normally unloaded. Hermes was untouched.
The Strata window then closed normally and its process was confirmed absent.

The full host suite initially ran 2159 tests: 2013 passed, 29 failed, 117 skipped.
A detached d9207991 baseline replayed every failing file: all 28 pre-existing
failure titles reproduced; its two additional command failures were environment
differences. The only newly introduced failure was duplicate Dismiss translation,
which was removed and the tools-locale tests then passed. The new feature strings
are translated in nine UI languages; the two remaining literal-coverage gaps
(Workspace / Move to trash) reproduce on the baseline. These failures are retained,
not recategorized as success. The broad suite does not pass.

The actual Harness research tests passed 2/2: existing research and deep-research
limited-evidence handling, including omission of an unread source. The side-turn
store test verifies a live main request, a separate answer and independent side
cancellation while the main request keeps running; all 3 stream lifecycle tests
passed. The test DOM stub now supplies its real-used hasFocus API, and a sourceURL
keeps bundled test stacks from dumping megabytes of source. No acceptance assertion
was removed. All eight root README languages now credit and link Strata,
llama.cpp and RustXNG in their own language. The upstream supporter block remains.

Self-review-event: qa_defect. The resource admission gate worked as intended;
the locale collision was caught by existing coverage. Keep the standards unchanged.
Use the narrow candidate QA checklist and retain baseline failures and receipts.
Python commands use uv with the existing Python 3.12 interpreter and the project's
preserved process/resource guard; large outputs and caches stay on H:.

Build, installation, archive and publication remain in progress. No success for
those stages is claimed yet.

Final pre-build focused checks: TypeScript passed; 37 tests passed, 3 explicitly
optional Harness/browser tests skipped, 0 failed. The separately executed real
Harness research checks passed 2/2. Guard receipts have confirmed cleanup with
zero active owned processes and unchanged resource floors. `git diff --check`
passes using the repository's configured CRLF normalization. A diagnostic run
with core.autocrlf disabled treated existing CRLF endings as whitespace; it was
not a source defect and no repository-wide line-ending rewrite was performed.
