// A bounded BF16 -> PQ2_0 compressor and an inverse-basis GPU reader.
#include <cuda_bf16.h>
#include <cuda_fp16.h>
#include <cuda_runtime.h>
#include <cub/block/block_radix_sort.cuh>
#include <cub/block/block_scan.cuh>
#include <cmath>
#include <cstdint>

constexpr int group_width = 128;
constexpr int group_bytes = 34;

template<int width>
__device__ float hadamard(float value, float *scratch) {
    const int lane = threadIdx.x;
    for (int span = 1; span < width; span *= 2) {
        float peer;
        if (span < 32) {
            peer = __shfl_xor_sync(0xffffffff, value, span);
        } else {
            scratch[lane] = value;
            __syncthreads();
            peer = scratch[lane ^ span];
            __syncthreads();
        }
        value = (lane & span) ? peer - value : value + peer;
    }
    return __fdiv_rn(value, sqrtf(float(width)));
}

template<int width>
__global__ void rotate(const uint16_t *source, const int8_t *signs, int original,
                       int physical, float *values, int *invalid) {
    __shared__ float scratch[width];
    int column = (blockIdx.x % (physical / width)) * width + threadIdx.x;
    int row = blockIdx.x / (physical / width);
    float value = column < original ? __uint_as_float(uint32_t(source[size_t(row)*original + column]) << 16) : 0;
    value = hadamard<width>(value * signs[column], scratch);
    if (!isfinite(value) || fabsf(value) > 65504.f) atomicExch(invalid, 1);
    values[size_t(row)*physical + column] = value;
}

__global__ void fit_groups(const float *values, uint8_t *packed) {
    using Sort = cub::BlockRadixSort<uint64_t, group_width, 1>;
    using Scan = cub::BlockScan<double, group_width>;
    __shared__ union { typename Sort::TempStorage sort; typename Scan::TempStorage scan; } temp;
    __shared__ unsigned char rank[group_width], best[group_width];
    __shared__ uint16_t scale_bits[group_width];
    __shared__ double scores[group_width];
    const int i = threadIdx.x;
    const float value = values[size_t(blockIdx.x)*group_width + i];
    uint64_t key[1] = {(uint64_t(__float_as_uint(fabsf(value))) << 7) | uint64_t(127-i)};
    Sort(temp.sort).SortDescending(key, 0, 38);
    __syncthreads();
    rank[127-(key[0] & 127)] = i;
    double sum;
    Scan(temp.scan).InclusiveSum(double(__uint_as_float(uint32_t(key[0] >> 7))), sum);
    // Direct double to binary16 rounding avoids a second rounding at midpoints.
    __half half_scale = __double2half(sum / (i+1));
    double scale = __half2float(half_scale);
    scale_bits[i] = __half_as_ushort(half_scale);
    scores[i] = __dsub_rn(__dmul_rn(2*scale, sum), __dmul_rn(i+1, scale*scale));
    best[i] = i;
    __syncthreads();
    for (int step = group_width/2; step; step /= 2) {
        if (i < step) {
            int a = best[i], b = best[i+step];
            if (scores[b] > scores[a] || (scores[a] == scores[b] && b < a)) best[i] = b;
        }
        __syncthreads();
    }
    const int winner = best[0];
    const bool active = rank[i] <= winner && scale_bits[winner] != 0;
    int code = 1 + (active ? int(value > 0) - int(value < 0) : 0);
    const int n1 = __shfl_down_sync(0xffffffff, code, 1);
    const int n2 = __shfl_down_sync(0xffffffff, code, 2);
    const int n3 = __shfl_down_sync(0xffffffff, code, 3);
    uint8_t *out = packed + size_t(blockIdx.x)*group_bytes;
    if ((i % 4) == 0) out[2+i/4] = uint8_t(code | n1<<2 | n2<<4 | n3<<6);
    if (i == 0) {
        out[0] = uint8_t(scale_bits[winner]);
        out[1] = uint8_t(scale_bits[winner] >> 8);
    }
}

