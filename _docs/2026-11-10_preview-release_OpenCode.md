# 0.5.4-local.1 preview publication

Status: IN_PROGRESS. Agent: OpenCode. User requested the official-style installer,
a 7z distribution, a release tag and a rewritten README despite the retained
twelve resource violations. Objective: publish the exact tested binaries with
clear limits and independently verified distribution archives.

## Requirements and scope

REL-1: retain product0.5.4-local.1 / Control0.5.5 / native0.5.4 byte identities.
Use immutable tag v0.5.4-local.1 and GitHub prerelease status. No binary version
relabel is needed. This is publication of the measured candidate, not new
releaseQualified=true or general/full-window qualification.

REL-2: follow official Tauri NSIS Windows naming/layout, with a separate signed
GPU engine package. Add the fork's established real tar-then-7z one-download
bundle containing the same installer, engine/Control archives, feed, checksums
and instructions. Preserve all prior assets and frozen evidence.

REL-3: check source receipts, builtin trusted-key signatures, complete archive
membership/hashes, sanitized public metadata and the combined archive readback.
After upload, verify public asset digests and anonymous downloads.

REL-4: rewrite the README and installation/publication guidance around the new
preview download, custom features, tested scope and known failures. Keep stable
and preview routing explicit.

## Standards and decisions

Applied compatible canonical prompt and PC/project AGENTS, Common, Start Gate,
Skill Selection, DeepResearch, Security, Application, Internet Connectivity and
Python SOPs. Existing deepresearch-defense-standard / milspec-codex-standard
baseline and github-repo-management skill apply. No Goal API is exposed; this
objective and the task list track work. No formal compliance claim is made.

The default stable client expects the feed schema's stable channel. The preview
feed therefore uses that transport channel at its explicit immutable prerelease
URL, with preview warnings in signed notes. GitHub Latest and the default stable
endpoint are not promoted by publishing a prerelease. Channel is not a quality
flag. Manual engine import from this preview's own package is the desktop path.

## Primary sources inspected on 2026-11-10

- Official release API for Niko1221/Strata v0.2.13 and its checked-in
  packaging/UPDATES.md: Windows app is a Tauri NSIS EXE; GPU engines are separate,
  with signed manifests/feed, tar.gz engine and ZIP Windows Control packages.
- https://github.com/Niko1221/Strata/releases/tag/v0.2.13
- Fork release API for v0.5.1: existing NSIS, tar.7z, Control, signed feed,
  checksums and scripts. Older assets are preserved.
- https://github.com/zapabob/Strata/releases/tag/v0.5.1
- Current stable feed sequence20261105235321, read from its public asset.

The fork installer has no Authenticode or Tauri updater signature. No official
endorsement or equivalence to upstream's signing key is claimed. The existing
fork component/feed signing key is used only through the production signer.

## Artifact baseline

App/Control source85a78234; native source7bb24974, frozen separately on H:.
Exact tested installer112415417 bytes, SHA256
ae05518656ee5afdf92665f5dd71a06a69425ae1957a9ac31468d8a4a1790750.
Signed native manifest52e8674bf1dec83df9d972ec4fd5dfa5607bc9b1d30ec3eb99ade499de116ab3.
Build/install/model evidence remains in the preceding integration log and
H:/Strata/releases/upstream-0213-20261109-opencode/app-native054.
The app is left running normally; publication work does not alter user profiles.

## Verification and publication

Packaging, complete archive verification and README/version checks passed.
Tag creation, publication and anonymous readback remain pending.
Failed/NOT_RUN checks will not become PASS.
Known residuals remain twelve native resource violations, one observed Prism
warm-up timeout before passing rerun, incomplete full-suite/browser-fixture
checks and unqualified long-context/general/low-precision quality.

## Retained packaging attempt

The initial owned preparation created the exact EXE, signed engine tar.gz,
official Control ZIP and signed feed, verified engine and Control archive
membership/hashes, and created the inner tar. During second-pass LZMA compression
the unchanged3GiB RAM floor stopped the Job (RESOURCE_PRESSURE, drained, zero
active children). That failed receipt and partial7z remain preserved. No release
was created/uploaded. C: and H: floors were not relaxed.

The low-memory continuation uses 7z Copy mode because its inner EXE/gzip/ZIP files
are already compressed. It preserves the failed partial file and re-verifies
signed inputs plus streamed tar/7z member hashes before publishing a prepared
receipt. This is a packaging-method change, not a binary or quality change.

