# Hakua / Strata 0.5.9

Windows local-model loading and generation now have host-side physical RAM
admission and continuous containment. Fully GPU-resident loads reserve staging
and mapped-page headroom. Pressure stops only the owned engine and reports how
to reload; the host never silently reduces context or changes user preferences.

Research gathering offers only web search and page retrieval. Final writing has
no tools, and direct or stale disallowed calls are denied without approval
prompts. The original chat's ordinary capabilities return after research.

Inventory CSV audits have a deterministic comparison tool. It compares exact
versions by ID, reports duplicate/missing IDs and counts non-passed checks.
A passed check does not require invented additional verification evidence.
Malformed or incomplete CSV is rejected. File access still uses the ordinary
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

Exact build commits, test/actual-model results, CI, installation and public
readback are recorded in the delivery log and packaged quality records. This
source draft does not itself assert those pending gates passed. General model
quality, full-window inference and GPU concurrency remain unqualified;
releaseQualified=false. The Windows installer lacks Authenticode signing;
component/feed signatures are independently verified.

Thanks to [Strata](https://github.com/Niko1221/Strata),
[llama.cpp](https://github.com/ggml-org/llama.cpp),
[RustXNG](https://github.com/sahenjp/RustXNG) and
[Hermes Agent](https://github.com/NousResearch/hermes-agent).
This independent fork does not imply upstream endorsement.