template<int width>
__global__ void undo_basis(const uint8_t *packed, const int8_t *signs, int original,
                           int physical, int kind, void *output) {
    __shared__ float scratch[width];
    size_t ix = size_t(blockIdx.x)*width + threadIdx.x;
    const uint8_t *g = packed + (ix / group_width)*group_bytes;
    int j = int(ix % group_width);
    int level = ((g[2+j/4] >> (2*(j%4))) & 3) - 1;
    float scale = __half2float(__ushort_as_half(uint16_t(g[0]) | (uint16_t(g[1])<<8)));
    float value = hadamard<width>(level*scale, scratch);
    int column = ix % physical;
    if (column < original) {
        size_t pos = (ix / physical)*original + column;
        value *= signs[column];
        if (kind == 0) static_cast<float*>(output)[pos] = value;
        else static_cast<__nv_bfloat16*>(output)[pos] = __float2bfloat16(value);
    }
}

extern "C" __declspec(dllexport) int hy4_pq_decode(const void *packed, const void *signs,
    int rows, int original, int physical, int block, int kind, void *out, void *stream) {
    if (!packed || !signs || !out || rows <= 0 || original < 1 || physical < original ||
        (block != 128 && block != 512) || physical % block || (kind != 0 && kind != 1)) return -1;
    auto q = static_cast<const uint8_t*>(packed);
    auto d = static_cast<const int8_t*>(signs);
    auto st = reinterpret_cast<cudaStream_t>(stream);
    int blocks = rows*(physical/block);
    if (block == 512) undo_basis<512><<<blocks,512,0,st>>>(q,d,original,physical,kind,out);
    else undo_basis<128><<<blocks,128,0,st>>>(q,d,original,physical,kind,out);
    return cudaGetLastError();
}

// The host facade owns one non-blocking stream per tile. Each invocation
// drains the stream before returning or releasing its bounded allocations.
extern "C" __declspec(dllexport) int hy4_pq_fit(const uint16_t *host, const int8_t *signs,
    int rows, int original, int physical, int block, uint8_t *out) {
    if (!host || !signs || !out || rows <= 0 || original < 1 || original > physical ||
        (block != 128 && block != 512) || physical % block) return -1;
    const size_t n = size_t(rows)*physical, bytes = n/group_width*group_bytes;
    cudaStream_t st = nullptr;
    uint16_t *src = nullptr;
    int8_t *direction = nullptr;
    float *rotated = nullptr;
    uint8_t *packed = nullptr;
    int *invalid = nullptr, bad = 0;
    cudaError_t err = cudaStreamCreateWithFlags(&st, cudaStreamNonBlocking);
    if (err != cudaSuccess) return err;
#define TRY(call) do { err = (call); if (err != cudaSuccess) goto cleanup; } while (0)
    TRY(cudaMallocAsync(&src,size_t(rows)*original*2,st));
    TRY(cudaMallocAsync(&direction,physical,st));
    TRY(cudaMallocAsync(&rotated,n*sizeof(float),st));
    TRY(cudaMallocAsync(&packed,bytes,st));
    TRY(cudaMallocAsync(&invalid,sizeof(int),st));
    TRY(cudaMemsetAsync(invalid,0,sizeof(int),st));
    TRY(cudaMemcpyAsync(src,host,size_t(rows)*original*2,cudaMemcpyHostToDevice,st));
    TRY(cudaMemcpyAsync(direction,signs,physical,cudaMemcpyHostToDevice,st));
    if (block == 512) rotate<512><<<n/512,512,0,st>>>(src,direction,original,physical,rotated,invalid);
    else rotate<128><<<n/128,128,0,st>>>(src,direction,original,physical,rotated,invalid);
    TRY(cudaGetLastError());
    fit_groups<<<n/group_width,group_width,0,st>>>(rotated,packed);
    TRY(cudaGetLastError());
    TRY(cudaMemcpyAsync(out,packed,bytes,cudaMemcpyDeviceToHost,st));
    TRY(cudaMemcpyAsync(&bad,invalid,sizeof(int),cudaMemcpyDeviceToHost,st));
    TRY(cudaStreamSynchronize(st));
cleanup:
    if (src) cudaFreeAsync(src,st);
    if (direction) cudaFreeAsync(direction,st);
    if (rotated) cudaFreeAsync(rotated,st);
    if (packed) cudaFreeAsync(packed,st);
    if (invalid) cudaFreeAsync(invalid,st);
    cudaStreamSynchronize(st);
    cudaStreamDestroy(st);
    return err == cudaSuccess && bad ? -2 : int(err);
#undef TRY
}
