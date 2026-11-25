# NKAT–URT Theory of Scientific Intelligence (TSI) and Variational Reasoning Engine (VRE)

Status: **Opt-in Python research layer implemented on `research/tsi-verified-evaluation`** · **`releaseQualified=false`**

This document specifies the **NKAT–URT Theory of Scientific Intelligence (TSI)** and **Variational Reasoning Engine (VRE)** programme for `zapabob/Strata` (Hakua / Strata). The primary objective is not isolated decode speed (`tokens per second`), but maximising **verified scientific reasoning solutions per unit of computational resource** under the physical limits of consumer hardware (NVIDIA RTX 5060 Ti 16 GB, AMD Ryzen 5 4500, 32 GB RAM, dual SSD storage).

All TSI and VRE modules are opt-in and implemented strictly outside Strata's default inference paths, native CUDA kernels, and user configuration.

---

## 1. Epistemic Boundaries and Non-Claims

1. **Proven theorems and identities (audited by CPU unit tests)**:
   - Stopping-time cumulative success $S_\pi(B) = \Pr(\tau_q \le B)$ and exact finite-horizon Restricted Mean Time to Success $\mathrm{RMST}(B_{\max}) = \int_0^{B_{\max}} (1 - S_\pi(b))\,db$ with all censored and unsuccessful trials retained.
   - Quantisation discovery-rate theorem $\Lambda_Q = -\ln(1 - p_Q)/c_Q$, critical threshold $p_{\mathrm{crit}} = 1 - (1 - p_R)^{c_Q/c_R}$, Data Processing Inequality $\mathrm{KL}(P_R \| P_Q) \ge d_{\mathrm{bin}}(p_R \| p_Q)$, and Pinsker bound $p_Q \ge p_R - \sqrt{\mathrm{KL}/2}$.
   - Variational Reasoning Engine Theorems 1–7: minimum KL cost $d_{\mathrm{bin}}(p_1 \| p_0)$, Gibbs variational optimality and gap $(1/\lambda)D_{\mathrm{KL}}(\widehat{Q} \| Q^*_\lambda)$, Doob $h$-transform and Feynman–Kac backward recursion, error-propagation bound (Theorem 4), log-Bellman residual telescoping identity and non-perturbative logit lower bound (Theorem 5), unified quantisation-plus-control bound (Theorem 6), and proof-state bisimulation quotient invariance (Theorem 7).
   - Non-commutative GDN state transitions $\Phi(t, j) = A[t] \cdots A[j+1]$, backward URT observability Gramians $M[j]$, exact readout error energy $E[j] = \operatorname{Tr}(R[j]M[j]R[j]^\top)$, Hankel singular values for fixed linear input–output operators, and $\mathrm{SO}(8)$ orthogonal invariance.
2. **Research hypotheses (subject to empirical verification, never assumed proven)**:
   - Whether Gramian-aligned low-rank residual compensation or $\mathrm{Spin}(8)$ triality outperforms generic $\mathrm{SO}(8)$ rotations on real nonlinear language models.
   - Whether empirical adaptive schedulers or step-level VRE candidate selectors improve verified solutions per second once all failed retries and verification overhead are counted.
   - Whether the Weibull curve $S(B) = s_\infty[1 - \exp(-(B/B_0)^\beta)]$ fits held-out budgets across real models.
3. **Explicit non-claims**:
   - The **Riemann Hypothesis (RH)** is never invoked to justify LLM quantisation, SSD streaming, or reasoning performance.
   - Finite-budget experiments never establish infinite-horizon $\mathbb{E}[\tau_q]$, true continuous $B^*_\pi(\delta)$, or asymptotic ceiling $s_\infty$.
   - `empirical_topk_kl` (such as top-64 renormalised KL) and single-prefix empirical KL never qualify as `certified_sequence_kl_upper_bound`.
   - Known benchmark solutions (`known_benchmark_problem`) are aggregated separately from independently novelty-checked scientific discoveries (`novel_discovery_candidate`).
   - `releaseQualified=false` remains explicit throughout.

---

## 2. Architecture (`tools/tsi/` and `tools/tsi_eval.py`)

