#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <cuda_bf16.h>
#include <cub/block/block_radix_sort.cuh>
#include <cub/block/block_scan.cuh>
#include <stdint.h>
#include <math.h>

static __global__ void ternary_fit(const float * w, const float * h, int width, uint8_t * out) {
    using Sort = cub::BlockRadixSort<uint64_t,128,1>;
    using Scan = cub::BlockScan<double,128>;
    __shared__ union { typename Sort::TempStorage sort; typename Scan::TempStorage scan; } tmp;
    __shared__ double gain[128];
    __shared__ int index[128];
    __shared__ unsigned short grid[128];
    __shared__ unsigned char code[128];
    const int i=threadIdx.x, column=(blockIdx.x%(width/128))*128;
    const float val=w[int64_t(blockIdx.x)*128+i];
    uint64_t key[1]={(uint64_t(__float_as_uint(fabsf(val)))<<7)|uint64_t(127-i)};
    Sort(tmp.sort).SortDescending(key,0,38);
    __syncthreads();
    const double mag=__uint_as_float(uint32_t(key[0]>>7));
    const double importance=h?h[column+127-int(key[0]&127)]:1.;
    double num, den;
    Scan(tmp.scan).InclusiveSum(importance*mag,num);
    __syncthreads();
    Scan(tmp.scan).InclusiveSum(importance,den);
    const __half candidate=__double2half(den>0 ? fmin(num/den,65504.) : 0.);
    const double a=__half2float(candidate);
    grid[i]=__half_as_ushort(candidate);
    gain[i]=__dsub_rn(__dmul_rn(2*a,num),__dmul_rn(den,a*a)); index[i]=i;
    __syncthreads();
    for (int stride=64; stride; stride/=2) {
        if (i<stride && (gain[index[i+stride]]>gain[index[i]] ||
            (gain[index[i+stride]]==gain[index[i]] && index[i+stride]<index[i]))) { index[i]=index[i+stride]; }
        __syncthreads();
    }
    const unsigned short alpha=grid[index[0]];
    const float scale=__half2float(__ushort_as_half(alpha));
    code[i]=(scale!=0 && fabsf(val)>.5f*scale) ? (val>0?2:0) : 1;
    __syncthreads();
    auto dst=out+int64_t(blockIdx.x)*34;
    if (i==0) { dst[0]=alpha&255; dst[1]=alpha>>8; }
    if (i<32) { dst[2+i]=code[4*i]|(code[4*i+1]<<2)|(code[4*i+2]<<4)|(code[4*i+3]<<6); }
}
#if defined(_WIN32)
#define PQ_EXPORT __declspec(dllexport)
#else
#define PQ_EXPORT __attribute__((visibility("default")))
#endif
extern "C" PQ_EXPORT int spin8_fit_pq2(const float * w,const float * h,int rows,int width,
                                         uint8_t * packed,cudaStream_t stream) {
    if (!w || !packed || rows<=0 || width<=0 || width%128 || int64_t(rows)*(width/128)>2147483647) {
        return cudaErrorInvalidValue;
    }
    ternary_fit<<<rows*(width/128),128,0,stream>>>(w,h,width,packed);
    return int(cudaPeekAtLastError());
}

// One CTA owns one physical Prism group. All comparisons include the stored binary16 scale.
static __global__ void refine_covariance(const float * w,const float * cov,int groups,uint8_t * packed) {
    using Scan=cub::BlockScan<double,128>;
    __shared__ typename Scan::TempStorage tmp;
    __shared__ double original_error,scale,denominator;
    __shared__ float weight[128],symbol[128];
    __shared__ double change;
    const int lane=threadIdx.x;
    const float * c=cov+int64_t(blockIdx.x%groups)*128*128;
    uint8_t * dest=packed+int64_t(blockIdx.x)*34;
    weight[lane]=w[int64_t(blockIdx.x)*128+lane];
    symbol[lane]=int((dest[2+lane/4]>>(2*(lane%4)))&3)-1;
    if (lane==0) { scale=__half2float(__ushort_as_half(uint16_t(dest[0])|(uint16_t(dest[1])<<8))); }
    __syncthreads();
    double grad=0;
    for (int k=0;k<128;++k) { grad+=c[k*128+lane]*(weight[k]-scale*symbol[k]); }
    double sum=0;
    Scan(tmp).InclusiveSum(grad*(weight[lane]-scale*symbol[lane]),sum);
    if (lane==127) { original_error=sum; }
    __syncthreads();
    for (int j=0;j<128;++j) {
        if (lane==j) {
            const double h=scale*c[j*128+j];
            const double target=h>0?symbol[j]+grad/h:symbol[j];
            const float next=target>.5?1.f:(target<-.5?-1.f:0.f);
            change=(next-symbol[j])*scale; symbol[j]=next;
        }
        __syncthreads();
        grad-=change*c[j*128+lane];
        __syncthreads();
    }
    double ct=0;
    for (int k=0;k<128;++k) { ct+=double(c[k*128+lane])*symbol[k]; }
    Scan(tmp).InclusiveSum(ct*symbol[lane],sum);
    if (lane==127) { denominator=sum; }
    __syncthreads();
    Scan(tmp).InclusiveSum(ct*weight[lane],sum);
    if (lane==127) { scale=__half2float(__double2half(denominator>0?fmin(65504.,fmax(0.,sum/denominator)):0.)); }
    __syncthreads();
    grad=0;
    for (int k=0;k<128;++k) { grad+=c[k*128+lane]*(weight[k]-scale*symbol[k]); }
    Scan(tmp).InclusiveSum(grad*(weight[lane]-scale*symbol[lane]),sum);
    if (lane==127) { change=(sum<=original_error); }
    __syncthreads();
    if (change) {
        if (lane==0) {
            const uint16_t bits=__half_as_ushort(__double2half(scale));
            dest[0]=bits&255; dest[1]=bits>>8;
        }
        if (lane<32) {
            uint8_t byte=0;
            for (int k=0;k<4;++k) { byte|=(scale==0?1:int(symbol[4*lane+k])+1)<<(2*k); }
            dest[2+lane]=byte;
        }
    }
}
extern "C" PQ_EXPORT int spin8_refine_pq2(const float * w,const float * cov,int rows,int width,
                                           uint8_t * packed,cudaStream_t stream) {
    if (!w||!cov||!packed||rows<=0||width<=0||width%128||int64_t(rows)*(width/128)>2147483647) {
        return cudaErrorInvalidValue;
    }
    refine_covariance<<<rows*(width/128),128,0,stream>>>(w,cov,width/128,packed);
    return int(cudaPeekAtLastError());
}

