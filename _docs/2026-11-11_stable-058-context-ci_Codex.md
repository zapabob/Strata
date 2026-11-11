# Stable 0.5.8 — context, search guard and CI repair

The user requested fixing all four retained extended-test failures, passing CI,
committing/pushing main, and distributing/installing the next formal tar.7z
release. Start from clean main 9bbc77ecc6f51c4ed0b853fed14f8e8e84049aaa.
Keep 0.5.7 and earlier immutable releases/tags/assets unchanged. Retain native
0.5.5, Control 0.5.6 and RustXNG 0.31.1 Full unless owning evidence requires an
additional change. Preserve private profiles, learned skills, models and chats.

## Requirements and acceptance

CTX-1: dense repeated turns compact before a model-window refusal, and each
requested message receives its own answer. CTX-2: a message that fits after a
summary is summarized before sending, without a refused request. CTX-3: explicit
/compact uses measured figures after a completed turn and handles little history
plainly. GUARD-1: a search-heavy Plan run stops after the failed-search limit and
offers its current plan with the reason. Fix owning behavior or a demonstrably
invalid fixture, without relaxing these assertions or adding timing sleeps.

CI-1: run actual GitHub Actions Checks on the exact corrected product source;
inspect job conclusions and retained logs, and fix blocking failures. PACK-1:
fresh five-job 0.5.8 build, packaged checks, private backup, normal authorized
stop/unload when present, standard overwrite, installed WebView2 checks, archive
member hashes, signed component feed, immutable tag and stable Latest/alias.
PUB-1: full anonymous readback, retained older identities, final clean main push.

Use H:/Strata/releases/stable-058-20261111-codex for new receipts/cache/artifacts.
Keep RAM 3 GiB, commit 4 GiB, C: free 5 GiB and H: free 10 GiB floors. Builds
request five jobs. Retain failed attempts; no broad process kill or private data
publication. The task authorizes CI, fixes, main pushes, overwrite and release;
no redundant approval step is introduced. No subagents are requested or spawned.

## Standards and verification approach

Read PC/project AGENTS and canonical CLAUDE-FABLE-5.md; only compatible guidance
applies. Skills: milspec-codex-standard, debug-failing-test and gh-fix-ci; earlier
app packaging, documentation, browser QA and self-review guidance remain
applicable. Apply common/start-gate/skill-selection/security/application/LLMOps,
TypeScript and Python SOPs. Existing project tools and frozen resource guard are
preferred. GitHub connector commit-run lookup is PR-filtered and offers no
workflow dispatch/release upload, so authenticated gh CLI provides those actions.

First reproduce the four cases with actual Harness, read assertions and owning
context/turn lifecycle plus scripted worker, then add only targeted diagnostics.
Run the full 42-case context/tools/guard group after fixes, related bridge/skill
tests, typecheck, and the full host suite/CI. Scripted model behavior qualifies
integration only; native model quality remains independently unqualified.

## Observations and outcomes

The retained 0.5.7 group was 38 passed / four failed. Failures were alternating
echo answers, a pre-send-summary case with two refused requests, /compact
reporting busy after awaited turns, and a Plan loop producing one search instead
of the three-search guard limit. Fresh reproduction and CI outcomes follow.

Fresh reproduction failed all four cases. The diagnostic showed 59K characters
of this PC's global skill catalog entering a nominally isolated fixture. A
control run with an empty home passed all four unchanged assertions. The bridge
accepted an injected environment but its actual Harness child inherited the
process environment instead. HarnessProcess now receives the selected base
environment through the existing filtered child-environment builder. Ordinary
app defaults remain unchanged. Each fixture owns HOME/USERPROFILE and skill
roots. A separate real spawned-child regression verifies home selection, secret
filtering and explicit credential forwarding. The full actual-Harness group
passed 43/43 with no skips; fixed-four passed 4/4 under the real parent profile.

