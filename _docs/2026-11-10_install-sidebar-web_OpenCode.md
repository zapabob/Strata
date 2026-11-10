# Installation entry points, folder chat deletion and proactive browser search

Agent: OpenCode. Status: IMPLEMENTED_INSTALLED_AND_PUBLISHED; measured limits below remain.

## Requests and scope

The user requested an easy installation entry point in the main repository,
one action to remove a sidebar folder's conversation history, more proactive
local-model web search, and browser/computer-use search. These steer the ongoing
055 distribution work; older artifacts and evidence remain immutable.

Apply PC/project AGENTS, compatible canonical prompt, Common/Start Gate/Skill
Selection, Security, WebApp/Frontend, Application, Internet, LLMOps, Python and
TypeScript SOPs. The desktop's existing Dialog/FloatingMenu/semantic styles are
the visual authority. No new UI design system or dependency is required. The
milspec/deepresearch baseline and llmops-manager prompt-management skill apply.
No Goal API is available; the working task list and logs record the objective.

## Source and artifact boundary

The native055 source b995af13 passed its final source-bound numerical/resource/
protected-model checks; see2026-11-10_release-055-repair_OpenCode.md. User approved
the local app checkpoint0ac20baaa3cc55bd5959145bcac5ff462daa1518. Its signed engine,
Control0.5.6 and five-job incremental desktop build passed. Installer112429779
bytes, SHA2a50e3ac32d9b0a2a06a84e5f2b091eebee83e961f5179d8e0c33564aa3639bb.
Its first archive qualification failed before self-tests: the outer owned runner
sanitized PATH and powershell.exe was absent. A targeted exact probe reproduced
ENOENT. Read-only source/resource/archive checks passed independently. Fresh
delivery-r4 adds the explicit Windows PowerShell tool directory, retaining all
assertions. Qualification r2 then passed, including13 production self-tests.
The failed receipt/extraction remains in app-native055/attempts/qualification-r1.

The user subsequently requested the new UI and search features. That installer
does not contain them. New app source and new packaging/installed evidence are
required; do not publish or install it as if it did. Native bytes need not be
rebuilt for app-only changes. Publication and actual installed055 acceptance have
not occurred.

Normal maintenance was separately approved. When the first normal-unload helper
ran, the normal shell was already absent, so it failed before acting. A later
normal shell was verified by its old packaged hashes; its model unload API and
WM_CLOSE were used, but the shell did not exit within60s. Preserve that failed
receipt. Minimize-to-tray is a possible explanation, not a proven stop. No forced
kill, credential extraction or settings change was used.

## Folder conversation deletion

Sidebar workspace menu now offers Delete all chats in folder. Its confirmation
names the folder and count, includes archived chats/old workspace aliases and
captures an explicit ID set. A chat created after confirmation is excluded. The
action checks for a running reply again at execution. It uses the existing host
chat writer and per-chat delete routes, preserving their client/origin checks.
Refused deletes return visibly to the folder and cancel the writer's delete
retry; other folders and actual workspace files are retained. It does not delete
models, memory or files. This is the existing permanent-chat-delete semantics.

Changed: Sidebar.tsx, store.ts, nine locale files, the new
workspace-chat-delete.test.mjs, and the Monitor component's existing store stub
for newly imported sidebar actions. QA browser/locales drivers were extended.

Verification under unchanged owned Job floors:

- bulk-delete-red-r1: fixture workspace-file lookup failed; some tests also
  reported the missing implementation. The fixture was corrected, not production.
- bulk-delete-red-r2: all3 cases reproduced the missing bulk-delete function.
- bulk-delete-green-r1:3passed over the actual writer and disk store.
- bulk-delete-focused-r1: Windows --import received a path instead of a file URL;
  failed before test execution. r2 used the explicit file URL and22tests passed.
- bulk-delete-typecheck-r1: passed. bulk-delete-locales-r1:29 sidebar keys in all
  nine catalogs, no new missing key; placeholder indices/counts match even when
  Japanese reorders them.
- sidebar-bulk-delete-r1: real Host refused an unnamed fixture chat request403.
  r2 supplied the existing required UI header and passed12 checks,0page errors.
  It verifies all26 target chats, including one archived and rows beyond the
  sidebar's20-row display, cancellation, another folder, a later chat, persistence
  after reload, existing file preservation and Japanese mobile confirmation.
  The430px screenshot was read and checked for clipping/overflow and action labels.

Commands: uv/offline Python3.12 via _docs/repair-055-20261110/run.py, node --test,
tsc --noEmit, locales.mjs and browser.mjs. Complete receipts/screenshots remain at
H:/Strata/releases/repair-055-20261110-opencode. These are source/UI results;
installed bulk-delete acceptance remains pending.

## Next actions and residual risk

Finish the installation index and browser/search implementation; verify real
isolated browser tools and permissions. Rebuild app/Control from a reviewed
checkpoint, then run packaged/installed model, agent and sidebar checks. Actual
LLM tool-choice quality needs real-model evidence; prompt text or a scripted
worker alone is not proof of improved autonomous search. Existing Manual/Plan
permissions, user-disabled tools, search backoff and private profiles remain
acceptance boundaries. Historical Prism timeout cause remains unconfirmed.

Self-review-event:qa_defect. Evidence: PATH/ESM-import/UI-header fixture failures.
Decision: correct only the command/fixture boundary, keep failed receipts and
unchanged assertions; no broad governance edits or relaxed quality gates.

