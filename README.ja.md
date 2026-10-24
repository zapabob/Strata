<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="380">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></p>

<h3 align="center">Strata — Spin(8) Triality KV キャッシュ・DeepSeek-V4.1 無検閲・任意 GGUF ローダー・長期記憶管理</h3>

<p align="center">
  <b><a href="https://github.com/Niko1221/Strata">Niko1221/Strata</a> 最新上流統合フォーク</b> · Spin(8) $\mathrm{Cl}(8,0)$ Triality Attention · DeepSeek-V4.1-Flash MLA 無検閲派生 · 任意 GGUF 内容検査ロード · Hermes & Hakua 長期記憶 · 32GB RAM 最適化
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.2"><img src="https://img.shields.io/github/v/release/zapabob/Strata?include_prereleases&label=fork%20release" alt="Fork release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/zapabob/Strata" alt="MIT license"></a>
  <a href="https://github.com/zapabob/Strata/stargazers"><img src="https://img.shields.io/github/stars/zapabob/Strata?style=flat" alt="GitHub stars"></a>
</p>

---

## このフォーク（`zapabob/Strata`）の概要

**`zapabob/Strata`** は、最新の上流 Strata（v0.2.4.2 / エンジン 0.1.49.2）と完全同期した高度なエンジニアリングフォークです。1250億パラメータの MoE モデル（**Qwen3.8-Flash-Next**、**Qwen3.6-35B-A3B**、**Gyro**、**Swift 1.5**、**NVFP4**）を GPU VRAM・システム RAM・SSD の3階層協調で1台のPC上で高速実行する機能に加え、**Spin(8) Triality KV キャッシュ**、**DeepSeek-V4.1-Flash 無検閲派生モデル**、**任意 GGUF の内容ベース安全ロード**、および **Hermes / 白亜（Hakua）長期記憶基盤** を包括的に統合しています：

1. **Spin(8) Triality & $\mathrm{Cl}(8,0)$ 直交変換ライブラリ（[`spin8/`](spin8/README.md)）**
   - 実八元数基底（$1, e_1, \dots, e_7$）および対称クリフォード代数 $\mathrm{Cl}(8,0)$ 生成子（$\Gamma_0, \dots, \Gamma_7$）に基づく厳密な8次元3ビュー表現を実装。
   - 16×16 スピノルをカイラリティ固有空間によって **ベクトル表現 ($V$)**・**正カイラル半スピン表現 ($S_+$)**・**負カイラル半スピン表現 ($S_-$)** の3つの8次元空間へ分解し、随伴インターツイナー関係 $U \Gamma(v) U^\top = \Gamma(Rv)$ を満たします。
   - すべての変換プランは数学的監査（フロベニウス直交誤差 $E_F = \|M^\top M - I\|_F / \sqrt{8} \le 10^{-12}$、最大グラム要素誤差 $\le 10^{-12}$、ピボット付き LU 分解符号付き対数行列式 $\operatorname{sign}=+1, |\log|\det|| \le 10^{-12}$）を通過。
   - 正規化 Sylvester Hadamard 変換（$n = 1 \dots 1024$）と、1,024トークンまたは60秒ごとに不変量を検査する監査スケジューラ（`spin8_monitor`）を備えています。

2. **3ビュー Triality KV キャッシュ & 非同期 TurboQuant CUDA ダイアレクト（[`tqcodec/`](tqcodec/README.md)）**
   - **物理 CUDA 3ビューキャッシュ（`cache_cuda.cu`）**: ヘッドごとに物理的に独立した3つの回転済み Key 配列（$V, S_+, S_-$）と共有量子化 Value 配列を保持。単一パスのオンライン Softmax 上でシンプレックス合意重み $(\alpha_0, \alpha_1, \alpha_2)$ による重み付き統合と、パック化符号ガウス投影 **QJL** による残差スケッチ補正を実行。
   - **非同期 CUDA 量子化ダイアレクト**: `TQ4_1S`（4.25 bpw）、`TQ3_0S`（3.3125 bpw）、`PQ2_0`（2.50 bpw）。
   - **SM120（RTX 50シリーズ）向け動的共有メモリ最適化**: スレッドローカル配列を動的共有メモリ（`65,536` bytes）へ移行し、3.375 GiB の CUDA スタック予約を完全解消。エキスパートキャッシュ用に約 3.3 GiB の VRAM を解放し、16 GiB GPU / 32 GiB RAM 環境での安定動作を実現。