Checks was disabled by GitHub's inactive-fork workflow pause. The repository
Actions page explicitly showed that state; re-enabling existing workflows
allowed baseline run 42996154240 on 9bbc77ec. This did not change token scopes or
job permissions. Linux/Windows CPU builds passed. Baseline host tests failed
63/30 cases, tools failed 16/36 (Windows includes 26 fixed-H-drive setup errors),
and Linux serve failed one missing Node-fixture environment input. Baseline
Linux tests finished with 23 reported failed/error cases. Remaining baseline
jobs may be superseded by the corrected main push; retained completed logs are
under the fresh H: output. No baseline failure is represented as a pass.

Repair also completes 56 pre-existing UX translation keys in six languages,
adds two missing keys across all nine catalogs, normalizes French punctuation,
uses installed platform browsers in isolated profiles, updates stale fixtures,
and compares NTFS ACEs by resolved SID rather than the Administrator SDDL alias.
Windows process integration runs only on Windows, with an isolated H: volume in
CI and unchanged production evidence-path/resource policy. Pure policy tests
still run on other OSes. Source-NUL checks keep maintained source/top-level
scripts in scope and preserve UTF-16 historical evidence. Independent fork,
upstream and historical release identities are explicitly validated. Existing
image models are re-hashed on rescan even after a same-size, restored-mtime edit.

Local focused Python repair group passed 79 tests. The final copy/locale group
passed 27 tests. The first host-wide diagnostic timed out with owned cleanup;
its retained output and subsequent focused diagnostics identified startup and
profile dependencies. Direct focused commands now create private profiles too.
External Hermes-plugin checkout integration is explicitly opt-in; file/SQLite
memory and CLI fallback tests use only synthetic temporary profiles. New CI
includes a required actual-Harness Windows job pinned by installer SHA-256 and
component commit, without weights or service keys. Fresh main CI, packaging,
installation and anonymous release verification remain pending at this commit.

User steering after the initial repair explicitly selected app, Terminal,
Control and native engine all at SemVer 0.5.8. This supersedes the earlier plan
to reuse 0.5.5/0.5.6 payloads. New versioned builds, component signatures, source
binding, numerical/resource checks and installed acceptance are required. No
old binary is relabeled. Upstream reference and third-party versions retain
their own identities. The user also requested removing obsolete builds that
cannot support incremental builds and old worktrees. Clean inactive worktrees
are archived by exact commit before Git removes them; dirty/active trees,
published assets, private data, retained test evidence and the currently useful
native/Cargo caches are preserved. Cleanup plans/results live in the new H:
output and are verified before recursive removals.

Local host-full-r2 and focused-python-r3 were stopped at the unchanged 3 GiB
RAM floor; both owned jobs drained to zero. They are incomplete failures, not
passing test evidence. The first host-wide diagnostic timed out at its 1800s
deadline with zero remaining owned processes. No unrelated user process was
terminated. Remaining tests will be run sequentially as capacity permits.

Cleanup completed eight clean inactive worktrees. Their Git source archives total
887,029,760 bytes; archive commit identities were verified and local archive refs
retain the commits. Recorded H: free-space difference was +2.762 GiB (other
processes also use the disks). Dirty worktrees remain. The latest native and
Cargo caches, published assets and historical validation outputs remain intact.

The user separately approved normal Hermes model unload because the active
Hermes llama-server left only 4,774 MiB VRAM free. Its isolated console contained
only the identified model and stop helper, so one normal CTRL_C was sent. It
did not finish within the first 45 seconds. The user then explicitly approved
force termination of that exact PID; by the time a retained process handle was
requested, the process had already exited. No TerminateProcess call occurred.
Verified free VRAM became 14,875 MiB. The failed normal deadline and absent-target
force-attempt receipts remain separate. Broad Hermes-profile content encountered
by an overbroad search was not used in code, reports, memory or release assets;
that search was interrupted and subsequent inspection was restricted to owning
source and process metadata.

