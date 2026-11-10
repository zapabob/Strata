# Hakua / Strata 0.5.4-local.1 — Windows preview

This preview integrates official Strata 0.2.13 with Hakua memory, existing GGUF
reuse, Qwen3.6 private caches and workspace file CRUD. It is not upstream's
official distribution. Product0.5.4-local.1, Control0.5.5, native0.5.4;
PrismML0.4.1, TurboQuant0.4.0, Node24.22.2, Python3.12.15, Hakua-memory0.3.5.

## Install the app

Check SHA256SUMS.txt against the downloaded file. For the combined download,
extract the 7z, then the tar, and check BUNDLE-SHA256SUMS.txt inside.

Unload models, finish requests and quit Strata including its tray app. Back up
the app data. Run Strata-0.5.4-local.1-windows-x64-setup.exe once. The normal
per-user location is %LOCALAPPDATA%\Programs\Strata. An older installer can
remember a different folder. Existing models, chats and memory stay in their
own data locations. No system Python, Node, pip or compiler is needed.

The Tauri NSIS app carries no GPU engine, following the upstream Windows layout.
For this preview, choose the preparation screen's existing-engine-file option
and select strata-engine-0.5.4-windows-x86_64-cuda-cuda13.tar.gz from this release.
Keep it compressed. The app verifies the fork component signature and every
payload hash before activation. Model loading is manual.

The default stable feed remains a separate distribution. Use this preview's
own engine file to obtain its measured native0.5.4. Existing native components
remain available for rollback. The installer has no Authenticode or Tauri app
updater signature; the engine/feed signatures are separate integrity checks.

## Hardware and measured limits

The native package targets Windows x64, CUDA sm_120. Checks used RTX5060Ti16GB,
32GB RAM, CUDA13.3 and driver621.01. Other GPUs/backends need their own builds.
Model weights and personal profiles are not in this bundle. The small licensed
optional control vector is in Control and is off by default.

Native bounded and legacy paths each passed7 short private-cache requests,
restart2, CPU/GPU/sanitizer and comparison checks. Installed Q36/Prism/workspace
checks and13 startup self-tests passed. These native requests used4096 capacity,
not a full4096-token input or general quality benchmark. Prism had one restart
warm-up timeout before the unchanged rerun passed.

The native resource guard still reports12 violations. releaseQualified=false.
Full-window generation, general/low-precision model quality and positive Qwen3.8
projection are unqualified. Native image input and a separate native DeepSeek
engine are not included. See QUALITY.json, SOURCE.json and the release notes.

## Optional Terminal

The Control ZIP includes private Python and the strata command. Installation
scripts are unchanged fork scripts. To opt into this preview's feed explicitly:

```powershell
$env:STRATA_FEED='https://github.com/zapabob/Strata/releases/download/v0.5.4-local.1'
irm "$env:STRATA_FEED/install.ps1" | iex
```

This is optional for desktop users. The preview feed uses the existing stable
transport channel for client compatibility at the explicit prerelease URL;
that channel does not change its quality status or make it GitHub Latest.

## 日本語

これは公式Strata0.2.13を取り込んだHakuaフォークのプレビューです。
7z、tarの順に展開し、チェックサム確認後に同梱EXEを実行してください。
更新前にモデルとアプリを終了します。導入先は通常Cドライブの
%LOCALAPPDATA%\Programs\Strataです。モデル・会話・記憶は別の保存先に残ります。
GPUエンジンは別配布です。準備画面で同梱の署名付きtar.gzを圧縮したまま選びます。
システムへのPythonやNodeの追加は不要です。モデル読み込みは手動です。
CUDA資源違反12件、Prismのwarm-up timeout1回、長文・低精度品質の未認定を
保持しています。公開してもreleaseQualified=falseのままです。
