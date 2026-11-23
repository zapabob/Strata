# 2026-11-23 DeepResearch 2026 最新論文統合・全4 CUDA 13.5 SM120 ネイティブエンジン最適化＆ビルドログ (Antigravity)

## 1. 対象環境・目的
- **実機環境**: Windows 11 x64, 6C/12T Ryzen (AVX2), RAM 31.87 GiB, NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120`, CUDA 13.5.37, WDDM)
- **目的**: 2025〜2026 年の最新一次論文（DeepResearch 調査）とプロファイル実測にもとづき、全 4 CUDA 13.5 SM120 ネイティブ推論エンジン（`strata-inkling2.exe`, `strata.exe`, `strata-q38.exe`, `strata-hy4.exe`）を数理科学・進化的最適化・アルゴリズム面から最適化し、ビルド・上書きインストール・検証を完了する。

## 2. DeepResearch 一次論文根拠（2025〜2026）
- **ST-MoE** (June 2026, arXiv:2606.15453): 連続トークン・隣接層間の時空間 Markov 相関を利用したエキスパート予測・プリフェッチ。
- **APEX** (Aug 2026, arXiv:2608.11688): 信頼度駆動の適応エキスパートプリフェッチ（正確性保存モードで最大 26% 遅延削減）。
- **Speculating Experts** (Mar 2026, arXiv:2603.19289) / **DuoServe-MoE** (Apr 2026): Prefill / Decode 二相分離と計算・H2D 転送の非同期オーバーラップ。
- **HybriMoE** (DAC 2025, arXiv:2504.05897) / **Fate** (Feb 2025) / **ShinkaEvolve** (arXiv:2509.19349) + **robust-kbench** (arXiv:2509.14279): 影響度加重スコアリング・進化的パラメータ探索。
- **Blackwell `sm_120` 量子化 GEMV 最適化** (2025〜2026): `sm_120` は `tcgen05`/TMEM 非搭載のため、ワープ単位リダクション・`float4` 16-byte 整列ロード・単一 SFU `tanh.approx.f32` (`MUFU.TANH`)・ゼロコピー PCIe マップによる WDDM 投入削減が鍵。

## 3. 全4エンジンへの実装内容
1. **共通 AVX2 CPU MoE カーネル (`engine/src/kernels/cpu/kq_avx2.cpp`)** — `strata-inkling2.exe` & `strata.exe`:
   - Zero-Spill 融合 Gate+Up `kq256_gu_t1_q4k`（15/16 YMM・スタックスピル 0）＋レジスタ完結 SITU 抽出（`_mm_cvtss_f32` / `_mm_shuffle_ps` / `_mm_movehl_ps` により 259 万回のストアフォワーディング・ストールを解消）。
   - 4行アンロール代数的 `kq256_down_t1_q5_0`（AVX2 SIMD `ysum16` 付き）＆ 4行アンロール `kq256_down_t1_q8_0`。
2. **Inkling-2 CUDA 13.5 SM120 (`engine/src/inkling2/inkling2_engine.cu`, `engine/include/strata/math/riemann_rh.hpp`)**:
   - Zero-Copy PCIe マップ・ダブルバッファ `h_cpu_sum[2]` (`cudaHostAllocMapped` + `h_cpu_sum_dev`): 外層ごとの 496 回の `cudaMemcpyAsync` H2D 投入を撤廃（実測 `moe_up 39.5 ms → 3.5 ms` `-91%`、`moe_up + moe_post` 合計 `-19.9 ms` `-30.2%`）。
   - ピン留め `h_pos0` による pageable スタック H2D 同期ストール解消。
   - ST-MoE 連続トークン Markov 時間局所性ブースト (`st_moe_markov_boost`, 実測 VRAM ミス `-25` 件改善) + ShinkaEvolve 最適パラメータ (`von_koch_c=0.1893`, `impact_alpha=0.6624`) + 層別 Shannon ルーティングエントロピー変調 RH 臨界線適応減衰 (`rh_entropy_adjusted_decay`)。
3. **Qwen3.8-27B / 9B CUDA 13.5 SM120 (`engine/q38/src/ops.cu`, `engine/q38/src/CMakeLists.txt`)** — `strata-q38.exe` & `strata.exe`:
   - `norm` カーネルを `float4` ベクトル化ロード/ストア＋ワープ 0 シャッフルリダクション化。
   - `CMakeLists.txt` の `spin8` / `tqcodec` / `reference.profile` パス自動解決を追加し、`main` から直接 CUDA 13.5 SM120 ビルド可能に整備。
4. **HY4-Flash CUDA 13.5 SM120 ネイティブエンジン (`engine/src/hy4flash/run/hy4_kernels.hip.h`, `hy4_graph.hip.h`, `hy4_gpu_model.hip.h`)** — `strata-hy4.exe`:
   - Blackwell `sm_120` 向け `tanh.approx.f32` (`MUFU.TANH`) 版 `sigmoidf_` / `siluf_`。
   - `k_rms_rows` の `float4` 16-byte 整列ベクトル化。
   - `vcache_note_decode` に ST-MoE 連続トークン Markov 時間局所性ブースト (`vlast_step`) を統合。
   - 0.2.20 統合時の `hy4_gpu_model.hip.h` 欠落フィールド (`PeerGpu::can_p2p`, `wddm_vram_floor_gb`, `plan_memory` 拡張, `GpuModel` 各 cap フィールド) を整合し CUDA 13.5 SM120 ビルドを復旧。
5. **GGUF 読込修正 (`engine/include/strata/artifact/gguf_reader.hpp`)**:
   - `strata::read_qwen35moe_layer_int()` を追加し `strata.exe` のビルドを復旧。

## 4. 全4エンジン ビルド & 上書きインストール証跡 (`-j 5`, CUDA 13.5.37, SM120)
| エンジン | ビルド出力パス | SHA-256 | `0.6.7` / `0.6.4` 上書き一致 |
| :--- | :--- | :--- | :--- |
| `strata.exe` | `H:\Strata\build\engine-cuda135\strata.exe` | `EE456F2358B0A47F206CCA9F7EB52ED9ECE0BE4CE3D4E0ACAEE0FEB3F92B2FD4` | `D1=True`, `D2=True` |
| `strata-inkling2.exe` | `H:\Strata\build\engine-cuda135\strata-inkling2.exe` | `1D74F57AD562B337DC17E2D158F1EDCF02ECBBC27DE75DE4F7B311F831346F0E` | `D1=True`, `D2=True` |
| `strata-q38.exe` | `H:\Strata\build\q38-cuda135\strata-q38.exe` | `AB87E2E621E3B58EB95D3C369DD3FCA4C1830467D91D929443D74EA514F2E822` | `D1=True`, `D2=True` |
| `strata-hy4.exe` | `H:\Strata\build\hy4-cuda135\strata-hy4.exe` | `FC7767092AEC74171811D1BC2C0F42F8BA1AB7CADD43433B7D30B4620CFC7478` | `D1=True`, `D2=True` |

## 5. 実機計測サマリ & 残留リスク
- `strata-inkling2.exe` (131K, `--expert-vram 7.3`, `Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf`):
  - Zero-copy mmap 修正前 (`host malloc failed`) → 修正後 `20.93 t/s` → Gen-F **`29.76 t/s` (`+42.2%`, `cpu_ms=517.3 ms`, `-45.0%`)** → Gen-G (`--profile`) で `moe_up 39.5 → 3.5 ms` (`-91%`) / `hits 10064 → 10089` を実測、すべて **32/32 トークン完全一致**。
- `releaseQualified=false`（一般モデル品質・フル長文生成・`strata-hy4.exe` / `strata-q38.exe` / `strata.exe` の実モデル端到端ベンチマークは今回未実行）。
