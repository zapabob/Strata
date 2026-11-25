# Empirical ablation of Spin(8) bases

## Real checkpoint and controls

The source was the official Thinking Machines Lab Inkling 2 Mini checkpoint. The first study inspected one expert in layers 6 and 20, covering both the NVFP4 and MXFP8 encodings and both routed projections. The independent reconstruction matched the official Transformers BF16 result on every inspected value. Each case used 64 leading rows for selection and 64 disjoint trailing rows for evaluation. No text activations enter these initial weight-only results. [Official checkpoint](https://huggingface.co/thinkingmachines/Inkling-2-Mini)

Adaptive triality obtained lower held-out weight MSE than the conventional Hadamard search in one of the first four comparisons. The study then sampled experts 7 and 101 at physical layers 0, 5, 6, 11, 17, 19, 20 and 23. Both projections were measured at each site. Each search received three candidate evaluations. The adaptive search considered the vector, positive and negative representations. The conventional search considered H128 and two reproducible signed variants. Independent controls used full Haar SO(128) and a Haar octet in the same Kronecker structure. The direct identity control has one distinct basis. Rotation metadata are excluded from the 2.125 payload bits per weight.

| Comparator | Adaptive wins out of 32 | Mean relative reduction in MSE | Paired 95% interval |
|---|---:|---:|---:|
| Conventional Hadamard search | 14 | −0.123% | −0.339% to +0.099% |
| Haar SO(128) | 17 | +0.051% | −0.108% to +0.216% |
| H16 with a Haar SO(8) octet | 15 | +0.001% | −0.144% to +0.151% |

Reductions are positive when triality has lower error. Bootstrap resampling used 16 physical layer/expert pairs with the two projections kept together and 4,000 draws. The intervals describe the selected sites under that resampling scheme. The layers and expert indices were deliberately selected. The measurements provide no evidence of a consistent advantage over either rotation control.

## Transform accuracy and cost

The RTX 5060 Ti evaluated 64 real rows of the layer 6 down projection at width 1152. Maximum fused-transform error against FP64 across all three representations was (1.48\times10^{-8}). FP16 scales and complete output bytes from the weighted CUDA packer matched the CPU calculation made on the identical rotated FP32 numbers. The feature weights used in this microbenchmark were synthetic diagnostic weights.

| Representation | Fused transform, µs | Dense reference transform, µs |
|---|---:|---:|
| Vector | 31.24 | 118.12 |
| Positive chirality | 28.09 | 104.60 |
| Negative chirality | 32.58 | 103.30 |

Each value is the median of five GPU-event batches of 50 launches after ten warm-up launches. The Windows host also had other work. These observations measure this transform workload and include dispatch gaps observable between event boundaries. The CUDA 13.5 libraries contain SM80 and SM120 device images. The hardware measurements above concern SM120.
