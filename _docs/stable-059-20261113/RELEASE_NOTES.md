# Hakua / Strata 0.5.9

Windows local-model loading and generation now have host-side physical RAM
admission and continuous containment. Fully GPU-resident loads reserve staging
and mapped-page headroom. Pressure stops only the owned engine and reports how
to reload; the host never silently reduces context or changes user preferences.

Research gathering offers only web search and page retrieval. Final writing has
no tools, and direct or stale disallowed calls are denied without approval
prompts. The original chat's ordinary capabilities return only after completed research; cancelled sessions remain restricted and are retired.

Inventory CSV audits have a deterministic comparison tool. It compares exact
versions by ID, reports duplicate/missing IDs and counts non-passed checks.
A passed check does not require invented additional verification evidence.
Complete consecutive read-tool line labels are removed before parsing; malformed or incomplete CSV is rejected. File access still uses the ordinary
read tools and requested writes keep the existing approval policy.

App, Terminal, Control and native engine use coordinated SemVer 0.5.9. RustXNG
remains 0.31.1 Full and other third-party components retain independent versions.
Fresh profiles keep skill learning and automatic application off; existing
choices are preserved. Older immutable releases and assets remain available.

The tar.7z contains the standard per-user NSIS installer, signed native and
Control components, installation instructions, notices, corresponding RustXNG
source and checksums. Verify SHA256SUMS.txt, extract 7z then tar and verify the
internal BUNDLE-SHA256SUMS.txt. Finish work, unload models, back up data and quit
Strata including its tray icon before running the EXE over the existing install.
Models, chats, keys and personal data are excluded from distribution.

Local verification passed: 13 packaged self-tests, 6 NSIS cleanup scenarios,
16 installed WebView2 checks with an explicit fixture model and real RustXNG,
and actual local-model workflows using explicitly selected PrismML 0.4.1.
The two saved CSV audits each had counts 1/0/0/0. Workflow learning generated a
private skill and the next task applied it without manual selection. Research
made four distinct searches and read four official pages, without workspace
writes or manual denials. The installed payload matched all 29558 managed files;
all 3789 inventoried user files were unchanged during the final overwrite.

A real UI attempt encountered falling free RAM. The production guard stopped
only its owned model at 8447000576 available bytes, above the unchanged 3 GiB
floor. After resource readback, the same model was reloaded without changing
any guard threshold and the UI /btw answer 42 was observed and persisted.
Final cleanup unloaded the model and restored user choices. All ten original
skill entries, tool/key/approval choices and model settings matched their
checkpoint after returning to the normal user profile.

These are workflow and containment checks, not a general answer-quality pass.
The generated Rust explanation incorrectly implied that Copy automatically
supplies Clone; Clone must also be implemented or derived ([official reference](https://doc.rust-lang.org/std/marker/trait.Copy.html)). One fetched official
page was the historical Rust 1.8.0 book. This observed model-answer limitation is
retained in QUALITY.json. The trunk-only Qwen3.5 test GGUF required explicit
PrismML selection; the unmodified GGUF did not load with the fresh Automatic
runtime choice. Native 0.5.9 has its separate signed-source and numerical evidence.

All eight required workflows and all thirteen Checks jobs passed on app/source
commit e6bd6a4ebc8b5e8a0c6f68de8acf76a861adeb49, including Windows, Linux
and macOS host checks. Source binding verified all 779 native and 401 Control
input files and the exact installed Host. Exact app/native/Control build commits, installation and public readback
are recorded in the delivery log and packaged quality records. General model
quality, full-window inference and GPU concurrency remain unqualified;
releaseQualified=false. The Windows installer lacks Authenticode signing;
component/feed signatures are independently verified.

Thanks to [Strata](https://github.com/Niko1221/Strata),
[llama.cpp](https://github.com/ggml-org/llama.cpp),
[RustXNG](https://github.com/sahenjp/RustXNG) and
[Hermes Agent](https://github.com/NousResearch/hermes-agent).
This independent fork does not imply upstream endorsement.