Copy-mode resume passed in90.300s, Job peak commit31354880 bytes, minimum sampled
available RAM19142033408 bytes. Contained before resume, native exit0, drained,
zero active children, no dropped output. Full tar/7z member SHA256 readback matched.
Bundle1654599858 bytes, SHA256
018dc44f6393f939b14c21c2a863e8e2813c46a8f25dd6929ce75c228d49a340.
The14 prepared public assets are fixed in H:/Strata/releases/public-054-20261110-opencode/prepared.json.

## Documentation and validation scope

English/Japanese READMEs were rewritten around preview download/install/features,
independent versions and measured limits. Six localized READMEs now have current
preview links, with their stable0.5.1 guides explicitly labeled historical/stable.
Supporter blocks are preserved. HAKUA_INSTALL, HAKUA_RELEASE, UPSTREAM_0213,
packaging README/UPDATES and the fork security-signing clarification align.
The release notes retain all known failed/NOT_RUN scopes and exact source identities.

The updater stores sequence per component folder across sources. Documentation
now explains that accepting preview sequence20261110000100 can reject the older
stable feed, and distinguishes installed-component rollback/separate state roots.
No anti-replay guard was removed. Packaged INSTALL.md remains its already hashed
version; the release notes and expanded installation guide add this detail.

Verification scripts default to a read-only plan. Local execution uses production
signed tar extraction/validation, real packaged private-Python CLI without model
execution, built-in feed trust and negative signature/architecture/replay cases.
Public execution is reserved until publication and requires all14 full anonymous
download hashes, GitHub digests, an annotated tag target and unchanged stable
release/alias/asset identities. New scripts and docs are the only source changes;
there is no new runtime build/qualification claim.

Self-review-event: qa_defect — initial compression hit the RAM floor. Review-only
governance response: choose bounded Copy packaging for already compressed inputs,
retain failed evidence, require full member readback. No AGENTS/Skill/SOP change.

## Local release gate — passed

`verified-local.json` and `receipts/verify-release-local-r1.{json,txt}` record:
14 fixed asset hashes/sizes;8 README supporter blocks unchanged and download/local
links checked; production tar.gz extraction/signature/hash/fit verification in a
fresh isolated H: component root; actual packaged private-Python CLI version and
update-check against the signed local feed; tampered feed rejected; unsupported
sm_86 rejected; older stable feed rejected after accepting preview in isolated
state; product-source consistency and all6 version tests passed. No synthetic
test-start, model execution or installed-profile change occurred in this gate.
Owned gate61.164s, native exit0, contained, drained, zero active children.

The publisher defaults to a no-write plan. Execution requires clean main, the
reviewed annotated tag, the local pass receipt, unchanged prepared hashes and
unchanged stable release/alias/assets. It creates a draft, verifies all uploaded
GitHub asset digests, then publishes a prerelease with latest=false. Existing
release/assets are refused rather than replaced. Anonymous full-byte verification
is a separate post-publication gate.

## Changed files and commands

Changed: README.md/ja/de/es/fr/pl/pt-BR/zh-CN, SECURITY.md (fork-signing scope),
docs/HAKUA_INSTALL.md, docs/HAKUA_RELEASE.md, docs/UPSTREAM_0213.md,
packaging/README.md, packaging/UPDATES.md, this log and
_docs/release-054-20261110/{prepare.py,resume.py,verify.py,publish.py,INSTALL.md,RELEASE_NOTES.md}.

Commands run through uv offline/no-project Python3.12.10 with UTF-8 and -B:
`prepare.py plan`; `prepare.py run --execute --key <opaque signer path>`;
`resume.py` (plan); `resume.py --execute`; `verify.py` (plan);
`verify.py local --execute`. Production package/CLI commands, environment,
deadlines, outputs and resource/Job evidence are in the immutable H: receipts.
`gh release view v0.5.1`, `gh api .../releases/latest`, `gh auth status`,
`gh release create/edit --help`, `git diff --check` and status/log were inspected.
No global dependencies, runtime sources or instruction baselines were changed.

Recommended next action: commit the reviewed release docs/recipes; create/push the
immutable annotated tag; run publish.py then verify.py public; record actual
publication and anonymous-download outcomes before completion.