| Module | Scope |
|---|---|
| `tools/tsi/math_foundations.py` | Wilson / Clopper–Pearson intervals, Bonferroni adjustment, finite attainment, GDN $\Phi(t, j)$, URT Gramian $M[j]$, Hankel SVD, full-vocab vs top-$k$ KL, $r^2/8$ bound, $\mathrm{SO}(8)$ rotation. |
| `tools/tsi/verifier.py` | Strict 5-level `VerificationLevel` hierarchy (`UNVERIFIED`, `EXACT_ANSWER_VERIFIED`, `DETERMINISTIC_TEST_VERIFIED`, `NUMERICAL_CERTIFICATE_VERIFIED`, `FORMAL_PROOF_VERIFIED`), zero-`eval`/`exec` deterministic verifiers, and an isolated Lean 4 kernel adapter rejecting `sorry`, `admit`, `unsafe`, and unauthorised `axiom` declarations. |
| `tools/tsi/tasks.py` | Four strictly disjoint deterministic splits: `dev` (`core-v1`, 12), `calibration` (4), `validation` (4), and `frozen-holdout` (`holdout-v1`, 8), plus external JSON/JSONL loading and `discovery_class` tagging. |
| `tools/tsi/survival.py` | Token-axis and wall-clock-axis survival curves, exact step-integral RMST, censored counts, and simultaneous Hoeffding lower bounds across $J$ pre-specified budgets. |
| `tools/tsi/discovery_rate.py` | Asymptotic discovery rate $\Lambda$, critical $p_{\mathrm{crit}}$, end-to-end `TrialCostBreakdown`, conservative robust adoption check, and Jensen pass@$k$ heterogeneity audit. |
| `tools/tsi/information.py` & `certificates.py` | Binary KL, DPI, Pinsker, shared-prefix chain rule, Strata `LOGS` reader, strict quantisation certification (refusing non-certified KL kinds), and URT policy stability bounds ($2N\varepsilon$ and $2[1-(1-\varepsilon)^N]$). |
| `tools/tsi/research_state.py` | Nine-field `ResearchState` separating `verified_lemmas` from unverified `failed_attempts`, recording non-commutative operator traces across all seven canonical `ResearchAction` values. |
| `tools/tsi/bellman.py` | Optimal restart cutoff $L(b) = [c_0 + \int_0^b (1-F(t))\,dt]/F(b)$, exact finite-budget discrete Bellman DP, policy evaluator, and transition TV distance. |
| `tools/tsi/variational.py`, `doob.py`, `bellman_residual.py`, `proof_graph.py`, `phase_diagram.py` | Complete VRE implementation: Theorems 1–7, Feynman–Kac Gibbs ensemble & exact cumulants, finite-tree Doob $h$-transform, step-level VRE candidate selector, log-Bellman residual audit, bisimulation quotient invariance, and $(\lambda, \eta)$ phase diagrams. |
| `tools/tsi/memory.py` & `scaling.py` | Key-dimension GDN trajectory contraction, key non-orthogonality, time-correlated quantisation amplification, low-rank residual compensation simulation with FLOP/DRAM accounting, and Weibull hypothesis fitter with jackknife uncertainty. |
| `tools/tsi/scheduler.py`, `metrics.py`, `runner.py`, `report.py`, `tsi_eval.py` | Bounded `standard`, `adaptive`, and `vre` runners, Section 16 JSONL recording (strict `null` for unmeasured metrics, redacted secrets/paths), four-gate `PrecisionEscalationGate`, paired `compare_runs()`, and Markdown report generation. |

---

## 3. CLI Usage

```powershell
# Verify Phase 1, Phase 2, and VRE Phase 3 mathematical identities (CPU-only)
python tools/tsi_eval.py math-check

# List all disjoint built-in benchmark splits
python tools/tsi_eval.py list-tasks --suite all

# Evaluate a local loopback Strata OpenAI-compatible server (standard vs adaptive vs step-level VRE)
python tools/tsi_eval.py eval --url http://127.0.0.1:8080 --suite dev --mode standard --budgets 256,512 --sample-hw-metrics --out std.json --jsonl std.jsonl
python tools/tsi_eval.py eval --url http://127.0.0.1:8080 --suite dev --mode adaptive --budgets 512 --attempts 3 --sample-hw-metrics --out adapt.json --jsonl adapt.jsonl
python tools/tsi_eval.py compare std.json adapt.json --out diff.json
python tools/tsi_eval.py report std.json adapt.json --out report.md
```

---

## 4. Safety Floors and Approval Discipline

- Loopback-only HTTP client by default (`127.0.0.1`, `localhost`, `::1`); non-loopback requires explicit `--allow-non-loopback`.
- Mandatory hardware safety floors: available RAM $\ge 3\text{ GiB}$, Windows commit $\ge 4\text{ GiB}$, GPU VRAM reserve $\ge 768\text{ MiB}$, free disk $\ge 5\text{ GiB}$ on `C:` and $\ge 10\text{ GiB}$ on `H:`, build parallelism capped at `5`.
- `ESCALATE_PRECISION` is disabled by default and requires target model presence, free memory above safety floors, accounted switch cost, and explicit user approval.
