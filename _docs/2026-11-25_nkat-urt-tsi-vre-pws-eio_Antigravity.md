# 2026-11-25 — NKAT–URT Scientific Intelligence Engine (TSI Phase 1–2, VRE Phase 3, PWS Phase 3, EIO Phase 3 Revised) — Antigravity

- **Date:** 2026-11-25
- **AI / Engineer:** Antigravity
- **Worktree:** `H:/Strata/worktrees/tsi-verified-evaluation`
- **Branch:** `research/tsi-verified-evaluation`
- **Baseline Commit:** `21473cc9b2fb33c27be1ffbd0bdc87c0e12fec02` (Hakua / Strata `0.8.1`, native engine `0.7.0`, upstream `0.2.21`)
- **Evidence Storage:** `H:/Strata/evidence/nkat-urt-20261125/`
- **Release Qualification:** `releaseQualified=false`
- **Default Inference Impact:** `auto_adopted_into_default_inference=false` (strictly opt-in under `tools/` and `docs/`; zero modifications to `engine/`, `app/`, `terminal/`, `serve/`, or `scripts/shinka_evolve_rh.py`)

---

## 1. Hardware & Safety Environment Verified

- **OS:** Windows 11
- **CPU:** AMD Ryzen 5 4500 (6C / 12T, AVX2)
- **GPU:** NVIDIA GeForce RTX 5060 Ti 16 GB (Blackwell SM120, Driver `621.24`, CUDA `13.5`, PCIe Gen 3 x8 link)
- **Memory:** 32 GiB RAM + 32 GiB pagefile
- **Storage (Physical Models Verified):**
  - `C:`: Crucial P3 1TB NVMe (`CT1000P3SSD8`)
  - `H:`: 1TB SATA SSD (`S5-1TB`)
- **Safety Floors Maintained:** Available RAM $\ge 3\text{ GiB}$, Commit $\ge 4\text{ GiB}$, VRAM reserve $\ge 768\text{ MiB}$ (`1536 MiB` for Inkling-2), `C:` $\ge 5\text{ GiB}$, `H:` $\ge 10\text{ GiB}$, build parallelism `5`.

---

## 2. Implemented Opt-In Modules & Documentation

All 45 opt-in Python files obey strict typing, UTF-8 encoding, `logging` + `tqdm`, and **zero** `print()` / `eval()` / `exec()` calls (verified via AST audit).

### A. Documentation (King's English)
- `docs/NKAT_URT_TSI.md`
- `docs/TSI_BENCHMARK_PROTOCOL.md`
- `docs/TSI_MATHEMATICAL_FOUNDATIONS.md`
- `docs/NKAT_URT_PWS.md`
- `docs/SSD_STREAMING_BENCHMARK.md`
- `docs/EVOLUTIONARY_INFERENCE.md`
- `docs/CUDA_EVOLUTION_PROTOCOL.md`

### B. TSI Phase 1–2 & VRE Phase 3 (`tools/tsi/`, `tools/tsi_eval.py`)
- `tools/tsi/math_foundations.py` — Non-commutative operator commutator, controllability Gramian vs rollout energy, Hankel singular values, Fisher information vs KL range bound, $\mathrm{SO}(8)$ orthogonality.
- `tools/tsi/survival.py` — Stopping-time $\tau_q$, Kaplan–Meier / Nelson–Aalen empirical survival curves, Clopper–Pearson exact binomial CIs.
- `tools/tsi/discovery_rate.py` — Asymptotic discovery rate $\lambda = -\log(1-p)/c$, critical threshold $p_{\mathrm{crit}}$, finite-budget model comparison with explicit independence caveat.
- `tools/tsi/variational.py` — Theorem 1 exact binary KL information limit $d_{\mathrm{bin}}(p_1 \| p_0)$ and tilted Gibbs distribution $Q_\lambda$.
- `tools/tsi/doob.py` — Theorem 3 / Section 8 Doob $h$-transform & Feynman–Kac exact equivalence on finite search trees.
- `tools/tsi/bellman.py` & `tools/tsi/bellman_residual.py` — Finite-horizon Bellman allocation and Theorem 5 Bellman residual oscillation lower bound ($L$, explicitly marking `uniform_bound_certified=false` when uncertified).
- `tools/tsi/information.py` — Empirical top-$k$ KL vs full-vocabulary KL separation (never equating top-$k$ KL with sequence KL).
- `tools/tsi/certificates.py` — URT lower-confidence certificates and non-regression gates.
- `tools/tsi/proof_graph.py`, `tools/tsi/research_state.py`, `tools/tsi/memory.py`, `tools/tsi/scaling.py`, `tools/tsi/phase_diagram.py`.
- `tools/tsi/tasks.py`, `tools/tsi/verifier.py`, `tools/tsi/scheduler.py`, `tools/tsi/client.py`, `tools/tsi/metrics.py`, `tools/tsi/runner.py`, `tools/tsi/report.py`, `tools/tsi_eval.py` — Deterministic `core-v1` / `dev` / `holdout` suite, independent programmatic verifier, `standard` / `adaptive` / `vre` execution modes, paired comparison & Markdown reporting, strictly separating `known_benchmark_problem` from `novel_discovery_candidate`.

