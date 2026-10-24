<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) Triality KV キャッシュ・TurboQuant CUDA ダイアレクト・ネイティブ MoE 推論エンジン</h3>

<p align="center">
  <b><a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a> 拡張フォーク</b> · Spin(8) $\mathrm{Cl}(8,0)$ Triality Attention · 3ビュー量子化 KV キャッシュ · Query-v3 `.prismq3` サイドカー · GUI & CLI 完全統合
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## このフォーク（`zapabob/Strata`）の概要

**`zapabob/Strata`** は、1250億パラメータの MoE モデル（**Qwen3.8-Flash-Next**、**Qwen3.6-35B-A3B**、**Gyro**、**Swift 1.5**、**NVFP4**）を GPU VRAM・システム RAM・SSD の3階層協調で1台のPC上で高速実行する [Strata](https://github.com/Niko1221/Strata)（v0.2.2 / engine 0.1.47）をベースに、**Spin(8) Triality（三元性）変換と TurboQuant 量子化 KV キャッシュ機構**を C++/CUDA エンジン・Python サーバー・CLI・デスクトップ/Web GUI の全階層へ統合した独自フォークです。

### 本フォーク独自の4大機能

1. **Spin(8) Triality & $\mathrm{Cl}(8,0)$ 直交変換ライブラリ（[`spin8/`](spin8/README.md)）**
   - 実八元数基底（$1, e_1, \dots, e_7$）および対称クリフォード代数 $\mathrm{Cl}(8,0)$ 生成子（$\Gamma_0, \dots, \Gamma_7$）に基づく厳密な8次元3ビュー表現を実装。
   - 16×16 スピノルをカイラリティ固有空間によって **ベクトル表現 ($V$)**・**正カイラル半スピン表現 ($S_+$)**・**負カイラル半スピン表現 ($S_-$)** の3つの8次元空間へ分解し、随伴インターツイナー関係 $U \Gamma(v) U^\top = \Gamma(Rv)$ を満たします。
   - すべての変換プランは適用前に数学的監査（フロベニウス直交誤差 $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$、最大グラム要素誤差 $\le 10^{-12}$、ピボット付き LU 分解による符号付き対数行列式 $\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$）を通過する必要があります。
   - 2のべき乗ブロック（$1 \dots 1024$、8要素 Spin(8) 符号マスクおよび 128要素 Bonsai ブロックを含む）の正規化 Sylvester Hadamard 変換と、1,024トークンまたは60秒ごとに不変量を検査するスティッキー監査スケジューラ（`spin8_monitor`）を備えています。

2. **3ビュー Triality KV キャッシュ & 非同期 TurboQuant CUDA ダイアレクト（[`tqcodec/`](tqcodec/README.md)）**
   - **物理 CUDA 3ビューキャッシュ（`cache_cuda.cu`）**: Attention ヘッドごとに物理的に独立した3つの回転済み Key 配列（$V, S_+, S_-$）と共有量子化 Value 配列を保持。単一パスのオンライン Softmax 上でシンプレックス合意重み $(\alpha_0, \alpha_1, \alpha_2)$ による重み付き統合と、パック化符号ガウス投影 **QJL** による残差スケッチ補正を実行します。
   - **非同期 CUDA 量子化ダイアレクト**:
     - `TQ4_1S`（4.25 bits/weight）
     - `TQ3_0S`（3.3125 bits/weight）
     - `PQ2_0`（2.50 bits/weight）
   - **SM120（RTX 50シリーズ）向け `audit_kernel` 動的共有メモリ最適化**: スレッドローカルな `float f[128 * 128]`（64 KiB/thread）配列を動的共有メモリ（`65,536` bytes）へ移行したことで、`tqc_cache_cuda_initialize` 時に発生していた **3.375 GiB（`3,623,878,656 B`）** の CUDA デバイススタック予約を解消（`audit_local=0`, `audit_delta=0`）。エキスパートキャッシュ用に約 3.3 GiB の VRAM を解放し、16 GiB GPU / 32 GiB RAM 環境で3ビューすべて（`off`, `f32`, `compressed`）の Q2 実モデル生成が安定動作します。

3. **Query-v3 有理接空間アダプタ & `.prismq3` サイドカー**
   - 監査済み $\mathrm{Cl}(8,0)$ ブロックから導出された7個の歪対称生成子上で有界有理接空間チャートを構成し、位置エンコーディング（RoPE）適用前の正規化済み Query ($Q$) に対してランク8コントローラを適用します。
   - 動的メモリ確保ゼロの融合 CUDA カーネル（`query_v3_cuda.h`）および SHA-256 バインド済み `.prismq3` サイドカー（`--query-v3-sidecar`）をサポートし、**Prism / TheTom (`qwen35-9b-thetom-q2kxl`)** や **Hikari / Bonsai (`bonsai-8b-prism-q1_0_g128`)** の検証に対応しています。

4. **GUI・CLI・Control プレーンのシームレス統合**
   - **デスクトップ / Web GUI (`apps/host`)**: **Settings → GPU & memory** 内に **K cache type**、**V cache type**（`f16`, `tq3`, `tq3_spin8_hadamard`, `tq3_spin8_native`）、**Spin(8) KV cache mode**（`off`, `f32`, `compressed`）、**Spin(8) native config path**、**Spin(8) native config SHA-256** を違和感なく統合。起動前のリアルタイムプリフライト検証（`run-config-check.mjs`）も備えています。
   - **CLI & Python サーバー (`strata_cli`, `strata_control`, `serve/server.py`)**: `strata launch --set ...` や `strata serve` からすべての Spin(8) / KV キャッシュ設定を指定でき、起動前にカプセル JSON と SHA-256 ハッシュを厳密に検証します。

---

## 最新フォークリリース: `v0.3.0-preview.20261024.2`

- **リリースページ**: [GitHub Release `v0.3.0-preview.20261024.2`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2)
- **Engine + GUI + Control 統合アーカイブ**: `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z`
  - **ファイルサイズ**: `412,311,508` bytes
  - **アーカイブ SHA-256**: `7639fb8ffb3c8fd13857a59c6b5d9d8b392c8b82a496442f0486a9405fd16e21`
  - **エンジン本体 (`strata.exe`) SHA-256**: `564e23b5bcd2b0670d0a2d82e7cd2c20cd5afedf85ddca7c653bea11403727db`
- **先行 CLI プレビュー**: [`v0.3.0-preview.20261024.1`](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1) · [リリース検証記録](docs/releases/preview030.md) · [Triality PoC 研究記録](research/triality_poc/README.md)

### `v0.3.0-preview.20261024.2` における検証済み項目

| 対象コンポーネント | 状態 | 検証エビデンス |
| --- | --- | --- |
| **ネイティブ Windows CUDA エンジン (`sm120`)** | **検証済み** | Q2 (`Qwen3.8-Flash-Next-GSQ-RCO-Q2_0`) による診断生成において、`--spin8-mode off` / `f32` / `compressed` の全3ビューすべてで `READY` デコードおよび EOS 正常終了（`exit 0`, `--vram-reserve-mib 10240`）を確認。 |
| **`tqcodec` CUDA `audit_kernel` 修正** | **検証済み** | 動的共有メモリ（`65,536` bytes）化により 3.375 GiB の CUDA スタック予約を解消（`audit_local=0`, `audit_delta=0`）。`tqc_cache_cuda_test.exe`（28,068 checks）および `strata_spin8_native_owner_test.exe`（17,361 checks）パス（`exit 0`）。 |
| **Host GUI & プリフライト検証** | **検証済み** | `pnpm --dir apps/host typecheck`（エラー 0）、`pnpm --dir apps/host build` 完了、`node --test`（`native-settings`, `spin8-backend`, `kv-settings`, `kv-engine` 計19テスト全パス）。 |
| **Control & Terminal CLI** | **検証済み** | `pytest tests/terminal/test_profiles.py`（21 passed）、`strata doctor --json`（`ok: true`）、および `engine_component.resolve(..., full=True)` による全ファイル SHA-256 完全一致を確認。 |

---

## クイックスタート（本フォーク独自機能の使い方）

### 1. GUI（デスクトップ / Web Host）での設定

1. `Strata-0.3.0-preview.20261024.2-windows-x64-sm120-engine-gui.tar.7z` を展開（`.7z` 展開後に `.tar` を展開）するか、ローカルの `%LOCALAPPDATA%\Programs\Strata` および `%LOCALAPPDATA%\Strata\components\engine\0.1.47-windows-x86_64-cuda-cuda13` に上書き配置します。
2. アプリの **Settings（設定） → GPU & memory** を開きます。
3. 以下の項目から KV キャッシュおよび Spin(8) モードを選択できます：
   - **K cache type (`cache_type_k`)**: `f16`（既定）、`tq3`、`tq3_spin8_hadamard`、`tq3_spin8_native`
   - **V cache type (`cache_type_v`)**: `f16`（既定）、`tq3`、`tq3_spin8_hadamard`、`tq3_spin8_native`
   - **Spin(8) KV cache mode (`spin8_mode`)**: `off`（既定）、`f32`、`compressed`
   - **Spin(8) native config path (`spin8_native_config`)**: 検証済み Spin(8) カプセル JSON の絶対パス（`f32` / `compressed` または `tq3_spin8_native` 選択時に必須）
   - **Spin(8) native config SHA-256 (`spin8_native_sha256`)**: カプセル JSON の 64文字 Hex SHA-256 ダイジェスト

### 2. `strata` CLI / サーバーからの起動

```powershell
# 既定起動（アップストリーム互換・変更なし）
strata launch --model q2_0 --yes --no-tui

# Hadamard 回転付き TurboQuant 3-bit KV キャッシュを有効化して起動
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_hadamard \
  --set cache_type_v=tq3_spin8_hadamard \
  --yes --no-tui

# SHA-256 検証済み Spin(8) 3ビュー圧縮カプセルを指定して起動
strata launch --model q2_0 \
  --set cache_type_k=tq3_spin8_native \
  --set cache_type_v=tq3_spin8_native \
  --set spin8_mode=compressed \
  --set spin8_native_config=C:\path\to\capsule.json \
  --set spin8_native_sha256=<64-hex-sha256> \
  --yes --no-tui
```

### 3. ネイティブエンジン (`strata.exe`) の直接実行

事前トークン化済みファイルとネイティブパックを用いた3ビュー検証コマンド：

```powershell
# Compressed Spin(8) 3ビューモード実行例
.\strata.exe --pack .\models\q2_0\native-pack `
  --native .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf `
  --ple-gguf .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf `
  --tokens-file .\examples\ready-tokens.txt --max-new 32 --max-context 256 `
  --mmap-experts --expert-cache auto --expert-profile .\data\expert-profile.bin `
  --prefill 32 --eos-ids 248044,248046 --spin8-mode compressed `
  --spin8-native-config .\capsules\q2_0-compressed-capsule.json `
  --spin8-native-sha256 <64-hex-sha256> `
  --check-logits --gpu 0 --spec 2 --suffix-draft 0 --lookup-chain 0 --vram-reserve-mib 10240
```

---

## Strata の基本機能と推奨ハードウェア

Strata は **[Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)**（125B MoE）や **[Qwen3.6-35B-A3B](docs/QWEN36.md)** をローカルPC上で動作させ、OpenAI 互換 API（`/v1/chat/completions`, `/v1/responses`）および Anthropic 互換 API（`/v1/messages`）を提供します。Claude Code、Codex CLI、OpenCode などのエージェントからそのまま接続できます。

### 必要なハードウェア環境

**システム RAM と GPU VRAM の合計が 32 GB 以上必要です**（Mac や Ryzen AI Max ではユニファイドメモリ）。

| ハードウェア | 対応状況・備考 |
| --- | --- |
| **NVIDIA** GeForce RTX 20 / 30 / 40 / 50 シリーズ（12 GB VRAM 以上） | メインの CUDA ターゲット（SM120 ネイティブ Spin(8) プレビューは RTX 5060 Ti 16 GB および RTX 5090 32 GB で実機検証済み）。 |
| **AMD** Radeon RX 6800 以降、RX 7000 / 9000、Radeon AI PRO R9700 | [AMD HIP ガイド](docs/AMD_HIP.md) |
| **Intel** Arc | [Intel Arc](docs/INTEL_ARC.md)、[SYCL エンジン](docs/INTEL.md) |
| **Apple Silicon Mac**（M1 以降、macOS 15 以降） | [Mac Metal ガイド](docs/MAC.md) |
| **AMD Ryzen AI Max (Strix Halo)** | [Strix Halo ガイド](docs/STRIX_HALO.md) |

### メモリ容量別の推奨モデル

| 合計メモリ (RAM + VRAM) | 推奨モデル | 特徴 |
| --- | --- | --- |
| **28〜32 GB** | **[Gyro-S](docs/GYRO.md)** (27.6 GB) または **[Coder](docs/MODELS.md#coder)** | Gyro-S は最小メモリ構成向け。Coder はコーディング特化でエキスパートを半減。 |
| **35〜40 GB** | **[Swift 1.5](docs/MODELS.md#swift-15)** IQ2_XS (39.2 GB) または **Gyro-M** (35 GB) | Swift 1.5 は思考トークンを短縮。Gyro-M は約20%少ない VRAM で IQ3_XXS に迫る品質。 |
| **48 GB** | **IQ3_XXS** (47.0 GB) | 2-bit 系より高い推論品質。 |
| **64 GB** | **IQ3_S** (54.8 GB) または **Q2_0** | IQ3_S はフルモデル同等のベンチマーク精度。Q2_0 は最高速（RTX 5070 で 94 tok/s）。 |
| **96 GB 以上** | **UD-IQ4_XS** (72 GB) 〜 **Q8_0** (136 GB)、**[NVFP4](docs/NVFP4.md)** | 全エキスパートを RAM に保持できる大容量環境向けの 4〜8 bit モデル。 |

---

## ソースからのビルドとテスト

```powershell
# 1. Spin(8) 単体ライブラリ（CPU）のビルドとテスト
cmake -S spin8 -B build\spin8-cpu -G "Visual Studio 17 2022" -A x64 -DSPIN8_ENABLE_CUDA=OFF
cmake --build build\spin8-cpu --config Release
ctest --test-dir build\spin8-cpu -C Release --output-on-failure

# 2. tqcodec（CPU + CUDA + Spin8 結合テスト）のビルドとテスト
cmake -S tqcodec -B build\tqcodec-cuda -G "Visual Studio 17 2022" -A x64 -DTQCODEC_ENABLE_CUDA=ON -DTQCODEC_SPIN8_TESTS=ON
cmake --build build\tqcodec-cuda --config Release
ctest --test-dir build\tqcodec-cuda -C Release --output-on-failure

# 3. ネイティブ CUDA エンジン (strata.exe / spin8_verify) のビルド
cmake -S . -B build\engine-cuda -G "Visual Studio 17 2022" -A x64 -DSTRATA_CUDA=ON
cmake --build build\engine-cuda --config Release --target strata spin8_verify

# 4. Host GUI & Control テスト
pnpm --dir apps/host typecheck
pnpm --dir apps/host build
node --test apps/host/tests/native-settings.test.mjs apps/host/tests/spin8-backend.test.mjs apps/host/tests/kv-settings.test.mjs apps/host/tests/kv-engine.test.mjs
py -3 -m pytest -p no:randomly tests/terminal/test_profiles.py
```

---

## クレジットとライセンス

- **フォーク開発 (`zapabob/Strata`)**: Spin(8) $\mathrm{Cl}(8,0)$ Triality KV キャッシュ、`tqcodec` CUDA ダイアレクト、Query-v3 `.prismq3` サイドカー統合、SM120 `audit_kernel` 動的共有メモリ最適化、および GUI/CLI フルスタック統合。
- **アップストリーム ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**: 3階層 MoE ストリーミングエンジン、エキスパートキャッシュ、投機的デコーディング、デスクトップ/Host アプリ、Terminal CLI。
- **モデル・量子化**: [Qwen Team](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)、[ISTA-DASLab](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)、UkisAI (Swift 1.5)、agentionai (Gyro)、Unsloth、および [llama.cpp / ggml](https://github.com/ggml-org/llama.cpp)。
- **ライセンス**: [MIT License](LICENSE) の下で公開されています。リリースアーカイブに同梱される CUDA/cuBLAS および Microsoft Visual C++ ランタイム DLL には各ベンダーの再配布規約が適用されます。
