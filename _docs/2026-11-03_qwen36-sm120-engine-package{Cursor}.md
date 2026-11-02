# sm_120 エンジンの再リンクとパッケージ

- **日時**: 2026-11-03 00:07 JST（robocopy の開始表示）
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。起動時間とトークン速度は未計測。

## 概要

既存の Visual Studio 2022 / CUDA 13.3 / sm_120 ビルドで `strata.exe` と `strata-q36.exe` を Release リンクした。`strata.exe` の SHA-256 をホストの mapped-pack allowlist に1件だけ入れ、CUDA 13.3 の cublas と一緒にエンジンパッケージへ載せた。

## 背景・要求

`q36_engine.cu` と `expert_store.cpp` はソースに入っていたが、インストールされるバイナリには無かった。計画の配布は、このバイナリをパッケージにしてからインストーラとリリースへ進む。

## 前提・判断

- ビルドディレクトリは `H:\Strata\releases\hakua040-nsis-native-20261102`。ソースは今の checkout。`CMAKE_CUDA_ARCHITECTURES=120`、`STRATA_NATIVE_EXPERTS=ON`。
- `tools/build_hakua_engine.mjs` は `cuda_spill_guard` が無い状態で止まった。テストを有効にしたあとの guard は「reviewed baseline の compiler / ggml 同一性に合わない」で失敗した。新しい baseline は測って見直していないので、`native-build.json` に `cudaSpillBaseline` は書いていない。前回の公開パッケージもこの欄は空だった。
- cublas は `CUDA_PATH` の 13.2 ではなく、コンパイラと同じ CUDA 13.3 の DLL。`cublas64_13.dll` は `8c6bac24474af29627ec96500025a5d410a1b7e8ffa00e1fe13b1781fc6b3ddc`、`cublasLt64_13.dll` は `e323abd89e0f03c1db91a09d7aeb1928de08e1f86192cc713b335fefe3e368a9`。前回パッケージと同じ中身。
- 画像リーダーは同梱していない。テキストのみ。
- 署名は付けていない。

## 変更対象ファイル

- `apps/host/server/q36-run-contract.mjs`
- `apps/host/tests/q36-run-contract.test.mjs`
- ビルド成果物: `H:\Strata\releases\hakua040-nsis-native-20261102\Release\strata.exe`
- パッケージ: `H:\Strata\releases\hakua040-q36-engine-20261103\0.4.0-windows-x86_64-cuda-cuda13\`
- ステージ: `apps/desktop/src-tauri/resources/engine-bundle/0.4.0-windows-x86_64-cuda-cuda13\`

## 実行コマンド

```powershell
cmake --build H:\Strata\releases\hakua040-nsis-native-20261102 --config Release --target strata --target strata-q36 --parallel
node H:\Strata\tmp\record-native-build.mjs
py -3 packaging/package_engine.py --src H:\Strata\releases\hakua040-nsis-native-20261102\Release --backend cuda --version 0.4.0 --platform windows-x86_64 --out H:\Strata\releases\hakua040-q36-engine-20261103 --arch sm_120 --min-driver nvidia=580.65 --variant cuda13 --include native-build.json --include strata-q36.exe --search "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.3\bin\x64"
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| `cmake --build` strata / strata-q36 | exit 0。約 288 秒 |
| `strata.exe --version` | `strata 0.4.0` |
| `strata.exe` SHA-256 | `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046` |
| パッケージ | 686.2 MiB、7 files、manifest SHA-256 `3bb3beea49604593805ad2e60d7cc0421acfb39cddd226cf128bd604e4e9dc33` |
| `cuda_spill_guard` | 失敗。baseline の同一性が合わない。spill の再計測はしていない |
| host contract tests | 11 pass / 0 fail |
| 実モデルの起動と速度 | 未計測 |

## 残留リスク

- mapped-pack はこの `strata.exe` にだけ許可される。次にリンクし直すと allowlist は古くなる。
- spill guard は合格していない。新しいデバイスカーネルの STACK/LOCAL は見直していない。今回の差分は host 側のパックと起動ログが中心。
- NSIS、上書きインストール、GitHub リリース、README はまだ。

## 次の推奨アクション

1. 公開 UI の `STRATA_PUBLIC_PACKAGE=1` で host をビルドし、`verify-release` を通してから NSIS。
2. 通ったインストーラだけを `/S /UPDATE` し、新しいタグでリリースする。既存 `v0.4.0-preview.20261101.1` の資産は別物として残す。
3. README には、このパッケージのファイルと「速度は未計測」「署名なし」「画像リーダーなし」を書く。
