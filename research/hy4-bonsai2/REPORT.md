# Hy4-Flash expert quantisation with PrismML PQ2_0

25 November 2026 JST. The pilot encoded a 1,536 × 1,536 routed expert down-projection from Tencent's BF16 checkpoint with the locally installed PrismML 0.4.1 `ggml-base.dll`. The PrismML decoder read the output. A GGML graph using the same bytes executed routed matrix multiplication with the matching signed transform on both the Ryzen 5 4500 and GeForce RTX 5060 Ti. No complete runnable Hy4-Flash checkpoint was produced. [Tencent checkpoint](https://huggingface.co/tencent/Hy4-flash), [PrismML formats](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/MODEL-FORMATS.md).

## Payload and accuracy

The program verifies GGML type ID 142 and a 34-byte block for 128 weights through the DLL API. It retrieves the first expert of `model.layers.1.mlp.experts.down_proj` with verified HTTP byte ranges. The original tensor sample is 4,718,592 bytes. The quantised sample is 626,688 bytes, or 2.125 bits per weight including its FP16 scales.

PrismML's folding interface uses an input-side signed Walsh–Hadamard transform. This experiment uses 512-wide blocks so three blocks fit a 1,536-wide expert without padding. PrismML's `ggml_quantize_chunk` and `dequantize_row_pq2_0` handle the byte format in every PQ2_0 row below. The fitted case applies a local groupwise ternary least-squares fit before that encoder. The estimate uses the weights and assumes isotropic activation energy. The 48 Gaussian test vectors are synthetic. [PrismML checkpoint caveat](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/main/KNOWN_ISSUES.md#runtimes-other-than-the-prismml-build).

| Encoding | Bits per weight | Relative output L2 error against BF16 |
| --- | ---: | ---: |
| PQ2_0 without rotation, PrismML reference scaling | 2.1250 | 76.08% |
| PQ2_0 with signed H512, PrismML reference scaling | 2.1250 | 77.08% |
| PQ2_0 with signed H512 and a fitted ternary scale | 2.1250 | **43.42%** |
| Strata S1.5 with H64 | 1.8125 | 43.01% |
| Strata S2_K with H64 | 2.1875 | 33.96% |
| Strata S3_K with H64 | 3.1875 | 18.32% |
| Strata S4_K with H64 | 4.1875 | 9.45% |

The Strata rows are local codec controls with no activation calibration. A blind switch of this expert from S2_K to the fitted PQ2_0 sample saves 2.86% of its bytes and raises output error by 9.46 percentage points. The result gives no model-quality basis for an all-expert conversion. Calibrating the expert selection and ternary fit on held-out activations is required to test the quality constraint.

The second trial routed Gaussian latent inputs through the original BF16 gate/up tensor and its clamped SwiGLU computed in FP32. The first 256 columns supplied per-feature mean squared energy in the rotated basis. On the independent 256 columns, the weight-only fit gave 40.04% output error and the activation-weighted fit gave 40.02%. S2_K gave 30.94% on those same columns. The diagonal calibration left a 9.08-point gap in this fixture.

## Routed computation

The two weight specimens, original and directly projected, were repeated across 16 expert slots. Each token used a distinct seeded ordering of those slots and a separate activation for each slot. The timed graph included the sign multiplication, Hadamard transform and `MUL_MAT_ID`. Measurements are medians of seven synchronous calls after three warm-up calls with all tensors resident. Transfer, SSD reads, routing logits, the rest of the model and sampling were outside this timed region.

| Device | Input tokens per call | F16 (ms) | PQ2_0 (ms) | PQ2_0 arithmetic error against its F32 decode |
| --- | ---: | ---: | ---: | ---: |
| Ryzen 5 4500, six threads | 1 | 6.6562 | 13.1471 | 0.708% |
| Ryzen 5 4500, six threads | 16 | 20.2131 | 12.3028 | 0.695% |
| RTX 5060 Ti, CUDA SM120 | 1 | 0.2282 | 0.0772 | 0.536% |
| RTX 5060 Ti, CUDA SM120 | 16 | 0.3445 | 0.0708 | 0.535% |

The CUDA result is 2.96× faster at one token, and the CPU result is 1.98× slower in that case. Against the F16 graph, the PQ2_0 output differed by about 43% on both backends. Arithmetic agreement with its own decoded weights tests the operator implementation. The difference from the F16 graph tests the cost of the compression.

## Direct weight projection

For a unit vector \(u\) in the 1,536-dimensional expert output space, the detached FP32 matrix was changed to \((I-uu^\top)W\) and saved. Its leakage \(\lVert u^\top W'\rVert_2/\lVert W'\rVert_F\) was \(7.59\times10^{-9}\). The PQ2_0 round trip raised the proportion to \(1.071\times10^{-2}\). A projection after decoding brought it to \(6.15\times10^{-9}\). The direct edit changed the output on the synthetic vectors by 2.43%. The tested direction was drawn from a seeded random distribution. A behavioural direction requires telemetry and paired evaluation on benign prompts with false refusals, ordinary tasks and safety controls.

Let \(A\) be the expert's output adapter and take \(G=A^\top A+\lambda I\) with \(\lambda>0\). Fix the constraint \(u^\top W'=0\). For every input \(x\), write \(e=(W'-W)x\). The constraint gives \(u^\top e=-u^\top Wx\). Cauchy–Schwarz in the \(G\) metric gives \((u^\top e)^2\le(u^\top G^{-1}u)(e^\top Ge)\). Put

\[
v=\frac{G^{-1}u}{u^\top G^{-1}u},\qquad W_\star=(I-vu^\top)W.
\]

Since \(u^\top v=1\), \(W_\star\) satisfies the constraint and attains equality for every input. This minimises the regularised output distortion \(\lVert Ae\rVert_2^2+\lambda\lVert e\rVert_2^2\) for any distribution of inputs with finite second moments. If the input second moment is positive definite, the minimiser is unique. The method only assumes a supplied direction and a fixed linear output metric.

Using the source model's BF16 routed-up adapter, the measured regularised squared loss on 256 independent gated inputs was 22.43098, equal within floating-point precision to the lower bound. The ordinary orthogonal projection gave 43.86594. The following table uses relative L2 after the adapter against the BF16 reference, without the ridge term in the reported error.

| Specimen | Relative hidden-output L2 | Axis leakage |
| --- | ---: | ---: |
| Ordinary orthogonal projection | 2.205% | \(2.19\times10^{-17}\) |
| Metric projection, saved FP32 | **1.577%** | \(6.49\times10^{-10}\) |
| Metric projection, saved BF16 | 1.584% | \(8.06\times10^{-5}\) |
| Metric projection, PrismML PQ2_0 | 36.462% | \(1.07\times10^{-2}\) |
| PQ2_0 with FP64 application of the projection formula after decode | 36.458% | \(1.52\times10^{-17}\) |
| PQ2_0 with rank-32 FP16 correction and projection after decode | 33.586% | \(1.52\times10^{-17}\) |

For the rank test, let \(G=LL^\top\) and \(Q\) be the decoded PQ2_0 matrix. The projected residual is \(R=W_\star-(I-vu^\top)Q\). By the Eckart–Young theorem the best rank-\(r\) correction in this weighted Frobenius norm is \(L^{-\top}[L^\top R]_r\), where the brackets mean truncated SVD. Its columns lie in the constraint plane because the retained weighted singular vectors lie in the transformed residual column space. Rounding the factors to FP16 can perturb that property. The numerical test reapplies the projection to the corrected output using FP64. Including FP32 direction and projection vectors, stored signs and both FP16 factors, the rank-32 variant used 2.839 bits per weight before file framing. Its factors are available for evaluation. Their inference latency and whole-model quality are unmeasured.

A behavioural trial compares the original BF16, quantisation alone and quantisation with the fitted direction applied. The prompt IDs, decoding parameters and scoring remain fixed. Record answers, false refusals and exact task success on held-out, benign examples. The present experiment verifies the local projection and compression errors on synthetic inputs. Identifying a refusal direction remains open.

## Spin(8) triality and GGUF evaluation

Identify the three eight-dimensional representation spaces with the real octonions, and let \(L_z\) denote octonion left multiplication by \(z\). The matrix \(\Gamma(z)=\left(\begin{smallmatrix}0&L_z^\top\\ L_z&0\end{smallmatrix}\right)\) has square \(\lVert z\rVert^2 I\). Polarisation gives the Euclidean Clifford relation. For unit \(a,b\), the even product \(\Gamma(a)\Gamma(b)\) has half-spin actions \(S_+=L_a^\top L_b\) and \(S_-=L_a L_b^\top\). Its vector action is the product \(V=R_a R_b\) of hyperplane reflections. Conjugation of \(\Gamma(z)\) gives \(L_{Vz}S_+=S_- L_z\). Thus all three actions come from the same Spin(8) element. The signed octonion table passed the Clifford anticommutator check on all 64 ordered pairs of basis vectors in integer arithmetic. [Baez, *The Octonions*](https://arxiv.org/abs/math/0105155).

In each eight-coordinate output block, choose the second reflection to send the normalised block of \(u\) to the scalar basis vector and the first reflection to fix that vector. The measured triality intertwiner defect was \(5.55\times10^{-16}\). After the vector action, 192 coordinates carried the synthetic direction, down from 1,536. The maximum component outside those coordinates was \(2.78\times10^{-17}\). With the block vector action \(V\) on outputs and a paired half-spin action \(S\) on inputs, store the transformed matrix \(VW_\star S^\top\). Before quantisation, \(V^\top(VW_\star S^\top)(Sx)=W_\star x\). For quantised weights, both forward and inverse changes of basis belong in the graph.

On 256 selection inputs, the negative half-spin branch with signed H512 was the strongest of the four half-spin candidates. On 256 different, gated inputs the selected branch gave 36.085% output L2 error against BF16 after the learnt adapter. The matched signed-H512 control gave 36.079%. Using the half-spin branch improved over the vector-only rotation with H512, which scored 36.222%. The full comparison therefore shows axis localisation and no accuracy gain over the ordinary H512 reference in this expert. The code and the receipts retain both half-spin branches and the vector-only controls. These representation spaces are numerical coordinates for the experiment.

The GGUF v3 fixture is `Hy4-Bonsai2-Expert-PQ2_0-Pilot.gguf` with six tensors and 5,986,816 bytes. It contains the selected PQ2_0 expert, the H512 PQ2_0 control, the original BF16 expert, and axis, projection and sign vectors. The vendor Python reader matched the original bytes for all three weight tensors. The separate native `llama-gguf` reader parsed all six tensors and reported both exact weight types. The benchmark parsed the GGUF again before constructing the resident GGML expert banks. Both PQ2_0 paths include the rank-one correction in their timed graph. The Spin(8) graph also includes the input half-spin transform and inverse output vector transform.

| GGUF read-back bench on 16 resident expert slots | BF16 (ms) | H512 PQ2_0 (ms) | Spin(8) + H512 PQ2_0 (ms) |
| --- | ---: | ---: | ---: |
| RTX 5060 Ti, 1 token | 0.1952 | 0.0395 | 0.0568 |
| RTX 5060 Ti, 16 tokens | 0.3365 | 0.0767 | 0.1401 |
| Ryzen 5 4500, 1 token | 2.7154 | 0.7344 | 2.1711 |
| Ryzen 5 4500, 16 tokens | 11.8092 | 9.7511 | 13.7563 |

These values are medians of seven timed calls after three warm-ups. Each of the 16 slots holds a copy of the same expert. The arithmetic error of Spin(8) PQ2_0 against the independently decoded F32 calculation was 0.53–0.69%. Output-axis leakage was at most \(7.47\times10^{-9}\) over the native Spin(8) calls. The difference from BF16 was about 43.3% on the resident benchmark's Gaussian inputs. The independent gated-input error above measures the effect after the learnt adapter. The timings exclude I/O, routing, attention, Engram and token sampling. No end-to-end throughput or refusal behaviour is inferred.

## Full-model constraints

The installed PrismML CLI returned `unknown model architecture: 'hy_v4_flash'` when opening the fixture as a model. Its GGUF reader supports both tensor types. Its model loader restricts folded weights to the supported architectures, and the Hy4-Flash graph patch is being reviewed separately upstream. A complete port needs to admit the new architecture after verifying that every folded matrix receives the corresponding transform, including both routed projections around the gated activation. The original Hy4 graph's Engram lookup, routers, latent maps, shared experts and draft model have separate numerical requirements. [PrismML runtime](https://github.com/PrismML-Eng/llama.cpp), [Hy4-Flash graph patch](https://github.com/ggml-org/llama.cpp/pull/32517).

For the 41 MoE layers, the logical payload of all three routed matrices at 2.125 bits per weight would total 36.76 GiB. The 16 routes per layer would reference 1.23 GB per token with no expert cache hits. A simple bandwidth model using the measured H-drive read rate of 108.14 MB/s gives about 0.088 tok/s for that all-miss workload. A throughput goal of 10 tok/s at that read rate allows at most 10.81 MB of physical device traffic per token. Under the assumption that miss bytes equal physical bytes, expert reads alone would require at least a 99.1% byte hit rate. Buffering, hit locality, storage compression and read amplification must be measured on real routes. The estimate excludes the 63.5B-parameter Engram and other model weights. The complete original BF16 archive is approximately 410 GiB, above free local storage. Layer-wise streaming can bound temporary conversion storage. [Hy4 model geometry](https://github.com/Tencent-Hunyuan/Hy4-flash/blob/main/README.md), [local SSD evidence and constraints](../../_docs/2026-11-25_nkat-urt-cik-strata_Codex.md).

The full source index lists 1,964 tensors across 148 shards with 440,520,833,910 data bytes. There are 82 stacked routed tensors in the 41 trunk MoE blocks. The upstream loader requires separate gate and up tensors, so the 41 fused gate/up sources expand to 82 output tensors. The graph patch's text converter skips the vision weights and DFly2 weights. The source index identifies 441 vision and 87 DFly tensors, which still need a complete-model export and load path. The latest PrismML branch used GGML 0.27 and the Hy4-Flash patch used GGML 1.0. Direct application failed. A three-way merge initially found nine text-path conflicts in a separate checkout. The text candidate resolves those conflicts, preserves the separate existing indexer path and adapts the new cache interfaces. MSVC syntax-checked the new model and indexed cache sources and the changed model, graph, context and saver units. The vision-side APIs still differ. [Upstream converter and architecture change](https://github.com/ggml-org/llama.cpp/pull/32517).

The isolated AVX2 CPU `llama` target linked successfully using the five-job build. The build receipt records exit code zero and zero active descendants after cleanup. An MSVC probe linked to the resulting DLL loaded 120,832 real vocabulary entries from a metadata-only GGUF generated from verified byte ranges of the AngelSlim reference. It then recognised the architecture of the streamed down-bank fixture and rejected that file at the expected missing-tokenizer check. The smoke test covers architecture registration and vocabulary parsing. A complete text model, its numerical generation path and a CUDA build of the port remain unvalidated. Building the isolated CPU target did not require changes to the installed PrismML or Strata runtimes. [Source GGUF reference](https://huggingface.co/AngelSlim/Hy4-flash-GGUF).

The reference GGUF prefixes list 1,415 tensors in the main split and one in the lookup-table split. Its trunk requires 123 routed matrices, including the three converted here. The full ordered tensor inventory records the names, dimensions and offsets under `H:/Strata/evidence/hy4-streamed-pq2_0-20261125/reference-gguf-inventory.json`.

## Streamed routed layer

The streaming encoder verifies each HTTP range against the exact offset and size, fits a signed H512 ternary value and uses the PrismML DLL to pack every row. Staging is on H. The encoder enforces the Windows RAM, commit and disk reserves, keeps the original checkpoint online and resumes from a whole-row boundary if the pinned source and tensor plan match. Its gate/up writer splits the stacked source along the output axis in the order the Hy4 loader expects.

The complete down-projection bank for trunk layer 1 was exported with all 512 distinct experts. The encoder read 2,415,919,104 source bytes in bounded ranges and wrote 320,864,256 PQ2_0 bytes. The source read and fit took 467.45 seconds. The GGUF was 320,871,232 bytes and matched the staged payload on read-back. The one-expert prefix was byte-identical to the original unprojected PQ2_0 pilot.

The complete gate/up source for the same layer was read as 4,831,838,208 BF16 bytes. The streaming fit took 757.44 seconds with three range workers. The GGUF separates `ffn_gate_exps` and `ffn_up_exps` and has 641,735,616 bytes. Both 512-expert outputs matched the staged payload, including the per-expert gate/up split. The three matrices total 918 MiB of PQ2_0 payload. The measured conversion rates imply about 13.6 hours for the 40 remaining routed layers if the same throughput holds, before the other parts of the model.

| Full layer-1 down bank, 16 routed experts per token | 1 token (ms) | 16 tokens (ms) | Arithmetic relative L2 |
| --- | ---: | ---: | ---: |
| Ryzen 5 4500, six threads | 1.3241 | 19.4210 | 0.686–0.697% |
| RTX 5060 Ti | 0.0447 | 0.2876 | 0.531–0.533% |

The gate/up GPU medians were 0.0423/0.0392 ms for one token on the first run and 0.0405/0.0480 ms on the repeat. For 16 tokens the first run was 0.9394/0.3260 ms and the repeat was 0.2091/0.2148 ms. The corresponding CPU gate/up medians for one token were 169.1503/2.2454 ms and 4.7379/1.6791 ms. The timing variation in these measurements precludes a stable CPU gate throughput claim. Both runs agreed with their FP32 decode to 0.531–0.536% on CUDA and 0.676–0.704% on CPU across the gate and up cases, rounding outwards.

The bank measurements use the signed H512 transform and distinct selected expert IDs. The reference is the multiplication against the same weights decoded to FP32. This quantisation stage uses the PrismML Hadamard layout and no behavioural projection. The single-expert Spin(8) fixture records the separate change-of-basis trial. The two code paths have separate performance receipts.

For 256 fixed synthetic activations through expert zero and its original BF16 output adapter, down-only conversion gave 36.06% relative output L2 error, gate/up gave 55.42%, and conversion of all three gave 63.52%. The gates use the real checkpoint weights and clamped SwiGLU. The experiment isolates quantisation distortion under that input law. Prompt-level accuracy and full-model text generation remain unmeasured.

## Reproduce

Run from the repository root with the installed PrismML 0.4.1 DLLs. Use a fresh output directory for each run. The converter retrieves only one expert if `--source` is omitted. To re-use the captured BF16 range, pass `--source` with the directory containing `source-expert.bf16` and `source.json`.

```powershell
$bin = 'C:/Users/downl/AppData/Local/Programs/llama-prism/0.4.1/bin'
$out = 'H:/Strata/evidence/hy4-pq2_0-repeat'
$project = 'H:/Strata/evidence/shinka-phase3-smoke-20261125/upstream'
$env:OPENBLAS_NUM_THREADS = '1'
uv run --project $project --no-sync python research/hy4-bonsai2/experiment.py --prism-bin $bin --output $out
foreach ($backend in @('cpu','cuda')) {
    uv run --project $project --no-sync python research/hy4-bonsai2/routed_bench.py --prism-bin $bin --pilot $out --backend $backend
}
$gated = 'H:/Strata/evidence/hy4-pq2_0-gated-repeat'
uv run --project $project --no-sync python research/hy4-bonsai2/experiment.py --prism-bin $bin --source $out --output $gated --gated-activations
$env:OPENBLAS_NUM_THREADS = '5'
$metric = 'H:/Strata/evidence/hy4-metric-projection-repeat'
uv run --project $project --no-sync python research/hy4-bonsai2/ablation.py --prism-bin $bin --gated-pilot $gated --output $metric
$spin = 'H:/Strata/evidence/hy4-spin8-triality-repeat'
uv run --project $project --no-sync python research/hy4-bonsai2/triality.py --prism-bin $bin --gated-pilot $gated --metric-pilot $metric --output $spin
$ggufPython = 'H:/Strata/deps/prism-73bfe6cc-sm120/gguf-py'
$gguf = "$spin/Hy4-Bonsai2-Expert-PQ2_0-Pilot.gguf"
uv run --project $project --no-sync python research/hy4-bonsai2/gguf_trial.py --gguf-python $ggufPython export --gated-pilot $gated --metric-pilot $metric --triality-pilot $spin --gguf $gguf
$env:OPENBLAS_NUM_THREADS = '1'
foreach ($backend in @('cpu','cuda')) {
    uv run --project $project --no-sync python research/hy4-bonsai2/gguf_trial.py --gguf-python $ggufPython benchmark --gguf $gguf --prism-bin $bin --backend $backend --output "$spin/gguf-bench-$backend.json"
}
$bank = 'H:/Strata/evidence/hy4-layer-1-down-repeat'
uv run --project $project --no-sync python research/hy4-bonsai2/stream_routed.py --prism-bin $bin --gguf-python $ggufPython --layer 1 --matrix down_proj --output $bank
uv run --project $project --no-sync python research/hy4-bonsai2/gguf_trial.py --gguf-python $ggufPython benchmark --gguf "$bank/routed-experts.gguf" --prism-bin $bin --backend cuda --output "$bank/bank-bench-cuda.json"
$gateBank = 'H:/Strata/evidence/hy4-layer-1-gate-up-repeat'
uv run --project $project --no-sync python research/hy4-bonsai2/stream_routed.py --prism-bin $bin --gguf-python $ggufPython --layer 1 --matrix gate_up_proj --output $gateBank
uv run --project $project --no-sync python research/hy4-bonsai2/gguf_trial.py --gguf-python $ggufPython compare-layer --down "$bank/routed-experts.gguf" --gate-up "$gateBank/routed-experts.gguf" --gated-pilot $gated --metric-pilot $metric --prism-bin $bin --output "$gateBank/three-projections-numerics.json"
```

The captured full-precision and PQ2_0 weights, transform signs, synthetic direction and the three machine-readable receipts are under `H:/Strata/evidence/hy4-pq2_0-pilot-20261125`. The `.pq2_0` files are individual tensor payloads. `source.json` identifies the tensor and its geometry. `results.json` and the routed receipts record the measurement scope.

The activation-weighted trial is under `H:/Strata/evidence/hy4-pq2_0-gated-20261125`. The direct, metric-optimal FP32 and BF16 writes, PQ2_0 payload, rank-32 factors and loss certificate are under `H:/Strata/evidence/hy4-metric-projection-20261125`.

The GGUF, six-candidate triality comparison, two hardware receipts and CLI model-load result are under `H:/Strata/evidence/hy4-spin8-triality-20261125`.

The streamed banks, source plans, conversion receipts, distinct-expert hardware traces and three-matrix comparison are under `H:/Strata/evidence/hy4-streamed-pq2_0-20261125`. The three-way merge compatibility log is `H:/Strata/evidence/hy4-spin8-triality-20261125/upstream-hy4-prism-three-way-check.log`.

The CPU port source is in the isolated `H:/Strata/worktrees/hy4-prism-conversion-20261125` checkout and the build is under `H:/Strata/builds/hy4-prism-text-20261125`. The successful containment receipt is in `H:/Strata/build/task5a-hy4-pq2-text-20261125`. The vocabulary-only probe and its negative control logs accompany the streamed banks. An earlier build was stopped when GPU telemetry timed out. The successful retry sampled CPU memory, commit and disk only, and the private Windows Job Object contained the build tree.