3. **DeepSeek-V4.1-Flash-1017 無検閲派生モデル & MLA バックエンド（[`strata_control/backends/dsv41.py`](strata_control/backends/dsv41.py)）**
   - 専用 `strata-dsv41` バックエンドによる Multi-Head Latent Attention（MLA）射影行列のネイティブサポート。
   - 受入試験済みモデル: ISTA 基準モデル、Kiwimaker Maya-S abliterated スロット置換レシピ、AtomicChat 単体無検閲モデル。
   - アブレーション済みモデルでは拒絶方向ステアリングを自動バイパスし、二重アブレーションによる回答歪みを防止。Qwen のステアリングベクトルや $\mathrm{Cl}(8,0)$ キャッシュが DeepSeek 潜在空間に混入しない安全隔離を達成。

4. **任意 GGUF 内容検査 ModelBundle & 決定論的ルーター（[`strata_control/model_bundle.py`](strata_control/model_bundle.py)）**
   - 有界ヘッダーパーサー（$\le 16$ MiB）およびテンソル次元オーバーフロー防止ガード（$\operatorname{rank} \le 4, \operatorname{dim} \le 2^{30}$、GHSA-vgg9-87g3-85w8 対策）。
   - ストリーミング SHA-256 ダイジェストと改ざん・置換を検知するドリフト検出機能。
   - 決定論的ローカルルーティング（`strata-dsv41`、`strata-native`、`prism`、`llama-cpp`）と **未知のクラウドフォールバック完全禁止**（100% オフライン・ローカル完結プライバシー）。

