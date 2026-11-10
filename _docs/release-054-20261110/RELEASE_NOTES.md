# Hakua / Strata 0.5.4-local.1 — Windows preview

Official Strata **0.2.13** integration, retaining Hakua memory, existing GGUF
reuse, Qwen3.6 private conversation caches and reversible workspace file CRUD.
This is the zapabob fork, packaged in the upstream Windows Tauri NSIS layout.

**Prerelease. Twelve CUDA resource-guard violations remain;
`releaseQualified=false`.** Publication does not turn failed or unrun checks
into passes. Stable0.5.1 remains GitHub Latest and the default stable feed.

## Downloads and installation

- `Strata-0.5.4-local.1-windows-x64-setup.exe` —112415417 bytes, the exact tested installer.
- `Strata-0.5.4-local.1-windows-x64.tar.7z` —1654599858 bytes, one-download bundle.
- `strata-engine-0.5.4-windows-x86_64-cuda-cuda13.tar.gz` —signed separate engine.
- `strata-control-0.5.5-windows-x86_64.zip` —optional self-contained Terminal.
- `SHA256SUMS.txt`, `BUNDLE-SHA256SUMS.txt`, `INSTALL.md`, `SOURCE.json`,
  `QUALITY.json`, signed feed and unchanged fork install scripts.

Verify downloads against SHA256SUMS.txt. For the bundle extract **7z, then tar**,
and verify BUNDLE-SHA256SUMS.txt. It is a real tar in a Copy-mode7z container;
inner files are already compressed. Every extracted member matched its input hash.

Finish requests, unload models, back up app data and quit Strata including its
tray icon. Run the EXE once. The app contains private Node/Python/Control, with
no system pip/compiler required. GPU engines are separate: on the preparation
screen choose **I already have the file** and select this release's signed
engine tar.gz, still compressed. Model loading is manual. Full model weights and
personal profiles are excluded; the licensed small, default-off control vector
is included in Control. WebView2 first-time installation may need the internet.

The fork signs components/feed. The EXE has **no Authenticode or Tauri updater
signature**; app updates are manual. See [installation](https://github.com/zapabob/Strata/blob/v0.5.4-local.1/docs/HAKUA_INSTALL.md).

## What is included

Official tuned/stock Auto preparation, drafter sizes, generated policy and
geometry/signed-feed APIs, deferred screens/catalogs/highlighting, alongside
the fork's consent-based memory, local model reuse, native cache ownership,
mapped/bounded experts, on-demand workspace editor and reversible trash.
Spin(8), Triality, TurboQuant settings and compatible Qwen3.8 refusal-direction
controls remain opt-in. Positive Qwen3.8 projection is unqualified.

Product0.5.4-local.1; Control0.5.5; native0.5.4; PrismML0.4.1;
TurboQuant0.4.0; Node24.22.2; Python3.12.15; Hakua-memory0.3.5.

## Validation passed

Measured on Windows x64, RTX5060Ti16GB,32GB RAM, CUDA13.3/sm_120.

- Five-job incremental native/app builds, CPU/GPU/sanitizer checks.
- Actual short native requests: bounded7, legacy7, restart2; comparison and
  model/pack/tokenizer preservation passed. Capacity4096, not full4096-token input.
- Thirteen packaged startup self-tests and29544 matched payload files.
- Backed-up overwrite preserved4028 user files. Actual installed WebView2
  Qwen3.6, Prism and workspace CRUD checks passed. Normal startup was checked
  without debugging, models unloaded and settings retained.
- Signed manifest/feed verification with built-in keys, complete engine/Control
  archive hashes, combined-archive readback. The installer bytes were not rebuilt.

## Failed, retained or unqualified

- CUDA resource guard **FAIL:12 violations**. No allowance/floor was relaxed.
- Prism first restart warm-up timed out after one successful answer. An unchanged
  serial rerun passed both answers and restart. Cause remains unresolved.
- Full server discovery timed out; six language catalogs retain pre-existing
  missing keys; a supplemental memory browser fixture failed to launch.
- Full-window generation, general/low-precision model quality, positive Qwen3.8
  projection and other GPUs/backends are unqualified. This Windows package has
  no native image input or separate native DeepSeek engine.
- First LZMA bundle preparation stopped at the unchanged3GiB RAM floor. The
  preserved failed attempt was followed by a passing low-memory Copy-mode run.

See [the integration record](https://github.com/zapabob/Strata/blob/v0.5.4-local.1/docs/UPSTREAM_0213.md)
and [release limits](https://github.com/zapabob/Strata/blob/v0.5.4-local.1/docs/HAKUA_RELEASE.md).

## Feed selection and source identities

Preview updates require the explicit immutable prerelease URL. The signed
feed's `stable` transport channel is client compatibility, not quality approval.
Accepted sequence20261110000100 is remembered across sources within a component
folder; the older stable feed is then rejected by the anti-replay guard. Keep
that protection. Use retained-component rollback or separate data/component roots
for independent stable/preview update state. `STRATA_FEED` set in a terminal is
session-scoped. The desktop preview path above uses the local signed engine file.

Upstream: `f33c8c30588ff00e24b6b63bad0bf6a14da19081`.
App/Control build source: `85a78234cfcdccd8741cc921677802aba1869e44`.
Native build source: `7bb2497400b8ea40d5d07f5244f010d3aa5eacc0`.
The release tag includes later documentation/packaging recipes; it does not
relabel the build-source commits. SOURCE.json records full artifact bindings.

Installer SHA256: `ae05518656ee5afdf92665f5dd71a06a69425ae1957a9ac31468d8a4a1790750`.
Bundle SHA256: `018dc44f6393f939b14c21c2a863e8e2813c46a8f25dd6929ce75c228d49a340`.

## 日本語

公式0.2.13と独自機能を統合したWindowsプレビューです。7z→tarの順に展開し、
チェックサム確認後に同梱EXEを実行します。GPUエンジンは別配布です。
準備画面から同梱tar.gzを圧縮したまま選び、署名・ハッシュ確認後に利用します。
CUDA資源違反12件とPrismのtimeoutを残し、`releaseQualified=false`です。
長文・一般品質・低精度品質・Qwen3.8実projectionは未認定です。
既存stable0.5.1／Latestと過去の配布物は保持します。
