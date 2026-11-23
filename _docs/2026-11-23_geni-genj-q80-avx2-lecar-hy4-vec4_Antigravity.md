# 2026-11-23 Gen-I / Gen-J AVX2 `q8_0_quant_avx2`・LeCaR 後悔最小化キャッシュ・HY4 `float4` iHC 実装ログ (Antigravity)

## 1. DeepResearch 論文根拠（2025〜2026）
- **Sakana AI ShinkaEvolve** (Sept 2025, Lange et al.) & **robust-kbench** (2025): サンプル効率的な進化的プログラム探索と、リワードハッキングを防ぐ厳格な不変条件検証ゲート。
- **LeCaR** (Online Multiplicative-Weights Regret Minimization for Cache Replacement) & 2025–2026 MoE Expert Caching 研究: ゴースト退去履歴を用いた $O(1)$ 乗法重み更新により、LFU（頻度）と LRU（直近性）の混合比を $O(\sqrt{T \ln 2})$ 後悔上界で動的に適応。
- **T-MAC** (EuroSys) / AVX2 低ビット GEMV 研究: 量子化・逆量子化のスカラボトルネックを SIMD パック命令で排除。

## 2. 実装内容
1. **AVX2 + F16C 量子化カーネル `q8_0_quant_avx2`** (`engine/include/strata/kernels/cpu/kq_avx2.hpp`, `engine/src/kernels/cpu/kq_avx2.cpp`, `engine/src/kernels/cpu/native_expert.cpp`) — `strata-inkling2.exe` & `strata.exe` 共通:
   - `Q8_0` 活性化量子化（`Q5_0`/`Q8_0` down-proj 用）を 4 YMM ロード + `_mm256_packs_epi32/16` + `_mm256_permute4x64_epi64(..., 0xD8)` + F16C `_mm_cvtps_ph` の AVX2 実装へ置換。
2. **LeCaR オンライン乗法重み後悔最小化コントローラ (`strata::math::LeCaRController`)** (`engine/include/strata/math/riemann_rh.hpp`, `engine/src/inkling2/inkling2_engine.cu`):
   - 16 エントリのゴースト退去リングで LFU/LRU 退去直後のミスを検知し、`w_lfu` を `[0.15, 0.90]` の範囲で乗法重み更新 (`blend_score` で頻度と直近性を混合)。
3. **HY4-Flash `k_hc_reduce_norm` & `k_hc_post` の `float4` ベクトル化** (`engine/src/hy4flash/run/hy4_kernels.hip.h`):
   - `HID = 3072` (`PER4 = 3` `float4`s/thread) に対し 16-byte 整列 `float4` ロード/ストア化（グローバルメモリトランザクション 1/4）。

## 3. ビルド & 上書きインストール証跡 (`-j 5`, CUDA 13.5.37, SM120)
| エンジン | SHA-256 | `0.6.7` / `0.6.4` 上書き一致 |
| :--- | :--- | :--- |
| `strata-inkling2.exe` (Gen-J) | `17759A44AF5F2CB739A54297F7E82182F8EA04B8F7873FA4C7910A15B7334441` | `D1=True`, `D2=True` |
| `strata.exe` (Gen-J) | `6AC28C846E433F5D9068C8E3C7991DD9E87107C58BB3987C5074977D23B82F42` | `D1=True`, `D2=True` |
| `strata-hy4.exe` (Gen-I) | `CD2F36E5F6945BA808F4F04D1ECE7283054DD997D7E1D917CE1B934DAAED3573` | `D1=True`, `D2=True` |

## 4. 検証結果 & 公式 Issue 連携
- **131K 実機ベンチマーク (`task-903`, `Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf`, `--expert-vram 7.3`)**:
  - `pp 16 tok in 1360.0 ms (11.76 t/s) | tg 31 tok in 1339.5 ms (23.14 t/s) | hits=10088 misses=4024 cpu_ms=787.8`（ホスト負荷下 `placed in 113.99 s`）、**32/32 トークン完全一致** (`EXIT=0`)。
- **ShinkaEvolve 6D ハーネス (`scripts/shinka_evolve_rh.py`)**: `EXIT 0`。
- **公式リポジトリ (`Niko1221/Strata`) スコープ合意 Issue 作成済み**:
  - Inkling-2: https://github.com/Niko1221/Strata/issues/6748
  - HY4-Flash: https://github.com/Niko1221/Strata/issues/6749
- **残留リスク**: `releaseQualified=false`。`strata-hy4.exe` の実モデル端到端ベンチマークは未実行。
