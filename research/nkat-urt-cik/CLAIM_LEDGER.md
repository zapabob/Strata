# CIK claim ledger

Date 25 November 2026 JST. PROVED denotes a mathematical argument under the assumptions in [THEOREMS.md](THEOREMS.md). CONDITIONAL records an explicit inherited hypothesis. REFUTED denotes a counterexample to the stated claim. OPEN denotes an outstanding result. Kernel checks and experiments have their own columns.

| Claim | Mathematical status | Lean 4.29.0 | Experiment and scope |
| --- | --- | --- | --- |
| C1 finite causal KL projection (including the $P$-weighted gap) | PROVED | Support witness only | Exact input probabilities, floating-point logarithms. Future-copy, feedback and selection controls passed. |
| C1 alternative gap $D_\mu(Q^*\Vert Q)$ | REFUTED | — | Gap $0$ under $P$ and $\log(2)/2$ under $Q^*$. |
| C2 robust TV lower bound and finite block-triangular closure | PROVED | Binary TV grid bound verified | Binary example attains the TV lower bound. |
| C3 trace-norm comb repair | PROVED | — | Two-slot complex Hermitian fixture, numeric sanity check. |
| C3 operational strategy-norm repair bound | OPEN | — | Trace-norm guarantees are the available result. |
| I1 finite effect-span stabilisation and pair equivalence | PROVED | Abstract bounded-growth and fixed-point steps verified | Incremental span closure and length-one counterexample checked on qubit fixtures. |
| I1 restricted tomography bound | PROVED | — | Nearly singular qubit control on $\mathbb R Z$. |
| I2 Hankel rank lower bound with certified noise | PROVED | — | Rational pivots certify a three-by-three block. The equality-at-threshold control fails certification as required. |
| I2 rank $\le d^2$ suffices for positive $d$-dimensional realisation | REFUTED | — | Three perfectly distinguishable repeated labels need dimension three, although the rank bound gives two. |
| I3 conditional information identity | PROVED | — | Chain-rule identity under the stated Markov condition. |
| K1 universal $K_B=f(B,D_{\rm pred},\{\sigma_i\})$ | REFUTED | Exact equal Gram, per-row optimality and unequal success verified. Canonical budget lemma verified. | Equal-spectrum optimal one-attempt success $1/2$ and $5/12$. A fixed constant observation also supports opposing task distributions. |
| K2 length and exhaustive-search bounds, no computable uniform shortest-proof bound for the stated arithmetic theories | PROVED | Canonical length special case | General statements are analytic. |
| K2 calibrated top-$m$ law and task-labelled spectral tail bound | PROVED | Exact integer witness for $m=1$ only | Symmetric law and one rank-one truncation checked. |
| K3 von Mangoldt prior budget curve under RH | CONDITIONAL | — | Finite prime-weighted curves are directly computed. The asymptotic error rate uses RH. |
| A1 predictive contraction and fixed-trajectory GDN Gramian | PROVED | Integer temporal cross-term witness verified | Fixed-trajectory Gramian and Hankel reconstruction, noncommuting keys and unseen-query controls. |
| A1 universal beneficial Spin(8) triality, adaptive low-rank residuals on real models | OPEN | — | Equal-bit synthetic rotation controls. The vector-level rotation identity does not predict quantisation benefit. |
| A1 general higher-dimensional signalling from reasoning outputs | OPEN | — | Only counterfactual synthetic data are within the experimental evidence. |
| A1 general Strata reasoning improvement and sustained out-of-core deployment | OPEN | — | Refer to the scope of the real 27B trials in [REPORT.md](REPORT.md). |
| A1 Hy4-Flash PQ2_0 with preserved whole-model quality, throughput and a validated behavioural projection | OPEN | — | A real expert was packed and dispatched on CUDA and CPU. The fitted PQ2_0 control increased matrix output error over S2_K, and quantisation reintroduced part of the synthetic axis. [Routed pilot](../hy4-bonsai2/REPORT.md). |
| A1 minimum-distortion removal of a specified linear output direction under a positive definite metric | PROVED | — | Verified the equality bound on a live checkpoint expert and its output adapter. Error against the BF16 reference fell from 2.205% to 1.577% at FP32. The direction is synthetic. [Projection proof and precision controls](../hy4-bonsai2/REPORT.md#direct-weight-projection). |
| A1 Spin(8) triality preserves the exact paired-basis operator and localises the selected direction block by block | PROVED | — | Exact Clifford-table check, numerical intertwiner, and native GGUF dispatch on CPU and CUDA. The selected half-spin branch did not improve the holdout error over H512. [Spin(8) and GGUF evidence](../hy4-bonsai2/REPORT.md#spin8-triality-and-gguf-evaluation). |

The Lean dependency report lists `propext` and `Quot.sound` from Lean's standard foundation where used. The project declares no axioms of its own. The full analytic proofs of C1, C3, I2, K2 and A1 remain suitable for later formalisation.
