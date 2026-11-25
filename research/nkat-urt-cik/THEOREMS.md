# CIK finite causality, inference and knowledge

## Scope and conventions

All alphabets, instrument spaces and experimental budgets below are finite except where explicitly quantified. Logarithms are natural. The trace norm is the sum of singular values. Total variation is half the \(\ell^1\) distance. A theorem marked proved has the mathematical proof given here. The Lean file verifies the specific algebraic statements named in the ledger. Each numerical check uses a separate tolerance or rational certificate.

## C1 Causal projection of a finite channel

Let \(P(a,y)=\mu(a)P_a(y)\), where \(\mu\) specifies externally imposed input words with no feedback. Let \(h_t=(y_{<t},a_{\le t})\), and let \(Q_a(y)=\prod_t q_t(y_t\mid h_t)\). Define \(q_t^*(\cdot\mid h_t)=P(Y_t\in\cdot\mid h_t)\) on histories with positive \(P\)-mass and choose any probability law on other histories. Then
\[
\begin{aligned}
D_\mu(P\Vert Q)&=D_{\rm caus}(P)+\sum_t
  \mathbb E_{P(h_t)}D_{\rm KL}(q_t^*(\cdot\mid h_t)\Vert q_t(\cdot\mid h_t)),\\
D_{\rm caus}(P)&=\min_Q D_\mu(P\Vert Q)
  =\sum_t I_P(Y_t;A_{>t}\mid Y_{<t},A_{\le t}).
\end{aligned}
\]

**Proof.** On a positive joint event, factor \(P_a(y)\) into the full-input conditional probabilities \(p_t(y_t\mid y_{<t},a)\). The logarithm of the likelihood ratio is the sum of \(\log(p_t/q_t^*)\) and \(\log(q_t^*/q_t)\). The first expectation is conditional mutual information by its finite-sum definition. In the second expectation, first sum over \(y_t\) conditional on \(h_t\). A positive \(q_t^*\) paired with zero \(q_t\) contributes \(+\infty\) as usual. The first term is finite and each second term is non-negative, with equality at \(q_t=q_t^*\) on positive histories. This proves attainment and uniqueness on those histories. A minimum of zero gives \(P_a=Q_a^*\) for each \(a\) in the support of \(\mu\). Full support makes this a statement about all intervention words.

**History-measure control.** Take a singleton \(A_1\), a fair \(A_2\), \(Y_1=A_2\) and \(Y_2=0\). The projection draws \(Y_1\) fairly. Give \(q_2\) probability one for \(Y_2=0\) on \(Y_1=A_2\) and probability one-half elsewhere. The \(P\)-weighted gap is zero, while \(D_\mu(Q^*\Vert Q)=\tfrac12\log 2\). The two expectations assign different weights to mismatched histories.

**Support, feedback and selection controls.** On the restricted intervention set \(A_2=A_1\), \(Y_1=A_2\) agrees with a causal predictor on the observed support but its extension to all interventions depends on the future. In a feedback experiment, let \(Y_1\) be a fresh fair bit and set \(A_2=Y_1\) in the controller. Conditioning on \(A_2\) produces \(\log 2\) of apparent backwards dependence although intervening on \(A_2\) leaves \(Y_1\) fair. Finally, with independent fair \(Y_1,A_2\), selecting records with \(Y_1=A_2\) gives the same apparent dependence. These are synthetic controls for intervention design.

## C2 Robust separation and linear causality

For a cut \(t\), take two full input words agreeing through \(t\) and compare the output distributions restricted through \(t\). Let \(\Delta_t\) be the maximum total variation over such pairs. Under any causal channel \(Q\) the two restricted distributions coincide. Marginalisation contracts total variation. Applying the triangle inequality to a pair that attains \(\Delta_t\) therefore gives
\[
\inf_Q\sup_a {\rm TV}(P_a,Q_a) \ge \tfrac12\max_t \Delta_t.
\]
For the binary future-copy control the bound is attained by a fair first output and the fixed second output.

On a finite ordered direct sum of Hilbert spaces, blocks above the diagonal vanish for causal linear maps. Taking a sum, a product or a norm limit preserves those zero blocks. Elimination of an invertible diagonal pivot leaves the remaining Schur complement block lower triangular by the same block-product test. Taking the adjoint exchanges the upper and lower triangles. The algebra is closed under adjoints only when restricted to its block diagonal part.

## C3 Repair of a finite quantum comb

