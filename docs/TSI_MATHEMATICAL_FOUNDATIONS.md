# TSI and VRE Mathematical Foundations

Status: **Technical specification (`research/tsi-verified-evaluation`)** · **`releaseQualified=false`**

This document collects the mathematical definitions, proven theorems, counterexamples, and explicit scope conditions implemented across `tools/tsi/`. All statistical-mechanical terms (partition function, effective action, inverse temperature) are formal variational correspondences and never denote physical hardware temperature or power.

---

## 1. Stopping-Time Survival Theory

For task $q$, reasoning policy $\pi$, and independent verifier $V \in \{0, 1\}$, define the cumulative computational cost to first verification:

$$\tau_q = \inf \{ b \ge 0 : V(q, \pi_b) = 1 \}, \qquad S_\pi(B) = \Pr(\tau_q \le B).$$

On a finite maximum budget $B_{\max}$, the Restricted Mean Time to Success retains all unsuccessful, timed-out, and right-censored trials:

$$\mathrm{RMST}(B_{\max}) = \int_0^{B_{\max}} \bigl(1 - S_\pi(b)\bigr)\,db.$$

For $n$ independent tasks and $J$ pre-specified budgets $\{B_1, \dots, B_J\}$, Hoeffding's inequality with union bound yields the simultaneous one-sided lower confidence bound at level $1 - \alpha$:

$$S_\pi(B_j) \ge \widehat{S}_\pi(B_j) - \sqrt{\frac{\ln(J / \alpha)}{2 n}}.$$

A continuous-policy cumulative curve (`curve_type="continuous_policy"`) must never be conflated with separate per-budget configurations (`curve_type="per_budget_config"`).

---

## 2. Quantisation Discovery-Rate Theorem and URT Certification

Under independent constant-cost trials with single-trial verified probability $p_Q$ and complete end-to-end trial cost $c_Q$ (prefill, decode, model switch, context rebuild, retries, verification, counterexample search, and initialisation):

$$S_Q(B) = 1 - (1 - p_Q)^{\lfloor B / c_Q \rfloor}, \qquad \Lambda_Q = -\frac{\ln(1 - p_Q)}{c_Q}.$$

Thus $\Lambda_Q > \Lambda_R$ holds if and only if

$$p_Q > p_{\mathrm{crit}} := 1 - (1 - p_R)^{c_Q / c_R}.$$

**Theoretical numerical verification check** (not a hardware measurement): for $p_R = 0.40, c_R = 1.0, p_Q = 0.25, c_Q = 0.5$, we obtain $p_{\mathrm{crit}} = 1 - \sqrt{0.60} \approx 0.225403 < 0.25$, and at $B = 3$: $S_R(3) = 1 - 0.60^3 = 0.784$ versus $S_Q(3) = 1 - 0.75^6 \approx 0.822021$.

**Information-geometric certification (Data Processing Inequality and Pinsker)**:
Because $V \in \{0, 1\}$ is a deterministic function of the generated response,

$$D_{\mathrm{KL}}(P_R \| P_Q) \ge d_{\mathrm{bin}}(p_R \| p_Q), \qquad p_Q \ge p_R - \sqrt{\frac{D_{\mathrm{KL}}(P_R \| P_Q)}{2}}.$$

Consequently, when $c_Q < c_R$, a certified upper bound satisfying $D_{\mathrm{KL}}(P_R \| P_Q) < d_{\mathrm{bin}}(p_R \| p_{\mathrm{crit}})$ guarantees $p_Q > p_{\mathrm{crit}}$ and $\Lambda_Q > \Lambda_R$. Top-$k$ renormalised KL (`empirical_topk_kl`) and single-prefix teacher-forced KL are strictly refused by `certify_quantisation_discovery_rate()`.

