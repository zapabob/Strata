#ifndef SPIN8_QUERY_V3_CUDA_H
#define SPIN8_QUERY_V3_CUDA_H

#include "spin8/cuda.h"
#include "spin8/query_v3.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct spin8_query_v3_cuda_plan spin8_query_v3_cuda_plan;

/* Host descriptor, device arrays. All parameters are contiguous row-major F32:
 * Win[8,width], bin[8], Wout[7,8], bout[7]. Capacities count bytes. Arrays must
 * be disjoint from each other, source, destination and error_flag. The caller
 * keeps arrays immutable until every launch using them finishes. ALL rows in
 * one call share this parameter set; callers choose the per-head grouping. */
typedef struct {
  const float *win;
  size_t win_bytes;
  const float *bin;
  size_t bin_bytes;
  const float *wout;
  size_t wout_bytes;
  const float *bout;
  size_t bout_bytes;
} spin8_query_v3_cuda_parameters_f32;

/* Host-only creation/destruction. Version must be SPIN8_QUERY_V3_VERSION.
 * Derives and audits signed permutations from spin8_query_v3_generators;
 * no GPU allocation, upload or device state. *out is null on failure.
 * Plans are immutable, shareable and copied into each launch. The caller
 * serializes destruction against calls that are still enqueueing work. */
spin8_status spin8_query_v3_cuda_plan_create(uint32_t version,
                                             spin8_query_v3_cuda_plan **out);
void spin8_query_v3_cuda_plan_free(spin8_query_v3_cuda_plan *plan);

/* Explicit opt-in fused v3 controller and Triality Q transform. src/dst are
 * device F32 [rows,width]; BOTH strides and capacities count BYTES. q is
 * already model-normalized: no extra RMS. Per row, on GPU:
 * a=Wout*tanh(Win*q+bin)+bout; tau=tan(pi/8);
 * u=tau*a/sqrt(tau^2+||a||^2); c=(1,u)/sqrt(1+||u||^2).
 * Full block8 groups share c and apply c0*I+sum(c[a+1]*J[a]). A 1..7 tail
 * feeds the controller but copies exactly. Wout=bout=0 gives bitwise identity,
 * including signed zeros. Double accumulation/chart favors reference accuracy;
 * product/sum rounding and dot reduction order follow the CPU reference.
 * Host/device tanh may differ. Tolerances are measured for tested cases only;
 * no universal CPU bitwise/tolerance guarantee holds for arbitrary finite
 * weights. Callers must calibrate/audit their parameter profiles.
 * No speed claim is made. No per-row dense matrices or global spinor buffer.
 *
 * ALL source/parameter scalars and computed results must be finite, even at
 * identity. Unlike CPU apply's identity shortcut, GPU checks Win/bin too.
 * Caller clears device error_flag; this function only ORs SPIN8_CUDA_NONFINITE.
 * Discard ALL output on any nonzero flag. Device failure is NOT atomic.
 *
 * Nonzero rows/width, float alignment, checked spans, capacity and alias rules
 * are validated before launch. Only exact src==dst with equal strides may
 * overlap. Padding is untouched. Device pointer validity, actual allocation
 * bounds, device/stream ownership and buffer lifetime remain caller contracts.
 * No allocation, host-device copy, synchronization or hidden default-stream
 * work. One kernel is enqueued on stream; launch errors are returned. Caller
 * must synchronize stream and check its asynchronous status and error_flag
 * before consuming output. The host descriptor is borrowed only for this call.
 */
cudaError_t spin8_query_v3_cuda_apply_f32(
    const spin8_query_v3_cuda_plan *plan,
    const spin8_query_v3_cuda_parameters_f32 *parameters, const float *src,
    size_t src_capacity_bytes, size_t src_stride_bytes, float *dst,
    size_t dst_capacity_bytes, size_t dst_stride_bytes, size_t rows,
    size_t width, int *error_flag, cudaStream_t stream);

#ifdef __cplusplus
}
#endif
#endif