Use the normalised Choi convention. At slot \(t\) the constraint is
\(\operatorname{Tr}_{O_t} W^{(t)}=(I_{I_t}/d_{I_t})\otimes W^{(t-1)}\), with \(W^{(0)}=\operatorname{Tr}W\). The order of tensor factors is part of this convention. Collect the linear residuals in \(L\), with the direct-sum Frobenius norm, and assume \(W\succeq0\), \(\operatorname{Tr}W=1\). The maximally mixed \(\tau=I_D/D\) satisfies \(L(\tau)=0\). For \(r=\|L(W)\|_2\) and \(L_0\) the restriction to traceless Hermitian matrices, put \(Z=L_0^+L(W)\), \(\delta=\|L_0^+\|_{2\to2}r\) and
\[
W_{\rm repair}=\frac{W-Z+D\delta\tau}{1+D\delta}.
\]
Then \(W_{\rm repair}\) is feasible. With \(\mathcal Q\) the feasible set,
\[
\frac{r}{\|L\|_{1\to2}}\ \le\ {\rm dist}_1(W,\mathcal Q)\
\le\ \|W-W_{\rm repair}\|_1
\ \le\ \frac{\sqrt D\,\delta+2D\delta}{1+D\delta}.
\]
Use a zero lower bound when \(L=0\).

**Proof.** For any feasible \(V\), \(r=\|L(W-V)\|_2\le\|L\|_{1\to2}\|W-V\|_1\). For the repair, \(L(W)=L_0(W-\tau)\) puts the residual in the range of \(L_0\). Hence \(L(Z)=L(W)\), \(\operatorname{Tr}Z=0\) and \(\|Z\|_{\rm op}\le\|Z\|_F\le\delta\). Adding \(D\delta\tau=\delta I_D\) restores positivity. Dividing by \(1+D\delta\) restores trace one. The numerator of \(W-W_{\rm repair}\) is \(Z+D\delta(W-\tau)\), so \(\|Z\|_1\le\sqrt D\,\delta\) and \(\|W-\tau\|_1\le2\) give the upper bound. For the two-qubit-pair example, partial trace over \(d\) dimensions has Frobenius operator norm at most \(\sqrt d\) by Cauchy–Schwarz, and subtracting the normalised input trace is an orthogonal projection. The two residual blocks give \(\|L\|_{1\to2}\le\sqrt{2+8}\).