First coordinated source c629ee37 was pushed to main. Its pinned actual-Harness
CI job passed all 43 tests. Windows host typecheck/build passed, with 2062 host
tests passed, zero failed and 119 explicitly skipped. Linux Python tests passed
3845 tests and 491 subtests, with 109 explicit skips and one remaining synthetic
memory fixture failure. CUDA 12.9/13.0, HIP 7.2 and Metal compiled successfully;
SYCL exposed an outdated implementation signature, now corrected to accept and
reject the unsupported nonzero native-cache arena explicitly. No SYCL native
cache support is claimed. The current Windows CUDA build uses frozen c629ee37
and identical CUDA inputs; later app/Control source commits are recorded apart.

Follow-up fixes keep Chrome's POSIX temporary socket path short, use the real
Windows account root only for token discovery while browser profiles/data stay
private, handle case-only renames on case-insensitive APFS without replacing a
distinct hardlink, and make simulated PC setup targets explicit on Apple Silicon.
The Docker shell fixture now keeps its /run directory inside its own sandbox.
The capability generator uses the declared upstream reference inventory; the
benchmark index uses Git-tracked public files and ignores unpublished local runs.
Focused generators passed 9 tests. Host cross-platform follow-up passed 35 with
zero failed and two actual platform/privilege skips. Earlier failed attempts and
the third host-wide timeout remain retained with zero owned processes remaining.

Fresh snapshots were generated and reviewed across all 32 machine/model cells.
The first generation exposed eight invalid DeepSeek fixture loads that injected
a Qwen drafting setting; those records were rejected, never used as goldens.
The corrected fixture follows the model-family controls. The second generation
retains the unchanged 24 Qwen records and reruns all eight DeepSeek cells, with
no failed entry. The 448 reviewed field changes are explicit architecture and
existing Hakua private-cache configuration, disabled Q36-only requirements on
other models, and the DeepSeek fixture's family-specific default. Cloud snapshot
verification must still reproduce these records on both operating systems.

The synthetic memory fixture now creates its own SQLite schema instead of
depending on an existing personal database. The bridge previously returned saved
even when no backend stored anything; it now reports that case as false, with a
separate regression. PowerShell installer diagnostics use the actual Windows
OEM encoding when the parent Python is in UTF-8 mode. Full follow-up CI, native
qualification, formal packaging, installation and publication remain pending.

The final focused Python repair group passed 42 tests with five explicit external
Hermes/OS skips. The first negative storage test exposed the fixture's unclosed
SQLite connection; it now closes before testing missing storage. Current and
frozen CUDA source maps match all 779 files. One generated PowerShell analysis
cache was retained outside the checkout and removed from the source tree after
hash verification; direct test profiles now create all declared user directories.
No runtime cache or personal profile content is committed or packaged.

Main 7912cf72 includes the unrelated incoming issue-template update 5e406c14;
the first non-fast-forward push was resolved by rebasing the unpublished change
and pushing normally. CI reproduced all 32 regenerated snapshot cells, but its
separate entry-point parity gate exposed the fork's existing private-principal
differences. The explicit allowlist now validates the complete synthetic local
principal, requires exactly disabled prompt/conversation cache values in both
saved and executed arguments, and still compares every other engine argument.
A negative regression rejects enabling that cache. The app's explicit validated
architecture is checked separately. A simulated Windows hardware test now uses
its own sys object rather than changing the interpreter platform and breaking
Linux shutil.which. The focused follow-up passed six tests.

Native 0.5.8 build completed with five jobs. Stage, CPU, GPU, Compute Sanitizer
and unchanged CUDA spill/resource guard all passed. During the first model
attempt, another Strata Prism runtime had been loaded, leaving 7320 MiB free;
the model admission correctly refused its unchanged 14336 MiB floor. Normal
0.5.7 APIs unloaded one observed runtime instance; zero turns needed stopping by
then, no native instance was present, and no force kill occurred. The original
attempt remains retained. A fresh r2 evidence namespace repeats authoritative
binding, staging and every functional gate without changing the resource floors.

