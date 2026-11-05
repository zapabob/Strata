// Bounded, opt-in CUDA 13.5 library/transfer benchmark. No model files are opened.
// Build for sm_120 with CUDA 13.5; run each library version in a separate process.
#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <cuda_bf16.h>
#include <cublas_v2.h>
#include "strata/core/dma_batch.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

#if CUDART_VERSION < 13050
#error This benchmark requires CUDA 13.5 or newer.
#endif
#define CUDA_OK(x) do { const auto e=(x); if(e!=cudaSuccess) { \
    std::fprintf(stderr,"CUDA %s:%d: %s\n",__FILE__,__LINE__,cudaGetErrorString(e)); std::exit(1); } } while(0)
#define BLAS_OK(x) do { const auto e=(x); if(e!=CUBLAS_STATUS_SUCCESS) { \
    std::fprintf(stderr,"cuBLAS %s:%d: %d\n",__FILE__,__LINE__,int(e)); std::exit(1); } } while(0)
using Clock=std::chrono::steady_clock;

template<class F> float median_ms(F run, cudaStream_t stream) {
    for(int i=0;i<5;++i) run();
    CUDA_OK(cudaStreamSynchronize(stream));
    cudaEvent_t a,b;
    CUDA_OK(cudaEventCreate(&a)); CUDA_OK(cudaEventCreate(&b));
    std::vector<float> samples;
    for(int r=0;r<7;++r) {
        CUDA_OK(cudaEventRecord(a,stream));
        for(int i=0;i<20;++i) run();
        CUDA_OK(cudaEventRecord(b,stream)); CUDA_OK(cudaEventSynchronize(b));
        float ms=0; CUDA_OK(cudaEventElapsedTime(&ms,a,b)); samples.push_back(ms/20);
    }
    CUDA_OK(cudaEventDestroy(a)); CUDA_OK(cudaEventDestroy(b));
    std::sort(samples.begin(),samples.end()); return samples[samples.size()/2];
}

static void transfers(cudaStream_t stream) {
    constexpr size_t count=8, bytes=1024*1024, total=count*bytes;
    unsigned char *host=nullptr,*device=nullptr;
    CUDA_OK(cudaHostAlloc(&host,total,cudaHostAllocMapped)); CUDA_OK(cudaMalloc(&device,total));
    for(size_t i=0;i<total;++i) host[i]=static_cast<unsigned char>((i*17+i/65536)%251);
    void* dst[count]; const void* src[count]; size_t sizes[count];
    for(size_t i=0;i<count;++i) { dst[i]=device+i*bytes; src[i]=host+i*bytes; sizes[i]=bytes; }
    std::vector<unsigned char> check(total);
    for(int mode=0;mode<=2;++mode) {
        CUDA_OK(cudaMemsetAsync(device,0,total,stream));
        auto copy=[&] { CUDA_OK(strata::core::copy_blobs(dst,src,sizes,count,stream,mode)); };
        copy(); CUDA_OK(cudaStreamSynchronize(stream));
        CUDA_OK(cudaMemcpy(check.data(),device,total,cudaMemcpyDeviceToHost));
        if(!std::equal(check.begin(),check.end(),host)) { std::fputs("DMA parity failed\n",stderr); std::exit(1); }
        const float ms=median_ms(copy,stream);
        const auto start=Clock::now();
        for(int i=0;i<100;++i) copy();
        CUDA_OK(cudaStreamSynchronize(stream));
        const double wall=std::chrono::duration<double,std::milli>(Clock::now()-start).count()/100;
        std::printf("{\"kind\":\"dma\",\"mode\":%d,\"bytes\":%zu,\"gpuMs\":%.6f,\"wallMs\":%.6f,\"parity\":true}\n",mode,total,ms,wall);
    }
    CUDA_OK(cudaFree(device)); CUDA_OK(cudaFreeHost(host));
}

