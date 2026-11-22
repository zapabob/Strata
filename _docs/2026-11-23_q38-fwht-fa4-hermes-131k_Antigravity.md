# 2026-11-23 Qwen3.8-27B/9B 数理・ハードウェア最適化（Kronecker FWHT / FA4 / PQ2_0）+ Hermes Agent Windows 98K–131K 対応ログ (Antigravity)

## 1. 概要
- `engine/q38/src/ops.cu` および `engine/q38/src/kv.cu` に数理科学的・ハードウェア最適化を実装し、`strata.exe` を CUDA 13.5 (`sm_120`, `-j 5`) でビルド＆上書きインストール（SHA-256 完全一致確認済）。
- Windows 上の Hermes Agent から **98K–131K コンテキスト**（`Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf`）を 1 コマンドで起動・利用できるよう設定ファイル・起動スクリプト・`~/.hermes/config.yaml` を整備。

## 2. 変更ファイル
- `engine/q38/src/ops.cu`:
  - **Kronecker 分解 FWHT ($H_{1024} = H_{32} \otimes H_{32}$)**（`had`, `had_batch`）: ワープシャッフル `__shfl_xor_sync`＋バンクコンフリクトゼロ転置 `b[32][33]` により、21 回の `__syncthreads()` バリアを **2 回（10.5x 削減）**・20 回の共有メモリ往復を **2 回（10x 削減）** へ圧縮。
  - **`mv_pq2_0` 2行同時ワープ GEMV**: `float4` 活性化 `__ldg` を 2 行で共有し活性化メモリ帯域を半減。
  - **Blackwell `sm_120` `MUFU.TANH` `q38_sigmf`**: `elt` (SiLU)・`gb` (GDN ゲート)・`attend` ゲートへ適用。
  - **`attend` 共有メモリ確率キャッシュ**: `prob[4096]` + Base-2 `exp2f` により 256 スレッド間の重複 `expf` を 256x 削減。
- `engine/q38/src/kv.cu`:
  - `attend_batch_gqa_tiled` および `spin8_attend_decode_split_kernel` に **FlashAttention-4 (2026) 条件付き Softmax 再スケーリング＋ Base-2 `exp2f` (`MUFU.EX2`)** を導入。
- `configs/strata-sakura-inkling2-131k.json`（新規）: `--max-context 131072 --kv-q8 --expert-vram 7.3` プリセット。
- `configs/strata-sakura-inkling2-98k.json`: `--expert-vram 7.8` を明示（WDDM スワップ防止）。
- `scripts/start-sakura-inkling2-hermes.ps1`: `-Context 131k | 98k | 65k` 対応（デフォルト `131k`）。
- `C:\Users\downl\.hermes\config.yaml`（ワークスペース外）: `providers.inkling2` を 98K–131K（`sakura-inkling-2-mini-131k`: `131072`, `sakura-inkling-2-mini`: `98304`）へ拡張。

## 3. ビルド・上書きインストール・実機計測結果
- ビルド: `cmake --build H:/Strata/build/engine-cuda135 --target strata -j 5` — **EXIT 0**
- 上書きインストール先: `%LOCALAPPDATA%\Strata\components\engine\strata-engine-0.6.4-windows-x86_64-cuda-cuda13\strata.exe`
- SHA-256（SRC/DST 完全一致）: `783A1677263F26A83490760993787C5BC9FD71A4CAA553C59CDC04E02B4FD9A3`
- 実機計測（RTX 5060 Ti 16 GB / CUDA 13.5 / `SM120`, `qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf`, `--ctx-size 4096 --tokens 1..16 --n 32`）:
  - Prefill (16 tok): **`339.397 ms`** (**`47.14 t/s`**)
  - Decode (31 steps): **`1063.979 ms`** (**`29.14 tok/s`**)
  - E2E: **`1424.818 ms`**（EXIT 0、非有限エラー 0）

## 4. 残余リスク・推奨アクション
- Windows で Hermes Agent を 98K–131K で使う際は、まず PowerShell で `$env:STRATA_API_KEY="local-key"` を設定し、`.\scripts\start-sakura-inkling2-hermes.ps1 -Context 131k`（または `-Context 98k`）を起動した状態で Hermes Agent の `inkling2` プロバイダを選択する。
- `releaseQualified=false` は継続。
