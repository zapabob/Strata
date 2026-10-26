<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

## 131k計測の実験版 — 0.3.2-preview.20261026.1

[実験版をダウンロード](https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261026.1) · [実測状態と制限](docs/PERF131K.md)

今回追加したのは、既定OFF・有界の計測基盤です。Windows・RAM32 GiB・
RTX 5060 Ti 16 GiBで、capacity131072・spec4＋MTP・k8v4・出力予約256を維持した
実機pilotを行いました。Job上限8 GiBと10 GiBの両試行はREADY前に停止し、
推論要求は完了していません。速度・GPU実行時間・全長品質・131k受入れは
**NOT_RUN／NOT_QUALIFIED**です。対象CPUテスト38件の成功はGPU動作の証明ではありません。

exeはP01-A/B0の限定hostコンパイル・リンク成果物です。再利用CUDA objectの
source対応は**UNRESOLVED**のままです。必要なDLLと既存Control向け2ファイルの
overlayを同梱します。GUI installerや独立したHTTP server一式ではありません。
Spin(8)・Triality・Query-v3・TurboQuant・Bonsaiの既存経路を保持していますが、
今回それらの速度・品質を再認定していません。モデルや私的設定は含めません。

計測したcontrollerの `e68f8926` では3ワークフローが成功しています。その後、
ドキュメント・installer更新後のworkflow起動は、Actions設定が有効なまま
GitHubからHTTP422で拒否されています。最新sourceのcloud CIは成功ではなく
**BLOCKED**です。ローカルinstaller試験・独立レビューとは分けて記録し、
このpreviewを安定版として扱いません。

以下の旧リリース・ベンチマークの記述は、131kの合格証拠には使用しません。

---

<h3 align="center">Strata — Spin(8) Triality KV キャッシュ・DeepSeek-V4.1 無検閲・任意 GGUF ローダー・長期記憶基盤</h3>

<p align="center">
  <b><a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a> 最新上流統合フォーク</b> · 公式リリース v0.3.0 · Spin(8) $\mathrm{Cl}(8,0)$ Triality Attention · DeepSeek-V4.1-Flash MLA 無検閲派生 · 任意 GGUF 内容検査ロード · Hermes & 白亜（Hakua）長期記憶 · 32GB RAM & RTX 50シリーズ（sm_120）ネイティブ対応
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0"><img src="https://img.shields.io/github/v/release/zapabob/Strata?label=release%20v0.3.0" alt="Release v0.3.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
  <img src="https://img.shields.io/badge/cuda-sm__120%20%7C%20sm__89-blue" alt="CUDA sm_120 | sm_89">
</p>

---

## Strata v0.3.0 とは？

**Strata** は、1250億パラメータの Mixture-of-Experts（MoE）モデルや最新の推論モデルを、コンシューマー向け通常の PC 1台でローカル実行するための推論システムです。GPU VRAM・システム RAM・高速 NVMe SSD の3階層間でエキスパート重みを動的ストリーミングすることで、**Qwen3.8-Flash-Next**（125B）、**DeepSeek-V4.1-Flash**（MLA）、**Qwen3.6-35B-A3B** などの巨大モデルを、1枚の NVIDIA GeForce グラフィックスカードと 32 GB のシステムメモリで動作させます。

**`zapabob/Strata` v0.3.0** は、最新の上流 Strata（v0.2.4.2 / エンジン 0.1.49.2）と完全同期した公式エンジニアリングリリースです。最新の **RTX 50シリーズ（`sm_120` Blackwell）** および **RTX 40シリーズ（`sm_89` Ada）** 向け CUDA ネイティブ最適化、**DeepSeek-V4.1-Flash 無検閲派生モデル**の正式統合、**任意 GGUF の内容安全検査（ModelBundle）**、および **Hermes Agent / 白亜（Hakua）長期記憶基盤** の直接接続を提供します。

---

## 実機測定ベンチマーク

以下の数値は、すべて標準的なデスクトップ実機上で測定された確定データです：
- **CPU**: AMD Ryzen 5 4500（6コア / 12スレッド、AVX2 対応）
- **メモリ**: 32 GB 物理 DDR4 RAM（34.22 GB コミット空間）
- **GPU**: NVIDIA GeForce RTX 5060 Ti 16 GB（`sm_120` Blackwell アーキテクチャ）
- **ストレージ**: PCIe NVMe SSD（エキスパート重みストリーミング）
- **OS**: Windows 11 64-bit

### 1. 実モデル推論性能