Fresh Control 0.5.8 was built from 7912cf72 with pinned Python 3.12.15 and the
locked runtime; its actual version and installer catalog check passed. It retains
that actual source commit. Current packaged Control source matches all 401 files
and its data verifier, independently of subsequent test-only/app changes. The
native freeze remains c629ee37 with all 779 CUDA source files identical. These
separate source identities are carried through the final package metadata.

The user changed the order to install the local candidate before completing
cloud CI and publication. The bounded local browser group passed all 36 cases
after giving cold browser launch its own 30-second deadline, sharing only the
browser process, and giving every case a fresh context and intercepted trusted
loopback origin. An intermediate untrusted synthetic origin broke UUID access;
that failed attempt remains recorded. No functional assertions were removed.

The Mac follow-up exposed completed owned install children remaining visible to
the non-procfs liveness probe. install_job now reaps owned children first. A
deterministic POSIX zombie regression covers that path. The synthetic HTTP
fixture does not perform reverse DNS, and simulated PC fixtures set the actual
architecture helper as well as their private platform object. The focused
installation/setup group passed 121 tests, with one POSIX-only skip on Windows.
Control must be rebuilt from this actual production source; the first 0.5.8
Control and its receipts remain intact, with a separate r2 adapter/output.

All 21 final numerical checks passed against the r2 bound native binaries.
The r2 protected-model protocol remains in progress. A second observed Strata
runtime was normally unloaded through the app API to recover GPU headroom; no
force termination was used. Eight obsolete build caches were archived privately,
decoded and checked against every source file before removal. Published assets,
dirty worktrees, active native/Cargo caches, models and evidence remain intact.

To honor installation first, a separate preinstall composition adapter requires
the completed source binding, stage, CPU, GPU, sanitizer, resource guard and all
21 final numerical cases. It records the protected-model protocols as pending,
never passed. The original strict native validator is unchanged. Publication
additionally requires finalize-native.py to validate the complete actual audit
against the identical signed manifest and engine bytes installed locally. This
changes the order of installation and qualification, not the final release gates.
The second Control build completed from 42ca8ebd, with actual source and pinned
runtime verified. Its earlier rejected wrong-commit invocation did not build or
stage anything; that invocation log remains retained separately.

Preinstall composition completed and verified the signed payload and its archive.
Its pending-model status is explicit; the full native protocol continues against
the same bytes. Backup verified 3,727 user files (99,920,664 bytes) plus the full
old managed app. All six actual NSIS cleanup scenarios passed in fresh fixtures.
The first NSIS invocation used a missing PowerShell path and executed no fixture;
its failed receipt remains separate from the successful observed-path r2 run.

Mac tools CI now passes 2,113 tests with five remaining simulated-PC fixture
failures. The HIP fixture now declares its simulated AVX2 CPU rather than probing
the runner. The fresh setup sys proxy forwards argv live, and the feed catalog's
MCP fixture selects a private PC sys object. The scoped Windows run passed all
99 tests, including a regression for later CLI argument replacement. No new
runtime change or Control rebuild is needed; all 401 packaged Control source
files still match. Docs now supports manual exact-source workflow dispatch.

App build source 91107e48 completed with five compiler jobs. The standard NSIS
installer is 127,118,039 bytes, SHA256
300252511099ed1a7b42d6a5c82bf6c6bc399da01e51933205a2365e15a9c384.
Packaged self-test passed. The overwrite matched 29,555 managed files and kept
all 3,727 backed-up user files unchanged. Shipped bundled installation/selection
code authenticated and installed the new native component with bundled trust
keys; actual app ProductVersion, global Terminal, embedded Control and both
native executable versions report 0.5.8. Previous engine manifests and entrypoints
remain unchanged. Normal startup passed unloaded, without debug arguments, with
RustXNG Full and both requested workflow options enabled; other tool/key/approval
choices stayed identical.

