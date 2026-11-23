# 2026-11-23 RAM 32 GB / VRAM 16 GB 実機最適化・ゼロコピー mmap 実装ログ (Antigravity)

## 1. 対象環境・目的
- **実機環境**: Windows 11 x64, 6C/12T Ryzen (AVX2), **RAM 31.87 GiB**, **NVIDIA GeForce RTX 5060 Ti 16 GB (`sm_120`, CUDA 13.5.37, WDDM)**
- **課題**: Windows 32 GB RAM 実機で `Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf` (17.5 GB, 24 物理層 / 128 experts/層) を 131K コンテキスト (`--max-context 131072 --kv-q8`) で起動すると、Tier-2 の 16 層に対して `L.hblobs` が `16 × ~700 MiB ≈ 11.2 GiB` のプライベートコミット (`malloc` / `cudaHostAlloc`) を確保しようとし、Windows のコミット残量不足（計測時 `FreeCommit_GiB: 9.27`, `FreeRAM_GiB: 16.16`）で `host malloc failed for layer 0` / `layer 16` によりクラッシュしていた。
- **目標**: 32 GB RAM / 16 GB VRAM Windows 実機で 131K コンテキストが安定・高速に動作するようメモリ構造を最適化し、ビルド・上書きインストール・実機検証を完了する。

## 2. 実装内容
### 2.1 `engine/src/inkling2/inkling2_engine.cu`
1. **コミット安全な Windows 動的ピン留め上限 (`GlobalMemoryStatusEx`)**
   - `avail_b = std::min(avail_phys, avail_commit)` と OS/CUDA ドライバ用ヘッドルーム `7.5 GiB` (`7680 MiB`) から `max_pin_bytes = (avail_b > head_b) ? min(avail_b - head_b, 10240 MiB) : 0` を算出。
   - コミット圧迫時に強制下限（旧 6 GiB）で OOM しないよう安全化。
2. **ゼロコピー mmap 直接実行（プライベートコミット 11.2 GiB → 0 B 削減）**
   - `PhysLayer` に `zc_fmts` (`std::vector<strata::kernels::cpu::NativeFmt>`) と `build_zc_fmts()` を追加。
   - `place_experts()` および KV 拡張時の `ensure_hblobs()` で、ピン留め (`cudaHostAlloc`) が上限を超える層（かつ `tail_off == 0` の GGUF 層）については `std::malloc(hb_bytes)` を行わず `L.hblobs = nullptr` とし、既存の read-only GGUF ファイルマッピング (`L.h_gate_up` / `L.h_down`, プライベートコミット消費 0) を `ExpertJobMulti::fmt` (`149-cold` 互換のモジュラオフセット) 経由で CPU AVX2 カーネルから直接参照。
3. **ゼロコピー mmap 対応の非同期リバランス & GPU Prefill ストリーミング**
   - `rebalance()`: `L.hblobs == nullptr` の層向けに小容量再利用ピン留めバッファ `Engine::rebal_stage` を導入（リバランス対象 1〜10 expert 分のみステージング、`~Engine()` で確実解放）。
   - `pp_begin()` / `pp_kick_next()` / `run_moe()`: `L.hblobs == nullptr` の層でも `L.h_gate_up` / `L.h_down` から直接 `pp_stage[b]` へ `cudaMemcpyAsync` でストリーミング転送可能にし、131K Prefill 時の CPU フォールバックと `h_h` サイズ超過エラー (`invalid argument`) を解消。
   - `shrink_layer()`: `!L.hblobs` 時の安全な再アップロード経路を追加。

### 2.2 `terminal/serve/server.py` / `engine/include/strata/inkling2/profile_rules.hpp` / `engine/include/strata/core/expert_cache.hpp`
- `server.py`: `<= 36 GiB` RAM 環境での事前 `ram_fit.squeeze()` 対象に `inkling_kind.is_inkling(cfg)` を追加（`f8cf23502` / `main` 統合済み）。
- `profile_rules.hpp`: 到達不能だった `cc_major == 8 && cc_minor == 9` 内の `cc_major == 12` デッドコードを削除（`main` 統合済み）。
- `expert_cache.hpp`: `slot_capacity` / `scrub_loan_boundary` 宣言を復元（`main` 統合済み）。

