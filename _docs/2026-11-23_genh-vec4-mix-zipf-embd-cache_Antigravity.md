# 2026-11-23 Gen-H `float4` Depth-Mix & Zipf 語彙キャッシュ・Zero-Copy 埋め込み最適化ログ (Antigravity)

## 1. 実装内容
1. **全 48 仮想層 `k_stack_rms_norm` & `k_mix` の `float4` ベクトル化 + `exp2f` (`MUFU.EX2`)** (`engine/src/inkling2/inkling2_kernels.cuh`)
   - スカラーロード/ストアだった `k_stack_rms_norm` および `k_mix` の内積・加重和を 16-byte `float4` ベクトル化（`N % 4 == 0` 時）し、Blackwell `sm_120` でのグローバルメモリトランザクションを 1/4 に削減。
   - `k_mix` の深さ softmax に単一 SFU `exp2f((w[d] - m) * log2(e))` を適用。
2. **Zipf ホット語彙キャッシュ (1024 スロット / 約 10 MiB) + Zero-Copy PCIe マップ `h_tok_buf_dev`** (`engine/src/inkling2/inkling2_engine.cu`)
   - Knuth 乗算ハッシュによるダイレクトマップ語彙キャッシュ (`tok_cache_id` / `tok_cache_vec`) を導入し、頻出トークンの mmap ページフォルトと再逆量子化を回避。
   - `h_tok_buf` を `cudaHostAllocMapped` 化し、`T == 1` 時は `cudaMemcpyAsync` なしで `h_tok_buf_dev` を `k_rms_norm` へ直接供給。
3. **進化的最適化ハーネス 6 次元化** (`scripts/shinka_evolve_rh.py`)
   - `CacheGenome` を ST-MoE `markov_dt1` および Shannon `entropy_gain` を含む 6 次元ゲノムへ拡張。

## 2. ビルド & 上書きインストール証跡 (`-j 5`, CUDA 13.5.37, SM120)
- `strata-inkling2.exe`: `EXIT 0` / SHA-256 `BC15A68B8E46F793D0B451DBD7FC1F5771A3411E43AF02F6537E0D3DCE4C2DD3`（`0.6.7` / `0.6.4` 両コンポーネント上書き一致確認済み `D1=True D2=True`）
- `strata.exe`: `EXIT 0` / SHA-256 `50C2FDD888D764FDBED801FC58720315B1466EB93AD267A0BA6BEFC12CF5754F`（`D1=True D2=True`）

## 3. 検証結果 & 残留リスク
- `strata-inkling2.exe --profile` (131K, `--expert-vram 7.3`, 並列ファイルコピー負荷下): `hits=10089`, `misses=4023`, `moe_up=4.6 ms`（旧 `39.5 ms` 比 `-88%`）, `moe_wait=0.5 ms`, **32/32 トークン完全一致** (`EXIT=0`)。
- `releaseQualified=false`。