The actual installed WebView2 follow-up passed all 16 feature checks and emitted
zero console errors. Model API replies were explicitly synthetic; RustXNG made
a real query with results. The retained first attempt exceeded its response timer
during cold Harness startup. The second observed startup, then a closed page of
unknown origin. A synthetic Windows USERPROFILE prevented WebView CDP startup in
the third. The successful fourth keeps the real Windows account profile for OS
token lookup while isolating app/profile data and HOME, separates bounded cold
startup from the unchanged 30-second response deadline, and records its complete
normal cleanup lifecycle. The native model audit independently passed all three
protected protocols (7+7+2 requests), bounded/legacy parity and restart comparison,
with unchanged model hashes and all 21 numerical checks against the same binary.

Full Windows Python CI then exposed 15 H-volume fixture/owned-stdin mismatches
and one impossible full-line assertion on a narrow Windows footer. The developer
guard now names its unchanged H default as a module constant, so both fixture
layers use the same private test volume. Negative checks still reject the wrong
production volume. The footer test checks the nonempty visible prefix after
help closes; every help key is still required in full. The scoped run passed
33 tests. The related host fixtures passed 11 with two explicit Harness skips.
Mac host CI timed out after 1800 seconds and reported canonical-path cleanup
failures. The suite scratch root now resolves the /tmp alias before all private
environment paths are constructed. Mac suites are required and request one
runner at a time; logs are retained on every result.

These follow-ups change only unshipped tests, CI and developer validation tooling.
The app retains its actual 91107e48 build commit. Release binding compares every
later Git change against an explicit unshipped allowlist, expands the guard's
default constant back to byte-identical prior code, rejects any distributed
source change, rechecks Native/Control/installed Host source bindings and the
exact installer hash. The public records keep the actual CI and build commits
separate. All eight workflows and the complete named 13-job Checks matrix must
still pass before publication; no failed job is waived.

The same scoped Windows group also passed all 33 tests on C:, independently of
the real H: build drive. Its first C: attempt retained one owner-death fixture
failure: the separately spawned production CLI correctly reloaded its H default.
That fixture now configures its separate CPU-only interpreter explicitly before
calling the real runner, while production CLI admission remains unchanged.

The installed 0.5.8 app is now open normally. Eight cached old NSIS installers
were removed only after matching their retained private backup hashes; the
current installer, incremental compiler caches and published assets remain.
The 547dcd69 CI run passed both Windows/Linux host, tools and serving suites,
the pinned Harness and CPU checks. Mac tools never acquired a runner: GitHub's
annotations explicitly report macOS ARM64 capacity constraints. Both required
Mac suites now use macOS 26 ARM64, already allocated by this run's successful
Metal compile job. Four Linux container jobs failed before checkout/compilation
because archive.ubuntu.com and security.ubuntu.com could not resolve, including
the same-commit retry. Job-local public DNS and bounded strict apt index retries
address that preparation failure without changing compiler images, versions,
build flags, package authentication or test requirements. Full exact-head CI
remains required before publication; the installed runtime sources are unchanged.

The c2d8140c run passed all five backend compile jobs and Mac tools (2,119
passed, 89 skipped, 838 subtests passed). Mac host did not acquire a runner and
was cancelled with explicit capacity annotations. GitHub rejected its individual
retry while the Python suites were still active. Linux full tests reported one
test-only footer assertion failure, with 3,846 tests and 491 subtests passing.
The earlier prefix repair incorrectly used only Read only as the complete
default footer. The regression now requires exact restoration of the visible
footer observed before opening help, and exercises both default and long classic
console tips at both narrow sizes on every OS. All help keys remain mandatory.
This does not change the distributed Terminal or require a runtime rebuild.
The focused four-test module passed locally with both footer styles at both
sizes. The required Mac matrix now schedules the still-unexecuted host suite
first, then tools; both remain mandatory and serial. The new exact-head run
repeats the full Python suites with this corrected regression.
