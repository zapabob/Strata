// Routed PQ2_0 multiplication in the stored signed Hadamard basis. No dense expert expansion.
#include "../hy4-bonsai2/pq2_cuda.cu"

template<int width>
__global__ void rotate_inputs(const __nv_bfloat16 *x, const int8_t *signs, int columns, float *rotated) {
    __shared__ float scratch[width];
    size_t ix = size_t(blockIdx.x)*width + threadIdx.x;
    const float v = __bfloat162float(x[ix]) * signs[ix%columns];
    rotated[ix] = hadamard<width>(v, scratch);
}

// One warp computes one output row for a (token, selected expert) pair.
__global__ void expert_dot(const uint8_t *banks, const float *x, const int64_t *ids, int rows,
                           int columns, int repeats, __nv_bfloat16 *out) {
    const int lane = threadIdx.x & 31;
    const int row = blockIdx.x * (blockDim.x/32) + threadIdx.x/32;
    if (row >= rows) return;
    const int pair = blockIdx.y;
    const int groups = columns/128;
    const uint8_t *weight = banks + (size_t(ids[pair])*rows + row)*groups*34;
    const float *input = x + size_t(pair/repeats)*columns;
    float acc = 0;
    for (int g=0; g<groups; ++g) {
        const uint8_t *q = weight + g*34;
        float scale = __half2float(__ushort_as_half(uint16_t(q[0]) | (uint16_t(q[1])<<8)));
        int bits = q[2+lane];
        float4 v = reinterpret_cast<const float4*>(input+g*128)[lane];
        float s = (((bits    )&3)-1)*v.x + (((bits>>2)&3)-1)*v.y
                + (((bits>>4)&3)-1)*v.z + (((bits>>6)&3)-1)*v.w;
        acc = fmaf(scale,s,acc);
    }
    for (int d=16; d; d/=2) acc += __shfl_down_sync(0xffffffff,acc,d);
    if (!lane) out[size_t(pair)*rows + row] = __float2bfloat16(acc);
}

extern "C" __declspec(dllexport) int inkling_pq_matmul(const uint8_t *weights, const void *activation,
    const int8_t *signs, const int64_t *experts, int tokens, int repeats, int rows, int columns, int block,
    float *rotated, void *output, void *stream) {
    if (!weights || !activation || !signs || !experts || !rotated || !output || tokens<=0 || repeats<=0 ||
        rows<=0 || columns<=0 || (block!=128 && block!=512) || columns%block || int64_t(tokens)*repeats>65535)
        return -1;
    auto st = reinterpret_cast<cudaStream_t>(stream);
    auto x = static_cast<const __nv_bfloat16*>(activation);
    size_t n = size_t(tokens)*columns;
    if (block==512) rotate_inputs<512><<<n/512,512,0,st>>>(x,signs,columns,rotated);
    else rotate_inputs<128><<<n/128,128,0,st>>>(x,signs,columns,rotated);
    cudaError_t err = cudaGetLastError();
    if (err!=cudaSuccess) return err;
    expert_dot<<<dim3((rows+7)/8,tokens*repeats),256,0,st>>>(weights,rotated,experts,rows,columns,repeats,
                                                          static_cast<__nv_bfloat16*>(output));
    return cudaGetLastError();
}
