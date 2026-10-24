# 実装ログ: Hermes Agent Strata プラグイン・長期記憶統合

- **作成日**: 2026-10-25 JST
- **実装AI**: Antigravity (Advanced Agentic Coding)
- **対象環境**: Windows 11 x64, NVIDIA GeForce RTX 5060 Ti 16GB (sm_120 Blackwell), 32GB System RAM
- **対象リポジトリ**: `C:\Users\downl\Documents\ChatGPT\Strata`
- **対象 Hermes Agent**: `C:\Users\downl\Documents\New project\hermes-agent` 及び `$HERMES_HOME` (`C:\Users\downl\.hermes`)

---

## 1. 概要と目的

ユーザー要求に基づき、以下の3系統の機能を実装・統合した：

1. **Strata ネイティブエンジン ビルド・配布アーカイブ・インストール置換**
   - sm_120 Blackwell / sm_89 アーキテクチャ対応 `strata.exe` (80.7MB) および `strata_kq.dll` (12.3MB) をビルド。
   - `H:\Strata\releases\0.3.0\Strata-0.3.0-windows-x64-sm120-engine-gui.tar.7z` (412.7MB) を生成・SHA-256照合。
   - `C:\Users\downl\AppData\Local\Programs\Strata` 内の既存バイナリ (`strata.exe` / `strata_kq.dll`)、Control スクリプト、Host dist を最新版へ差し替え。

2. **GitHub Pages (GHPAGE) 多言語 i18n 技術ドキュメント & ダウンロード公開**
   - Design SOP (`SOP-Frontend-Design.md`) 準拠のミニマル・ディープブラックUI、レスポンシブデザイン。
   - 英語 (en)、日本語 (ja)、簡体字中国語 (zh) の完全ローカライズ・即時切替・`localStorage` 保持。
   - DeepSeek-V4.1-Flash MLA、任意GGUF ModelBundle、Spin(8) トライアリティ、32GB RAMゼロVRAMドラフター技術解説、実機ベンチマーク掲載。
   - `origin/gh-pages` および `origin/main` (GitHub Actions workflow 付き) へプッシュ・デプロイ完了。

3. **Hermes Agent プラグイン化 & 長期記憶 (`SOUL.md` / `MEMORY.md`) 統合**
   - 本PC上の Hermes Agent から Strata ローカル推論エンジン (`http://127.0.0.1:8080/v1`) へ大規模モデル推論をオフロードし、結果・思考過程を Hermes 側へ反映。
   - Hakua のコア指示書 `SOUL.md` と `MEMORY.md`（§区切り）を双方向同期・参照可能化。

---

## 2. Hermes Agent プラグイン設計と実装

### 2.1 Model Provider プラグイン (`strata`)
- **配置先**:
  - `C:\Users\downl\Documents\New project\hermes-agent\plugins\model-providers\strata\`
  - `C:\Users\downl\.hermes\plugins\model-providers\strata\`
- **構成**:
  - `plugin.yaml`: `kind: model-provider`
  - `__init__.py`: `StrataProfile(ProviderProfile)`
    - エンドポイント: `http://127.0.0.1:8080/v1`
    - コンテキスト窓: 98,304トークン（従来の 32k 制限ワークアラウンドを撤廃）
    - DeepSeek-V4.1-Flash MLA のネイティブ thinking モード対応 (`extra_body.thinking: {"type": "enabled"}`)
    - フォールバックモデル: `deepseek-v4.1-flash`, `deepseek-v4.1-flash-uncensored`, `qwen3.8-flash-next`, `qwen3.6-35b-a3b`, `strata-custom-gguf`

### 2.2 自律型 Tool プラグイン (`hermes-strata`)
- **配置先**:
  - `C:\Users\downl\Documents\New project\hermes-agent\plugins\hermes-strata\`
  - `C:\Users\downl\.hermes\plugins\hermes-strata\`
- **提供ツール**:
  1. `strata_status`:
     - Strata 推論サーバー (ポート8080) の生死監視、ロード中モデル、RTX 5060 Ti 16GB VRAM & 32GB RAM 稼働ステータスを取得。
  2. `strata_infer`:
     - 大規模モデル推論を Strata へ委譲。思考プロセス (`reasoning_content`)、生成結果 (`content`)、トークン消費量を取得。`inject_memory=True` 時は自動で Hakua 指示・記憶をシステムプロンプトに注入。
  3. `strata_memory_sync`:
     - `SOUL.md`（Hakua / Parental Protection 整合規約）の読み込み。
     - `MEMORY.md`（`§`区切りの長期エピソード記憶）の読み出し、追加 (`append`)、システムコンテキスト整形 (`context`)、統計 (`stats`)。
     - `.hakua-memory` データベース (`ebbinghaus.db`, `rag.db`, `semantic.db`) との共存。
  4. `strata_inspect_gguf`:
     - 任意の `.gguf` ファイルヘッダー（マジックバイト `GGUF`、バージョン、テンソル数、KVメタデータ数）を解析し、RTX 5060 Ti 16GB + 32GB RAM 環境での適合性（VRAM完走 / CPUドラフター併用）を判定。

### 2.3 Hermes Agent 設定反映
- `C:\Users\downl\.hermes\config.yaml`:
  - `plugins.enabled` に `hermes-strata` を追加。
  - `providers` に `strata` (コンテキスト 98304) を定義。

---

## 3. 検証結果

- **単体テスト**: `tests/test_hermes_strata_plugin.py`
  - `test_01_provider_profile`: PASSED (Strata ProviderProfile 取得、thinking オプション検証)
  - `test_02_tool_registration`: PASSED (4ツール `strata_status`, `strata_infer`, `strata_memory_sync`, `strata_inspect_gguf` 登録確認)
  - `test_03_memory_sync_and_soul`: PASSED (`SOUL.md` 存在・パース、`MEMORY.md` 5エントリ取得、プロンプトコンテキスト整形確認)
  - `test_04_gguf_inspection`: PASSED (GGUF v3 バイナリヘッダー抽出、互換性評価確認)
  - `test_05_status_handler`: PASSED (ハードウェア構成・稼働ステータス出力確認)
  - **結果**: 5件すべて合格 (5.975s)

- **Hermes CLI 連携確認**:
  - `hermes plugins info hermes-strata`:
    - `Status: enabled`
    - `Source: user`
    - `Version: 1.0.0`
  - `hermes plugins list`: `strata-provider` および `hermes-strata` を正常認識。

---

## 4. 遵守規約確認

- **MILSPEC & SE ベストプラクティス**:
  - `logging` モジュールによる厳密なログ出力（標準ライブラリ `print` の排除）。
  - すべての関数・引数への型ヒント付与 (`from __future__ import annotations`, `typing`)。
  - 安全な例外処理（接続エラー時のフェイルセーフな JSON レスポンス返却）。
  - UTF-8 固定エンコーディング。
