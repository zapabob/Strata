# Triality and scaled ternary quantisation of Inkling 2 Mini

## Construction

Let the real octonion coordinates be ordered as (1,e_1,ldots,e_7). The multiplication table in spin8_clifford.py fixes the orientation. Write (L_i) for left multiplication by the eight basis octonions in this order, with (L_0=I). On the real sixteen-dimensional module take

\[
\Gamma_i=\begin{pmatrix}0&-L_i^{\mathsf T}\\ L_i&0\end{pmatrix}.
\]

Polarisation of norm multiplicativity gives (L_i^{\mathsf T}L_j+L_j^{\mathsf T}L_i=2\delta_{ij}I), with the corresponding identity for right transposes. Therefore (\Gamma_i\Gamma_j+\Gamma_j\Gamma_i=-2\delta_{ij}I). The integer implementation checks all 64 ordered pairs. The volume element (\omega=\Gamma_0\cdots\Gamma_7) squares to the identity and anticommutes with every generator. Its two eigenspaces each have dimension eight. Their ordered coordinate columns define (B_+) and (B_-). Every even product commutes with (\omega).

## Lift and trilinear invariant

The normalised Sylvester matrix (H_8) has determinant (+1). Successive unit Householder normals reduce its columns to the ordered coordinate vectors. The product of the reflections reproduces the requested vector action. A reflection with normal (u) acts as minus conjugation by (\Gamma(u)). With an even number of reflections these signs cancel. The implementation checks the determinant before decomposition, checks even parity afterwards and recovers the vector representation by Clifford conjugation. A fixed column order and a fixed reflection sign convention select one of the two lifts.

For the lifted matrix (G), put (R_+=B_+^{\mathsf T}GB_+), (R_-=B_-^{\mathsf T}GB_-) and (c(v)=B_-^{\mathsf T}\Gamma(v)B_+). Conjugating Clifford multiplication gives (c(R_Vv)R_+=R_-c(v)). The Euclidean pairing (T(v,p,m)=m^{\mathsf T}c(v)p) is consequently invariant. Testing its 512 coordinate entries checks the entire trilinear form. This construction uses three actions of one group element. It makes no identification of vector and spinor coordinates by an outer automorphism. A change of chiral basis conjugates the corresponding matrix and can affect a coordinate-dependent quantiser. The experiment includes a conjugated positive-spinor control. [Schray and Manogue](https://arxiv.org/abs/hep-th/9407179)

## Continuous coordinates and physical operators

Order the 28 planes lexicographically by (0\le i<j<8). The search uses a chart about the verified Hadamard lift (G_H),

\[
G(\theta)=G_H\exp\left(\tfrac12\sum_{i<j}\theta_{ij}\Gamma_i\Gamma_j\right).
\]

The vector infinitesimal sends (e_i\) to (e_j\) and (e_j\) to (-e_i\). Restriction to each chiral eigenspace gives its spinor infinitesimal. All three infinitesimal maps have rank 28. Both chiral actions cover the connected group SO(8), as does the vector action. The independent continuous searches therefore have the same attainable rotations. Sharing one parameter vector across Gate/Up and Down, or across visits, restricts the joint choices. Whether this restriction improves generalisation is empirical.

For a 128-coordinate group take (R=H_{16}\otimes R_r). At the origin the vector candidate equals (H_{128}). For row-stored inputs the two transformed arrays are (WR^{\mathsf T}) and (XR^{\mathsf T}). Their product is (WX^{\mathsf T}). Gate and Up share the input coordinates. Down has its own transform after the nonlinear gate. The residual, router and cross-pass message vectors stay in their native coordinates. Mixed partitions must exactly cover the physical input width.

## Ternary optimisation

Each 128-weight group contains an FP16 scale and 32 packed bytes. The little-endian scale precedes four two-bit symbols per byte, starting at the least significant pair. Codes 0, 1 and 2 correspond to (-1,0,+1). The encoder measures the fourth physical code separately. [PrismML format description](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/MODEL-FORMATS.md)

For a diagonal empirical second moment with non-negative entries (h_i), the nearest symbol at fixed positive scale is determined by (|w_i|>\alpha/2). An optimum is therefore represented by a prefix of the magnitudes sorted in descending order. On each prefix the continuous optimal scale is the weighted mean magnitude. Rounding that mean to the nearest admissible binary16 value minimises the quadratic on the same prefix. Comparing the resulting scores together with the all-zero solution yields the optimum for the diagonal surrogate.

For correlated inputs the experimental estimator accumulates (C_b=\sum_v\lambda_v X_{v,b}^{\mathsf T}X_{v,b}/n_v) one group and visit at a time with normalised visit weights. For fixed codes the optimal non-negative scale is the binary16 rounding of (t^{\mathsf T}C_bw/(t^{\mathsf T}C_bt)), subject to the representable range. Updating one ternary coordinate at fixed scale has three possible values. The implementation scores the coordinate minimiser and rejects any sweep that increases the stored-scale objective. This procedure has a monotonicity guarantee and no assertion of global optimality. Candidate selection additionally measures the full output residual on observed sequences, including correlations between groups.

## Evaluation and scope

Rotation search and fallback decisions use calibration sequences. The research runner writes its selection lock before opening held-out sequences. It evaluates independent weight rows on those unseen sequences. A physical expert shares its stored weights across visits. The calibration record retains route counts for each visit, including zero counts. Paired intervals identify their resampling unit. A numerical identity, a local kernel timing and a change in model perplexity are distinct claims.
