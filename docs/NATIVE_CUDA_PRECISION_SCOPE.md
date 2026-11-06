# CUDA precision work across the native model families

The optimisation scope includes Qwen3.6, Qwen3.8-Flash-Next, and the separate
DeepSeek V4.1 engine. Preserve each model's numerical contract. A successful
test on one family is not qualification of another family.

| Family | Existing storage in this source | Relevant implementation | Current new-work status |
| --- | --- | --- | --- |
| Qwen3.6 | FP32 attention K/V | `src/qwen35/q36_engine.cu` | FP16 opt-in candidate and small GPU checks; see `QWEN36_KV_PRECISION.md` |
| Qwen3.8-Flash-Next | FP16 QSA pools, grouped-64 INT8, rotated Q4_0 and K8V4; separate native TurboQuant adapter | `src/core/layer.cpp`, `src/kernels/cuda/kv_q8.cu`, `kv_q4.cu`, `src/program/generate.cpp` | CUDA 13.5 model comparison and additional formats NOT_RUN |
| DeepSeek V4.1 | FP8 window ring; compressed E2M1/E4M3 KV; E2M1/UE8M0 index keys; BF16 working rows | `src/dsv41/ds4_kernels.cu`, `ds4_model.cu` | Separate Windows engine build and model qualification NOT_RUN |

Qwen3.8's `--kv int8` has one FP16 scale per 64 values. It is not GGUF Q8_0,
which stores a scale with 32 int8 values. The existing `--cache-type-k/v`
options in the generic driver belong to the native cache adapter; do not send
Qwen3.6's newly added values through that path without capability checks.

DeepSeek stores the model reference's own rounded values in packed formats.
Its compressed KV and index keys have different scale formats. They must not
be relabelled as the proposed Qwen row-scaled NVFP4 format, which has an
additional FP32 outer scale. DeepSeek's sparse attention also treats its
compressed latent rows differently from Qwen's separate K and V arrays.

The immediate cross-family work is to compare the same source and settings
under CUDA 13.3 and 13.5, retain existing storage parity tests, and record each
family's actual precision, allocation, transfer volume, and latency. Common
codec operations can be shared after their rounding, scale, and layout
contracts agree. Cache identity, session copies, rollback, and private
clearing remain family-specific integration gates.

Expert residency and transfer decisions also need separate measurements.
Do not copy Qwen3.6's per-layer slot budget or context-byte formula into the
generic Qwen or DeepSeek planners. Keep weights, router selection, recurrent
state precision, and the requested context fixed within each comparison.

The installed fork currently does not contain the separate native DeepSeek
executable. Source support does not establish an installed runtime. A full
DeepSeek model was not found in the checked Strata model directory. No model
download or replacement is authorised by the presence of a design document.

All new policies remain opt-in until their own numerical, lifecycle, memory,
and model tests pass. Small synthetic CUDA results do not establish 98K/131K
generation or a model throughput improvement.
