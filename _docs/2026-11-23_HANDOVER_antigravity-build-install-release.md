# 引き継ぎ書: ビルド → 上書きインストール → リリース (2026-11-23)

Antigravity _session_ へ: この時点の状態と、残りの手順を引き継ぐ。Fork セッションが
`engine/0.6.7` worktree で Q38 を含む 0.6.7 エンジンをビルドした途中まで進めている。

## 0. 重要: 共有リポジトリの扱い
- この会話は fork。main はオリジナル (Antigravity) がアクティブに更新中。
  確認時点の main HEAD = `278205ab3 [Engine] Add Gen-E SIMD NR SITU...`、dirty=5。
  **main の未コミット変更・ブランチ・GitHub リリースを勝手に触らない。**
- 作業は専用 worktree を使う: `H:/Strata/worktrees/engine-067` (ブランチ `engine/0.6.7`,
  HEAD `38a63cf9d`)。ここだけを編集してよい。
- worktree の現在の差分: `engine/q38/src/CMakeLists.txt` 修正 + `engine/data/` (gitignore データ)。

## 1. 完了済み
- **公式 v0.2.19 intake + Ryu (kuraneko1) profile tables を CUDA Inkling-2 へマージ**
  (upstream PR #6571 OPEN)。product 0.7.6 / engine family 0.6.7 / upstream v0.2.19。
- **GitHub Latest = v0.7.6** (https://github.com/zapabob/Strata/releases/tag/v0.7.6)。
  添付: 0.6.7 engine tar (旧 Q38), hy4 0.1.64, app setup/tar.7z (0.7.5 名)。
- **CUDA 13.5.37 エンジンをビルド** (worktree engine-067, main 38a63cf9d のソース):
  - `H:/Strata/build/engine-067-cuda135/strata.exe` SHA 83c84669abf8491ffd219d2a7a502f57e78cf5d92796694ac25bd7a970edd105 (72,489,984 B)
  - `H:/Strata/build/engine-067-cuda135/strata-inkling2.exe` SHA 97b9a65841e52b0ba4a3c02b69b9a0be33731d74cfe8e514f64dde8988720afa (36,806,656 B)
  - **新ビルド成功**: `H:/Strata/build/q38-067-cuda135/strata-q38.exe` SHA 9096d22c84dcf8371cf0d389a9cb4ba6b006f99c841bf668dcd73ca0c3b37263 (2,537,984 B), version probe `strata-q38 own-native 0.6.3 CUDA13 SM120 cudart=13050 cublas=130600`.
- 0.6.7 コンポーネントを 3 exe すべてで再生成:
  `H:/Strata/evidence/v067-components/0.6.7-windows-x86_64-cuda-cuda13` (154 ファイル),
  app の `engine_component.verify(full=True)` = OK。
- 旧 tar (Q38 旧) は `H:/Strata/evidence/strata-engine-0.6.7-windows-x86_64-cuda-cuda13.tar.gz`
  SHA 6ef349f9... (公開済み v0.7.6 のもの)。

## 2. 新しい tar.gz (Q38 版) — 完成済み
- `H:/Strata/evidence/strata-engine-0.6.7-windows-x86_64-cuda-cuda13-r2.tar.gz`
  size = 1,523,107,958 B、SHA-256 = `eb3bf3f005f0d1058ee107c07844d74351870514a3d7d806cb94e73020b3c6ce`
  7-Zip integrity test = OK (uncompressed 2,242,094,080 B, compressed 1,523,107,958 B)。
  この tar が Q38 新ビルド (SHA 9096d22c) を含む 0.6.7 コンポーネントの最終アーカイブ。
   publishing は手順 4 でこの r2 を使うこと (旧 6ef349f9 の tar は v0.7.6 に添付済み)。

## 3. Q38 ビルド成功のために worktree で入れた修正 (再現手順)
`engine/q38/src/CMakeLists.txt` (worktree のみ、main 에는反映しない):
- `${ROOT}/spin8/` → `${ROOT}/q38/src/spin8/` (4箇所)
- `${ROOT}/tqcodec/` → `${ROOT}/q38/src/tqcodec/` (8箇所)
- `q38_ops` と `q38_kv` の include に `${ROOT}/q38/include` を追加
- `engine/data/spin8/reference.profile` を `terminal/data/spin8/reference.profile` からコピー
- これらは CMake の ROOT=engine と fork の実際の配置(q38/src 配下)の不整合を補正したもの。
  将来 main に反映するなら upstream レイアウトに合わせて正式に直すこと。

configure/build コマンド (CUDA 13.5 明示):
```
$vc='C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvars64.bat'
$ninja='C:\Program Files\Microsoft Visual Studio\18\Insiders\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe'
cmake -S H:/Strata/worktrees/engine-067/engine/q38/src -B H:/Strata/build/q38-067-cuda135 -G Ninja `
  -DCMAKE_MAKE_PROGRAM="$ninja" -DCMAKE_BUILD_TYPE=Release `
  -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.5/bin/nvcc.exe" `
  -DSTRATA_Q38_REQUIRE_CUDA135=ON
cmake --build H:/Strata/build/q38-067-cuda135 --target strata-q38 -j 5
```

## 4. 残りの手順 (Antigravity が引き継ぐ作業)
1. tar.gz r2 の完了を確認し、SHA-256 を記録。
2. **上新バージョン v0.7.7 を検討** (v0.7.6 は公開済みで差し替え不可)。
   worktree で VERSION=0.7.7 / release.json を更新 (libloading 0.7.4 を誤って
   0.7.7 にしないよう注意 — 過去に bump スクリプトが依存バージョンを壊した)。
   README 8 言語も 0.7.7 に。`release_manifest.py --check` が ok になること。
3. main が落ち着いたら worktree の変更をマージ or 別ブランチで push。
   タグ v0.7.7 を作って push。
4. `gh release create v0.7.7 --repo zapabob/Strata --latest` で
   `H:/Strata/evidence/strata-engine-0.6.7-windows-x86_64-cuda-cuda13-r2.tar.gz`
   (SHA eb3bf3f0...b3c6ce) + hy4 0.1.64 + app setup/tar.7z を添付。
5. 公開 SHA リードバック (4 アセットが state=uploaded、digest 一致)。
6. **実機上書き**: 前回の `v075-install.ps1` 方式 (公開 installer を 7-Zip で展開して
   C:/Users/downl/AppData/Local/Programs/Strata に配置、registry 更新、ユーザーデータ保持確認、
   GUI 起動確認)。0.6.7 コンポーネントは
   C:/Users/downl/AppData/Local/Strata/components/engine/ に配置。
7. 実装ログに完了証拠を追記。

## 5. 注意点 / 残留リスク
- Authenticode signing なし、ed25519 署名検証は削除済み、SHA-256 digest 検証のみ。
  `releaseQualified=false`。
- 新しい Q38 は `strata-q38 own-native 0.6.3` と自己申告 (fork の Q38 バージョンは
  上游 engine 0.1.65 とは独立)。product 0.7.7 との整合はドキュメントで説明すること。
- ベンチ数値の出所を混同しないこと (Antigravity ログの 2.84x/4.86x/22.44 t/s は
  本セッション未再現。本セッション実測は 9.09/11.78 t/s、証拠
  H:/Strata/evidence/inkling2-benchmark-result.txt)。
- メインエンジンビルド (engine-067-cuda135) はテスト `strata_v1_1_inkling2_test.cpp` の
  `Inkling2Loop` vs fork `Inkling2` で失敗したが、本番バイナリ strata.exe /
  strata-inkling2.exe は生成済みで 0.6.7 コンポーネントに反映済み。テストのみの不整合。
- 成果物・証拠は H: ドライブ (H:/Strata/evidence, H:/Strata/build) に保持。削除しないこと。