__device__ static float inkling_e4m3(unsigned char x) {
    const int mag=x&127, e=mag>>3;
    if (mag==127) { return NAN; }
    const float v=e?ldexpf(float(8+(mag&7)),e-10):ldexpf(float(mag&7),-9);
    return (x&128)?-v:v;
}
static __global__ void reconstruct_original(const uint8_t * w,const uint8_t * scales,float outer,
                                             int nx,bool nv,bool bf16,void * out) {
    const int i=blockIdx.x*blockDim.x+threadIdx.x;
    if (i>=nx) { return; }
    float v;
    if (nv) {
        const float lut[]={0.f,.5f,1.f,1.5f,2.f,3.f,4.f,6.f};
        const unsigned code=(w[i/2]>>(4*(i%2)))&15;
        v=__fmul_rn(__fmul_rn((code&8)?-lut[code&7]:lut[code&7],inkling_e4m3(scales[i/16])),outer);
    } else {
        const int e=scales[i/32];
        v=e==255?NAN:ldexpf(inkling_e4m3(w[i]),e-127);
    }
    if (bf16) { static_cast<__nv_bfloat16 *>(out)[i]=__float2bfloat16_rn(v); }
    else { static_cast<float *>(out)[i]=v; }
}
extern "C" PQ_EXPORT int spin8_reconstruct_original(const uint8_t * w,const uint8_t * scales,float outer,
                                                      int nx,int nv,int bf16,void * out,cudaStream_t stream) {
    if (!w||!scales||!out||nx<=0||nx%(nv?16:32)) { return cudaErrorInvalidValue; }
    reconstruct_original<<<(nx+255)/256,256,0,stream>>>(w,scales,outer,nx,nv,bf16,out);
    return int(cudaPeekAtLastError());
}

static __global__ void unpack_statistics(const float * rotated,const uint8_t * packed,double * per_group) {
    const int lane=threadIdx.x;
    const uint8_t * b=packed+int64_t(blockIdx.x)*34;
    const int code=(b[2+lane/4]>>(2*(lane%4)))&3;
    const float alpha=__half2float(__ushort_as_half(uint16_t(b[0])|(uint16_t(b[1])<<8)));
    const double error=double(rotated[int64_t(blockIdx.x)*128+lane])-(code-1)*double(alpha);
    __shared__ double partial[4][5];
    double sum=error*error;
    for(int off=16;off;off/=2){sum+=__shfl_down_sync(0xffffffff,sum,off);}
    if (lane%32==0) { partial[lane/32][0]=sum; }
    for(int j=0;j<4;++j){
        const int n=__popc(__ballot_sync(0xffffffff,code==j));
        if(lane%32==0){partial[lane/32][j+1]=n;}
    }
    __syncthreads();
    if(lane<5){per_group[int64_t(blockIdx.x)*5+lane]=partial[0][lane]+partial[1][lane]+partial[2][lane]+partial[3][lane];}
}
extern "C" PQ_EXPORT int spin8_pq2_statistics(const float * w,const uint8_t * packed,int groups,double * totals,cudaStream_t stream) {
    if (!w||!packed||!totals||groups<=0) { return cudaErrorInvalidValue; }
    unpack_statistics<<<groups,128,0,stream>>>(w,packed,totals);
    return int(cudaPeekAtLastError());
}

static __global__ void packed_product(const uint8_t * w,const float * x,float * y,int rows,int width) {
    const int row=blockIdx.x*8+threadIdx.x/32, lane=threadIdx.x%32, token=blockIdx.y;
    if (row>=rows) { return; }
    float acc=0;
    for (int g=0;g<width/128;++g) {
        const auto * b=w+(int64_t(row)*(width/128)+g)*34;
        const float d=__half2float(__ushort_as_half(uint16_t(b[0])|(uint16_t(b[1])<<8)));
        unsigned v=b[2+lane]; const auto * a=x+int64_t(token)*width+g*128+4*lane;
        float dot=0;
        #pragma unroll
        for (int j=0;j<4;++j) { dot+=(int((v>>(2*j))&3)-1)*a[j]; }
        acc=fmaf(d,dot,acc);
    }
    for (int n=16;n;n/=2) { acc+=__shfl_down_sync(0xffffffff,acc,n,32); }
    if (lane==0) { y[int64_t(token)*rows+row]=acc; }
}
extern "C" PQ_EXPORT int spin8_weight_product(const uint8_t * w,const float * x,float * y,int rows,int width,
                                               int tokens,cudaStream_t stream) {
    if (!w||!x||!y||rows<=0||width<=0||width%128||tokens<=0||tokens>65535) { return cudaErrorInvalidValue; }
    packed_product<<<dim3((rows+7)/8,tokens),256,0,stream>>>(w,x,y,rows,width);
    return int(cudaPeekAtLastError());
}
