# NKAT–URT Evolutionary Inference Optimisation (EIO)

Status: **Opt-in evolutionary search framework (`tools/evolution/`, `tools/eio_bench.py`)** · **`releaseQualified=false`**

This document specifies the Phase 3 Revised integration of Sakana AI-inspired evolutionary optimisation (**ShinkaEvolve**, arXiv:2509.19349; **AI CUDA Engineer / robust-kbench**, arXiv:2509.14279) with Strata's PWS and TSI layers.

---

## 1. Static Audit of Existing `scripts/shinka_evolve_rh.py`

The pre-existing script `scripts/shinka_evolve_rh.py` is preserved untouched as a reproducible initial baseline. Direct inspection confirms six limitations:

1. Evaluates synthetic Zipf/Zeta traces rather than real Strata `--dump-routing` traces, physical SSD I/O, or GPU runtime.
2. `CacheGenome.markov_dt1` and `CacheGenome.entropy_gain` are declared but unused in `evaluate_genome()`.
3. Parent sampling (`rng.choice(top_k)`) is uniform over the top 5 candidates rather than fitness-proportionate.
4. `robust_kbench_verify()` checks scalar parameter bounds and byte budget only, not CUDA kernel numerical correctness or memory safety.
5. `weighted_cpu_saved` is a proxy score that does not guarantee real wall-clock reduction.
6. Hard-coded constants (`12` layers, `128` experts, uniform `4.8 MB` stride) cannot be treated as a general hardware profile.

---

## 2. Distinction Between Built-In Search and Official Sakana AI Packages

- **`shinka_inspired_builtin` (`tools/evolution/shinka_adapter.py`)**: self-contained multi-island Pareto evolutionary search with true fitness-proportionate parent sampling, novelty filtering, non-commutative operator-sequence swaps (`A1..A7`), five comparable mutation bandits (`uniform_random`, `ucb1`, `sliding_window_ucb`, `thompson_sampling`, `cost_aware_ucb`), 9-tuple evaluation provenance caching, and Level 0–2 multi-fidelity screening with random proxy-audit promotion.
- **Official `SakanaAI/ShinkaEvolve` & `SakanaAI/robust-kbench`**: `tools/eio_bench.py inspect-deps` audits actual installed packages and CLI binaries. Custom built-in runs are never mislabelled as official ShinkaEvolve or robust-kbench runs, and published literature speedups (such as 1.49x from robust-kbench re-evaluation) are never cited as achieved Strata results.

---

## 3. Verification, Certification, and Amortisation

- **Automatic search vs adoption**: `auto_adopted_into_default_inference` is strictly `false`. Candidates discovered on search traces must pass immutable hard gates (`numerical_correctness`, `resource_guards`, `model_integrity`, `required_quality`, `verifier_integrity`) and independent holdout certification (`tools/evolution/certificates.py`) before human review.
- **URT paired log-speedup certification**: computes $d_i = \ln(T_{b,i} / T_{c,i})$ with Bonferroni multiplicity adjustment. Bounded-range Hoeffding LCB $\bar{d} - R\sqrt{\ln(1/\alpha)/(2n)}$ is emitted **only** when the range width $R$ is certified a priori; otherwise paired block bootstrap LCB is reported.
- **Search cost amortisation**: `search_amortisation_breakeven()` computes $\text{break\_even\_tokens} = (T_{\mathrm{search}} + T_{\mathrm{build+verify}}) / \Delta t_{\mathrm{token}}$ so optimisation overhead is accounted for honestly.