### C. Predictive Weight Streaming — PWS (`tools/pws/`, `tools/pws_bench.py`)
- `tools/pws/trace.py`, `tools/pws/bandwidth_model.py` (including Windows `FILE_FLAG_NO_BUFFERING` unbuffered physical SSD probe), `tools/pws/roofline.py`.
- `tools/pws/cache_policy.py` — Online policies (`lru`, `lfu`, `layer_aware`, `markov`, `nkat_seq`, `tsi_task`) + offline Belady MIN upper bound (`offline_oracle`, marked `deployable_online=false`).
- `tools/pws/expert_predictor.py`, `tools/pws/deadline_scheduler.py` — EDF deadline-constrained async prefetch & read-amplification accounting.
- `tools/pws/factorisation.py` — Shared-basis + low-rank expert factorisation with URT operator-2-norm error bound & Spin(8) vs generic $\mathrm{SO}(8)$ / Sylvester Hadamard comparison (noting Spin(8) vector representation acts through $\mathrm{SO}(8)$).
- `tools/pws/certificates.py`, `tools/pws/report.py`, `tools/pws_bench.py`.

### D. Evolutionary Inference Optimisation — EIO (`tools/evolution/`, `tools/eio_bench.py`)
- `tools/evolution/genome.py`, `tools/evolution/mutation.py`, `tools/evolution/bandit.py` (`uniform_random`, `ucb1`, `sliding_window_ucb`, `thompson_sampling`, `cost_aware_ucb`), `tools/evolution/archive.py` (Pareto archive), `tools/evolution/multi_fidelity.py`, `tools/evolution/invariant_verifier.py`, `tools/evolution/certificates.py` (paired holdout Hoeffding/bootstrap LCB with Bonferroni correction + break-even amortisation), `tools/evolution/shinka_adapter.py` (explicitly distinguishing `shinka_inspired_builtin` from external `SakanaAI/ShinkaEvolve`), `tools/evolution/hardware_evolve.py` (real-hardware Strata runner + independent paired holdout verification), `tools/eio_bench.py`.

---

## 3. Verification & Real-Hardware Measurements

### A. CPU Unit & Mathematical Self-Tests (PASSED)
- **8-suite pytest (`py -3 -m pytest -p no:randomly -q tools/test_tsi_*.py tools/test_pws_*.py tools/test_evolution_eio.py`):** **48 / 48 PASSED** (`14.86s`).
- **AST compliance audit:** 45 files checked, `0` forbidden calls (`print`/`eval`/`exec`).
- **TSI/VRE mathematical self-checks (`H:/Strata/evidence/nkat-urt-20261125/tsi_math_check.json`):** `pass=true`
  - Gramian vs rollout energy error: `0.0`
  - $\mathrm{SO}(8)$ orthogonality error: `3.24e-16`
  - Phase 2 discovery rate example ($p_{\mathrm{ref}}=0.40, c_{\mathrm{ref}}=1.0, p_{\mathrm{quant}}=0.25, c_{\mathrm{quant}}=0.5$): $p_{\mathrm{crit}}=0.225403$, finite-budget $B=3.0$ model delta `+0.038021`
  - Phase 3 Theorem 1 ($0.01 \to 0.90$): `3.820575 nats` (`5.511925 bits`)
  - Phase 3 Theorem 5 ($p_0=0.05, \lambda=5.0, L=1.0$): ideal `0.886508`, guaranteed lower bound `0.741841` (`uniform_bound_certified=false`)
  - Doob / Feynman–Kac equivalence: root partition abs err `4.44e-16`, max path prob abs err `2.78e-17`, `equivalent=true`.

