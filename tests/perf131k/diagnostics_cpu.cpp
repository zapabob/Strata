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
int failure=0, cleanup_failure=0, reserves=0, unmaps=0, releases=0, address_frees=0;
using cudaError_t=int;
int cudaDeviceSynchronize() { return cleanup_failure==4 ? 997 : 0; }
std::vector<std::string> calls;
int cudaGetDevice(int* p) { *p=0; return 0; }
int cudaGetLastError() { return 0; }
const char* cudaGetErrorString(int) { return "fake"; }
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
    int unmap(CUdeviceptr,size_t) const { ++unmaps; calls.push_back("unmap"); return cleanup_failure==1 ? 999 : 0; }
    int release(CUmemGenericAllocationHandle) const { ++releases; calls.push_back("release"); return cleanup_failure==2 ? 998 : 0; }
    int address_free(CUdeviceptr,size_t) const { ++address_frees; return cleanup_failure==3 ? 996 : 0; }
    int device_get(CUdevice* d,int) const { *d=0; return 0; }
    int attribute(int* p,int,CUdevice) const { *p=1; return 0; }
    int granularity(size_t* p,const CUmemAllocationProp*,int) const { *p=64; return 0; }
    int reserve(CUdeviceptr* p,size_t,int,int,int) const { ++reserves; *p=4096; return 0; }
};
const Vmm& vmm() { static Vmm v; return v; }
struct ExpertCache {
    int64_t seg_=0,seg_req_=64,mapped_segs_=0,live_slots_=0;
    uint8_t* base_=nullptr;
    uint64_t reserved_=0;
    std::vector<unsigned long long> segs_;
    std::vector<int64_t> seg_size_;
    std::vector<char> seg_mapped_;
    bool cleanup_pending_=false;
    // @CACHE_VALID@
    int64_t full_bytes() const { return 128; }
    bool open_segmented(uint64_t,std::string&);
    bool grow(int64_t,std::string&);
    int64_t mapped_bytes() const;
    bool shrink(int64_t,std::string&);
    int64_t slots_within(int64_t bytes) const { return bytes/32; }
    void release_segmented();
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
        calls.clear(); cleanup_failure=0;
        ExpertCache cache; std::string err="stale";
        assert(!cache.open_segmented(128,err));
        assert(err.find("cudaMalloc failed")!=std::string::npos);
        const char* api=failure==1 ? "cuMemCreate" : failure==2 ? "cuMemMap" : "cuMemSetAccess";
        assert(err.find(api)!=std::string::npos && err.find(std::to_string(700+failure))!=std::string::npos);
        assert(!cache.cleanup_pending_ && cache.base_==nullptr && cache.mapped_bytes()==0);
        assert(cache.segs_.empty() && cache.seg_mapped_.empty());
    }
    failure=0;
    for (int kind=1;kind<=4;++kind) {
        cleanup_failure=0;
        ExpertCache cache; std::string err;
        assert(cache.open_segmented(128,err) && cache.mapped_bytes()==128 && cache.valid());
        const int before_reserves=reserves;
        cleanup_failure=kind;
        cache.release_segmented();
        assert(cache.cleanup_pending_ && cache.base_!=nullptr && cache.reserved_==128);
        assert(cache.mapped_bytes()==-1 && !cache.valid() && cache.live_slots_==0);
        assert(!cache.open_segmented(64,err) && reserves==before_reserves);
        assert(err.find("ownership")!=std::string::npos);
        assert(!cache.grow(128,err) && !cache.shrink(0,err));
        const int before_unmaps=unmaps;
        cache.release_segmented();
        if(kind==2 || kind==3) assert(unmaps==before_unmaps); // unmapped segments are not unmapped twice
        assert(cache.cleanup_pending_ && cache.mapped_bytes()==-1);
        cleanup_failure=0;
        cache.release_segmented();
        assert(!cache.cleanup_pending_ && cache.base_==nullptr && cache.reserved_==0 && cache.mapped_bytes()==0);
        assert(cache.open_segmented(64,err) && cache.valid());
        cache.release_segmented();
    }
    // Rollback of a segment whose access setup failed retains its handle/mapping.
    for(int kind=1;kind<=2;++kind) {
        failure=3;cleanup_failure=kind;
        ExpertCache cache;std::string err;
        assert(!cache.open_segmented(128,err));
        assert(cache.cleanup_pending_ && cache.segs_[0]!=0 && cache.mapped_bytes()==-1);
        assert(cache.seg_mapped_[0]==(kind==1));
        assert(err.find("CUresult=703")!=std::string::npos);
        assert(err.find("cudaMalloc failed")==std::string::npos); // unknown ownership cannot enter the smaller retry
        int before=reserves;
        assert(!cache.open_segmented(64,err) && reserves==before);
        cleanup_failure=0;cache.release_segmented();
        assert(!cache.cleanup_pending_ && cache.base_==nullptr);
    }
    failure=0;cleanup_failure=0;
    ExpertCache cache;std::string err;
    assert(cache.open_segmented(128,err));
    assert(cache.shrink(0,err) && cache.mapped_bytes()==0);
    failure=3;cleanup_failure=1;
    assert(!cache.grow(128,err) && cache.cleanup_pending_ && cache.segs_[0]!=0 && cache.mapped_bytes()==-1);
    assert(!cache.grow(128,err));
    failure=0;cleanup_failure=0;cache.release_segmented();
    assert(!cache.cleanup_pending_ && cache.mapped_bytes()==0);
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