## 3. ビルド & 上書きインストール証跡
- **ビルドコマンド** (VS 2026 Insiders + CUDA 13.5.37 + Ninja, `-j 5`):
  ```cmd
  cmd /c "call `"C:\Program Files\Microsoft Visual Studio\18\Insiders\VC\Auxiliary\Build\vcvars64.bat`" && cmake --build H:\Strata\build\engine-cuda135 --target strata-inkling2 -j 5"
  ```
  - 結果: `EXIT 0` (`[3/3] Linking CXX executable strata-inkling2.exe`)
- **上書きインストール先 & SHA-256 一致確認**:
  - ビルド成果物: `H:\Strata\build\engine-cuda135\strata-inkling2.exe`
  - SHA-256: `B92E00314BEF652ABC5B37E653B39BAE0038FD0B53AB23DF56E9A3F15E015898`
  - `C:\Users\downl\AppData\Local\Strata\components\engine\0.6.7-windows-x86_64-cuda-cuda13\strata-inkling2.exe` (`D1_MATCH=True`)
  - `C:\Users\downl\AppData\Local\Strata\components\engine\strata-engine-0.6.4-windows-x86_64-cuda-cuda13\strata-inkling2.exe` (`D2_MATCH=True`)

## 4. 検証結果（実機・単体テスト）
### 4.1 単体テスト
- `py -3 -m pytest terminal/tests/terminal/test_ram_fit.py -q`: **19 passed in 3.33s** (`EXIT 0`)

### 4.2 131K 実機ベンチマーク (`Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf`, `FreeCommit_GiB=9.27`, `FreeRAM_GiB=16.16`)
共通条件: `--max-context 131072 --kv-q8 --bench --chunk 512 --tokens 1..16 --max-new 32`

| 条件 | 配置結果 | Prefill (16 tok) | Decode (31 tok) | Hits / Misses | CPU ms | トークン一致 | 結果 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 修正前 (旧 `hblobs` malloc) | layer 0 / layer 16 で失敗 | — | — | — | — | — | `EXIT=1` (`host malloc failed`) |
| **修正後 (`--expert-vram 7.3`, 131K 推奨構成)** | `1580/3072` (7.58 GiB, `free=5280 MiB`) | `1308.8 ms` (`12.22 t/s`) | **`1481.2 ms` (`20.93 t/s`)** | `10066 / 4046` | `941.1 ms` | **32/32 完全一致** | **`EXIT=0`** |
| 修正後 (自動配置, `--expert-vram` なし) | `2025/3072` (9.81 GiB, `free=3003 MiB`) | `1062.9 ms` (`15.05 t/s`) | `5260.4 ms` (`5.89 t/s`) ※WDDM spill | `11552 / 2560` | `636.0 ms` | **32/32 完全一致** | `EXIT=0` |

- **重要な知見**: 16 GB WDDM GPU では自動配置（9.81 GiB expert + dense + KV + DWM）が Windows 共有メモリへの VRAM スピルを引き起こしデコードが `5.89 t/s` に低下する一方、`--expert-vram 7.3` (`configs/strata-sakura-inkling2-131k.json`) では専用 VRAM 内に完全に収まり (`free=5280 MiB`)、**3.55 倍高速な `20.93 t/s`** で動作する。

## 5. 残留リスク・スコープ制限
- `releaseQualified=false`（一般モデル品質・フル 131K 長文生成・GPU 同時実行の包括検証は未実施）。
- 本ログの数値は本実機（RTX 5060 Ti 16 GB + 32 GB RAM Windows WDDM）かつ 16 pp / 31 tg ベンチマークでの実測値であり、他環境・長文生成での性能を保証しない。
- `H:\Strata\build` / `H:\Strata\evidence` の成果物はすべて保持済み。