### B. Unbuffered Physical SSD Probes (`FILE_FLAG_NO_BUFFERING`, Read-Only)
- **`C:` Crucial P3 1TB NVMe (`CT1000P3SSD8`, `ssd_probe_C_nvme.json`):**
  - Sequential 1 MiB QD=1 (256 MiB): **82.55 MB/s** (`p50=0.438 ms`, `p95=41.639 ms`, `p99=70.937 ms`)
  - Random 64 KiB QD=1 (256 reads): **24.40 MB/s** (`p50=1.564 ms`, `p95=7.773 ms`, `p99=19.616 ms`)
- **`H:` 1TB SATA SSD (`S5-1TB`, `ssd_probe_H_sata.json`):**
  - Sequential 1 MiB QD=1 (256 MiB): **53.03 MB/s** (`p50=20.042 ms`, `p95=37.138 ms`, `p99=44.627 ms`)
  - Random 64 KiB QD=1 (256 reads): **19.76 MB/s** (`p50=2.715 ms`, `p95=5.502 ms`, `p99=8.863 ms`)

### C. Real-Hardware RTX 5060 Ti EIO Evolutionary Optimisation (`real_eio_inkling2_ud.json`)
- **Engine / Model:** `H:/Strata/build/engine-cuda135/strata-inkling2.exe` + `H:/Strata/models/Inkling-2-Mini-UD-Q4_K_M.gguf` (`ctx=16384`, `max_tokens=32`, `STRATA_RAM_SQUEEZE=on`, `sliding_window_ucb`)
- **Search Phase (`818.0s`, 5/5 verified, 0 rejected, 100% bit-exact greedy parity):**
  - Baseline (`26d59abef29dfc9d`, `STRATA_SATA_COALESCE_GAP_KB=256`): `tg=37.91 t/s`, `pp=33.64 t/s`, `hits=17579 / misses=1909 (90.20%)`, `cpu_expert_ms=242.8 ms`
  - Best Candidate (`afe94f216b8bc931`, `STRATA_SATA_COALESCE_GAP_KB=1024`): **`tg=39.71 t/s (+4.7%)`**, **`pp=38.81 t/s (+15.4%)`**, `cpu_expert_ms=201.3 ms (-17.1%)`, `bit_exact_parity=true`
- **Independent Paired Holdout Verification (`1325.2s`, 3 separate prompts):**
  - **Bit-exact parity:** **3 / 3 (100%, `holdout_all_bit_exact_parity=true`)**
  - Prompt 0: `51.37 -> 48.48 t/s` (`hit_rate=93.53%`)
  - Prompt 1: `15.25 -> 38.13 t/s` (`+150.0%`, `cpu_expert_ms 943.8 -> 232.8 ms`, `hit_rate=88.24%`)
  - Prompt 2: `35.04 -> 36.43 t/s` (`hit_rate=89.43%`)
  - **Holdout median decode:** **`35.04 -> 38.13 t/s (+8.82%)`**, geometric mean speedup **`1.349x`**, `-2.313 ms/tok`
  - **URT Paired Speedup Certificate:** `hoeffding_lcb_d=null` (unbounded $R$), `bootstrap_lcb_d=-0.057903` (`active_lcb_speedup=0.9437x`), **`certified_speedup=false`** (honestly uncertified at $n=3$ with Bonferroni $\alpha/4=0.0125$ due to Prompt 0 variance).
  - **Amortisation:** `total_search_and_verify_s=2143.2s`, `break_even_tokens=926,700`, `cost_recovered_at_expected_usage (100k)=false`.
  - **Auto-adoption:** `auto_adopted_into_default_inference=false`.

### D. Tests Not Run / Interrupted
- **Live RTX 5060 Ti OpenAI API TSI Evaluation (`standard` vs `adaptive` vs `vre`):** Cancelled at user request (`いったん中止` -> `ライブ TSI 評価なしで現状を研究ブランチへコミット`). Prior launch attempts also surfaced: (1) `Hikari-LoRA-fixed-scale-PQ2_0.gguf` rejected by `strata-q38` (`GGUF tensor has an unsupported encoding or shape`), and (2) `strata-inkling` 0.6.9 pageable host arena (`4.61 GB`) exceeded available RAM (`3.2 GB`) during concurrent desktop load.
- **External `SakanaAI/ShinkaEvolve` & `robust-kbench`:** Not installed locally; all runs explicitly tagged `shinka_inspired_builtin` / `shinka_inspired_real_hardware_eio`.
- **100B+ MoE real-hardware streaming:** Not run; no speed claims made.
