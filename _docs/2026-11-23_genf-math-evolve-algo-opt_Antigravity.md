# 2026-11-23 Gen-F 数理科学・進化的最適化・アルゴリズム高速化＆ビルドログ (Antigravity)

## 1. 対象環境・目的
- **実機環境**: Windows 11 x64, 6C/12T Ryzen (AVX2), RAM 31.87 GiB, NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120`, CUDA 13.5.37)
- **目的**: 本 PC の推論エンジン群（`strata-inkling2.exe` および `strata.exe` [Qwen3.6-35B-A3B / Qwen3.8-Flash-Next / 内蔵 Q38-27B・9B]）を数理科学・進化的最適化・アルゴリズム面から高速化し、ビルド・上書きインストール・実機検証を完了する。

## 2. 実装内容
### 2.1 共通 AVX2 CPU MoE カーネル (`engine/src/kernels/cpu/kq_avx2.cpp`) — `strata-inkling2` & `strata` 共通
1. **Zero-Spill 融合 Gate+Up `kq256_gu_t1_q4k`**
   - 従来の 8-YMM `q8l[4]/q8h[4]` 配列（合計 ~20 YMM > 16 ハードウェア YMM によるスタックスピル）を廃止し、`j = 0..3` の各反復内で `gate` と `up` を融合計算する 2-YMM (`q8l, q8h`) 保持構造へ変更（計 15/16 YMM 以内・スタックスピル 0・L1 活性化ロード 1 回）。
2. **4行アンロール代数的 `kq256_down_t1_q5_0` + AVX2 SIMD `ysum16`**
   - ブロックごとの 32 反復スカラー和 `ysum16` を `_mm256_maddubs_epi16(ones_u8, qy)` + `_mm256_madd_epi16` の AVX2 SIMD リダクションへ置換。
   - `r += 4` の 4行アンロール (`acc0..acc3`, `bias0..bias3`) で 4 本の独立 FMA 依存鎖を生成し、活性化ロードを 4 倍再利用。
3. **4行アンロール代数的 `kq256_down_t1_q8_0`**
   - `r += 4` の 4行アンロール (`acc0..acc3`, 9/16 YMM・スピル 0) により、Q8_0 層のデコード計算スループットを向上。

### 2.2 数理科学・進化的最適化 (`engine/include/strata/math/riemann_rh.hpp`, `engine/src/inkling2/inkling2_engine.cu`)
1. **ShinkaEvolve (`scripts/shinka_evolve_rh.py`, `robust-kbench` 検証ゲート付き) による進化的最適化**:
   - 実行結果 (`EXIT 0`): `CacheGenome(s_shallow=1.4826, s_deep=1.3852, von_koch_c=0.1893, impact_alpha=0.6624)` (`weighted_saved=2568.1`, ベースライン比 `+0.10%`)。
   - 進化で得られた `von_koch_c = 0.1893` および HybriMoE 影響度係数 `impact_alpha = 0.6624` を `inkling2_engine.cu` に適用。
2. **情報理論的 Shannon ルーティングエントロピー変調による RH 臨界線適応減衰**:
   - `normalized_shannon_entropy()` と `rh_entropy_adjusted_decay(step, norm_entropy)` を `riemann_rh.hpp` に追加し、Zipf 集中層（低エントロピー）では保持力を高め、レジーム変化層（高エントロピー）では迅速に忘却・追従するよう層別適応減衰を統合。

### 2.3 Qwen3.8 CUDA 13.5 SM120 (`engine/q38/src/ops.cu`) & GGUF 読込修正 (`engine/include/strata/artifact/gguf_reader.hpp`)
- `engine/q38/src/ops.cu`: `norm` カーネルを `float4` ベクトル化ロード/ストア（16-byte 整列かつ `n % 4 == 0` 時）＋ワープ 0 シャッフルリダクション化。
- `engine/include/strata/artifact/gguf_reader.hpp`: upstream 0.2.20 intake 後に未定義となっていた `strata::read_qwen35moe_layer_int()` を追加し、`strata.exe` のビルドエラーを解消。

## 3. ビルド & 上書きインストール証跡
- **ビルドコマンド** (VS 2026 Insiders + CUDA 13.5.37 + Ninja, `-j 5`):
  - `cmake --build H:\Strata\build\engine-cuda135 --target strata-inkling2 -j 5` → **`EXIT 0`**
  - `cmake --build H:\Strata\build\engine-cuda135 --target strata -j 5` → **`EXIT 0`** (`strata 0.1.66`)
- **上書きインストール & SHA-256 一致確認**:
  - `strata-inkling2.exe`: `SHA256=4CCC099638BF27A9743C1FF5DA0607E334616F6BADB372A03E9E2798F4C0DC3D`
    - `0.6.7-windows-x86_64-cuda-cuda13`: `MATCH=True`
    - `strata-engine-0.6.4-windows-x86_64-cuda-cuda13`: `MATCH=True`
  - `strata.exe`: `SHA256=D77668478DA7323266F2C6402D6BA39A47B514CBAF073E142FD9E71B0A65FF3B`
    - `0.6.7-windows-x86_64-cuda-cuda13`: `MATCH=True`
    - `strata-engine-0.6.4-windows-x86_64-cuda-cuda13`: `MATCH=True`

## 4. 実機ベンチマーク検証 (`Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf`, 131K)
条件: `--max-context 131072 --kv-q8 --expert-vram 7.3 --bench --chunk 512 --tokens 1..16 --max-new 32`

| バージョン | VRAM 配置 | Prefill (16 tok) | Decode (31 tok) | CPU ms | ms / miss | トークン一致 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 修正前 (Zero-copy mmap) | `1580/3072` (`free=5280 MiB`) | `1308.8 ms` (`12.22 t/s`) | `1481.2 ms` (`20.93 t/s`) | `941.1 ms` | `0.2326 ms` | 32/32 |
| **Gen-F (今回ビルド)** | `1580/3072` (`free=5280 MiB`) | `1423.6 ms` (`11.24 t/s`) | **`1041.5 ms` (`29.76 t/s`, `+42.2%`)** | **`517.3 ms` (`-45.0%`)** | **`0.1278 ms` (`-45.1%`)** | **32/32 完全一致** |

## 5. 残留リスク・スコープ制限
- `releaseQualified=false`（一般モデル品質・フル 131K 長文生成・GPU 同時実行の包括評価は未実施）。
- `strata.exe` の Q38 / Qwen3.6 実モデルベンチマークは今回未実行（`--version` 起動確認およびビルド/リンク検証のみ完了）。
- 変更ファイルは作業ツリーに保持済み（コミット・プッシュはユーザー指示待ち）。
