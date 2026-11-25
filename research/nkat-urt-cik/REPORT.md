# Predictive structure and budgeted proof discovery

NKAT–URT–CIK research report, 25 November 2026 JST.

## Abstract

Finite prediction statistics do not determine the chance of finding a verified proof within a fixed budget. We give two counterexamples and a conditional result. With a uniform prior and a single verification attempt, two calibrated, three-label posterior kernels have identical Gram matrices and different optimal success probabilities, \(1/2\) and \(5/12\). An exact Lean check certifies the algebraic witness. With a known, calibrated posterior and a uniform verification cost, success is the expected posterior mass of the top affordable candidates. A tail bound follows for a task-labelled low-rank approximation. We also prove a finite causal KL projection, examine a quantum-comb repair, and give a rational Hankel rank certificate. Synthetic GDN and real Qwen3.8-27B diagnostics illustrate how much the resulting claims depend on the observed task and execution path.

## 1. Reproducibility and audit scope

The primary Strata checkout was on `main` and matched the remote main during the initial read-only check. The working tree contained ongoing CUDA, SSD scheduling and launcher work. The existing `research/tsi-verified-evaluation` worktree held the TSI specification and PWS tools as local work. This study keeps its implementation under this research directory. The separate Phase 3 handover identifies the files that Neon can reuse.

Lean 4.29.0 and its standard library are pinned. No mathlib dependency is needed by this batch of theorems. Thirteen theorem declarations were kernel-checked. Their dependency report includes only `propext` and `Quot.sound` where used, with several declarations requiring no axioms. Python 3.12.10 and NumPy 2.5.5 ran the CPU experiments. Rational arithmetic supports the finite score and noisy rank witnesses. The Choi matrix and GDN computations are floating-point checks with an explicit tolerance, separate from their mathematical derivations.