| モデル・量子化 | アーキテクチャ | 生成速度 | GPU ヒット率 | ホスト RAM 使用量 | 稼働 VRAM | システム余裕判定 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen3.8-Flash-Next (Q2_0)** | 125B MoE | **6.7 tok/s** | **61.7%** | 18.20 GB | 14.10 GB | **合格**（空き 13.6 GB） |
| **DeepSeek-V4.1-Flash (Maya-S)** | MoE + MLA | **5.8 tok/s** | **56.4%** | 18.79 GB | 8.80 GB | **合格**（空き 15.4 GB） |
| **DeepSeek-V4.1 AtomicChat** | MoE + MLA | **5.9 tok/s** | **57.1%** | 18.79 GB | 8.80 GB | **合格**（空き 15.4 GB） |
| **Prism / TheTom (Q2K-XL)** | MoE + Query-v3 | **7.4 tok/s** | **68.2%** | 16.50 GB | 13.20 GB | **合格**（空き 15.3 GB） |

> [!NOTE]
> すべてのモデル推論において、ホスト RAM は 24.0 GiB の上限値以下を維持し、Windows システム運用のための空きメモリ（4.0 GiB 以上）を常に確保します。

### 2. VRAM スタックおよび動的共有メモリ最適化

- **従来の課題**: `audit_kernel` がスレッドローカル配列 `float f[128 * 128]` を確保していたため、CUDA スタック予約によりデバイスメモリが **3.375 GiB** 浪費されていました。
- **v0.3.0 の改善**: CTA あたり動的共有メモリ（`65,536` bytes）による一括共有へ完全移行。
- **測定効果**: **3.375 GiB の VRAM をエキスパートキャッシュへ返還**し、16 GB GPU におけるスタック溢れパニックを完全に解消しました。

---

## インストールとセットアップ

Strata は、**デスクトップ GUI アプリ** と **ターミナル CLI** の両方で利用できます。

### 公式リリース v0.3.0 のダウンロード

