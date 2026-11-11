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
The first window-close observation was insufficient: Strata was still running
in its tray. Backup admission refused that live process. To exit normally, the
exact shell-preferences bytes were privately saved, tray behavior was temporarily
disabled through the app API, and Alt+F4 exited the app. The original preferences
were restored byte-for-byte and no installed app process remained. No live
user process was forcibly terminated for the upgrade.

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

The production app source is frozen at
6da4a421eeddade8cab74c7e6b80c9746031c721. The native and Control sources remain
independent. Later recipe and documentation commits do not change the app bytes.

Final pre-build focused checks: TypeScript passed; 37 tests passed, 3 explicitly
optional Harness/browser tests skipped, 0 failed. The separately executed real
Harness research checks passed 2/2. Guard receipts have confirmed cleanup with
zero active owned processes and unchanged resource floors. `git diff --check`
passes using the repository's configured CRLF normalization. A diagnostic run
with core.autocrlf disabled treated existing CRLF endings as whitespace; it was
not a source defect and no repository-wide line-ending rewrite was performed.

## Build, extraction and backup

The five-job production build passed. Installer SHA-256:
fb91cd8866895645fb30880160e31a35c814b22c2be1c6b2551fceefe94f80ed
(127079626 bytes). Its extracted shell differs from the unbundled Rust build
only at Tauri's single official bundle-type marker, UNK to NSS. Complete byte
comparison after that substitution passed. NSIS shell SHA-256:
e987fde14ebab4ab27b8a10482c1972f22f6a36906287bf2b83dacc6724592ff.
The original unbundled-shell receipt remains unchanged. Owning implementation:
tauri-utils 2.10.2 src/platform.rs; binding receipt: nsis-shell-binding.json.

The first extraction completed but serial hashing exceeded its 300-second
budget. The next verification caught the bundle-marker difference in the
verification assumption. Both failed receipts remain preserved. The corrected
bounded five-worker verification matched 29552 managed files; all 13 actual
packaged self-tests passed. No production acceptance check was removed.

The first private backup was refused while the tray process remained live.
The next sequential backup exceeded its 600-second budget; its partial directory
remains preserved. A fresh five-worker backup, r3, passed complete source/copy
hash and membership checks: 3719 inventoried user files, 100581931 bytes,
plus the previous installed app and uninstall-registry export. Model weights
were excluded from copying. The backup has a private current-user/SYSTEM ACL.
Private inventories are not included in this repository or public artifacts.

The production NSIS cleanup fixture passed all six scenarios: upgrade, fresh,
empty, locked file, managed-folder junction and root junction. Initial compiler
wrapper attempts reported failure despite a valid direct compilation. The
PowerShell helper now waits for an explicit compiler process and reads its
observed ExitCode, preserving stdout and stderr separately; the acceptance
checks and production installer are unchanged. The r3 receipt records all six
outcomes and expected refusal behavior for locked/linked paths.

Candidate WebView2 QA passed nine checks with the real candidate shell and real
RustXNG Full. Its language-model API is an explicit isolated local fixture;
it establishes UI/request lifecycle behavior, not real-model quality or GPU
throughput. The first UI attempt caught a missing client header in the fixture;
r2 passed after correcting that fixture. Isolated desktop/mobile screenshots
were inspected. No personal chat screenshot is published.

## Actual overwrite and normal startup

The standard NSIS overwrite passed under the resource guard (install-r1).
All 29552 managed files match the extracted installer; all 3719 inventoried
user files were unchanged immediately after installation. The installed exe
reports product 0.5.6-local.1. The private r3 backup remains available.

The actual installed shell/WebView2 passed all nine isolated UI checks
(installed-ui-r1), including side question during live main output, no main
cancellation or queuing, tool-free side API, separate durable aside, the
deepresearch slash option, real RustXNG Full public search, reload persistence,
and 390-pixel layout without horizontal overflow. Console/page errors: zero.
The model API was a local fixture, explicitly not GPU/model qualification.

