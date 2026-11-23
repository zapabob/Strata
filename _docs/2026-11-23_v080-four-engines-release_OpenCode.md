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

## Evidence
(filled in as steps complete)

## Residual risks
- Windows Authenticode signing absent; SHA-256 digests only; `releaseQualified=false`.
- Speedups measured only on RTX 5060 Ti (CUDA 13.5 / sm_120); some figures come
  from Antigravity logs not independently reproduced in this build session.