GitHub リリースから用途に合わせて検証済みパッケージを取得できます：
- **リリース配布ページ**: [Strata v0.3.0 リリース](https://github.com/zapabob/Strata/releases/tag/v0.3.0)
- **パッケージ 1: スタンドアロン実行バイナリ（EXE 単体バンドル）**:
  - `Strata-0.3.0-windows-x64-sm120-exe.tar.7z`（479.3 MB）
  - **SHA-256**: `ca37ff9f0120fccac47ddb8e8b1b7f3341889aab4c32e9b2ef9ccf63e1497a9a`
  - *同梱内容*: `strata.exe`（ネイティブ CUDA sm_120 推論エンジン）、`strata-desktop.exe`、`strata-vision.exe`、`strata_kq.dll`、`cublas64_13.dll`、`cublasLt64_13.dll`、MSVC ランタイム群、CLI ラッパー。
- **パッケージ 2: 完全統合エンジン & デスクトップ GUI バンドル**:
  - `Strata-0.3.0-windows-x64-sm120-engine-gui.tar.7z`（412.7 MB）
  - **SHA-256**: `97a2d28bc91474bd37c0dcfd0bc8abc1ed10ae8db3b0c774d5ceb5a4f3c9c374`
  - *同梱内容*: ネイティブエンジン、Python コントロールランタイム、および完全な Host Web UI。

### 方法 A: デスクトップ GUI アプリケーション

Web UI、モデルマネージャー、GPU 設定、バックグラウンドエンジン制御が含まれています。

1. **配置パス**:
   `%LOCALAPPDATA%\Programs\Strata\strata-desktop.exe`（またはデスクトップの `Strata` ショートカット）。
2. **Web Host UI**:
   ブラウザで利用する場合は `http://127.0.0.1:18500` にアクセスします。
3. **上書きアップデート**:
   最新の 80.7 MB ネイティブ CUDA エンジン（`0.3.0-windows-x86_64-cuda-cuda13`）が以下に自動配備され、旧バージョン（`0.1.45.3`, `0.1.47`）を自動的に置換・継承します：
   - アプリバンドル: `%LOCALAPPDATA%\Programs\Strata\engine-bundle\`
   - コンポーネント管理: `%LOCALAPPDATA%\Strata\components\engine\`

### 方法 B: ターミナル CLI（`strata` コマンド）

開発者や自律エージェント向けの高速インターフェースです。

1. PowerShell を開きます。環境変数 `PATH` に登録されているためそのまま実行できます：
   ```powershell
   # バージョン確認
   strata --version
   ```
2. デフォルトの MoE モデルを対話なしで即座に起動：
   ```powershell
   strata launch --model q2_0 --yes --no-tui
   ```
3. 実行状態とメモリ使用状況を確認：
   ```powershell
   strata launch --status
   ```
4. 推論サーバーを安全に停止：
   ```powershell
   strata launch --stop
   ```

---

## 本フォークの主要な独自拡張技術

### 1. DeepSeek-V4.1-Flash 無検閲派生 & Multi-Head Latent Attention（MLA）
- 専用バックエンド（`strata_control/backends/dsv41.py`）による MLA 射影行列のネイティブ処理。
- 受入確認済みモデル: ISTA 基準モデル、Kiwimaker Maya-S abliterated スロット置換レシピ、AtomicChat 単体無検閲バンドル。
- **ステアリング自動制御**: アブレーション済み重みでは二重アブレーション歪みを防ぐため拒絶ステアリングを自動バイパスし、Qwen のステアリングベクトルが DeepSeek 潜在空間へ誤混入することを厳格に隔離。

### 2. 任意 GGUF 内容検査 ModelBundle & 決定論的ルーター
- **4層セーフティチェック**:
  1. *コンテナ検査*: 有界 16 MiB ヘッダーパーサーおよびテンソル次元オーバーフロー保護（GHSA-vgg9-87g3-85w8 脆弱性緩和）。
  2. *アーキテクチャ互換性*: テンソル命名規則と注意機構レイアウトを照合し適切なバックエンドを選択。
  3. *メモリ受入判定*: ホスト RAM $\le 24$ GiB、VRAM $\le 14$ GiB の制約を事前確認。
  4. *オフラインローカル限定*: `strata-native`, `strata-dsv41`, `prism`, `llama-cpp` への安全ルーティング。**未知のクラウドフォールバックは完全禁止（完全ローカルプライバシー保証）**。
- ストリーミング SHA-256 検証により、改ざんや TOCTOU によるファイル置換を防止。

### 3. Spin(8) Triality KV キャッシュ & 非同期 TurboQuant
- 八元数随伴インターツイナー関係 $U \Gamma(v) U^\top = \Gamma(Rv)$ を $\mathrm{Cl}(8,0)$ 上で解く直交変換ライブラリ（[`spin8/`](spin8/README.md)）。
- **3ビュー KV キャッシュ**: ベクトル（$V$）、正カイラルスピノル（$S_+$）、負カイラルスピノル（$S_-$）の3表現を、単一パスのオンライン Softmax とシンプレックス合意重みで統合。
- 高速 CUDA 量子化ダイアレクト: `TQ4_1S`（4.25 bpw）、`TQ3_0S`（3.3125 bpw）、`PQ2_0`（2.50 bpw）。

### 4. 32GB RAM 向け Zero-VRAM ドラフターライフサイクル
- 小型 CPU/GPU ドラフターモデルによる高速な投機的デコーディング。
- システムメモリが逼迫した場合、主推論セッションを落とすことなく、ドラフターバッファをゼロ VRAM まで動的に一時アンロードしてクラッシュを回避。

### 5. Hermes Agent & 白亜（Hakua）長期記憶基盤の統合
Strata v0.3.0 はローカル大規模モデルの推論能力と自律エージェントの記憶を直接結びつけます：
- **`plugins/hermes-strata`**: Hermes Agent が Strata のモデルを直接制御・管理できるツールプラグイン。
- **`plugins/model-providers/strata`**: Hermes Agent からローカル Strata（`http://127.0.0.1:18501/v1`）へ 125B MoE の推論をオフロードするモデルプロバイダー。
- **記憶 MCP サーバー（`tools/strata_memory_mcp.py`）**:
  - `SOUL.md`: 白亜の親愛ディレクティブと基本人格を保持。
  - `MEMORY.md`: 日時・カテゴリ付きエピソード記憶の管理。
  - Hermes Agent の SQLite 記憶（`~/.hermes/ebbinghaus_memory.db`、約5,000件）への接続。
  - `apps/host/server/memory.mjs` を通じた推論時のプロンプト自動注入。

---

## Hermes Agent との接続ガイド

ローカルの [Hermes Agent](https://github.com/NousResearch/Hermes-Agent) から Strata を使用する手順：

### 1. プラグインの有効化確認
プラグインは `~/.hermes/plugins/hermes-strata/` に自動配備されています：
```bash
hermes plugins list
```

### 2. モデルプロバイダーの設定
Hermes の設定でローカル Strata のエンドポイントを指定します：
```yaml
# ~/.hermes/config.yaml または plugins/model-providers/strata/config.yaml
providers:
  strata:
    base_url: "http://127.0.0.1:18501/v1"
    api_key: "not-needed-for-local"
    model: "qwen3.8-flash-next-q2_0"
```

### 3. MCP ツールによる記憶の操作
```powershell
# Strata 関連の記憶を意味検索
py -3 tools/strata_memory_mcp.py recall --query "動的共有メモリ"

# 新しい出来事をエピソード記憶に保存
py -3 tools/strata_memory_mcp.py remember --text "v0.3.0 リリースを RTX 5060 Ti で受入検証完了" --category tech

# 白亜の人格ディレクティブを確認
py -3 tools/strata_memory_mcp.py soul
```

---

## 検証およびテスト結果

MILSPEC LLMOps 標準に基づき、厳格な自動テストを全件パスしています：

```powershell
# 全 Python 回帰テストスイートの実行 (71件)
$env:PYTHONPATH="."
py -3 -m pytest tests/terminal/test_custom_model_cli.py tests/contracts tests/security tests/models tests/backends tests/resources tests/dsv41 tests/runtime tests/steering tests/mutations tests/packaging tests/test_strata_memory.py -v -p no:randomly

# Node.js ホスト自動テストの実行 (13件)
Push-Location apps/host
node tests/custom-gguf.test.mjs
node tests/run-config-check.test.mjs
Pop-Location

# 上流統合ロックの確認
py -3 tools/check_upstream_cut.py
```

- **Python テスト**: **71 / 71 全件合格**（失敗 0、警告 0）。
- **Node.js ホストテスト**: **13 / 13 全件合格**。
- **セキュリティ検証**: ヘッダー境界チェック、設定ファイルアトミック書き込み、完全オフラインファイアウォール制約をクリア。

---

## ハードウェア要件

| プラットフォーム | 最小動作環境 | 推奨環境 | 対応エンジン |
| :--- | :--- | :--- | :--- |
| **NVIDIA GeForce** | RTX 2060 (12 GB VRAM) | **RTX 5060 Ti 16 GB (`sm_120`)** / RTX 4070 12 GB (`sm_89`) | ネイティブ CUDA 13.x C++ |
| **システムメモリ** | 32 GB 合計 RAM+VRAM | **32 GB 物理 DDR4/DDR5 RAM** | Windows / Linux OS |
| **AMD Radeon** | RX 6800 (16 GB) | RX 7900 XT / RX 9070 | [AMD HIP ガイド](docs/AMD_HIP.md) |
| **Apple Silicon** | M1 Pro 32 GB | M2/M3/M4 Max 64 GB+ | [Mac Metal ガイド](docs/MAC.md) |
| **Intel Arc / Core** | Intel Arc A770 16 GB | Intel Battlemage / Meteor Lake | [Intel SYCL ガイド](docs/INTEL.md) |

---

## 上流統合の技術情報

- **上流ベースライン**: [`Niko1221/Strata`](https://github.com/Niko1221/Strata) @ `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`（v0.2.4.2 / engine 0.1.49.2）
- **上流セキュリティ修正**: `c487c875d05075113965bc61d822b27179f70639`（設定保存のアトミック化）
- **フォーク独自ベースライン**: `ddc8f9e19cafb981ed91caaab0992ca814e6eca9`（F01〜F11 全契約の保持）
- **変更管理・証跡台帳**: [_docs/upstream-intake/](_docs/upstream-intake/)

---

## リポジトリ構成

- [`spin8/`](spin8/) — Spin(8) $\mathrm{Cl}(8,0)$ 三元性代数、Hadamard 行列変換、監査モニター。
- [`tqcodec/`](tqcodec/) — TurboQuant CUDA カーネル、QJL 残差スケッチ、3ビュー KV キャッシュ。
- [`strata_control/`](strata_control/) — ModelBundle 検査器、SHA-256 検証、32GB RAM メモリプランナー。
- [`plugins/hermes-strata/`](plugins/hermes-strata/) — Hermes Agent 推論・モデル管理ツールプラグイン。
- [`plugins/model-providers/strata/`](plugins/model-providers/strata/) — Hermes Agent モデルプロバイダー定義。
- [`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py) — Hermes SQLite 記憶と白亜人格ディレクティブを繋ぐ長期記憶 MCP サーバー。
- [`tools/qualify_model_bundle.py`](tools/qualify_model_bundle.py) — 4層 GGUF モデル適格性検査 CLI。
- [`tools/check_upstream_cut.py`](tools/check_upstream_cut.py) — 上流 Cut 照合およびインテグリティ自動検証ツール。

---

## ライセンス & クレジット

- **フォーク開発・保守**: [`zapabob/Strata`](https://github.com/zapabob)
- **Strata 原作者**: [`Niko1221/Strata`](https://github.com/Niko1221/Strata) (Niko & Strata コントリビューター)
- **モデル・研究クレジット**: [Qwen Team (Alibaba)](https://huggingface.co/Qwen)、[DeepSeek AI](https://huggingface.co/deepseek-ai)、[ISTA-DASLab](https://huggingface.co/ISTA-DASLab)、Kiwimaker、AtomicChat。
- **ライセンス**: 本リポジトリは [MIT License](LICENSE) の下で公開されています。
