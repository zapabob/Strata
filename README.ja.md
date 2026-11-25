# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

**Windows PC の全リソース（GPU・物理コア＋SMT スレッド・システム RAM・NVMe/SSD）を総動員して推論するローカル AI 環境。** Hakua は [Niko1221/Strata](https://github.com/Niko1221/Strata) の独立フォーク（`zapabob/Strata`）であり、公式上流 **v0.2.21**（`d46f5f268`、エンジン/Control `0.1.67`）を取り込みつつ、フォーク独自のランタイム・メモリー・エージェント機能および Blackwell CUDA 13.5 最適化を維持しています。

## 0.8.1（エンジン 0.7.0）の主な更新

- **実機の全4階層（GPU + 6物理コア/6SMT CPU + RAM + SSD）を使う異種混合推論**:
  - **Windows ネイティブ `aux_cpus` CPU Sets ＋ SMT I/O 分離**（`aux_cpus.hpp`, `ssd_stream_scheduler.hpp`, `direct_file.cpp`）: GPU ホストおよび AVX2 MoE 計算を物理プライマリコアに固定し、全 SMT セカンダリスレッド（6コア12スレッド機では `io_smt=[1,3,5,7,9,11]`）を 6スレッド非同期 Direct I/O と `PrefetchVirtualMemory` 先読み専用に割り当てます。
  - **CUDA 13.5 / SM120 Blackwell 向けネイティブエンジン5種を再ビルド**（`strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`）: Gen-K/L ゼロコピーマップドドアベル、WDDM 1536 MiB VRAM 予約（Shared GPU Memory 退避防止）、Windows コミット上限連動の安全 RAM 予算（`hy4_cpu_experts.cpp`, `inkling2_engine.cu`）、Windows 物理コア固定＋`_mm_pause` スピン待機（`ink_hybrid.cuh`）、SM120 Q38 向けピン留め埋め込みステージング＋バッチ `PrefetchVirtualMemory`（`engine/q38/src/engine.cu`）を統合。
  - **全実機推論ランチャー＆プリセット**: `tools/full_machine_infer.py`（`--list-models`, `--plan`, `--bench`, `--serve`）が GPU・CPU 物理/SMT トポロジ・RAM/コミット残量・SSD 空き容量を自動検出し、最適な 3階層配置プランと `configs/` サーバー設定を生成・実行します。
- **公式上流 v0.2.21 3-way マージ**: 公式の 4階層 GPU+RAM+CPU+SSD MoE、マルチ GPU `--layer-split`、GUI 同期および Control/エンジン `0.1.67` の修正を取り込みつつ、`/btw`・`/deepresearch`・RustXNG Full・ワークフロースキル・Q38 Dense ランナー・DeepSeek 拡張・Hermes `inkling2` プロバイダ・kuraneko1（MIT）プロファイル表をすべて保持しています。

## 実機ベンチマーク結果

計測環境: **NVIDIA GeForce RTX 5060 Ti 16 GB（SM120, CUDA 13.5）・AMD Ryzen 5 4500（6コア12スレッド）・32 GB DDR4・デュアル SSD（`C:` Crucial P3 NVMe + `H:` S5-1TB SSD）**（16トークン入力 / 32トークン貪欲生成）:

| モデル（サイズ） | エンジン・コンテキスト | 稼働階層 | Prefill (`pp`) | Decode (`tg`) | トークン一致 |
|---|---|---|---:|---:|---|
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | GPU 10.85 GiB (2232 exps) + Pinned RAM 4.34 GiB (840 exps) + 6P/6SMT | **85.08 t/s** | **42.22–42.33 t/s** | **32/32 完全一致** |
| **Sakura Inkling-2-Mini Q4_K_M** (16.28 GiB) | `strata-inkling2.exe` · 131K (Q8 KV) | 3階層スピル: GPU 10.85 GiB + RAM 3.60 GiB + **SSD mmap 0.74 GiB (`prefetch=on`)** + 6P/6SMT | 64.80 t/s | 14.24 t/s | **32/32 完全一致** |
| **Inkling-2-Mini UD Q4_K_M** (15.47 GiB) | `strata-inkling2.exe` · 16K (Q8 KV) | GPU 10.42 GiB (2339 exps) + Pinned RAM 3.34 GiB (733 exps) + 6P/6SMT | **109.64 t/s** | **53.28 t/s** | 正常生成 |
| **Qwen3.8-27B 3.69bpw MTP** (11.73 GiB) | `strata-q38.exe` · 4K (F16 KV) | GPU SM120 重み (10.44 GiB) + ピン留め埋め込み転送 + `PrefetchVirtualMemory` | 6.21 s (初回) | **29.95 t/s** | 正常生成 |

*CPU スレッド設計の実測根拠（Ryzen 5 4500 A/B 検証）*: 6物理コア（`host=0`, `workers=2,4,6,8,10`）を計算専用、6 SMT（`1,3,5,7,9,11`）を非同期 I/O 専用にした場合は **42.22–42.33 t/s** だったのに対し、11ワーカー（12計算スレッド）へ過負荷割り当てするとメモリ帯域競合により **29.68 t/s**（-21.9%）へ低下しました。

## バージョンと配布物

現在のリリース: **0.8.1** — GitHub Latest: [v0.8.1 リリースページ](https://github.com/zapabob/Strata/releases/tag/v0.8.1)

- **デスクトップインストーラー**: `Strata-0.8.1-windows-x64-setup.exe`（ユーザー単位 Tauri/NSIS 導入、専用 Node 24.22.3・Python・Control 0.6.3・RustXNG Full 同梱）
- **バンドルアーカイブ**: `Strata-0.8.1-windows-x64.tar.7z`（インストーラー＋`SHA256SUMS.txt`）
- **CUDA 13.5 SM120 エンジンコンポーネント（opt-in）**: `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz`（再ビルド済み SM120 エンジン5種: `strata.exe`, `strata-inkling2.exe`, `strata-inkling.exe`, `strata-hy4.exe`, `strata-q38.exe`）
- **Hy4-Flash コンポーネント（opt-in）**: `strata-hy4-0.1.64-windows-x86_64-cuda-cuda13.tar.gz`

必ずリリースページの **Assets** から正確なファイルを選び、SHA-256 ダイジェストを確認してください。コンポーネントの ed25519 署名検証は削除済み（署名鍵なし）、Windows Authenticode 署名は未付与であり、**`releaseQualified=false`** です。

![Hakua / Strata real-model Japanese chat on Qwen3.8-27B](docs/media/native-qwen38-japanese-chat.png)
*`strata-q38.exe` で `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf` を実行している実環境スクリーンショット（CUDA 13.5 / RTX 5060 Ti 16 GB）。*

## クイックスタート（デスクトップ＆全実機ランチャー）

### デスクトップの導入・上書き更新

1. 実行中の依頼を終え、モデルをアンロードし、アプリデータをバックアップしてから、トレイアイコンを含めて Strata を終了します。
2. `Strata-0.8.1-windows-x64-setup.exe` を既存の導入フォルダへ上書き実行すると、モデル・会話・メモリー・ツール・API キー・承認設定を保持したまま更新できます。
3. アプリの「手元のファイルを使う」から `strata-engine-0.7.0-windows-x86_64-cuda-cuda13.tar.gz` を取り込み、対応モデルまたはローカル GGUF を選んで読み込みます。詳細は [導入と戻し方](docs/HAKUA_INSTALL.md) を参照してください。

### 全実機推論ランチャー（`tools/full_machine_infer.py`）

```powershell
# GPU/CPU/RAM/SSD の全階層を診断し、ローカルモデル一覧と配置プランを表示
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --list-models

# Sakura Inkling-2-Mini 131K を全実機設定でベンチマーク実行
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --bench --model Sakura --max-new 32

# RAM スクイーズ付きで OpenAI/Anthropic 互換 API サーバーを起動 (127.0.0.1:8092)
terminal\.venv\Scripts\python.exe tools\full_machine_infer.py --serve --model Sakura --port 8092 --squeeze
```

## 推奨 GGUF とフォーク独自機能

- **16 GB VRAM 向け Qwen3.8-27B 推奨 GGUF**: 実機検証済みの [soyaakinohara さんの 3.69 bpw 混合量子化 GGUF](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) をおすすめします（量子化・公開の **soyaakinohara さん**、元重みの **AEON-7** に感謝）。まずは 4,096 コンテキストでお試しください（ファイル名の `12GB` は VRAM 12 GB での動作保証ではありません）。
- **自社ネイティブ Q38 Dense ランナー（`strata-q38.exe`）**: 全11種（`F32`, `F16`, `BF16`, `Q8_0`, `Q4_K`, `Q5_K`, `Q6_K`, `IQ3_S`, `IQ2_S`, `IQ4_XS`, `PQ2_0`）のテンソル単位混合量子化ディスパッチ、Tensor Core Prefill、Spin(8) / TurboQuant KV（`auto`: `f16` → `f16_turbo4` → `spin8_k8v4`）、MTP `K=3` ドラフト検証、任意の日本語正書法プロファイルに対応。詳しくは [QWEN38_DENSE_NATIVE.md](docs/QWEN38_DENSE_NATIVE.md)。
- **エージェント＆ワークフロー機能**: 独立停止できるツール非使用サブエージェント `/btw`、同梱 RustXNG Full を使う `/research`・`/deepresearch`（有効時は外部検索プロバイダへ送信）、オプトインの非公開ワークフロースキル学習／自動適用、ワークスペース＆サイドバーファイル操作、スコープ限定チャットメモリーを搭載。詳細は [WORKFLOW_SKILLS.md](docs/WORKFLOW_SKILLS.md) と [BROWSER_SEARCH.md](docs/BROWSER_SEARCH.md)。

## 保護条件と制限

安全下限は変更していません：**空き RAM 3 GiB 以上**、**コミット余力 4 GiB 以上**、**GPU 予約領域 768 MiB 以上**（17 GiB 以下の Inkling-2 では WDDM 1536 MiB 既定）、**`C:` 空き 5 GiB 以上**、**`H:` 空き 10 GiB 以上**。一般的なモデル品質・最大ウィンドウ推論・GPU 同時多重実行は未認定（**`releaseQualified=false`**）です。本 Windows 配布にはネイティブ画像入力や Linux/macOS 推論検証は含まれません。過去の測定記録は [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md) に元のバージョンで保持しています。

## 資料と開発

[導入](docs/HAKUA_INSTALL.md) · [リリース記録](docs/HAKUA_RELEASE.md) · [API・ハードウェア](docs/AI_REFERENCE.md) · [Terminal](docs/TERMINAL.md) · [ソースビルド](docs/SOURCE_INSTALL.md) · [パッケージ化](tools/packaging/README.md) · [貢献ガイド](.github/CONTRIBUTING.md) · [セキュリティ](.github/SECURITY.md) · [ライセンス](LICENSE)

```powershell
pytest tests/test_full_machine_infer.py
python -m pytest terminal/tests/terminal
```

```powershell
cd app/host
pnpm test
pnpm run build
```

[Niko1221/Strata](https://github.com/Niko1221/Strata) · [Hermes Agent](https://github.com/NousResearch/hermes-agent) · [サードパーティ表記](third_party/)

## 謝辞

Hakua / Strata を支える基盤技術・重み・研究成果を提供してくださっている **Niko1221/Strata**、**kuraneko1 (`_ryu15_`)**、**ggml & llama.cpp**、**NousResearch（Hermes Agent）**、**Qwen Team（Alibaba Cloud）**、**NVIDIA**、**RustXNG**、**libstrix**、**Node.js / Python / Tauri**、**Microsoft**、**ISTA-DASLab**、**PrismML**、**TurboQuant**、**Spin(8)**、**soyaakinohara さん**、**AEON-7** の皆様に心より感謝いたします。