5. **Hermes Agent & 白亜（Hakua）長期記憶基盤（[`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py)）**
   - 標準 MCP stdio サーバー + CLI:
     - `SOUL.md`: 白亜の基本人格と親愛ディレクティブの読込・追記・自動バックアップ。
     - `MEMORY.md`: `§ [カテゴリ] YYYY-MM-DD: タイトル` 形式に準拠したエピソード記憶管理。
     - Hermes Agent SQLite 記憶ストア（`~/.hermes/ebbinghaus_memory.db`、約5,000件の記憶を接続）。
     - Hakua Composite Memory（`~/.hakua-memory`）。
   - `apps/host/server/memory.mjs` および `getEffectiveSystemPrompt()` を通じたチャット時の自動注入。

6. **32GB RAM / 16GB VRAM Zero-VRAM ドラフターライフサイクル**
   - Windows 11 + 32 GB RAM + NVIDIA GeForce RTX 5060 Ti 16 GB（`sm_120`）で実機受入検証済み。
   - 計画ホスト RAM $\le 24.0$ GiB、OS最低予約 $\ge 4.0$ GiB、VRAM $\le 14.0$ GiB を遵守。
   - システムメモリ圧迫時には投機的デコーディングドラフターを自動アンロードし、主推論プロセスを停止させずにドラフターバッファをゼロ VRAM まで安全解放。

---

## リリース & 上流統合ステータス: `v0.3.0` Upstream Integrated Edition

- **取り込み済み最新上流**: `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5` (v0.2.4.2 / engine 0.1.49.2)
- **GUI セキュリティ修正**: `c487c875d05075113965bc61d822b27179f70639` (設定保存 TOCTOU 修正)
- **フォーク独自契約**: `ddc8f9e19cafb981ed91caaab0992ca814e6eca9` (F01〜F11 全機能保持)
- **受入・検証ドキュメント**:
  - モデル受入台帳: [_docs/qa/model-acceptance.json](_docs/qa/model-acceptance.json)
  - ベンチマークレポート: [bench/custom-gguf/report.md](bench/custom-gguf/report.md)
  - リリース資格確認書: [_docs/releases/custom-gguf-qualification.md](_docs/releases/custom-gguf-qualification.md)

### 検証エビデンスサマリー

| 対象コンポーネント | 状態 | 検証エビデンス |
| --- | --- | --- |
| **ネイティブ Windows CUDA エンジン (`sm120`)** | **検証済み** | ポート 18501 で Q2_0 ベースライン（6.7 tok/s, GPU hit 61.7%）が全テスト中も一切停止せず安定稼働。 |
| **`tqcodec` 動的共有メモリ** | **検証済み** | 64 KiB/thread スタック配列を動的共有メモリへ置換し、RTX 5060 Ti 16GB 上で 3.375 GiB の VRAM 浪費を解消。 |
| **任意 GGUF & DeepSeek ルーター** | **検証済み** | ISTA、Maya-S 置換レシピ、AtomicChat 単体モデルに対する 4層受入検査を全件パス。 |
| **長期記憶 MCP & GUI** | **検証済み** | `tests/test_strata_memory.py`（5/5 PASS）、プロンプト生成時の `SOUL.md` 自動注入を確認。 |
| **回帰テストスイート** | **検証済み** | **Python テスト 71件全合格**（`pytest -p no:randomly`）、**Node.js テスト 13件全合格**（`apps/host`）。 |

---

## クイックスタート（本フォーク独自機能の使い方）

### 1. GUI（デスクトップ / Web Host）での設定

1. アプリの **Settings（設定） → GPU & memory** を開きます。
2. 以下の項目から KV キャッシュおよび Spin(8) モードを選択できます：
   - **K cache type (`cache_type_k`)**: `f16`（標準）、`tq3`、`tq3_spin8_hadamard`、`tq3_spin8_native`
   - **V cache type (`cache_type_v`)**: `f16`（標準）、`tq3`、`tq3_spin8_hadamard`、`tq3_spin8_native`
   - **Spin(8) KV cache mode (`spin8_mode`)**: `off`（標準）、`f32`、`compressed`
   - **Spin(8) native config path (`spin8_native_config`)**: 監査済みカプセル JSON の絶対パス
   - **Spin(8) native config SHA-256 (`spin8_native_sha256`)**: カプセルファイルの 64桁 HEX ハッシュ
3. **Models（モデル）** タブから、ユーザー所有の任意 GGUF ファイルや DeepSeek 派生モデルを内容検査付きでプレビュー・ロードできます。

### 2. CLI & モデル適格性検証

```powershell
# 標準起動（上流互換パス）
py -3 strata.py launch --model q2_0 --yes --no-tui

# Hadamard 回転 TurboQuant 3-bit KV キャッシュでの起動
py -3 strata.py launch --model q2_0 `
  --set cache_type_k=tq3_spin8_hadamard `
  --set cache_type_v=tq3_spin8_hadamard `
  --yes --no-tui

# 32GB RAM 制限下での任意 GGUF バンドル適格性検査
py -3 tools/qualify_model_bundle.py --manifest path\to\model.gguf --architecture dsv41 --dialect standard

# 上流統合状態の整合性照合・ロック
py -3 tools/check_upstream_cut.py
```

### 3. 長期記憶機能（Hermes / Hakua / SOUL.md / Memory.md）の利用

```powershell
# 記憶システムの状態確認
py -3 tools/strata_memory_mcp.py status

# 意味検索による関連記憶の想起
py -3 tools/strata_memory_mcp.py recall --query "Strata 最適化"

# エピソード記憶の追加
py -3 tools/strata_memory_mcp.py remember --text "動的共有メモリにより audit_kernel の VRAM 浪費を解消" --category tech

# 現在の SOUL.md ディレクティブを表示
py -3 tools/strata_memory_mcp.py soul
```

---

## 必要なハードウェアスペック

Strata は **[Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)**（125B MoE）、**[DeepSeek-V4.1-Flash](docs/DEEPSEEK41.md)**、**[Qwen3.6-35B-A3B](docs/QWEN36.md)** を一般的な PC 1台でローカル実行し、OpenAI 互換（`/v1/chat/completions`）および Anthropic 互換（`/v1/messages`）API を提供します。

**合計 32 GB 以上のシステム RAM + GPU VRAM が必要です。**

| ハードウェア | 備考 |
| --- | --- |
| **NVIDIA** GeForce RTX 20, 30, 40, 50 シリーズ（12 GB+ VRAM） | 主要 CUDA ターゲット（RTX 5060 Ti 16 GB および RTX 5090 32 GB で `sm120` 動作検証済み）。 |
| **AMD** Radeon RX 6800+, RX 7000, RX 9000, Radeon AI PRO R9700 | [AMD HIP ガイド](docs/AMD_HIP.md) |
| **Intel** Arc | [Intel Arc](docs/INTEL_ARC.md), [SYCL ガイド](docs/INTEL.md) |
| **Apple Silicon Mac**（M1 以降、macOS 15+） | [Mac Metal ガイド](docs/MAC.md) |
| **AMD Ryzen AI Max (Strix Halo)** | [Strix Halo ガイド](docs/STRIX_HALO.md) |

---

## ソースコードからのビルドとテスト

```powershell
# 1. 全回帰テストスイートの実行 (Python)
$env:PYTHONPATH="."
py -3 -m pytest tests/terminal/test_custom_model_cli.py tests/contracts tests/security tests/models tests/backends tests/resources tests/dsv41 tests/runtime tests/steering tests/mutations tests/packaging tests/test_strata_memory.py -v -p no:randomly

# 2. Node.js ホストテストの実行
$env:NODE_OPTIONS=""
Push-Location apps/host
node tests/custom-gguf.test.mjs
node tests/run-config-check.test.mjs
Pop-Location

# 3. 上流 Cut 照合とインテグリティロックの確認
py -3 tools/check_upstream_cut.py
```

---

## リポジトリ構成（フォーク追加部分）

- [`spin8/`](spin8/README.md) — スタンドアロン Spin(8) $\mathrm{Cl}(8,0)$ 三元性ライブラリ、Sylvester Hadamard 変換、監査スケジューラ。
- [`tqcodec/`](tqcodec/README.md) — TurboQuant CUDA ダイアレクト（`TQ4_1S`, `TQ3_0S`, `PQ2_0`）、QJL 残差スケッチ、3ビュー CUDA KV キャッシュ。
- [`strata_control/`](strata_control/) — ModelBundle リゾルバー、ストリーミング SHA-256 検証、32GB メモリプランナー、決定論的ルーター。
- [`adapters/upstream/`](adapters/upstream/README.md) — ネイティブ注意機構および DeepSeek 隔離ステアリング用ブリッジ。
- [`tools/strata_memory_mcp.py`](tools/strata_memory_mcp.py) — Hermes Agent & Hakua Composite 長期記憶 MCP サーバー。
- [`tools/qualify_model_bundle.py`](tools/qualify_model_bundle.py) — 4層モデルバンドル適格性検証 CLI。
- [`tools/check_upstream_cut.py`](tools/check_upstream_cut.py) — 上流 Cut 照合・インテグリティロックツール。

---

## クレジット & ライセンス

- **フォーク開発 (`zapabob/Strata`)**: Spin(8) $\mathrm{Cl}(8,0)$ Triality キャッシュ、`tqcodec` CUDA ダイアレクト、DeepSeek-V4.1 無検閲統合、任意 GGUF 内容検査ロード、Hermes/白亜 長期記憶基盤、フルスタック GUI/CLI 制御。
- **上流 Strata ([`Niko1221/Strata`](https://github.com/Niko1221/Strata))**: 3階層 MoE ストリーミングエンジン、エキスパートキャッシュ、投機的デコーディング、デスクトップ/ホストアプリ、Terminal CLI。
- **モデル・量子化提供**: [Qwen Team](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)、[DeepSeek AI](https://huggingface.co/deepseek-ai)、[ISTA-DASLab](https://huggingface.co/ISTA-DASLab)、Kiwimaker、AtomicChat、[llama.cpp / ggml](https://github.com/ggml-org/llama.cpp)。
- **ライセンス**: 本フォークは [MIT License](LICENSE) の下で公開されています。
