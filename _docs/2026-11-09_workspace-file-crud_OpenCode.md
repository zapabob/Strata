# Sidebar workspace file CRUD

Date: 2026-11-09. Agent: OpenCode. Status: in progress.

## Request and acceptance

The user clarified that the left folder means Strata's own sidebar. Add access
to existing workspace files with create, read, edit, rename and delete operations.
Continue the five-job incremental build and overwrite task with this feature.
Use `C:/Users/downl/Documents/ChatGPT/Strata` on main. Preserve existing repository
files, previous artifacts, user conversations, settings and model weights.

Acceptance: an explicitly opened Files section lists existing on-disk files,
navigates folders and paginates large directories; text can be read/created/edited;
items can be renamed, moved to workspace trash and restored. Concurrent external
edits must not be overwritten. Only a registered workspace is addressable. Verify
desktop and narrow layouts, keyboard operation, Japanese labels, error handling,
API boundaries and actual disk effects. Installed-app verification remains required.

## Applicable standards and design

Applied the compatible canonical pre-implementation context, PC/project AGENTS,
Common Engineering, Start Gate, Skill Selection, Security, Application, WebApp,
Frontend Design and TypeScript SOPs. The supplied MILSPEC baseline remains active.
The existing kit tokens, Dialog/Btn/IconBtn primitives and design-system notes
are the visual authority. No new dependency or new visual-token family is needed.
No subagent was used. Initial routing used local file routes, origin enforcement
and path/folder helpers. The later Windows replacement metadata edge case was
checked against official Microsoft primary documentation and fresh local tests,
as recorded below. The pinned local Node is used throughout.

## Implementation

`apps/host/server/workspace-files.mjs` provides bounded directory pages and UTF-8
text access. Writes require revision agreement; an edit is staged and fsynced
before replacement, preserving CRLF and BOM. Paths are relative to a registered
workspace, reject traversal/drive/ADS/control directories, and reject nested
symbolic links/junctions. Binary/oversize content cannot be overwritten by the
text editor. Delete is a same-workspace rename into `.strata-trash`, with metadata
and Undo; original user file contents are retained. There is no recursive removal
of user folders. The only cleanup unlinks remove newly created request scratch
or metadata after an unsuccessful operation.

`index.mjs` adds the entry/create/update/rename/trash/restore/open routes behind
the existing Host origin checks. Unknown workspace IDs do not fall through to a
different write target. The old file-preview route's default primary read remains.

`WorkspaceFiles.tsx` adds a collapsed, on-demand Files section beside each
workspace's chat list. It uses real APIs, explicit loading/error/empty states,
visible item actions, a text-editor dialog and reversible trash. New text lives
only in the editor until Save. The app does not need a model to manage files.
The stylesheet uses existing kit tokens. Eighteen new labels have nine catalogs.

## Source checks so far

Ran the project wrapper with H: scratch and serial Node tests:
`node --test --test-concurrency=1 tests/workspace-files.test.mjs tests/workspaces.test.mjs`.
First run:9 passed/1 failed. The integration fixture's explicitly configured work
folder had not been created; the real API correctly returned404. The fixture now
creates its own folder before starting the Host. Second run:10 passed,0 skipped.
Coverage includes real Host HTTP CRUD/origin/scope checks, original-file byte
retention, CRLF/BOM, stale saves, Unicode names, collisions, nonempty folders,
traversal/ADS/drive paths, actual Windows junction refusal and directory paging.

`node --max-old-space-size=1024 node_modules/typescript/bin/tsc --noEmit` passed
after narrowing caught errors to strings before the existing error formatter.
Browser and installed-app results are pending; no GUI success is inferred from
these unit/HTTP checks.

The source browser check then passed eight actual UI/disk scenarios in Edge:
existing-file edit, create, rename, reversible trash, folder navigation, rejected
stale save, Japanese/mobile display and keyboard close. Page errors:0. A failed
first browser fixture had changed Edge's Windows identity with the Host sandbox;
the fixture now keeps the browser's original OS environment while the Host stays
isolated. The next run exposed editor ownership across sidebar breakpoints;
workspace widgets now stay mounted while hidden, so the dialog/draft survives
resizing. The passing run explicitly resizes from1600 to1100 and back with a draft
open. Source-browser receipts/screenshots are under the H: release root's
`crud-browser-r3`, separate from installed-EXE acceptance. Editor CSS specificity
was subsequently adjusted to retain its intended45vh height over the base input
rule; fresh visual confirmation follows.

The final CSS/source browser run `crud-browser-r4/result.json` passed the same
eight UI/disk scenarios with0 page errors. Both1600×1000 and430×900 screenshots
were inspected; the editor fits, wraps its mobile actions and preserves the draft
through sidebar breakpoints. The broader monitor-only component test initially
could not bundle the newly imported stylesheet; its existing unrelated-child
boundary now also isolates WorkspaceFiles, while the real file UI remains covered
by the separate browser run. This does not count as browser or file-CRUD coverage
from the monitor test.

