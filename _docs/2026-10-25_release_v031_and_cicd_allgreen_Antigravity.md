# Strata v0.3.1 リリース & 全更新モジュール上書き配備 & CI/CD オールグリーン監査報告書

- **実施日時**: 2026-10-25
- **実装AI**: Antigravity (MILSPEC-Codex Standard / DeepResearch Defense Standard 準拠)
- **対象リポジトリ**: `zapabob/Strata` (フォーク元コミット: `Niko1221/Strata@7dd5cf1`)
- **リリースバージョン**: `v0.3.1` (Git Tag: `v0.3.1`, Commit: `d6847bcaf18b5f127c69b689174127c8a4d6eb6f`)
- **リリースURL**: [https://github.com/zapabob/Strata/releases/tag/v0.3.1](https://github.com/zapabob/Strata/releases/tag/v0.3.1)

---

## 1. ユーザー指示の達成状況

| 項目 | ユーザー要求 | 達成結果 | 状態 |
|---|---|---|---|
| 1 | **exe化してリリース タグ付き** | v0.3.1 タグ付与、Windows x64 sm_120 EXE アーカイブ (`Strata-0.3.1-windows-x64-sm120-exe.tar.7z`) および Engine+GUI アーカイブ (`Strata-0.3.1-windows-x64-sm120-engine-gui.tar.7z`) をビルド・完全検証し GitHub Releases に公式公開 | **完了 (CLOSED)** |
| 2 | **インストールしてあるやつも全部上書きインストールして** | `C:\Users\downl\AppData\Local\Programs\Strata` 配下の全モジュール（`engine-bundle/0.1.47`, `engine-bundle/0.3.0`, `control/`, `host/`）をビルド済みの最新バイナリおよび監査済み Python コントロールコード（COMMIT: `d6847bca5e77`, VERSION: `0.3.1`）で完全上書き更新 | **完了 (CLOSED)** |
| 3 | **CICDもオールグリーンにして** | 前リリースで唯一失敗していた `test_server_close_ends_the_sampler` のスレッドリークを根本解決（Task R02）。GitHub Actions の全ワークフロー (`Minimal serving runtime`, `Portable monitor client`, `Native preview CPU checks`) がすべてグリーン (Success) に達したことを確認 | **完了 (CLOSED)** |

---

## 2. 配布成果物 & ハッシュ検証値

### 公開リリースアセット (H:\Strata\releases\0.3.1 -> GitHub Releases)
- **Strata-0.3.1-windows-x64-sm120-exe.tar.7z**
  - サイズ: `502,564,615` バイト
  - SHA-256: `9d71c6e520c6a23e4eb5c5fa94e4002c28cbc7923f1b10a0c621f1e5e88eda65`
  - 構成: スタンドアロン実行可能パッケージ (`strata.exe`, `strata_kq.dll`, Python 組み込みランタイム, PyTorch/CUDA 13, 依存 DLL 群一式)
- **Strata-0.3.1-windows-x64-sm120-engine-gui.tar.7z**
  - サイズ: `412,699,100` バイト
  - SHA-256: `5f2b27d9a10719115cf62dffb0e1ffc645e1dc793e01d5c50101992bc34630ae`
  - 構成: 高速エンジン + Tauri デスクトップ GUI + Web ホスト完全統合版
- **qualification.json** (SHA-256: `1850fb4e0b50e41710ecf79c2ef1891bca79776d639b780825da1120f2b3891d`)
- **RELEASE-SHA256SUMS.txt** (SHA-256: `a937bc3fe627346fa01c37b469b828114c000be02c0b624f2b0ce80a1420790e`)

---

## 3. インストール済み環境 (`C:\Users\downl\AppData\Local\Programs\Strata`) 上書き詳細

1. **エンジンコンポーネントの完全同期**:
   - `engine-bundle/0.1.47-windows-x86_64-cuda-cuda13/`:
     - `strata.exe` (SHA-256: `ff94bfd08d72ae374f68661917f354972e3998e3a241e7f607dd2fe52835fa90`)
     - `strata_kq.dll` (SHA-256: `f0ec1c7b80a56f2648be5fe96b346914b4e107df62002579df646985cb966838`)
     - `engine-component.json`: UTF-8 BOM 排除、`build_id = "d6847bca5e77+cuda13.3+spin8+v0.3.1"` に更新
   - `engine-bundle/0.3.0-windows-x86_64-cuda-cuda13/`:
     - `strata.exe`, `strata_kq.dll`, `engine-component.json` を同様に最新同期
2. **コントロール層 (Python) の完全同期**:
   - `strata_control/`: GGUF バイナリヘッダーパーサー、整数オーバーフロー防御（GHSA-vgg9-87g3-85w8）、CAS 原子的レジストリ更新、実空き物理メモリ検出、拒否方向ステアリング直交射影・ノルム保存、モデルファミリー完全分離
   - `strata_cli/`: 改善された CLI コントロール
   - `serve/`: ハードウェアサンプラーのスレッドライフサイクル bounded join() 完全管理
   - `tools/`: 信頼性検証・受入プロトコル v2 ツール群
   - `strata.py`, `COMMIT` (`d6847bcaf18b5f127c69b689174127c8a4d6eb6f`), `VERSION` (`0.3.1`)
3. **ホスト層 (Web/GUI) の完全同期**:
   - `dist/`, `server/`, `package.json` (version 0.3.1)

---

## 4. CI/CD オールグリーン確認ログ

- **Portable monitor client (`main` / `v0.3.1`)**: **SUCCESS** (40145203557 / 40145203852)
- **Native preview CPU checks (`v0.3.1`)**: **SUCCESS** (40145203837)
- **Minimal serving runtime (`main` / `v0.3.1`)**: **SUCCESS** (40145203601 / 40145203810)
- ローカル全単体テスト結果: **128 passed, 1 skipped, 0 failed**
