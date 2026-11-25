# Inkling 2 Mini predictive fidelity on a 16 GB RTX 5060 Ti

## Official-checkpoint attribution

Seven documents supplied 260 next-token predictions. The four interventions used the same Transformers BF16 graph, input IDs, scoring positions and original minibatch shapes. The reference weights reconstruct the published NVFP4 and MXFP8 experts. The embedding, router and language-model head retained their source precision throughout the factorial comparison.

| Expert precision | Attention precision | Mean NLL, nats/token |
| --- | --- | ---: |
| Source | Source | 2.676401 |
| PQ2_0 | Source | 3.384774 |
| Source | Q4_K | 2.662966 |
| PQ2_0 | Q4_K | 3.386732 |

The expert-only effect was +0.70837 nats/token. Its paired document-bootstrap 95% interval was +0.38299 to +0.97145. The attention-only effect was −0.01343 (−0.02601 to +0.00339). The interaction was +0.01539 (+0.00072 to +0.02900). Restoring the experts in the fully decoded GGUF recovered 0.72235 nats/token. Restoring attention recovered 0.00841. These interventions identify expert quantisation as the dominant contributor on this corpus. They do not measure tool use, mathematical reasoning or the downstream safety of a particular bank promotion.

The independently saved source run agreed at all 260 positions, with zero observed KL divergence. Replaying the source output projection on the 139 additional Japanese positions gave a mean KL divergence of 0.0000001931, a mean NLL difference of +0.00000553 and 139 matching argmax decisions. The original source perplexity was 13.7060 on these three documents. A preliminary run that batched the interventions together changed three argmax decisions on the legacy 121 positions. The table uses separate model calls at the original batch shapes. The order of subtraction is candidate minus reference throughout.

The earlier 32 held-out weight comparisons favoured adaptive Spin(8) in 14 cases. The mean weight-MSE improvement was −0.123%, with a 95% interval from −0.339% to +0.099%. A Spin(8)-specific advantage remains unestablished.

## Termination and deployment

In the frozen Heretic PQ2_0 AIME 2025 run, one of 30 attempts ended with a parseable final answer. That answer was correct. The other 29 reached the 4,096-token cap. The model emitted 120,916 tokens in total. The estimated probability of an unfinished response at the cap was 29/30. The median completion time was unreached. Thirteen records retain a complete sequence of output IDs. Historical KV states were unavailable. The extended-budget runner records whether a trajectory was regenerated, replayed from exact IDs, or resumed from a saved KV state.

The conventional official GGUF contains 7,768,852,448 bytes. The native Strata CUDA engine generated a 16-token smoke response beginning with Paris on the RTX 5060 Ti. The separate patched llama.cpp measurements and the Strata measurements use distinct engine identities. A previous 98,304-token retrieval attempt returned none of its three requested values. The 131,072-token attempt stopped under resource protection. Neither result qualifies long-context agent deployment.

The independent published 128K baseline has 13,427,368,512 bytes. Its content digest matched the publisher's file. The recipe retains native NVFP4 in 30 physical expert banks. In each bank the source scales for all 128 experts matched, and four fixed rows from each of three experts retained their original codes and block scales after rearrangement. The two runtime scale probes inspect all 48 physical-layer visits. The agentic protocol predefines the non-inferiority margins and the role of each data split. The generation of a model file, loading a context and completing a visible retrieval answer have separate receipts. [Published model and measurements](https://huggingface.co/drofn/Inkling-2-Mini-16GB-GGUF) · [Upstream recurrent scale correction](https://github.com/ggml-org/llama.cpp/pull/32704)

## Reproduction

Run the research regression suite with `python -m pytest research/inkling-bonsai2`. The evidence commands accept paths to a local checkpoint, runtime and output volume. `expert_attention.py summarise --profile serial` reads paired per-position and per-visit receipts. `termination_survival.py` copies and verifies the historical evidence before estimating survival. `agentic_external.py` retrieves the pinned external file and verifies its digest. `build_fidelity_probes.ps1` builds the termination probe and each runtime's independent scale reader. `agentic_quality.py` and `agentic_sensitivity.py` retain the measured values and denominators. Model weights and local job state live on the evaluation volume.