The October boundary-response supplement was available. It derives a residual certificate for a specified two-rotor Hamiltonian and states additional hypotheses for passing a gap to a thermodynamic limit. Its residual-check discipline motivates the finite CIK checks. The Li–Weil and RH criteria audit filenames were absent from the checked Downloads, Strata and TSI worktree paths. The comb normalisation and finite-word comparison were cross-checked against the primary works. [Quantum networks](https://arxiv.org/abs/0904.4483), [finite-word quantum equivalence](https://arxiv.org/abs/quant-ph/0604085).

## 2. Causality and inference

For exogenous finite intervention words, the causal KL projection has a simple history-weighted orthogonality identity. The history law must be the one induced by the original \(P\). The counterexample gives a gap of zero under \(P\) and \(\log(2)/2\) under the projected history law. The observational feedback and selection controls each produce \(\log 2\) of spurious future dependence. The associated interventional and unselected versions give zero. In feedback settings, a causal model requires the intervention and feedback protocol as part of the experiment. [Massey’s directed-information paper](https://www.isiweb.ee.ethz.ch/archive/massey_pub/pdf/BI532.pdf).

In the two-slot complex Choi fixture the constraint residual fell from \(0.35865\) to \(5.42\times 10^{-17}\) after repair. Its minimum eigenvalue was \(0.03296\). The measured trace-norm distance to the repaired state was \(1.36447\), within the analytic range \([0.11341,1.80514]\) formed by the lower bound and the repair upper bound rounded outwards. An optimal strategy-norm repair remains an open question.

A qubit effect span reached real dimension four after one letter, and the next stage was stable. Padding with an unobserved qubit gave the same finite Hankel section and no distinguishing word in the numerical paired-span closure. A changed reduced state produced a length-one witness. The separate exact rational certificate verified a three-by-three block at spectral data error \(1/100\), and rejected the equality-at-threshold negative control. In the three repeated-label example, the rank bound gives dimension at least two. Positive quantum realisation needs dimension three because three post-measurement states are perfectly distinguishable. The finite proofs and their assumptions are in [THEOREMS.md](THEOREMS.md).

## 3. Knowledge discovery at fixed cost

Use \(K_B=\Pr[T\le B]\), with \(T\) the cost to an independently accepted proof and \(T=+\infty\) upon failure. Conditions of a particular experiment include the verifier, representation, task law, policy and cost accounting.

An observation-only Hankel spectrum can remain identical while the distribution of minimum proof lengths changes. A stronger instance keeps a fixed uniform label prior and gives the policies the same marginal observation process. The two task-labelled posterior matrices have the same Gram matrix. For unit verification cost, the exact optimal curves are as follows.

| Available attempts | Positive centred eigenvalue | Negative centred eigenvalue |
| --- | ---: | ---: |
| 0 | 0 | 0 |
| 1 | 1/2 | 5/12 |
| 2 | 3/4 | 5/6 |
| 3 | 1 | 1 |

The difference at one attempt survives even if an estimator can see the full Gram matrix. Both channels have singular values \(1,1/4,1/4\) and the same prediction span. In the calibrated symmetric family with known non-negative centred eigenvalue \(\lambda\), the optimal curve is \(m/q+(1-m/q)\lambda\) when \(m\ge1\). For more general labelled posteriors, reconstruct from weighted singular vectors before applying the singular-tail guarantee. In the rank-one fixture the measured mean total variation was \(1/6\), below the derived upper bound \(0.17678\).

For an explicitly RH-conditional extension, give a unary task indexed by \(n\le N\) probability \(\Lambda(n)/\psi(N)\) and charge its canonical proof length. Its exact success probability is \(\psi(\min(N,\lfloor B\rfloor))/\psi(N)\). Assuming RH, the uniform-in-budget deviation from the uniform-task curve is \(O(\log^2(2N)/\sqrt N)\). The sample computations at \(N=10^3,10^4,10^5\) had deviations \(0.01415,0.00601,0.00207\), respectively. These are finite calculations of the chosen prior. The asymptotic argument uses the prime-counting error estimate. [Lee and Nosal](https://arxiv.org/abs/2312.05628v4).

## 4. GDN and Strata

For an eight-dimensional synthetic GDN trajectory, explicit propagation and the finite Hankel factorisation agreed within \(5.56\times 10^{-16}\). A common orthogonal coordinate change preserved the exact observation matrix to \(3.56\times10^{-15}\). Four-bit quantisation with one 32-bit scale per eight coordinates had effective cost eight bits per coordinate. The future readout error energies were \(0.07567\) with the identity, \(0.50617\) with the Hadamard rotation, and \(0.07301\) with a seeded \(\mathrm{SO}(8)\) rotation. Different signs of two equal-magnitude residuals yielded energies \(4.24\) and \(1.04\). A calibration-only Gramian can miss a new query direction entirely. These checks use frozen queries and keys. [Gated Delta Networks](https://arxiv.org/abs/2412.06464).

The real-model diagnostics used the same local Qwen3.8-27B mixed-IQ weights, the installed SM120 native engine built with CUDA 13.5, RTX 5060 Ti 16 GB, and Ryzen 5 4500. Both KV cases used 4,096 context capacity, 16 fixed prompt IDs and the same 32 forced completion IDs. The comparison covered 33 aligned logit rows across all 248,320 vocabulary entries. Observed minimum free VRAM is a whole-device reading. [Model card](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf).

| Fixed-token diagnostic | F16 KV | Spin(8) K8V4 |
| --- | ---: | ---: |
| KV payload | 256 MiB | 104 MiB |
| Minimum device free VRAM | 3,304 MiB | 3,541 MiB |
| Decode forward only | 30.23 tok/s | 30.95 tok/s |
| End-to-end diagnostic time | 1.512 s | 2.238 s |

Spin(8) reduced the KV payload by 59.4%. Top-1 agreement was 31/33, full-vocabulary mean KL was 0.10485 nats and the maximum row KL was 1.96014 nats. The single instrumented pair shows a memory saving and a longer end-to-end diagnostic for this fixture. The matched archive keeps both timing components. Weight quantisation and GDN-state quantisation were held fixed in these hardware runs. The separate synthetic state experiment tests GDN-state quantisation.

A serial A–B–B–A run on the same 16 prompt IDs and 64 generated tokens compared F16 KV with MTP disabled to F16 KV with a draft cap of three. The mean end-to-end times were 2.395 s and 4.640 s respectively, equivalent to 26.72 and 13.79 emitted tokens per second over the measured request. Both MTP runs diverged from the baseline token sequence. The cap-three candidate fails the speed and parity gate for this workload. The reported decode step counter counts internal forwards, including speculative work. [Run summary](evidence/q38-mtp-ab.json).

The quantised checkpoint fits as a GPU trunk and a bounded host embedding. Its 12,599,187,808 logical file bytes and 27,320,697,856 stored tensor elements give 3.6893 effective bits per element, including GGUF metadata and the stored MTP tensors. The first concurrent acquisition and generation attempt hit a 300-second timeout during loading. The separate F16 run completed in approximately 169 seconds including process start, load and generation. Warm paired tests finished much sooner. The BF16 text GGUF is 53,808,282,240 bytes, or 50.11 GiB, and exceeds the machine's installed RAM and VRAM combined. The separate capacity probe targeted file-mapped CPU and CUDA placement. Its download wait expired following repeated HTTP 408 responses. A CPU header inspection could not open the active partial file. BF16 throughput and steady-state SSD traffic remain unmeasured. The native Q38 loader's current interface places the weight arena on the GPU. [Dense native design](../../docs/QWEN38_DENSE_NATIVE.md), [BF16 file source](https://huggingface.co/ggml-org/Qwen3.8-27B-GGUF).

The later Hy4-Flash branch used the real BF16 expert and output adapter for a minimum-distortion projection, then generated a PrismML PQ2_0 GGUF tensor fixture. Paired vector and half-spinor bases were verified through the octonion triality relation. CPU and CUDA ran the stored expert and its transformations. The held-out error remained at approximately 36.1% relative to BF16 after the adapter. [Hy4 geometry and GGUF report](../hy4-bonsai2/REPORT.md).

Long-context task success, quality after weight compression, and internal state compression on the real model require further paired trials. They remain open in the ledger. A causal or quantum certificate applies to the finite model and interventions specified in its proof. The higher-dimensional examples remain mathematical thought experiments.

## 5. Application to AI Scientist and next measurements

A scientific discovery run would specify a task suite, cumulative wall time, token and verification budgets, and a verifier with an immutable interface. Measure accepted proofs and time-to-first accepted proof over the same held-out tasks for every proposal policy. Include failed, invalid and timed-out attempts in the denominator. A proof kernel check establishes derivability under declared assumptions. The separate novelty check needs a literature and theorem-library comparison. The predictive statistic needed by the K2 guarantee is calibrated evidence about the verifier's actual acceptance events. An unlabelled activation spectrum can guide experiment selection. [The AI Scientist](https://arxiv.org/abs/2408.06292), [ShinkaEvolve](https://arxiv.org/abs/2509.19349).

For deployment, verify physical SSD bytes per generated token at steady decode, cold and warm. Run one GPU evaluation at a time, with identical token sequences for numerical comparison. A practical profile requires an independently measured speed and quality improvement for its task class. The [Phase 3 handover](../../_docs/2026-11-25_nkat-urt-cik-strata_Codex.md) gives the resource floors, baseline selection and order of work.

## Reproduce the finite checks

From the Strata checkout in PowerShell

```powershell
$elan = "$env:USERPROFILE/.elan/bin/elan.exe"
& $elan run leanprover/lean4:v4.29.0 lean research/nkat-urt-cik/lean/CIK.lean
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
uv run --no-project --isolated --python 3.12 --with numpy==2.5.5 python research/nkat-urt-cik/experiments/run.py --output H:/Strata/evidence/cik-reproduction
```

The saved [CPU results](evidence/results.json), [budget CSV](evidence/knowledge_budget.csv), [Lean kernel log](evidence/lean.log) and [real-model comparison](evidence/q38-kv-pair.json) accompany this report. [CLAIM_LEDGER.md](CLAIM_LEDGER.md) records the mathematical, Lean and experimental status of each claim.