static float input_a(int row,int k) { return float((row*3+k*5)%17-8)/32; }
static float input_b(int col,int k) { return float((col*7+k*3)%19-9)/32; }
template<class T> void gemm(cublasHandle_t handle,cudaStream_t stream,int n,int t,int k,cudaDataType_t dtype,const char* label) {
    std::vector<T> a(size_t(n)*k),b(size_t(t)*k);
    for(int i=0;i<n;++i) for(int j=0;j<k;++j) a[size_t(i)*k+j]=T(input_a(i,j));
    for(int i=0;i<t;++i) for(int j=0;j<k;++j) b[size_t(i)*k+j]=T(input_b(i,j));
    T *da=nullptr,*db=nullptr; float* dc=nullptr;
    CUDA_OK(cudaMalloc(&da,a.size()*sizeof(T))); CUDA_OK(cudaMalloc(&db,b.size()*sizeof(T)));
    CUDA_OK(cudaMalloc(&dc,size_t(n)*t*sizeof(float)));
    CUDA_OK(cudaMemcpy(da,a.data(),a.size()*sizeof(T),cudaMemcpyHostToDevice));
    CUDA_OK(cudaMemcpy(db,b.data(),b.size()*sizeof(T),cudaMemcpyHostToDevice));
    const float one=1,zero=0;
    auto run=[&] { BLAS_OK(cublasGemmEx(handle,CUBLAS_OP_T,CUBLAS_OP_N,n,t,k,&one,da,dtype,k,db,dtype,k,
                                      &zero,dc,CUDA_R_32F,n,CUBLAS_COMPUTE_32F,CUBLAS_GEMM_DEFAULT)); };
    run(); CUDA_OK(cudaStreamSynchronize(stream));
    std::vector<float> result(size_t(n)*t);
    CUDA_OK(cudaMemcpy(result.data(),dc,result.size()*4,cudaMemcpyDeviceToHost));
    for(float v:result) if(!std::isfinite(v)) { std::fputs("Nonfinite GEMM result\n",stderr); std::exit(1); }
    double maxerr=0;
    for(int sample=0;sample<128;++sample) {
        const int row=(sample*101)%n,col=(sample*53)%t;
        double reference=0;
        for(int j=0;j<k;++j) reference+=double(input_a(row,j))*input_b(col,j);
        maxerr=std::max(maxerr,std::abs(reference-result[size_t(col)*n+row]));
    }
    if(maxerr>1e-4) { std::fprintf(stderr,"GEMM parity failed: %.9g\n",maxerr); std::exit(1); }
    const float ms=median_ms(run,stream);
    std::printf("{\"kind\":\"gemm\",\"dtype\":\"%s\",\"N\":%d,\"T\":%d,\"K\":%d,\"gpuMs\":%.6f,\"maxAbsError\":%.9g}\n",label,n,t,k,ms,maxerr);
    CUDA_OK(cudaFree(da)); CUDA_OK(cudaFree(db)); CUDA_OK(cudaFree(dc));
}

int main() {
    cudaDeviceProp p{}; CUDA_OK(cudaGetDeviceProperties(&p,0));
    if(p.major!=12 || p.minor!=0) { std::fputs("This qualification is limited to sm_120\n",stderr); return 77; }
    size_t free=0,total=0; CUDA_OK(cudaMemGetInfo(&free,&total));
    if(free<1024ull*1024*1024) { std::fputs("Require 1 GiB free VRAM\n",stderr); return 77; }
    int driver=0,runtime=0,blas=0;
    CUDA_OK(cudaDriverGetVersion(&driver)); CUDA_OK(cudaRuntimeGetVersion(&runtime));
    cudaStream_t stream; CUDA_OK(cudaStreamCreateWithFlags(&stream,cudaStreamNonBlocking));
    cublasHandle_t handle; BLAS_OK(cublasCreate(&handle)); BLAS_OK(cublasSetStream(handle,stream));
    BLAS_OK(cublasSetMathMode(handle,CUBLAS_DEFAULT_MATH)); BLAS_OK(cublasGetVersion(handle,&blas));
    std::printf("{\"kind\":\"device\",\"name\":\"%s\",\"runtime\":%d,\"driver\":%d,\"cublas\":%d}\n",p.name,runtime,driver,blas);
    transfers(stream);
    for(int t:{1,32,512}) {
        gemm<__half>(handle,stream,4096,t,2048,CUDA_R_16F,"fp16");
        gemm<__nv_bfloat16>(handle,stream,4096,t,2048,CUDA_R_16BF,"bf16");
    }
    gemm<__nv_bfloat16>(handle,stream,2048,128,2049,CUDA_R_16BF,"bf16-unaligned-synthetic");
    BLAS_OK(cublasDestroy(handle)); CUDA_OK(cudaStreamDestroy(stream));
    return 0;
}