## Installation index

Added root INSTALL.md as the short Japanese/English entry point, linked at the top
of both primary READMEs and from HAKUA_INSTALL.md. It separates stable051, published
054preview and the pending055 feature installer, names the actual EXE/engine steps,
and maps source setup, packaging, workspace/browser guides and _docs evidence.
Large artifacts/models/history were not moved or deleted; public URLs stay at
their verified immutable releases. Updated WORKSPACE_FILES.md to match action
menus and document the new permanent chat deletion versus reversible file trash.

## Proactive search and browser computer-use source

preset.mjs appends capability-aware guidance to local-model profiles: use an
available web_search for current/uncertain facts, prefer primary sources and cite
pages actually read. Greetings/arithmetic/rewrites stay direct. Disabled search,
Manual approvals, source distrust, private data and provider rate limits remain
boundaries. API-only/base persona text is unchanged. Browser-enabled profiles
describe actual isolated search/type/result-reading, refs and observed coordinates.

profile.mjs now supplies --caps vision --snapshot-boxes and explicit image-response
mode to the already staged @playwright/mcp0.0.80 (no dependency update). The actual
CLI --help confirms these options. The default text-only local model gets omit;
a declared vision-capable route gets allow. This does not add native image input.
Coordinate calls still ask in Manual and are denied in Plan. Existing browser
enablement remains the user's Settings switch, not a new always-on browser.

agent-search-red-r1 reproduced missing policy/capabilities:1pass/3fail.
agent-search-green-r1 passed7 policy/OS tests. Extended source tests add actual
coordinate permission cases. browser-harness-tests-r2 passed27tests with0skips,
including the real staged Harness, tool refresh and actual Chrome/Edge navigation/
snapshot, with Manual approval/denial and Plan refusal. r1 had26passes/1failure
because the opt-in loader forced headless into an exact headed-argument test;
the fixture now leaves that switch to the real-browser test's own scoped setup.

browser-search.mjs directly exercised the production profile's real MCP/installed
browser. Fresh r7 passed coordinate-tool inventory, real query typing/submission
and coordinate click opening the fixture result. These calls are scripted,
explicitly not autonomous-model-selection evidence. r1–r3 retained fixture issues
(snapshot supplied as a file rather than inline; current tool schema uses target,
not ref). Their corrections request an explicit current snapshot and use the
tool's actual advertised schema. No production gate was relaxed.

Public search qualification did not pass. r4's public step initially accepted a
query echoed in the page title: review found no result-link evidence. Preserve
that original receipt, but invalidate its public-search claim. The stricter r5
Bing check failed for lack of result links. r6 DuckDuckGo displayed a Japanese
human-verification challenge; it was not solved or bypassed. No live search
retries after that refusal. r7 isolates the deterministic local browser path;
it does not turn the public-site failures into PASS. Public browsing and real
LLM search-choice quality remain unqualified for the new installer.

Self-review-event:local_fix/qa_defect. Evidence: browser fixture revisions and r4
false-positive public assertion. Response: explicit snapshots/schema validation,
require actual result links rather than query echo, preserve independent
local/public results and the refused provider evidence. Only narrow local QA
notes/docs changed; rejected stealth flags, CAPTCHA bypass, weakened assertions
and broad self-modification. docs/BROWSER_SEARCH.md states setup and measured limits.

## Next package preparation

Fresh adapters/delivery-ui-search-r1 and app-native055-ui-search output roots
retain the earlier0ac20baa installer and all earlier adapter revisions. The
permanent generator includes the PowerShell PATH correction. Its packaged
workspace helper now requires actual bulk-delete confirmation/cancel,26+ chats,
archive inclusion, another folder/later-chat preservation, reload persistence and
file retention in the real packaged WebView2. Native evidence remains bound to
b995af13 and is independently revalidated, not rebuilt or promoted.
prepare-ui-search-delivery-r1 and validate-ui-search-delivery-r1 passed generated
code/recipe syntax, all read-only plans and completed native evidence checks.
Helper flake8 E9/F and git diff --check passed. No new dependency was added.
The next action is a reviewed clean app-source checkpoint, then fresh signed
staging, Control/app build, packaged and installed acceptance. This log's current
source features are not yet installed or published.

The user explicitly approved committing these additional features and continuing
the installer rebuild/actual-machine checks. The checkpoint includes only the
reviewed UI/prompt/docs/QA files; secret/payload scanning and staged diff checks
precede the commit. This approval does not authorize a Git push or PR creation.

## Installed closeout

Fresh app/Control35863dea and nativeb995af13 passed candidate then actual installed
Q36/Prism/agent/restart/bulk-delete acceptance. The C:payload matched29544files.
Backup4078files includes three exact size/SHA-reviewed large non-weight files;
unknown large files still fail. Initial backup refusal and missing-temp-config
activation failure remain. Fresh captured-live-config Q36 acceptance and required
signature/full test-start passed afterward. Normal startup is open/no-debug/
unloaded. Browser/search is enabled through the actual verified Host; provider/
key/approval/other-tool choices remain. No new installer rebuild followed QA.

The user subsequently approved push to main and055prerelease publication, plus
normal model unload to finish publication after resource-floor pressure. Prepared
hashes/publication/anonymous readback are tracked separately in
2026-11-11_preview-055-release_OpenCode.md. The earlier local-only approval note
above describes its time, not that later publication approval.
