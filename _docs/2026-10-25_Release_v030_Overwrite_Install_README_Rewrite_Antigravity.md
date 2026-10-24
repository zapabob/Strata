# 2026-10-25 Strata v0.3.0 正式リリース・上書きインストール・README リライト実施記録

- **実施日時**: 2026-10-25 JST
- **実装担当**: Antigravity (MILSPEC-Codex Standard準拠)
- **対象リポジトリ**: `C:\Users\downl\Documents\ChatGPT\Strata` (`zapabob/Strata`)
- **コミットハッシュ**: `b8bc051c`
- **リリースバージョン**: `v0.3.0` (Tag: `v0.3.0`)
- **GitHub リリース URL**: [https://github.com/zapabob/Strata/releases/tag/v0.3.0](https://github.com/zapabob/Strata/releases/tag/v0.3.0)

---

## 1. 実施作業の概要

ユーザーからの指示に基づき、以下のタスクを完全実施しました：

1. **GitHub 正式リリース v0.3.0 の公開**:
   - `gh release create v0.3.0` を実行し、公式リリースを GitHub 上に公開。
   - 配布バイナリアーカイブ `Strata-0.3.0-windows-x64-sm120-engine-gui.tar.7z` (412,713,560 bytes) を添付。
   - `RELEASE-SHA256SUMS.txt` および `qualification.json` を添付。
   - SHA-256 チェックサム: `97a2d28bc91474bd37c0dcfd0bc8abc1ed10ae8db3b0c774d5ceb5a4f3c9c374`。

2. **既存インストール環境の上書きアップデート**:
   - 旧バージョン（`0.1.45.3` および `0.1.47`）のエンジンバイナリが存在していた各ディレクトリを、新世代 `0.3.0` (80.7 MB, sm_120/sm_89 ネイティブ CUDA エンジン) で安全に置換。
   - `C:\Users\downl\AppData\Local\Strata\components\engine\` 配下の `0.1.45.3`、`0.1.47`、および新規 `0.3.0-windows-x86_64-cuda-cuda13` を更新。
   - `C:\Users\downl\AppData\Local\Programs\Strata\engine-bundle\` 配下も同様に更新。
   - `engine_component.resolve(full=True)` により、`0.3.0` が最優先エンジンとして認識されることを確認。

3. **デスクトップアプリのバージョン不整合解消**:
   - デスクトップ版 Tauri シェルが古い `0.2.2` のバージョン文字列を環境変数経由でホストに渡していた問題を解決。
   - `apps/host/server/app-version.mjs` および `apps/host/src/lib/app-version.ts` を修正し、`control/VERSION`（`0.3.0`）を最優先判定するよう変更。
   - `apps/desktop` および `apps/host` の `package.json` / `Cargo.toml` を `0.3.0` に同期。
   - Vite ビルド（`pnpm --dir apps/host build`）を行い、`AppData\Local\Programs\Strata\host\` に再配備。
   - Node 実行環境にて `AppVersion: 0.3.0` と正しく表示されることを検証完了。

4. **README の全面リライト (日英中)**:
   - `README.md`、`README.ja.md`、`README.zh-CN.md` を更新。
   - プレビュー版表記を廃止し、正式リリース `v0.3.0` のダウンロードリンク・SHA-256 を明記。
   - 実機ベンチマーク測定結果（Ryzen 5 4500 6C/12T + RTX 5060 Ti 16GB sm_120 + 32GB RAM）を明記：
     - Qwen3.8-Flash-Next (125B MoE, Q2_0): 6.7 tok/s, GPU hit 61.7%
     - DeepSeek-V4.1-Flash (Maya-S, MLA): 5.8 tok/s, GPU hit 56.4%
     - 動的共有メモリ最適化による 3.375 GiB の CUDA スタック浪費解消
   - デスクトップ GUI アプリとターミナル CLI の両方のセットアップ手順を記載。
   - Hermes Agent プラグイン（`plugins/hermes-strata`）および長期記憶（SOUL.md / MEMORY.md / SQLite）の連携ガイドを追加。

---

## 2. 成果物一覧

| 種別 | ファイルパス / URL |
| :--- | :--- |
| **GitHub リリース** | `https://github.com/zapabob/Strata/releases/tag/v0.3.0` |
| **配布パッケージ** | `Strata-0.3.0-windows-x64-sm120-engine-gui.tar.7z` |
| **README (英語)** | [README.md](file:///C:/Users/downl/Documents/ChatGPT/Strata/README.md) |
| **README (日本語)** | [README.ja.md](file:///C:/Users/downl/Documents/ChatGPT/Strata/README.ja.md) |
| **README (中国語)** | [README.zh-CN.md](file:///C:/Users/downl/Documents/ChatGPT/Strata/README.zh-CN.md) |
| **Hermes プラグイン** | [plugins/hermes-strata/](file:///C:/Users/downl/Documents/ChatGPT/Strata/plugins/hermes-strata/) |
| **長期記憶 MCP** | [tools/strata_memory_mcp.py](file:///C:/Users/downl/Documents/ChatGPT/Strata/tools/strata_memory_mcp.py) |
| **受入記録** | [_docs/qa/model-acceptance.json](file:///C:/Users/downl/Documents/ChatGPT/Strata/_docs/qa/model-acceptance.json) |

全タスクは MILSPEC LLMOps 基準に基づき正常に完了しました。
