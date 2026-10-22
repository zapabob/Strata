# Integrated Triality Attention: mathematical contract and implementation map

This is an experimental Attention operator with a norm-preserving query
adapter and a three-view compressed-key estimator. It does not establish a
better Transformer, a quality gain, or a speed gain on either required model.
The original model weights stay unchanged. The existing off path stays the
baseline. Component validation and full-model acceptance are separate gates.

## Operator order

For a query head belonging to KV group h, let q be the model-normalized query.
The version-3 controller has rank eight and includes both biases:

\[
a=W_{out}\tanh(W_{in}q+b_{in})+b_{out},\quad
u=\frac{\tau a}{\sqrt{\tau^2+\|a\|^2}},\quad
c=\frac{(1,u)}{\sqrt{1+\|u\|^2}},\quad \tau=\tan(\pi/8).
\]

The production Clifford convention defines seven skew generators J_a obeying
J_a J_b+J_b J_a=-2 delta_ab I. In each complete block of eight,

\[
A(c)=c_0I+\sum_{a=1}^7 c_aJ_a,\qquad q'=A(c(q))q.
\]

The head shares one c across its complete blocks; a shorter tail is copied.
Apply the model's existing positional map P_t to q' next. Apply the original
K normalization and positional map P_j to keys independently. Only then apply
the codec transform U_r=B_r F, where B_r comes from the same ordered Spin lift
in the vector/plus/minus representation. F is the explicitly versioned signed,
normalized Hadamard sequence. Its inverse reverses factor order. No additional
Hadamard is implicitly inserted by the generic codec.

For k_j in these positioned coordinates, store three packed K views and one V:

\[
\hat k_{jr}=U_r^T\mathcal Q_r(U_r k_j),\quad
\bar k_j=\sum_r\alpha_r\hat k_{jr},\quad e_j=k_j-\bar k_j.
\]

Let x=P_t q'. With a shared residual sketch, the logit before bias/mask is

\[
s_j=\sigma\left[
\sum_r\alpha_r(U_rx)^T\mathcal Q_r(U_rk_j)
+\beta\sqrt{\pi/2}\frac{\|e_j\|}{m}
\operatorname{sign}(Ge_j)^TGx\right].
\]

Preserve the model's sigma, biases and mask. Compute softmax once, then one
product with the shared decoded V. Alpha/U/G are fixed within the KV-group
profile; c is query dependent. Beta is zero by default. A changed adapter or
profile invalidates downstream recurrent state as well as Attention caches.

## Exact identities and their boundaries

The generator relations give A^T A=(sum c_a^2)I=I. Since c varies continuously
from e0 in this chart, det A=+1. Setting Wout=bout=0 gives c=e0 and A=I exactly.
The chart derivative at a=0 is the seven tangent axes with unit scale. It is
not compatible with silently reinterpreting the older exponential-chart
parameters. The seven-parameter family is not all SO(8) and is not a subgroup.
The learned controller is not automatically Spin-equivariant.

For one complete block y, skew symmetry also gives

\[
\|A(c)y-y\|^2=2(1-c_0)\|y\|^2.
\]

Thus the adapter's displacement is bounded by its chart angle. This identity
concerns the same y and its transform. It does not assert that different
queries preserve their inner product, or that the query-dependent Jacobian
is orthogonal. No token-wise scalar rescaling replaces the model's Attention
scale. Tails contribute to the controller input even when copied unchanged.

With quantization removed, each view gives x^T k_j because U_r is orthogonal;
convex alpha then reproduces exactly the same logits in exact arithmetic.
For nonidentity A this reference is Attention using q', not the original
unmodified query. Identity initialization is required for original-model
equivalence. Floating-point tolerances and quantization errors are measured
separately.