After the boundary update, all6 monitor-state/translation checks passed. The app
helper suite passed15 checks, including a real Git repository with a Japanese
tracked filename and the nonconflicting isolated Q36 fixture. The helper now
decodes Git output explicitly as UTF-8, opens Japanese Expert mode only after
the translated control appears, seeds both app and Terminal settings in the
test home, starts Q36 with legacy memory and lets the UI explicitly select bounded
mode, and verifies the actual settings path stays inside that fixture.

## PR3 integration

The user reported merging fork PR3. GitHub confirms merged commit
`3a9bd2f4ad3225b25c00af68eebfd26829c7e6c7` (2026-11-09T13:02:40Z).
Its diff is limited to three16GB benchmark files: README, measurement schema and
workload manifest. C: main was fast-forwarded from ff299806 to3a9bd2f4.
The complete working source diff, untracked paths and all8 untracked content
hashes matched before/after. The native frozen checkout is unchanged. The98K
ladder is benchmark planning/schema source, not evidence of a near-full run or
new quality qualification; its provisional watchdog does not lower local floors.

## Fresh file-enabled package boundary

Use `H:/Strata/releases/local-053-20261109-opencode/app-files` for the new app
output. Preserve the earlier `app` directory, its ff299806 installer and all
failed/passing attempts. Reverify the unchanged signed native payload/archive
before copying its native-only receipt into the fresh output; do not transfer
the old app's13 self-tests as qualification of the new GUI. Native measured
bytes/source remain independently pinned. New Control staging also preserves
the previous tree in a distinct local archive directory.

The new real-app recipe requires workspace-file CRUD acceptance in Q36's
isolated actual WebView2 before candidate/installed acceptance can pass.
It checks existing-file edits, creating raw text without HTML execution, rename,
trash/Undo, folder navigation, external-edit conflicts, Japanese/mobile layout
and keyboard close. The source-browser pass is separate from this installed
acceptance. The feature and PR3 must be source-frozen, rebuilt with five jobs,
qualified and backed up before overwrite.

## Packaging continuity and remaining work

The previous ff299806 candidate installer is already built and its13 production
self-tests passed, but has not been installed. Its model GUI acceptance is still
in progress. It will be preserved when the new sidebar source is packaged.
Native source remains independently frozen at ded724a4; actual five-job native
incremental rebind15.297s retained identical measured bytes. The12 CUDA resource
findings and all qualification-false flags remain attached to the native package.

The prior GUI QA attempts exposed historical-root assumptions, missing language
reload waits and conflicting raw memory flags in the test fixture. They remain
failed evidence. The isolated fixture/navigation will be corrected in the tracked
helpers before the next package; no real model result will be mocked or inferred.
The old installed app/model was separately stopped through approved normal APIs
when it reopened and locked a runtime file. Source settings were preserved.

## Residual risks and next actions

Filesystem checks are defensive within the selected workspace. They are not an
OS sandbox against a hostile same-user process racing filesystem changes. Files
larger than200KiB and non-UTF8/binary files can be opened in their own app, renamed
or trashed, but are not edited as text. Trash entries remain on disk; no automatic
trash purge is introduced. Browser layout/interaction and installed payload checks
must pass before completion. Preserve all failed receipts and archived artifacts.

Self-review-event: qa_defect (fixture directory and typed error boundary caught
by fresh tests). Narrow fixes were made; no resource, origin, scope, source,
signature or installed-target gate was lowered. Broader governance changes are
not justified by these findings.

## Windows destination metadata

For bounded defensive API verification, checked these primary sources on
2026-11-09: [Win32 ReplaceFileW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew)
and [.NET File.Replace](https://learn.microsoft.com/en-us/dotnet/api/system.io.file.replace?view=netframework-4.8.1).
Applied SOP DeepResearch and the supplied defense baseline for this narrow API
semantics review; no package, trust-key or compiler dependency was added.

Windows saves now use the built-in metadata-preserving replacement with metadata
merge errors enforced. Scratch and previous text contents stay in private
workspace trash; backups and the original are not discarded on a failed replace.
The existing private-directory helper is reused, and a local trash .gitignore
prevents accidental Git staging of retained data. The child receives validated
paths as environment values, not interpolated commands; output is suppressed,
the command is fixed to System32 PowerShell, and execution has a15-second bound.
A fresh digest check rejects intervening content changes. No OS sandbox against
a hostile same-user filesystem racer is claimed.

Latest dedicated file module tests:9 passed,0 skipped. The added Windows test
measured unchanged destination DACL digest, retained Zone.Identifier stream,
new text at the original path, and old text in recovery storage. The case-only
rename test also passed while a different existing destination was preserved.
These tests are local observations, separate from documentation-backed semantics.
The final post-change source browser run `crud-browser-r5` passed all8 UI/disk
checks with0 page errors. Internally generated Windows paths now use extended
names for deeply nested existing files; request paths remain relative and scoped.
The final dedicated module run passed10 tests,0 skipped, including an actual
Windows path longer than260 characters. A generated PowerShell ModuleAnalysisCache
and the earlier ff299806 frontend output were preserved by same-volume rename;
`files-source-preparation.json` records both inventories with0 lost files.
