// CPU fault injection only: functions under test are extracted verbatim from the consumers.
#include "strata/perf131k/blob_failure.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>
#undef assert
#define assert(expr) do { if (!(expr)) { std::fprintf(stderr,"failed line %d: %s\n",__LINE__,#expr); return 1; } } while (0)
using CUdeviceptr = uintptr_t;
using CUdevice = int;
using CUresult = int;
using CUmemGenericAllocationHandle = unsigned long long;
struct CUmemAllocationProp {};
struct CUmemAccessDesc { struct { int type, id; } location; int flags; };
constexpr int CUDA_SUCCESS=0, cudaSuccess=0, CU_MEM_LOCATION_TYPE_DEVICE=1,
              CU_MEM_ACCESS_FLAGS_PROT_READWRITE=3,
              CU_DEVICE_ATTRIBUTE_VIRTUAL_MEMORY_MANAGEMENT_SUPPORTED=1,
              CU_MEM_ALLOC_GRANULARITY_RECOMMENDED=1;
int failure=0, cleanup_calls=0;
std::vector<std::string> calls;
int cudaGetDevice(int* p) { *p=0; return 0; }
int cudaGetLastError() { return 0; }
CUmemAllocationProp device_prop(int) { return {}; }
struct Vmm {
    bool ok=true;
    int create(CUmemGenericAllocationHandle* h, size_t, const CUmemAllocationProp*, int) const {
        calls.push_back("create"); *h=1; return failure==1 ? 701 : 0;
    }
    int map(CUdeviceptr,size_t,int,CUmemGenericAllocationHandle,int) const {
        calls.push_back("map"); return failure==2 ? 702 : 0;
    }
    int set_access(CUdeviceptr,size_t,const CUmemAccessDesc*,int) const {
        calls.push_back("access"); return failure==3 ? 703 : 0;
    }
    int unmap(CUdeviceptr,size_t) const { calls.push_back("unmap"); return 999; }
    int release(CUmemGenericAllocationHandle) const { calls.push_back("release"); return 998; }
    int device_get(CUdevice* d,int) const { *d=0; return 0; }
    int attribute(int* p,int,CUdevice) const { *p=1; return 0; }
    int granularity(size_t* p,const CUmemAllocationProp*,int) const { *p=64; return 0; }
    int reserve(CUdeviceptr* p,size_t,int,int,int) const { *p=4096; return 0; }
};
const Vmm& vmm() { static Vmm v; return v; }
struct ExpertCache {
    int64_t seg_=0,seg_req_=64,mapped_segs_=0,live_slots_=0;
    uint8_t* base_=nullptr;
    uint64_t reserved_=0;
    std::vector<unsigned long long> segs_;
    std::vector<int64_t> seg_size_;
    bool open_segmented(uint64_t,std::string&);
    bool grow(int64_t,std::string&);
    int64_t mapped_bytes() const { return mapped_segs_*64; }
    int64_t slots_within(int64_t bytes) const { return bytes/32; }
    void release_segmented() { ++cleanup_calls; }
};
// @CACHE_FUNCTIONS@
bool blob_present=true, transfer_ok=true;
int transfers=0;
struct Source { const uint8_t* blob_stable(int,int) { static uint8_t b; return blob_present ? &b : nullptr; } };
struct Cache {
    bool fill_slot_blocking(int,const uint8_t*,std::string& err,int64_t) {
        ++transfers; if (!transfer_ok) err="transfer failure 77"; return transfer_ok;
    }
};
namespace strata { namespace kernels { namespace cpu {
struct Layout { int blob_bytes(int) const { return 128; } };
Layout expert_layout() { return {}; }
}}}
int fill_profile(std::string& err) {
    Source source; Source* srcp=&source; Cache xcache;
    std::vector<std::pair<int,int>> profile{{2,3}};
    int i=0,slot=0;
    // @GENERATE_BLOCK@
    return 0;
}
int main(int argc, char**) {
    if (argc==1) {
    for (failure=1; failure<=3; ++failure) {
        calls.clear(); cleanup_calls=0;
        ExpertCache cache; std::string err="stale";
        assert(!cache.open_segmented(128,err));
        assert(err.find("cudaMalloc failed")!=std::string::npos); // Existing retry discriminator retained.
        const char* api=failure==1 ? "cuMemCreate" : failure==2 ? "cuMemMap" : "cuMemSetAccess";
        assert(err.find(api)!=std::string::npos);
        assert(err.find(std::to_string(700+failure))!=std::string::npos);
        assert(err.find("segment 1 of 2")!=std::string::npos);
        assert(err.find("64 bytes")!=std::string::npos);
        assert(cleanup_calls==1);
        std::vector<std::string> expected={"create"};
        if (failure>=2) expected.push_back("map");
        if (failure==3) { expected.push_back("access"); expected.push_back("unmap"); }
        if (failure>=2) expected.push_back("release");
        assert(calls==expected);
    }
    failure=0; calls.clear(); cleanup_calls=0;
    ExpertCache cache; std::string err;
    assert(cache.open_segmented(128,err) && cache.mapped_segs_==2 && cleanup_calls==0);
    assert((calls==std::vector<std::string>{"create","map","access","create","map","access"}));
    for (failure=1; failure<=3; ++failure) {
        calls.clear(); cache.mapped_segs_=0; cache.segs_.assign(2,0);
        assert(!cache.grow(128,err));
        const char* api=failure==1 ? "cuMemCreate" : failure==2 ? "cuMemMap" : "cuMemSetAccess";
        assert(err.find(api)!=std::string::npos);
        assert(err.find(std::to_string(700+failure))!=std::string::npos);
        assert(err.find("segment 1 of 2")!=std::string::npos && err.find("64 bytes")!=std::string::npos);
        assert(cache.mapped_segs_==0 && cache.live_slots_==0 && cache.segs_[0]==0 && cleanup_calls==0);
    }
    failure=0; calls.clear();
    assert(cache.grow(128,err) && cache.mapped_segs_==2 && cache.live_slots_==4 && cleanup_calls==0);
    assert((calls==std::vector<std::string>{"create","map","access","create","map","access"}));
    }
    std::string err;
    blob_present=false; err="stale cudaMalloc failure";
    assert(fill_profile(err)==1 && transfers==0);
    assert(err.find("blob acquisition failed")!=std::string::npos && err.find("unknown")!=std::string::npos);
    assert(err.find("stale")==std::string::npos);
    blob_present=true; transfer_ok=false; err="stale";
    assert(fill_profile(err)==1 && err=="transfer failure 77" && transfers==1);
    transfer_ok=true; assert(fill_profile(err)==0 && transfers==2);
    std::puts("CPU injected VMM/blob/transfer paths PASS; CUDA product compile/run NOT_RUN");
}
