# 2026-11-03 古いローカルリリース複製の削除

## 概要

`H:\Strata\releases` の古い展開、worktree、ソーススナップショット、診断、再公開の複製だけを削除した。ディスクの空きは削除開始直前 `59,686,305,792` バイトから完了直後 `127,566,139,392` バイトになり、空きの増加は `67,879,833,600` バイト（約 63.2 GiB）だった。削除した 116 エントリの論理サイズ合計は `95,673,917,924` バイト。ロックで残したディレクトリは無い。

Qwen3.6 の目標完了は、この作業では判断していない。

## 背景・要求

古いローカルリリースは捨ててよい、という依頼に対して、削除範囲は `H:\Strata\releases` だけに限定した。GitHub のリリースは削除していない。force-push はしていない。CUDA ビルドのプロセスは止めていない。

## 前提・判断

- 削除前にトップレベル 130 エントリの論理サイズを測り、KEEP / DELETE を出してから `Remove-Item -Recurse -Force` した。
- `hakua040-native-sync-20261103` は削除開始前に `cmake --build` がそのパスを指していた。ディレクトリと、名前が `hakua040-native-sync-20261103` で始まる隣接ログは残した。
- `hakua040-nsis-cargo-20261103` の中に `Strata_0.4.0-preview.20261103.2_x64-setup.exe` と `SHA256SUMS-20261103.2.txt` があるので、ディレクトリごと残した。
- `hakua040-q36-engine-20261103` は 2026-11-03 の未署名 Qwen3.6 エンジン包（`strata-engine-0.4.0-q36-windows-x86_64-cuda-cuda13.tar`）を含むので残した。この中の `engine-component.json` は `"signature": null`。
- 署名オブジェクトがある `0.4.0-windows-x86_64-cuda-cuda13` は `hakua040-components-r3` だけだった（`alg` `ed25519`、`key_id` `1daf8588d50b1049`）。例示リストには削除候補として挙がっていたが、最後の署名付きツリーなので残した。`hakua040-nsis-engine-pkg-20261102` の同名ツリーは `"signature": null` だったので削除した。
- `hakua033-public-assets` と `hakua033-public-assets.receipt.json` は releases 配下を名前検索し、どちらもトップレベルに1つだけあったので残した。`hakua033-public-asset-sources` は別名のスナップショットなので削除した。
- `hakua040-upstream-c62\apps\host\node_modules` は `hakua040-source-r1\apps\host\node_modules` へのジャンクションだった。両方とも削除対象なので、`Remove-Item` の前に `rmdir` でジャンクションだけ外した。指していた先は releases の外ではなかった。他の reparse point は削除対象の中に無かった。
- 削除中に新しく現れた `hakua040-q36-engine-sync-20261103` は、削除前の一覧に無かった。中身は `0.4.0-q36-windows-x86_64-cuda-cuda13`（最終更新 2026-11-03 21:18）。事前リストに無い 2026-11-03 の同期ツリーなので消していない。
- `shell-prefs.json`（53 バイト）はリリース複製ではないので残した。
- 触っていない: `H:\Strata\models`、`H:\Strata\packs`、`H:\Strata\deps`、`H:\Strata\private-keys`、この git リポジトリのソース、GitHub releases。

## 変更対象ファイル

- 追加: `_docs/2026-11-03_drop-old-release-copies{Cursor}.md`（このファイルだけをコミットする）
- 削除: 下の `H:\Strata\releases` 直下 116 エントリ。リポジトリ内のファイルは削除していない。

## 実装詳細

削除は `H:\Strata\releases\<name>` の直下だけ。KEEP 名と `*native-sync-20261103*` はスクリプト側でも拒否した。

### 残したもの

| 名前 | 削除前の論理バイト |
| --- | ---: |
| `hakua033-public-assets` | 33,435 |
| `hakua033-public-assets.receipt.json` | 1,966 |
| `hakua040-components-r3` | 2,102,581,230 |
| `hakua040-native-sync-20261103` | 667,219,254 |
| `hakua040-native-sync-20261103-build-resume.cmd` | 587 |
| `hakua040-native-sync-20261103-build-resume.log` | 521,228 |
| `hakua040-native-sync-20261103-build.cmd` | 548 |
| `hakua040-native-sync-20261103-build.log` | 2,863,452 |
| `hakua040-native-sync-20261103-configure.cmd` | 1,034 |
| `hakua040-native-sync-20261103-configure.err` | 4,339 |
| `hakua040-native-sync-20261103-configure.log` | 3,302 |
| `hakua040-nsis-cargo-20261103` | 2,496,585,432 |
| `hakua040-q36-engine-20261103` | 1,439,091,544 |
| `shell-prefs.json` | 53 |

削除後に測り直したとき、上に加えて次も残っていた。

- `hakua040-native-sync-20261103-spill-guard.log`（6,708 バイト）。削除前の一覧には無く、ビルド側のログなので残した。
- `hakua040-q36-engine-sync-20261103`（論理 726,359,119 バイト）。

削除後の `H:\Strata\releases` 論理サイズ合計は `7,435,356,003` バイト。ボリューム空きは `127,566,139,392` バイトのままだった。

