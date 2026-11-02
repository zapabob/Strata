# NSIS 上書きと README

- **日時**: 2026-11-03 00:31 JST（インストーラ終了 2026-11-02T15:28:42Z、上書き `INSTALL_EXIT=0` は 2026-11-02T15:31:47Z）
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。起動時間とトークン速度は未計測。

## 概要

`0.4.0-preview.20261103.1` の NSIS を作り、この PC の Strata へ `/S /UPDATE` した。署名済みエンジンは残し、未署名の Qwen3.6 パッケージを別フォルダへ置いた。README 8 本はその内容に合わせた。

## 前提・判断

- `cargo tauri` は入っていない。`apps/desktop/node_modules/.bin/tauri.cmd` を使った。
- 公開 UI は同梱 Node 24.22.2 と `H:\Strata\releases\hakua033-public-assets`。
- `verify-release` は notices の `.gitignore` を第三者通知の会員と数えて落ちた。会員比較からその 1 ファイルだけ外した。
- 新しいエンジンは 7 ファイル、画像リーダーなし、`signature` は null。署名済み `0.4.0-windows-x86_64-cuda-cuda13` は上書きしていない。
- 同バージョンでフォルダ名が先に並ぶため、`resolve()` は未署名パッケージ `0.4.0-q36-windows-x86_64-cuda-cuda13`（build `a91353feb0dc`）を選ぶ。PrismML と TurboQuant は署名済みフォルダの `llama-server.exe` のまま。

## 検証

| 項目 | 結果 |
|------|------|
| NSIS | exit 0。`Strata_0.4.0-preview.20261103.1_x64-setup.exe`、113762866 bytes、SHA-256 `335e442bfd174ff3dabf5ea612e37debd707f7f8ccb9b1811ec41d711807efb6` |
| `/S /UPDATE` | `INSTALL_EXIT=0` |
| DisplayVersion | `0.4.0-preview.20261103.1` |
| インストール先 host | `0.4.0-preview.20261103.1` |
| 選択エンジン | unsigned、`a91353feb0dc` |
| spill guard | 不合格のまま |
| 速度 | 未計測 |

## リリース

`https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.1`  
タグは `feat/q36-32gb16gb` の `4031d428`。`--latest=false`。GitHub の latest は `v0.4.0-preview.20261101.1` のまま。main は動かしていない。

資産: setup EXE 113762866 bytes、SHA256SUMS.txt、未署名エンジン tar 719548928 bytes。

## 残留リスク

- mapped-pack の実 GGUF 起動、起動時間、トークン速度は未計測。
- T06 の転送スケジュールと T07 の CUDA kernel は、測定が無いので既定化していない。
- 32GB では UD-Q4_K_XL の legacy arena を物理 RAM が拒否し得る。