The user app then started normally through its installed exe, outside QA, with
no debug arguments or automatic model loading. Its own API reports matching
host/shell 0.5.6-local.1, no native/runtime instances and a stopped supervisor.
Only this PC's selected search provider changed from builtin to rustxng through
the app API, as explicitly requested. The entire other tools view, key-set
state and approval choices compare unchanged. RustXNG uses the pinned Full
profile. The normal window is available with its model unloaded.

A later read-only status check during public readback found one ready legacy
runtime and a running supervisor, with zero native instances. No new unload
or interruption was performed: the upgrade's authorized stop/unload was already
complete. The no-model result above describes the measured initial normal
startup, not a permanent promise about subsequent app use. Windows uninstall
registration also reports 0.5.6-local.1 in the same existing install folder.

The unchanged signed feed was freshly verified using only the packaged
Control's bundled public keys; exactly one native and one Control package
verified. No signing private key was accessed. Archive and public download
checks are recorded below after completion.

## Frozen distribution package

bundle-r1 passed complete streamed 7z-to-tar readback of every member, with
matching byte counts and SHA-256 hashes. The outer archive uses 7z Copy mode
because its EXE/gzip/ZIP inputs are already compressed. Archive size:
1674393778 bytes; SHA-256:
14568efc35d53d8e0ab50b226ae6cf93a256780d470b0ab9a3f0cc598efbb60e.
The 17 whitelisted release assets include the same EXE, unchanged signed native
and Control packages/feed, exact RustXNG source/LICENSE/NOTICE, provenance,
quality limits, bilingual instructions and both checksum manifests. No models,
keys, personal memories or private inventories are included. The normal-start
setup recipe now requires an explicit --execute flag for future reuse.

The prior releases, asset IDs/digests, tags and stable Latest were snapshotted
before publication. GitHub connector capabilities are read-only for release
assets here, so the authenticated GitHub CLI performs this authorized upload.
Publication and anonymous readback have not been claimed by this prepublication
source tag; the following main-branch receipt records their actual result.

## Publication

Published preview:
https://github.com/zapabob/Strata/releases/tag/v0.5.6-local.1
Release ID 441271899, published 2026-11-11T05:34:02Z (14:34:02 JST).
The immutable annotated tag points to the prepublication recipe/evidence commit;
the packaged app source remains 6da4a421. Source, runtime and publication
identities are intentionally recorded separately.

All 17 assets uploaded without clobber. The first upload driver's final lookup
used the tag endpoint, which returned HTTP 404 for the draft despite a complete
upload. That failed receipt remains intact. The corrected driver finds the exact
draft through the authenticated release inventory and runs a separate read-only
verification action. It matched every server SHA-256 and size, then checked the
pushed immutable tag before publishing the same draft. No asset was replaced or
uploaded a second time. Postpublication metadata comparison confirmed all prior
24 releases, 25 tags, asset IDs/digests and stable v0.5.1 Latest unchanged.

The main-branch documentation now gives current 0.5.6 downloads and command
guidance in all eight README languages. The previous 0.5.5/0.5.1 measurements
remain labelled historical. These documentation and publication-helper fixes
do not rebuild or alter the frozen app or distribution bytes.

The first anonymous readback was stopped by the unchanged resource guard when
available RAM reached 3218317312 bytes, just below the 3 GiB floor. Its process
tree was confirmed absent; the user app was not stopped. Thirteen completed
public downloads already matched their frozen hashes. The two partial large
files and failed receipt are preserved. After available RAM recovered above
5 GiB, r2 started with one download worker. It reuses only fully size/hash-checked
public files from r1 and writes new large downloads to a fresh directory. The
resource floors are unchanged. Anonymous completion is recorded below only
after the final result exists.

Self-review-event: qa_defect. Fixes applied to verification drivers include
explicit NSIS compiler exit observation, official Tauri marker binding, exact
draft lookup and serialized readback with verified-cache reuse. The production
feature bytes and resource/security defaults were not weakened. Preserve all
failed receipts; no PC-wide skills, policy or global instructions were edited.