The normed tensor, rather than an arbitrary invariant trilinear form, is the
required mathematical basis. See [Baez's Spinors and Trialities](https://math.ucr.edu/home/baez/octonions/node7.html).
The original residual-sketch construction is described in
[TurboQuant v1](https://arxiv.org/html/2504.19874v1); this combined operator is
our proposed extension, not a claimed result from that paper.

## Error objective and memory comparison

Use per-query output sensitivities p_j(v_j-o) to form each view's first-order
error vector, including the common V perturbation once. Fit fixed simplex
alpha on calibration data using the actual cross-view error covariance.
Triality does not imply uncorrelated quantization errors. The implementation
uses direct residual comparisons and streaming QR rather than a normal
equation that squares the condition number. Rebuild residual sketches after
changing alpha. Select beta with actual outputs at a matched total memory
budget; independent-Gaussian unbiasedness is not a softmax guarantee.

The training objective uses detached teacher outputs and distributions,
normalized output MSE and KL(teacher||student). Bounded row recomputation
avoids a token-square matrix. The analytic controller VJP includes both
the direct A^T path and the query's influence on c. Training/calibration,
method selection and final evaluation must use disjoint data.

For illustration only, the generic reference layout at width256 with three
2-bit K views and one 2-bit V uses 256 payload bytes plus four FP64 norms,
or 288 bytes per KV-head/token. A single 4-bit K plus 4-bit V in the same
reference dialect uses 272 bytes. Equal payload bits are therefore not an
equal total budget. At 16 full-Attention layers, four KV heads and 32768
tokens, the first layout's row arrays alone total 576 MiB, before transform
matrices, codebooks, adapter weights, allocator reservations and scratch.
Active QJL additionally stores ceil(m/8) sign bytes and an FP64 residual norm
per key plus shared G. These are arithmetic layout estimates, not measured
VRAM figures or legacy Bonsai/TheTom format sizes. Recurrent-state storage
is additional and is not compressed by this operator.

## Uniform cache movement

For a common proper S applied to every selected logical key,
q^T S khat=(S^T q)^T khat. The external transport plan canonicalizes the query
once, leaving all physical cache bytes untouched. The existing residual
sketch becomes sign(Ge)^T G S^T q with unchanged residual norm. This does not
recover sign(GSe), which old sign/norm data generally cannot determine.
New logical keys must be canonicalized by S^T before append. Per-row different
S, real position metadata, MRoPE sections, cache persistence and the effect
of rerunning a hybrid recurrent model remain separate integration work.

## Current implementation and evidence

spin8/query_v3.h provides the audited basis, rational chart, immutable CPU
controller and analytic VJP. tqcodec provides actual packed three-K/shared-V
storage, optional shared residual QJL, fixed-alpha calibration, bounded
distillation and uniform transport. The transport-inclusive CPU reference
suite passed 8/8, including the pure-C ABI smoke. The optional v3 CUDA API now
fuses the controller, rational chart and block transform into one kernel,
sharing one parameter set per call. Spin8 CPU/C/CUDA CTest passed 8/8; new-kernel
memcheck reports0 errors and racecheck0 hazards. GPU VJP, multi-controller head
batching, GPU codec and qualified v3 model graphs remain separate work.

The private Prism GGML builder now batches all heads, blocks and tokens with
standard operators. Its CPU test passed against the pinned73bfe6cc GGML and
core F64 oracle, including256x24x2 contiguous/strided queries: maximum absolute
error4.32440864e-07 and maximum59 graph nodes. This removes the initial proposed
head-by-block graph expansion; it is not a throughput measurement. The helper
is not wired into llama_context or qwen35 inference. Exact-payload admission,
device error enforcement and output rejection before Attention/cache use are
mandatory future runtime obligations. Only OFF is pointer/bit exact.

The synthetic one-head training example reduced training loss but increased
held-out loss; its weights were rejected. The real zapabobouj 27B passed three
short baseline smoke cases on the existing Prism binary. It has not passed
the new operator's model acceptance. The frozen large Q2_0 is being acquired,
and the pinned Prism CUDA build is incomplete. TheTom real-model validation,
sidecars, real layer captures, periodic deployed-data audits and both-model
paired performance/quality acceptance remain open. See the v3 integration
record for exact logs, negative results and current limitations.