The normalised Choi constraints follow [Chiribella, D’Ariano and Perinotti](https://arxiv.org/abs/0904.4483). The displayed repair and its bounds are derived here with the trace norm. An operational strategy-norm bound remains open in this study.

## I1 Observational equivalence, finite words and conditioning

Consider time-homogeneous finite-dimensional quantum instruments \(\mathcal E_{a,y}\) with complete positivity and a trace-preserving sum over \(y\) for each input \(a\). For a word \(w\), compose maps in chronological order when acting on a state. Thus \(\mathcal E_{uv}=\mathcal E_v\circ\mathcal E_u\) and \(E_{uv}=\mathcal E_u^*(E_v)\), where \(E_w=\mathcal E_w^*(I)\). The word probability is \(\operatorname{Tr}(\rho E_w)\).

The effect span \(V_n\) of words of length at most \(n\) satisfies \(V_0=\operatorname{span}_{\mathbb R}(I)\) and
\[
V_{n+1}=V_n+\sum_{a,y}\mathcal E_{a,y}^*(V_n).
\]
Equality at one step makes the span invariant under every adjoint map. Any strict step increases dimension by at least one. The Hermitian ambient space has real dimension \(d^2\), so \(V_{d^2-1}=V_{\rm obs}\). Two states give the same word probabilities precisely when their difference is orthogonal to \(V_{\rm obs}\) in the trace inner product.

For two models, start from \((I_{d_1},I_{d_2})\) and apply the paired adjoint maps componentwise. Compare the two traces with a single linear functional on this direct sum. The ambient dimension is \(d_1^2+d_2^2\) and the initial span is one-dimensional. Agreement through word length \(d_1^2+d_2^2-1\) annihilates the entire reachable span. An incremental basis closes the span and can retain a witnessing word for each added basis element. Related finite-word bounds for sequential machines are due to [Li and Qiu](https://arxiv.org/abs/quant-ph/0604085).

Let \(M\) collect a finite family of effect measurements. On a subspace \(U\) with smallest restricted singular value \(\eta>0\), \(\|X\|_F\le\|MX\|_2/\eta\) follows directly from the definition of \(\eta\). To apply this to all differences of states, the trace-zero subspace must be observable. In the qubit control with \(E_\pm=I/2\pm\epsilon Z\), the restricted space \(\mathbb R Z\) has \(\eta=2\epsilon\) and the two orthogonal Pauli directions are invisible.

## I2 Certified finite Hankel lower bounds

Write \(H_{u,v}=P(uv)\) for any finite selection of words. Then \(H_{u,v}=\operatorname{Tr}(\mathcal E_u(\rho)E_v)\), a factorisation through at most \(d^2\) real coordinates. If \(\|\widehat H-H\|_2\le\epsilon_{\rm data}\), singular-value perturbation gives
\[
d\ \ge\ \left\lceil\sqrt{\#\{i:\widetilde\sigma_i>
\epsilon_{\rm data}+\epsilon_{\rm num}\}}\right\rceil ,
\]
provided \(\widetilde\sigma_i\) is computed with certified error at most \(\epsilon_{\rm num}\) from \(\widehat H\). Entrywise uncertainties \(|\widehat H_{ij}-H_{ij}|\le\epsilon_{ij}\) make \(\|(\epsilon_{ij})\|_F\) a valid choice of \(\epsilon_{\rm data}\). Interval rounding uncertainty in the input is included in it. The strict threshold is essential.

An exact alternative is to keep the measured centre rational. Choose a \(k\)-by-\(k\) submatrix \(M\) of \(\widehat H\). Certify \(M^\top M-\epsilon_{\rm data}^2I\succ0\) by exact rational pivots. The singular values of the submatrix are bounded above by those of the full matrix, since row and column restrictions have operator norm one. Then \(\sigma_k(H)>0\) and the \(d\) lower bound follows with \(k\) in place of the count. The arithmetic error of this pivot certificate is zero.

**Padding and positivity controls.** Tensoring each operation with an identity on an unobserved ancilla preserves all word probabilities. For a sharper limitation, let the output process be an initially uniform label from three symbols repeated forever under one fixed input. Its Hankel rank is exactly three, as seen from the three singleton rows and columns and a three-component mixture of rank-one factors. A qubit cannot realise it. Conditioned on each first label, the next measurement must discriminate the three resulting states perfectly. A positive effect with trace pairing one with its own state acts as identity on that support, and acts as zero on the supports of the other states. The three supports are therefore mutually orthogonal. They require dimension at least three, attained by the diagonal three-state instrument. Rank alone gives the weaker lower bound two. Neither the true physical dimension nor an unobserved information source is identified by the observed Hankel rank.

## K1 Obstructions to a universal budget law

Specify the experiment by a finitary verifier \(\Gamma\), a task law \(\mu\), an observation process, a policy \(P\) and a cost model. Let \(T\) be the cost until the first accepted proof, with \(T=+\infty\) if none is found. Then \(K_B=\Pr[T\le B]\). For a class of such experiments, a single \(f(B,D_{\rm pred},\{\sigma_i\})\) exists exactly when every pair with equal predictive statistics has the same discovery-cost distribution on the budgets considered. The following controls violate this condition.

**Proof length at fixed observation.** Take an observation process that is constant forever, of predictive dimension and nonzero Hankel rank one. Use a fixed proof language for reflexive unary goals \(n=n\), admitting the canonical certificate comprising exactly \(n\) marks. This verifier is sound for the stated reflexive goals. Charge one unit per mark and allow the policy to emit the canonical certificate. With \(B=1\), a law concentrated on \(n=1\) gives \(K_B=1\), and a law concentrated on \(n=2\) gives \(K_B=0\) even for an optimal policy. The entire observation law is identical. This is a protocol-specific length argument.

**Equal spectra even for an optimal one-attempt policy.** Let the task protocol require guessing one valid certificate label in \(\{0,1,2\}\), with a single accepted label. The law of the label is uniform ex ante. The solver's evidence is a uniform signal \(X\), repeated unchanged in its observation stream. The two calibrated conditional laws of the label given \(X\) are
\[
P_+=\tfrac1{12}\begin{pmatrix}6&3&3\\3&6&3\\3&3&6\end{pmatrix},\qquad
P_-=\tfrac1{12}\begin{pmatrix}2&5&5\\5&2&5\\5&5&2\end{pmatrix}.
\]
Both matrices have unit row and column sums. The prediction span of the repeated signal has dimension three, and its entire marginal Hankel operator is identical in both experiments. Every other statistic of the marginal law is also equal. The task-labelled matrices have the same Gram matrix. Indeed \(P_{\pm}=J/3\pm\tfrac14(I-J/3)\) for the all-ones \(J\). The eigenvalues on the centred subspace have opposite signs and equal magnitude. The singular values are \(1,1/4,1/4\) for both. At unit budget the largest entry of each posterior row gives the optimal success, \(1/2\) versus \(5/12\). The verifier, label prior and unit cost are fixed. The signal-to-label coupling changed. Lean verifies the exact integer Gram and score statements independently of singular-value numerics.

The label protocol is an abstraction of a search where exactly one of several candidates can pass and the candidate choice uses the stated signal. Extending its optimal-policy model to unrestricted Lean proof search is a separate problem.

## K2 Cost and task-relevant spectral bounds

**Cost bounds.** Fix a binary proof encoding and a decidable certificate predicate. If reading or emitting a proof of length \(L\) costs at least \(L\), then \(K_B(P)\le\Pr[L_\Gamma(\phi)\le B]\) for policies that start without precomputed certificates. If every length-\(k\) string can be enumerated and checked for at most \(c(k)\) units including enumeration and verification, then exhaustive search guarantees \(K_B\ge\Pr[L_\Gamma(\phi)\le\ell]\) whenever \(B\ge\sum_{k=0}^{\ell}2^k c(k)\). A decision procedure for theoremhood would result from a total computable upper bound on \(L_\Gamma\) by statement size. Effective axiom enumerations can be certified by bounded transcripts included in the proof encoding. In a consistent effective arithmetic theory extending an essentially undecidable base such as Robinson arithmetic, this rules out such a bound. Kernel validation certifies derivability in the declared system. Soundness for an intended interpretation and novelty relative to previous work each need their own evidence.

**Top-\(m\) law.** Suppose exactly one certificate label is accepted, each distinct attempt costs \(c\), and failed attempts disclose only that the attempted label was wrong. At observation \(x\) let \(p_x\) be the calibrated posterior over \(q\) labels. With \(m=\min(q,\lfloor B/c\rfloor)\),
\[
K_B^*=\mathbb E_x\!\left[\sum_{j=1}^m p_{x,(j)}\right].
\]
For a deterministic policy the all-fail path determines the attempted set, and acceptance occurs precisely when the true label lies in that set. The \(m\) largest probabilities maximise its mass. Randomisation takes a convex combination of such successes. The probability ordering is classical in the related theory of guessing. [Arıkan](https://doi.org/10.1109/18.481781).

For the explicitly calibrated symmetric family \(P=J/q+\lambda(I-J/q)\), \(0\le\lambda\le1\), with uniform \(X\), the task-labelled singular values are \(1\) and \(\lambda\) of multiplicity \(q-1\). If \(m\ge1\), the law becomes \(K_B^*=m/q+(1-m/q)\lambda\), and \(K_B^*=0\) for \(m=0\). The sign and calibration assumptions distinguish this sufficient condition from the counterexample in K1.

**Robust bound from a labelled spectrum.** Let \(\mu(x)>0\) be the distribution of \(X\). Put \(A=\operatorname{diag}(\sqrt\mu)P\) for the matrix of posterior rows, take its best rank-\(r\) approximation in Frobenius norm, and rescale the rows. Project each resulting row onto the probability simplex in the Euclidean norm. Non-expansiveness of this projection towards the true row and the truncated SVD identity give
\[
\mathbb E_x {\rm TV}(p_x,\widetilde p_x)
\le \tfrac12\sqrt q\,\|\operatorname{diag}(\sqrt\mu)(P-\widetilde P)\|_F
\le \tfrac12\sqrt q\,\left(\sum_{i>r}\sigma_i(A)^2\right)^{1/2}.
\]
The first inequality is the \(\ell^1\)-to-\(\ell^2\) inequality followed by Cauchy–Schwarz for the probability law \(\mu\). Every policy's success changes by at most the left-hand side, because each all-fail path selects an event in label space. The optimal value changes by at most the same bound, and the regret of the policy optimised on \(\widetilde P\) on true \(P\) is at most twice that bound. The singular values here belong to a task-labelled posterior, with its singular vectors used for reconstruction and with calibration assumed. A generic Hankel tail supplies no label calibration.

## K3 Budget curve under the Riemann Hypothesis

Use the unary certificate protocol with task \(n\in\{1,\dots,N\}\), \(N\ge2\), chosen with probability \(\Lambda(n)/\psi(N)\). Here \(\Lambda\) is the von Mangoldt function and \(\psi(x)=\sum_{n\le x}\Lambda(n)\). With unit cost per mark and access to the task, the optimal curve is exactly
\[
K_B^*=\frac{\psi(m)}{\psi(N)},\qquad
m=\min(N,\lfloor B\rfloor),\quad B\ge0.
\]
Under RH, \(\psi(x)=x+O(\sqrt x\log^2(2x))\). Put \(E(x)=\psi(x)-x\). For sufficiently large \(N\), \(\psi(N)\ge N/2\), and
\[
\left|K_B^*-\frac mN\right|
=\frac{|E(m)-(m/N)E(N)|}{\psi(N)}
=O\!\left(\frac{\log^2(2N)}{\sqrt N}\right)
\]
uniformly in \(B\), taking \(E(0)=0\). The observation process may be the same constant process as in K1. The theorem concerns a specified arithmetic task law. Its only RH dependency is the classical error term, for which explicit constants are available. [Lee and Nosal, arXiv:2312.05628v4](https://arxiv.org/abs/2312.05628v4).

## A1 Predictive metric and fixed-trajectory GDN

Let \(0<\kappa<1\). On the part of the prediction quotient where
\(d_\kappa(x,y)=\sup_w\kappa^{-|w|}d(p(F_wx),p(F_wy))\) is finite, the common-input map \(F_a\) is \(\kappa\)-Lipschitz. For a continuation \(w\) after \(a\), its term is \(\kappa\) times the term for the prefixed word \(aw\), and the supremum over such words is bounded by the full supremum. A uniform quantisation perturbation of at most \(\epsilon\) in this metric gives \(e_t\le\kappa^t e_0+\epsilon(1-\kappa^t)/(1-\kappa)\) by the triangle inequality and induction. Permanent, detectable differences may give infinite distance. Composition can be noncommutative while multiplication of scalar observation functions remains pointwise and commutative. Predictive equivalence is related to [Shalizi and Crutchfield](https://arxiv.org/abs/cond-mat/9907176).

Fix all \(k_t,q_t,\alpha_t,\beta_t\) in the row-state recurrence \(S_t=S_{t-1}A_t+B_t\), \(A_t=\alpha_t(I-\beta_t k_tk_t^\top)\), \(y_t=S_tq_t\). The response across a cut factors through the state at that cut. The finite trailing Gramian satisfies
\[
M_t=q_tq_t^\top+A_{t+1}M_{t+1}A_{t+1}^\top,
\quad M_T=q_Tq_T^\top.
\]
For one state error \(R_t\) at the cut, expand the subsequent readouts to obtain total squared error \(\operatorname{Tr}(R_t M_t R_t^\top)\). With several perturbations, their future responses add before squaring. Cross terms can increase or cancel the energy, as the aligned and alternating controls show. An unknown query outside the calibration span can expose errors with zero measured energy. Two nonorthogonal nonparallel key directions in two dimensions give projectors with no common invariant line. A common change of state coordinates by an orthogonal matrix preserves the exact input–output operator and its Hankel singular values when the transitions, injections and readouts are all transformed. The GDN architecture is described by [Yang et al.](https://arxiv.org/abs/2412.06464).

The vector representation of \(\operatorname{Spin}(8)\) has image \(\operatorname{SO}(8)\). The vector-level rotation candidates already range over that orthogonal group. Quantisation is a separate nonlinear step whose error depends on the chosen coordinates and scales. Whether triality changes feasible representations, error or speed beyond matched \(\operatorname{SO}(8)\) baselines remains an empirical and mathematical question. The finite fixed-trajectory Hankel rank characterises an associated linear realisation problem. It does not establish a minimal memory dimension for a whole nonlinear model.

## I3 Information and physically testable claims

Under \(I(M;Y\mid C,X)=0\), both chain-rule expansions of \(I(M;X,Y\mid C)\) give \(I(M;X\mid C)=I(M;Y\mid C)+I(M;X\mid C,Y)\). This is an identity about a specified joint law. In CIK the information needed to identify a target, the computation needed to find an accepted proof, and the physical evidence for an information channel have distinct experimental requirements. Extra-dimensional and retrocausal examples here specify artificial distributions or operators for negative controls. Physical channel claims would require separately designed interventions and observations.
