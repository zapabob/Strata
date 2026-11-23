# v0.8.0 — four optimized CUDA 13.5 SM120 engines, full release chain

## Objective
User request: main received a new commit (9b4b8b09f, "Optimize all 4 CUDA 13.5
SM120 native engines"); run the full chain — build everything, overwrite-install,
release, tag, rewrite all 8 localized READMEs.

## What was already done by the upstream engine commit
Commit 9b4b8b09f optimized four engines (DeepResearch-backed, Antigravity):
- `strata-inkling2.exe` — zero-spill AVX2 CPU MoE, zero-copy PCIe-mapped double
  buffer (`moe_up` 39.5 -> 3.5 ms, -91%), ST-MoE Rho bootstrap; Sakura 131K
  decode 20.93 -> 29.76 t/s (+42.2%), 32/32 exact tokens.
- `strata.exe` — Gen-F/G AVX2 math, reworked GGUF layer reader.
- `strata-q38.exe` — float4 norm kernel, SM120 CMake path fixes.
- `strata-hy4.exe` — Blackwell MUFU.TANH, float4 loads, ST-MoE decode bootstrap.
All four were rebuilt from that commit with 5 jobs; SHAs were read back:
ee456f23 / 1d74f57a / ab87e2e6 / fc776709.

## This session's work
1. Verified main was in sync (9b4b8b09f, behind=0/ahead=0, clean tree).
2. Built a new engine component 0.6.8 (155 files, schema 2 manifest, digest-only
   verification since signing is removed) from the 0.6.7 component layout plus
   the four fresh binaries. `strata-hy4.exe` is a new addition. `engine_component.verify(full=True)` OK.
   Packaged `strata-engine-0.6.8-windows-x86_64-cuda-cuda13.tar.gz`
   (1,536,644,379 B, SHA-256 52885b58bcff4d537f1a079538a640a483fbc96e964443e6ffadfcfa373f4ee7).
3. Bumped product 0.7.9 -> 0.8.0, engine family 0.6.7 -> 0.6.8
   (VERSION, package.json/lock, Cargo.toml/lock, release.json, 8 READMEs).
   `release_manifest --check` ok (0.8.0, engine 0.6.8). Cargo.lock libloading
   left at 0.7.4 (dependency, not the product).
4. Rewrote the "What changed" intro of all 8 READMEs (en/ja/de/es/fr/pl/pt-BR/
   zh-CN) for 0.8.0 with the four-engine details and the provenance note.
5. Rebuilt the Tauri/NSIS app with 5 jobs and the pinned public assets; the
   beforeBuildCommand rebuilt the host inventory and verify-release passed.
6. Tag v0.8.0 + GitHub release with four assets; public SHA readback.
7. Overwrite-installed on the real machine including the 0.6.8 engine component.

## Gen-H update and workflow restart (2026-11-23)
- While the first v0.8.0 build was cancelled at the user's request, main advanced
  to 21bedf91c ("Add Gen-H float4 k_mix/k_stack_rms_norm, Zipf vocab cache,
  zero-copy h_tok_buf, and 6D ShinkaEvolve genome"). This rebuilt `strata.exe`
  (SHA 50c2fdd8) and `strata-inkling2.exe` (SHA bc15a68b); Q38 and HY4 were
  unchanged. Gen-H `moe_up` 39.5 -> 4.6 ms (-88%), 32/32 exact tokens on Sakura 131K.
- Rebuilt the 0.6.8 component with those binaries (155 files, verify OK) and
  repackaged `strata-engine-0.6.8-windows-x86_64-cuda-cuda13.tar.gz`
  (1,536,648,216 B, SHA-256 58da074bb458bad11b0657207893885821eb96abaf2a672fb89bf34c4c8a2177).
- Added the Gen-H note to all 8 READMEs; `release_manifest --check` ok
  (0.8.0, engine 0.6.8); commit fb8e90b16 pushed to main.
- Restarted the app build (build-r2.log) with the same env/5 jobs.

## Evidence (v0.8.0 published and installed)
- Build r2: host inventory rebuilt + verify-release passed; Rust 5m32s;
  makensis produced installer 127,241,488 B, SHA-256
  `4f00c03c162efdf4e384cd77eb8ff68da1d04917e7b95c905c4ad21384fa2557`
  (7-Zip integrity test: 29,720 files, no errors). Parent shell hit the 1200 s
  timeout just after makensis finished — the installer itself was complete.
- NSIS upgrade/cleanup test 6/6; tar.7z 127,244,450 B, SHA-256
  `e0d4d89b5907e7e3b027326e088a2baafdeea20da5d5abdfd6c40ed57e24528a`.
- Tag v0.8.0 pushed (TAG_PUSH_EXIT=0); GitHub release v0.8.0 published with
  4 assets, all `uploaded` and public digests matching local exactly:
  setup 4f00c03c..., tar.7z e0d4d89b..., engine 0.6.8 58da074b...,
  hy4 0.1.64 fad3a195.... GitHub Latest = v0.8.0.
- Real-machine overwrite install: 29,714 app files; engine 0.6.8 component
  deployed (156 files: strata.exe 50c2fdd8, strata-inkling2.exe bc15a68b,
  strata-q38.exe ab87e2e6, strata-hy4.exe fc776709); registry 0.8.0; user
  settings SHA `6b7d7b11...` preserved; GUI launched with the host healthy on
  127.0.0.1:47831 and no new crash log.
- All 8 READMEs rewritten for 0.8.0 / engine 0.6.8 / upstream v0.2.20 with the
  four-engine + Gen-H details and the provenance note; `release_manifest --check` ok.

## Post-release note
During this workflow main advanced again to 232f8cf8b (12:27 JST, "Gen-I/J AVX2
q8_0_quant_avx2, LeCaR online regret cache, HY4 float4 iHC kernels") and the
engine binaries were rebuilt at 12:22 (strata.exe 6ac28c84, strata-inkling2.exe
17759a44). Those binaries are NOT in v0.8.0, which carries the Gen-H set.
A further patch release would be needed to ship Gen-I/J.

## Residual risks
- Windows Authenticode signing absent; SHA-256 digests only; `releaseQualified=false`.
- Speedups measured only on RTX 5060 Ti (CUDA 13.5 / sm_120); some figures come
  from Antigravity logs not independently reproduced in this build session.