**Heterogeneity (Jensen's inequality)**: for heterogeneous task probabilities $p_q$, convexity of $x \mapsto (1 - x)^k$ ($k \ge 1$) gives

$$S(k) = 1 - \mathbb{E}_q[(1 - p_q)^k] \le 1 - \bigl(1 - \mathbb{E}_q[p_q]\bigr)^k,$$

prohibiting naive pass@$k$ extrapolation from average pass@1.

---

## 3. Variational Reasoning Engine (Theorems 1–7)

Let $P(\omega) = \prod_{t=1}^T p(a_t \mid a_{<t}, q)$ be the base LLM path distribution, $E_q = \{\omega : V_q(\omega) = 1\}$, and $p_0 = P(E_q) \in (0, 1)$.

1. **Theorem 1 (Minimum KL Information Cost)**:
   $$\inf_{Q : Q(E_q) = p_1} D_{\mathrm{KL}}(Q \| P) = d_{\mathrm{bin}}(p_1 \| p_0), \qquad C_* = -\ln p_0 \text{ for } p_1 = 1.$$
   Example check: $p_0 = 0.01 \to p_1 = 0.90$ requires $3.8206\text{ nat}$ ($5.5119\text{ bit}$). If $p_0 = 0$, no finite-KL reweighting can achieve $p_1 > 0$.

2. **Theorem 2 (Gibbs Variational Principle)**:
   Maximising $\mathcal{J}_\lambda(Q) = \mathbb{E}_Q[V_q] - \frac{1}{\lambda} D_{\mathrm{KL}}(Q \| P)$ ($\lambda > 0$) yields
   $$Q^*_\lambda(\omega) = \frac{P(\omega) e^{\lambda V_q(\omega)}}{Z_\lambda}, \quad Z_\lambda = 1 - p_0 + p_0 e^\lambda, \quad \operatorname{logit}(p^*_\lambda) = \operatorname{logit}(p_0) + \lambda,$$
   with exact optimality gap $\mathcal{J}_\lambda(Q^*_\lambda) - \mathcal{J}_\lambda(\widehat{Q}) = \frac{1}{\lambda} D_{\mathrm{KL}}(\widehat{Q} \| Q^*_\lambda)$.

3. **Theorem 3 (Doob $h$-Transform and Feynman–Kac Cost Control)**:
   With committor $g(u) = P(V_q = 1 \mid u)$ and $h_\lambda(u) = 1 + (e^\lambda - 1) g(u)$, the exact step law is $q^*_\lambda(a \mid u) = p(a \mid u) h_\lambda(ua) / h_\lambda(u)$. Incorporating cumulative cost $C(\omega) = \sum_t c_t(a_{\le t})$ with penalty $\eta \ge 0$ yields the Feynman–Kac recursion
   $$h_t(u) = \sum_a p(a \mid u) e^{-\eta c_t(u, a)} h_{t+1}(ua), \qquad q^*_t(a \mid u) = \frac{p(a \mid u) e^{-\eta c_t(u, a)} h_{t+1}(ua)}{h_t(u)}.$$
   The effective action $\mathcal{S}_{\mathrm{eff}}(\omega) = -\ln P(\omega) - \lambda V_q(\omega) + \eta C(\omega)$ satisfies $\partial_\lambda \ln Z = \mathbb{E}_{Q^*}[V_q]$, $-\partial_\eta \ln Z = \mathbb{E}_{Q^*}[C]$, $\partial_\lambda^2 \ln Z = \operatorname{Var}_{Q^*}(V_q)$, and $-\partial_\lambda \partial_\eta \ln Z = \operatorname{Cov}_{Q^*}(V_q, C)$.

4. **Theorem 4 (Error Propagation)**:
   If $|\ln \widehat{h}_\lambda(ua) - \ln h_\lambda(ua)| \le \varepsilon_t$ uniformly across reachable prefixes and tokens, then
   $$D_{\mathrm{KL}}(\widehat{Q} \| Q^*_\lambda) \le \frac{1}{2}\sum_{t=1}^T \varepsilon_t^2, \qquad \widehat{Q}(E_q) \ge p^*_\lambda - \frac{1}{2}\sqrt{\sum_{t=1}^T \varepsilon_t^2}.$$

5. **Theorem 5 (Non-Perturbative Log-Bellman Residual Certification)**:
   Setting terminal $\widehat{h}_\lambda(\omega) = e^{\lambda V_q(\omega)}$ via the independent verifier and $r(u) = \ln \widehat{h}_\lambda(u) - \ln \sum_a p(a \mid u)\widehat{h}_\lambda(ua)$, $R(\omega) = \sum_{t=0}^{T-1} r(a_{\le t})$, telescoping yields
   $$\widehat{Q}(\omega) = \frac{P(\omega) e^{\lambda V_q(\omega) + R(\omega)}}{\widehat{h}_\lambda(\varnothing)}.$$
   Whenever $\sup_\omega R(\omega) - \inf_\omega R(\omega) \le L$ uniformly over all paths,
   $$\operatorname{logit}\widehat{Q}(E_q) \ge \operatorname{logit}(p_0) + \lambda - L.$$
   Example check: $p_0 = 0.05, \lambda = 5.0, L = 1.0 \implies p^*_\lambda \approx 88.65\%$ and guaranteed lower bound $\approx 74.18\%$. Connecting to discovery rate $\Lambda$ yields the sufficient criterion $\lambda - L > \operatorname{logit}(p_{\mathrm{crit}}) - \operatorname{logit}(p_0)$ when all quantities are certified.

6. **Theorem 6 (Unified Quantisation and Control Bound)**:
   For per-step quantisation logit span $r_t$ and control error $\varepsilon_t$ on shared support,
   $$D_{\mathrm{KL}}(\widehat{Q}_Q \| Q^*_R) \le \frac{1}{8}\sum_{t=1}^T (r_t + 2\varepsilon_t)^2, \qquad \widehat{p}_Q \ge p^*_R - \frac{1}{4}\sqrt{\sum_{t=1}^T (r_t + 2\varepsilon_t)^2}.$$

7. **Theorem 7 (Proof-State Bisimulation Quotient)**:
   Merging proof states preserves exact finite-budget Bellman value if and only if merged states share equal terminal verification reward, equal admissible actions and costs, and identical induced transition probabilities across equivalence classes. Counterexample: two histories presenting an identical visible Lean goal can induce different LLM next-token distributions due to differing KV-cache context and therefore fail bisimulation.

---

## 4. Optimal Restart, Bellman Policy Stability, and NKAT–GDN Memory

- **Optimal restart cutoff**: $L(b) = [c_0 + \int_0^b (1 - F(t))\,dt] / F(b)$ minimised over $b$ with $F(b) > 0$ (requires independent retries; correlated failure loops violate the model).
- **URT policy stability**: conditional on uniform transition error $\mathrm{TV}(P_a(\cdot \mid s), \widehat{P}_a(\cdot \mid s)) \le \varepsilon$ over horizon $N$,
  $$V^*_N - V^{\hat{\pi}}_N \le \min\bigl(1, 2[1 - (1 - \varepsilon)^N]\bigr) \le \min(1, 2 N \varepsilon).$$
- **GDN observability Gramian & low-rank residual compensation**: for $A[t] = \alpha[t](I - \beta[t] k[t] k[t]^\top)$ and $M[j] = q[j]q[j]^\top + A[j+1] M[j+1] A[j+1]^\top$, $E[j] = \operatorname{Tr}(R[j]M[j]R[j]^\top)$ measures exact linearised future readout energy, while $S_{\mathrm{corrected}}[t] = Q(Y[t]) + (Y[t] - Q(Y[t]))VV^\top$ projects quantisation error onto top Gramian eigenvectors at explicit FLOP and DRAM overhead $4 d_v d_k r$ FLOPs/step.
