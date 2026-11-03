# 2026-11-03 upstream-sync CUDA sm_120 build

## 概要

マージコミット `590c0b5bd31fb528c2d12910544106d15e09a5f5` のソースから、Windows CUDA sm_120 の `strata.exe` と `strata-q36.exe` を Release でリンクした。configure は exit 0。再開したビルドは exit 0。`cuda_spill_guard` は FAIL。予算ファイルは変更していない。コード変更はない。

## 背景・要求

HEAD は作業開始時もログ作成時も `590c0b5b`（`Merge upstream/main ffa80d73 and keep the Qwen3.6 launch contract.`）だった。`git merge-base --is-ancestor 590c0b5bd31fb528c2d12910544106d15e09a5f5 HEAD` の終了コードは 0。reset はしていない。

## 前提・判断

- ggml pin は `third_party/ggml/VERSION.txt` も `CMakeLists.txt` の `GIT_TAG` も `3cf03257f219afbe7334045ff7c6a06ac68c627d`。`H:/Strata/deps/ggml-3cf03257` の HEAD も同じだったので、そのディレクトリを `STRATA_GGML_DIR` に渡した。
- `STRATA_ENABLE_NATIVE_CACHE` の option は `STRATA_ENABLE_SPIN8` の内側にあり、既定は OFF のまま。upstream が必須にはしていなかったので OFF のまま configure した。
- マシンの `CUDA_PATH` は `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.2` だった。configure プロセスでは `CUDA_PATH` と `-T cuda=` と `CUDAToolkit_ROOT` と `CMAKE_CUDA_COMPILER` を v13.3 にした。生成後の `CMakeCache.txt` に `v13.2` は無かった。
- ビルドディレクトリは `H:\Strata\releases\hakua040-native-sync-20261103`。`H:\Strata\releases\hakua040-nsis-native-20261102` は上書きしていない。

## 変更対象ファイル

- このログのみ。C++ / CUDA のソース、spill の ALLOWED、Qwen3.6 の既定（legacy expert store、context 65536、FP32 KV、MTP 2、prefill auto）は変えていない。

## 実行コマンド

configure（成功した回）:

```text
cmake -S C:\Users\downl\Documents\ChatGPT\Strata -B H:\Strata\releases\hakua040-native-sync-20261103 -G "Visual Studio 17 2022" -A x64 -T "cuda=C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3" -DCUDAToolkit_ROOT="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3" -DCMAKE_CUDA_COMPILER="C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/nvcc.exe" -DCMAKE_CUDA_ARCHITECTURES=120 -DSTRATA_NATIVE_EXPERTS=ON -DSTRATA_PORTABLE=ON -DSTRATA_ENABLE_CUDA=ON -DSTRATA_ENABLE_SPIN8=ON -DSTRATA_ENABLE_NATIVE_CACHE=OFF -DSTRATA_GGML_DIR=H:/Strata/deps/ggml-3cf03257 -DSTRATA_BUILD_TESTS=ON
```

ビルド:

```text
cmake --build H:\Strata\releases\hakua040-native-sync-20261103 --config Release --target strata --target strata-q36 --parallel
```

spill guard:

```text
ctest --test-dir H:\Strata\releases\hakua040-native-sync-20261103 -C Release -R "^cuda_spill_guard$" --output-on-failure
```

## テスト・検証結果

| 項目 | 観測 |
| --- | --- |
| configure | `CONFIG_EXIT:0`。ログ: `The CUDA compiler identification is NVIDIA 13.3.73`、`Found CUDAToolkit ... version "13.3.73"`、`Strata: CUDA enabled, arch 120`、`ggml commit: 3cf0325` |
| cache | `STRATA_ENABLE_CUDA=ON`、`STRATA_ENABLE_SPIN8=ON`、`STRATA_ENABLE_NATIVE_CACHE=OFF`、`STRATA_NATIVE_EXPERTS=ON`、`STRATA_PORTABLE=ON`、`STRATA_BUILD_TESTS=ON`、`STRATA_GGML_DIR=H:/Strata/deps/ggml-3cf03257`、`CMAKE_CUDA_ARCHITECTURES=120`、`CUDAToolkit_ROOT=C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3`、`STRATA_CUDA_SPILL_BASELINE` は空 |
| 1回目の build | 15:26 開始。`strata_kernels.lib` まで進んだログで止まり、`BUILD_EXIT` 行は無い。エラー行も無い。プロセスは残っていなかった。`strata.exe` と `strata-q36.exe` は無かった |
| 再開した build | `RESUME_START:2026/11/03 20:49:37.19`、`BUILD_EXIT:0`。ラッパーの `exit_code: 0`、`elapsed_ms: 537515`。エラー行は無い |
| `strata.exe` | `H:\Strata\releases\hakua040-native-sync-20261103\Release\strata.exe`、114184704 bytes、SHA256 `DD53DF07789E0FEFCB87E33ACAB54F5BFE1FAF312EF6BAD515924736B715C5B5`、mtime 2026-11-03 20:58:21 |
| `strata-q36.exe` | `H:\Strata\releases\hakua040-native-sync-20261103\Release\strata-q36.exe`、83173888 bytes、SHA256 `0A39DFD54ED13F64A8DEAFB9971F95B24D406883F5BDB24317891CDE2C27DEDD`、mtime 2026-11-03 20:58:29 |
| `cuda_spill_guard` | FAIL。ctest 終了コード 8。Test #214、7.97 sec。`419 use stack / local memory, 4 not allowed` |

spill の 4 件（ログのまま）:

- `expdec_down_kernel<(int)20, (int)4>` sm_120 STACK 152 LOCAL 0（allowance STACK 136 LOCAL 0）`iq_kernels.obj`
- `gemm4_rows_kernel<(int)8, (int)1, (int)8>` sm_120 STACK 24 LOCAL 0（ALLOWED に無い）`dflash2.obj`
- `gemm4_rows_kernel<(int)8, (int)1, (int)4>` sm_120 STACK 16 LOCAL 0（ALLOWED に無い）`dflash2.obj`
- `block_topk_reg_kernel<(int)33>` sm_120 STACK 96 LOCAL 0（allowance STACK 88 LOCAL 0）`qsa_select.obj`

`strata_core.lib`、`strata_engine.lib`、`strata_prefill.lib`、`strata_qwen35.lib`、`strata_mmq.lib`、`strata_mmq_w4a4.lib`、`strata_kq.dll` の行は `0 not allowed` だった。baseline ファイルは渡していない。ALLOWED は編集していない。

最初の configure 起動は、PowerShell が `There is not enough space on the disk` で cmake を 1 秒で落とした。その時点の `Get-PSDrive` は H: の FreeGB が 0 だった。引数を配列で渡した再試行は、CUDA パスの空白でコマンドラインが割れ、exit 1 だった。上の cmd 経由の configure が exit 0。

## 実行していないこと

- 22GB の Qwen モデルは起動していない。
- GitHub release は作っていない。パッケージも作っていない。
- インストール済みアプリは上書きしていない。
- force-push はしていない。
- spill 予算は緩めていない。
- 速度向上もコード署名も主張しない。
- ctest 全体は回していない。`cuda_spill_baseline_unit` も回していない。

## 残留リスク

リンクは通った。`cuda_spill_guard` は FAIL のまま。Qwen3.6 の起動契約が満たせたとは言えない。1回目の build は終了コードが残っていない。
