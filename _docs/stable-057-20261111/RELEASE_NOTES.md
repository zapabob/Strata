Hakua / Strata 0.5.7 adds real `/btw` subagents, learning from completed
agent workflows, and automatic application of matching skills. This is a Windows
stable release of the zapabob fork, using upstream's per-user Tauri NSIS app layout.

`/btw` starts a tool-free Harness child under an isolated side parent. The parent
makes no model request. Main-chat history, generation and Stop remain separate.
The selected model and completed-message snapshot stay fixed for the request.
Helper assistants must be enabled; unavailable delegation has no direct-answer
fallback. A single-slot model may queue inference.

In Skills, opt into learning and automatic application independently. Eligible
completed workflows receive one bounded, tool-free review by the same task
model. Host-observed successful tool steps become private, editable SKILL.md
documents. Raw file contents, tool outputs, full transcripts and saved keys are
excluded from the review packet. Complete matching documents can then be applied
to agent work, research and goal/plan steps, respecting triggers, workspace scope,
manual edits and approvals. Revision history, status, retry and undo are exposed.
Both options remain off in new profiles.

The stable app retains `/deepresearch`, RustXNG 0.31.1 Full, native engine 0.5.5,
Control 0.5.6 and the previous signed component feed bytes. Full queries enabled
external providers. Paid providers need their own configuration. This release becomes GitHub Latest and the mutable latest alias. All historical
releases, assets and immutable tags remain unchanged.

The tar.7z contains the identical EXE, signed engine, Control, instructions and
internal checksums. Extract 7z, then tar. Finish requests, unload models, back up
data and quit Strata including the tray icon before overwriting the existing
installation. Models and personal profiles are excluded. The EXE has no Windows
code signature; component signatures are separate.

Validation and exact download hashes are in QUALITY.json, SOURCE.json and
SHA256SUMS.txt. Real Harness/tool execution and installed WebView2 checks use a
scripted model and do not qualify general model quality or GPU concurrency.
Broader native/full-window/low-precision quality remains unqualified:
releaseQualified=false. Earlier broad-suite failures remain recorded separately.
Local verification passed: 65 focused host tests, 15 actual Harness cases,
13 packaged self-tests, six NSIS cleanup scenarios and 16 installed WebView2
checks. The exact build SHA had no matching GitHub Actions run when checked;
no cloud-CI success is claimed.

We appreciate [Strata](https://github.com/Niko1221/Strata),
[llama.cpp](https://github.com/ggml-org/llama.cpp),
[RustXNG](https://github.com/sahenjp/RustXNG), and
[Hermes Agent](https://github.com/NousResearch/hermes-agent).
The Strata, llama.cpp and RustXNG official URLs and credits are retained in all
eight README languages. Hermes is credited in the workflow guide and English
README. This fork is independent; no upstream endorsement is implied.

[Workflow settings, data and undo](https://github.com/zapabob/Strata/blob/main/docs/WORKFLOW_SKILLS.md)
· [Delivery evidence](https://github.com/zapabob/Strata/blob/main/_docs/2026-11-11_stable-057-release_Codex.md)