### 削除したもの（116）

論理サイズ合計 `95,673,917,924` バイト。すべて `Remove-Item -Recurse -Force` が成功し、削除後にパスは残っていなかった。

- `H:\Strata\releases\0.3.2-preview.20261029.1`
- `H:\Strata\releases\0.3.2-preview.20261029.2`
- `H:\Strata\releases\0.4.0-preview.20261101.1`
- `H:\Strata\releases\hakua033`
- `H:\Strata\releases\hakua033-candidate-control-r10-preserved`
- `H:\Strata\releases\hakua033-candidate-control-r11-preserved`
- `H:\Strata\releases\hakua033-candidate-control-r7-preserved`
- `H:\Strata\releases\hakua033-candidate-control-r8-preserved`
- `H:\Strata\releases\hakua033-candidate-control-r9-preserved`
- `H:\Strata\releases\hakua033-candidate-engine-r4-preserved`
- `H:\Strata\releases\hakua033-candidate-notices-r1-preserved`
- `H:\Strata\releases\hakua033-cargo-target`
- `H:\Strata\releases\hakua033-components`
- `H:\Strata\releases\hakua033-components-r2`
- `H:\Strata\releases\hakua033-components-r3`
- `H:\Strata\releases\hakua033-components-r4`
- `H:\Strata\releases\hakua033-components-r5`
- `H:\Strata\releases\hakua033-control-r10`
- `H:\Strata\releases\hakua033-control-r11`
- `H:\Strata\releases\hakua033-control-r12`
- `H:\Strata\releases\hakua033-control-r5`
- `H:\Strata\releases\hakua033-control-r6`
- `H:\Strata\releases\hakua033-control-r7`
- `H:\Strata\releases\hakua033-control-r8`
- `H:\Strata\releases\hakua033-control-r9`
- `H:\Strata\releases\hakua033-downloaded-draft-r1`
- `H:\Strata\releases\hakua033-engine-stage-r5`
- `H:\Strata\releases\hakua033-extracted-r2`
- `H:\Strata\releases\hakua033-extracted-r4`
- `H:\Strata\releases\hakua033-extracted-r5`
- `H:\Strata\releases\hakua033-extracted-r6`
- `H:\Strata\releases\hakua033-gui-repro-fresh-r3`
- `H:\Strata\releases\hakua033-installer-r2`
- `H:\Strata\releases\hakua033-native-recovery`
- `H:\Strata\releases\hakua033-node-24.22.2`
- `H:\Strata\releases\hakua033-node-with-license`
- `H:\Strata\releases\hakua033-notices-r1`
- `H:\Strata\releases\hakua033-notices-r2`
- `H:\Strata\releases\hakua033-outer-check-r6`
- `H:\Strata\releases\hakua033-ple-oracle`
- `H:\Strata\releases\hakua033-previous-release`
- `H:\Strata\releases\hakua033-public-asset-sources`
- `H:\Strata\releases\hakua033-publication`
- `H:\Strata\releases\hakua033-publication-r5`
- `H:\Strata\releases\hakua033-publication-r6`
- `H:\Strata\releases\hakua033-runtime-stage`
- `H:\Strata\releases\hakua033-runtime-stage-r6`
- `H:\Strata\releases\hakua033-runtime-stage-r6-dist-before-raw-sync`
- `H:\Strata\releases\hakua033-source-control-r5-preserved`
- `H:\Strata\releases\hakua033-source-control-r6-preserved`
- `H:\Strata\releases\hakua033-source-native-old-preserved`
- `H:\Strata\releases\hakua033-source-r1`
- `H:\Strata\releases\hakua033-source-turbo-r3-preserved`
- `H:\Strata\releases\hakua033-vendor-notices`
- `H:\Strata\releases\hakua033-window-r6`
- `H:\Strata\releases\hakua033-worktree`
- `H:\Strata\releases\hakua034-diagnostics-fresh-r4`
- `H:\Strata\releases\hakua034-diagnostics-target`
- `H:\Strata\releases\hakua034-memory-probe-source-r2`
- `H:\Strata\releases\hakua034-memory-probe-source-r5`
- `H:\Strata\releases\hakua034-startup-ui-r1`
- `H:\Strata\releases\hakua040-ca-outer-check-r1`
- `H:\Strata\releases\hakua040-ca-prefix-installer-preserved-r2`
- `H:\Strata\releases\hakua040-ca-public-download-r1`
- `H:\Strata\releases\hakua040-ca-publication-r1`
- `H:\Strata\releases\hakua040-component-assets-r3`
- `H:\Strata\releases\hakua040-control-assets-r4`
- `H:\Strata\releases\hakua040-control-assets-r5`
- `H:\Strata\releases\hakua040-control-assets-r6`
- `H:\Strata\releases\hakua040-control-r1`
- `H:\Strata\releases\hakua040-control-r2`
- `H:\Strata\releases\hakua040-control-r3`
- `H:\Strata\releases\hakua040-control-r4`
- `H:\Strata\releases\hakua040-control-resource-r1-preserved`
- `H:\Strata\releases\hakua040-control-resource-r3-preserved`
- `H:\Strata\releases\hakua040-control-resource-r4-preserved`
- `H:\Strata\releases\hakua040-extracted-upstream-c62-r1`
- `H:\Strata\releases\hakua040-extracted-upstream-c62-r2`
- `H:\Strata\releases\hakua040-failed-local-backends-r1`
- `H:\Strata\releases\hakua040-feed-r3`
- `H:\Strata\releases\hakua040-feed-r4`
- `H:\Strata\releases\hakua040-feed-r5`
- `H:\Strata\releases\hakua040-feed-r6`
- `H:\Strata\releases\hakua040-install-temp-r1`
- `H:\Strata\releases\hakua040-install-temp-r2`
- `H:\Strata\releases\hakua040-installer-r1`
- `H:\Strata\releases\hakua040-installer-r2-preserved`
- `H:\Strata\releases\hakua040-memory-probe-source-r10`
- `H:\Strata\releases\hakua040-memory-probe-source-r12`
- `H:\Strata\releases\hakua040-memory-probe-source-r7`
- `H:\Strata\releases\hakua040-native-upstream-r1`
- `H:\Strata\releases\hakua040-notices-r1-preserved`
- `H:\Strata\releases\hakua040-nsis-cargo-20261102`
- `H:\Strata\releases\hakua040-nsis-engine-pkg-20261102`
- `H:\Strata\releases\hakua040-nsis-native-20261102`
- `H:\Strata\releases\hakua040-nsis-public-download-20261102`
- `H:\Strata\releases\hakua040-nsis-publication-20261102`
- `H:\Strata\releases\hakua040-official-app-extracted-r1`
- `H:\Strata\releases\hakua040-official-app-extracted-r3`
- `H:\Strata\releases\hakua040-official-install-temp-r1`
- `H:\Strata\releases\hakua040-official-installer-r2-preserved`
- `H:\Strata\releases\hakua040-official-outer-check-r2`
- `H:\Strata\releases\hakua040-official-publication-r2`
- `H:\Strata\releases\hakua040-qualified-feed-entries-r1`
- `H:\Strata\releases\hakua040-source-r1`
- `H:\Strata\releases\hakua040-startup-app-extracted-r1`
- `H:\Strata\releases\hakua040-startup-outer-check-r1`
- `H:\Strata\releases\hakua040-startup-pre-fix-installer-r4-preserved`
- `H:\Strata\releases\hakua040-startup-publication-r1`
- `H:\Strata\releases\hakua040-terminal-r1`
- `H:\Strata\releases\hakua040-terminal-r2`
- `H:\Strata\releases\hakua040-terminal-r3`
- `H:\Strata\releases\hakua040-terminal-r4`
- `H:\Strata\releases\hakua040-terminal-r5`
- `H:\Strata\releases\hakua040-upstream-c62`
- `H:\Strata\releases\install`

