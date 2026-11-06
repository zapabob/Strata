# Native Qwen3.6 KV precision candidate

This is an opt-in implementation on top of the 0.5.1 startup fixes. It is not in
the installed app or a published release. The app still requires a qualified
engine capability before offering low-precision native KV settings.

The native CLI accepts `--cache-type-k f32|f16` and `--cache-type-v f32|f16`.
Both default to `f32`. These names follow the existing server's cache options.
An unsupported value returns an error before model loading. Q8_0 and NVFP4
storage are not implemented by this change.

FP16 applies to attention K/V storage after normalization and RoPE. Query
arithmetic, attention accumulation, softmax, and GDN recurrent state retain
their existing precision. The model weights and router are unchanged. K and V
may use different storage types. Session allocation, session prefix copies,
MTP state, and private-cache clearing use the corresponding element size.

Prefill GEMMs read FP16 cache heads directly using the context-capacity stride.
An FP32 side still uses the existing compact FP16 conversion buffer. There is
no full-context FP32 shadow of an FP16 cache. The existing score/probability
workspace remains allocated; this change is not tiled attention.

For 11 attention states, two KV heads, head dimension 256, one session, and
131072 context cells, persistent K+V capacity is theoretically 5.5 GiB in FP32
or 2.75 GiB in FP16. Two FP16 sides also avoid 256 MiB of shared conversion
buffers at that capacity. These are allocation formulae, not a successful
131072-token model test or a speed measurement. Other state, weights, and
workspace are additional.

## Evidence from 2026-11-06

`q36_kv_cache_test` includes the production driver and runs its kernels and
session methods without a model. On Windows, RTX 5060 Ti 16 GB, driver 621.01,
the test translation unit compiled with CUDA 13.5.37 and linked with the
existing CUDA 13.3 engine libraries and CUDA 13.5 runtime. This is not a full
engine toolchain comparison.

All eight cases passed: four K/V type combinations for the kernels and four
for session operations. The 257-token, 513-cell fixture crosses the 256-cell
attention partition boundary and uses two KV heads. It checks rounded storage,
untouched suffixes, compact operands, direct FP16 prefill GEMM operands,
per-session addressing, prefix copies, and private clearing of the full
capacity including the MTP state. Attention is compared with a double-precision
CPU reference of the stored values. Maximum absolute error across the four
combinations was below 3e-7; the predeclared test limit was 2e-5.

The second test executable SHA-256 was
`d9c7eaa9c10f19e57003e842e42223547dc59526baf23ab26a38cd958b5f229f`.
Private run evidence is retained in the worktree under
`_docs/evidence/kv-f16/r2/`. No real-model speed or quality claim follows from
these kernel cases.

## Remaining qualification

Real-model FP32/FP16 teacher-forced quality, MTP acceptance/rejection/rollback,
prefix reuse through the server, long-context input, cancellation, graph
capture, and Compute Sanitizer are NOT_RUN for this candidate. Extreme and
non-finite input handling needs dedicated cases. Host capability, typed memory
estimates, and the installed application are not integrated. HIP is NOT_RUN.
Do not make FP16 the default or publish it as qualified until those gates pass.

The supplied implementation plan version 1.1 uses 0.5.0 as its baseline. The
0.5.1 startup changes remain the base here. Its proposed `--q36-kv-type` name
and separate layout descriptor are design inputs, not existing binary options.
The remaining Q8_0 and NVFP4 work must include their scales in allocation,
copy, rollback, identity, and clearing. An NVFP4 KV layout with per-row outer
scales must be identified as a native layout, not TensorRT cache compatibility.
