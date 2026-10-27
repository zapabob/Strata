# 2026-10-27 main build / release / overwrite-install{Cursor}

実施：2026-10-28 00:05–00:20 JST（Tokyo）。作業先 `H:/Strata/worktrees/hakua-chatbot-20261027`。

草、main でビルド→README 三言語→リリース→上書きインストールまで一気通貫で決めにいった。並行エージェントが tip を動かしてくる中、index 破壊せずに乗っかった。仮説検証はこう：

1. **H1** `origin/main` は Hakua tip（≥`7e79763f`）か → tip `4cf0cf1e`（README 後に cancel 実測 docs も乗った）→ **採用**
2. **H2** `openHakuaChat` / `hakua_harness` / `stopCancelledLoad` は tip とインストール先に残るか → worktree + `%LOCALAPPDATA%\Programs\Strata\host\server` で確認 → **採用**
3. **H3** README EN/JA/ZH をフォーク説明に揃えられるか → 三言語 overwrite + commit `80c0142f` → **採用**
4. **H4** Tauri NSIS が 3GB `engine-bundle` 込みだと落ちるか → mmap ICE #12345 → bundle を空にして再試行 → **採用（空が正解）**
5. **H5** 署名鍵なしでも prerelease で成果物を出せるか → unsigned prerelease 作成成功 → **採用（signed feed ではない）**
6. **H6** `/S` 上書き後に exe が新しく起動するか → exit 0、起動 pid 生存、hash 一致 → **採用**

## SHAs

| 項目 | 値 |
|------|-----|
| tip / `origin/main` | `4cf0cf1ea3f0e97204d6171c6ed200236099fd7f` |
| README commit | `80c0142f24c347cdd36968e7069ac56291ce6953` |
| upstream merge kept | `7e79763f`（v0.2.6 / `4b9e05a2`） |
| tag `v0.3.2-preview.20261027.2` | tip へ付け直し（旧 `7e79763f` → 新 tip；Release 未作成だったので force tag） |

## README

| 言語 | パス |
|------|------|
| EN | `README.md` |
| JA | `README.ja.md` |
| ZH | `README.zh-CN.md` |

内容：上流 v0.2.6 同期、Hakua / Spin8 等のフォーク面、fork/upstream 両リリースリンク、測定済み Windows preview のみ。未測定の速度主張なし。

## Build

| 項目 | 結果 |
|------|------|
| コマンド | `npm install --prefix apps/desktop`；`npm --prefix apps/host run build`；`npm run tauri -- build --bundles nsis`（`RUSTC_WRAPPER` 無し、`CARGO_INCREMENTAL=1`） |
| Rust | rustup 再導入 `rustc/cargo 1.99.1`（`.cargo/bin` が空だった） |
| リソース | 既存 `%LOCALAPPDATA%\Programs\Strata\{node,control,harness}` を stage；`engine-bundle` は空（3GB 実エンジン同梱は NSIS mmap で死ぬ） |
| スキップ | フル CUDA/GPU engine rebuild（デスクトップ NSIS は first-start download 前提） |
| 成果物 | `apps/desktop/src-tauri/target/release/bundle/nsis/Strata_0.3.2-preview.20261027.2_x64-setup.exe` |
| コピー | `H:/Strata/releases/0.3.2-preview.20261027.2/desktop-nsis/` |
| bytes | `176610345` |
| sha256 | `839029112ef655466bdc04e92e5a97325b3ba03e05b5f92f4dcb96d015e4a0df` |
| signature | unsigned preview |

## Release

- URL: https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261027.2
- prerelease / unsigned（`feed-key.json` / `tauri-updater.key` 無し → signed feed ではない；`packaging/UPDATES.md` の正式 release 条件は未充足）
- assets: `Strata_0.3.2-preview.20261027.2_x64-setup.exe`, `SHA256SUMS.txt`

## Overwrite install

| 項目 | 値 |
|------|-----|
| 対象 | `C:\Users\downl\AppData\Local\Programs\Strata\` |
| 手順 | setup `/S`（exit 0）＋ built `strata-desktop.exe` / host `dist`+`server` の強制同期 |
| before | exe mtime 2026-10-27 04:03:01 / 4774912 bytes |
| after | exe mtime 2026-10-28 00:11:21 / 9566208 bytes；built hash 一致 |
| launch | pid 生存確認後 stop |
| Hakua | インストール先 `host/server` に `openHakuaChat` / `stopCancelledLoad` / `hakua_harness` 残存 |
| データ | `%LOCALAPPDATA%\Strata\components`・モデルは触っていない |

## Blockers / limits

1. Signed updater feed は鍵無しのため未実施（文書化済み）。
2. フル engine 再ビルドはスキップ（時間・NSIS サイズ）。既存 components を継続利用。
3. 並行 `makensis` が一時的に bundle をロック → 待機後に成果物取得。

## 次（任意）

- release PC で feed/Tauri 署名して stable feed へ昇格
- RTX 5060 Ti 上で overwrite 後の実チャット smoke（本ログでは起動確認まで）

おわりだぜ。