## 実行コマンド

サイズ計測、reparse 走査、削除はそれぞれ一時スクリプトで実行した。削除本体は各対象に `Remove-Item -LiteralPath <path> -Recurse -Force`。ジャンクション1件だけ事前に `cmd /c rmdir`。

空き容量は `GetDiskFreeSpaceExW`（`H:\Strata\releases`）。

## テスト・検証結果

- 削除成功 116。`SKIPPED_COUNT 0`。ロックでスキップしたものは無い。
- 削除後も次が存在する: `.2` の setup exe、その `SHA256SUMS-20261103.2.txt`、未署名 Qwen3.6 tar、署名付き `engine-component.json`、`hakua033-public-assets`、receipt、`hakua040-native-sync-20261103`。
- 削除開始前、`cmake.exe`（PID 18836）と `cmd.exe`（PID 25904）が `hakua040-native-sync-20261103` を指していた。削除操作の時点ではその2プロセスは既に終了していた。残っていた MSBuild は `/nodemode:1 /nodeReuse:true` で、コマンドラインに releases のパスは無かった。それらを止める操作はしていない。削除完了後の確認では cmake / MSBuild / cl / nvcc は見えていなかった。
- この確認は Qwen3.6 対応の完了証明ではない。

## 残留リスク

- 論理サイズ合計とボリューム空き増加は一致しない。差は約 27.8 GiB。NTFS 圧縮、ハードリンク、削除中に増えた `hakua040-q36-engine-sync-20261103` とビルドログで説明できる範囲であり、割り当てバイトの内訳は取っていない。ディスクが空いた量はボリューム差の `67,879,833,600` バイトである。
- `hakua040-q36-engine-sync-20261103` は作業中に出現したため残した。古い複製だと後で分かるなら、署名付きツリーと未署名 tar が別にあることを確認したうえで個別に判断できる。
- 署名付きコンポーネントのローカル最後の1本は `hakua040-components-r3` に置いたままである。

## 次の推奨アクション

- 署名付きエンジンを別の保管場所へ複製するなら、そのあとで `hakua040-components-r3` を消すかどうかを決める。
- `hakua040-q36-engine-sync-20261103` の出所を、作った側の作業ログで確認する。
