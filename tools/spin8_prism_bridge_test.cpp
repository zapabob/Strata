#include "ggml-spin8.h"
#include "ggml-backend.h"
#include "ggml-cpu.h"
#include "ggml-cpp.h"
#include <cmath>
#include <cstring>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <vector>

static void require(bool ok, const char * message) { if (!ok) { throw std::runtime_error(message); } }
static void unrelated(ggml_tensor *, int, int, void *) {}

static void run(bool cuda, bool identity, size_t width) {
    constexpr size_t heads=6,tokens=19,padding=5;
    const size_t stride=width+padding;
    std::vector<float> input(stride*heads*tokens,123.0f);
    for(size_t t=0;t<tokens;++t) for(size_t h=0;h<heads;++h) for(size_t i=0;i<width;++i) {
        input[(t*heads+h)*stride+i]=float(std::sin(double(17*t+3*h+i))*0.7);
    }
    input[0]=-0.0f;
    std::vector<float> win(heads*8*width),bin(heads*8),wout(heads*56),bout(heads*7);
    for(size_t i=0;i<win.size();++i) { win[i]=float(0.003*std::sin(double(i))); }
    if(!identity) {
        for(size_t i=0;i<wout.size();++i) { wout[i]=float(0.07*std::cos(double(i))); }
        for(size_t i=0;i<bout.size();++i) { bout[i]=float(0.04*std::sin(double(i+1))); }
    }
    spin8_query_adapter_layer_view view{}; view.spec={3,heads,2,uint32_t(width)};
    view.win=win.data();view.bin=bin.data();view.wout=wout.data();view.bout=bout.data();
    view.win_bytes=win.size()*4;view.bin_bytes=bin.size()*4;view.wout_bytes=wout.size()*4;view.bout_bytes=bout.size()*4;
    std::unique_ptr<ggml_spin8_state,decltype(&ggml_spin8_state_free)> state(ggml_spin8_state_create(),ggml_spin8_state_free);
    std::unique_ptr<ggml_spin8_layer,decltype(&ggml_spin8_layer_free)> layer(ggml_spin8_layer_create(state.get(),view),ggml_spin8_layer_free);
    ggml_context_ptr data(ggml_init({ggml_tensor_overhead()*4,nullptr,true}));
    auto * storage=ggml_new_tensor_3d(data.get(),GGML_TYPE_F32,stride,heads,tokens);
    auto * q=ggml_view_3d(data.get(),storage,width,heads,tokens,stride*4,stride*heads*4,0);
    auto * bank=ggml_new_tensor_1d(data.get(),GGML_TYPE_F32,heads*(8*width+71));
    ggml_backend_buffer_ptr buffer(ggml_backend_alloc_ctx_tensors_from_buft(data.get(),ggml_backend_cpu_buffer_type()));
    require(bool(buffer),"host allocation"); ggml_backend_tensor_set(storage,input.data(),0,input.size()*4);
    size_t offset=0;for(const auto * array : {&win,&bin,&wout,&bout}) {
        ggml_backend_tensor_set(bank,array->data(),offset,array->size()*4);offset+=array->size()*4;
    }
    ggml_context_ptr graph_ctx(ggml_init({ggml_tensor_overhead()*8+ggml_graph_overhead_custom(32,false),nullptr,true}));
    auto * result=ggml_spin8_query(graph_ctx.get(),q,bank,layer.get());
    ggml_tensor * args[]={q};
    auto * foreign=ggml_custom_4d(graph_ctx.get(),GGML_TYPE_F32,width,heads,tokens,1,args,1,unrelated,1,reinterpret_cast<void *>(uintptr_t(1)));
    require(!ggml_spin8_match(foreign),"foreign userdata inspected");
    auto * graph=ggml_new_graph_custom(graph_ctx.get(),32,false);ggml_build_forward_expand(graph,result);
    ggml_backend_ptr cpu(ggml_backend_init_by_type(GGML_BACKEND_DEVICE_TYPE_CPU,nullptr));
    ggml_backend_ptr gpu(cuda?ggml_backend_init_by_type(GGML_BACKEND_DEVICE_TYPE_GPU,nullptr):nullptr);
    require(bool(cpu)&&(!cuda||bool(gpu)),"requested backend unavailable");
    ggml_backend_t backends[]={cuda?gpu.get():cpu.get(),cpu.get()};
    ggml_backend_sched_ptr sched(ggml_backend_sched_new(backends,nullptr,cuda?2:1,32,false,true));
    require(bool(sched),"scheduler allocation");
    if(cuda) { require(!ggml_backend_supports_op(gpu.get(),foreign),"foreign custom advertised as CUDA"); }
    require(ggml_backend_supports_op(backends[0],result),"requested operation unsupported");
    ggml_backend_sched_set_tensor_backend(sched.get(),result,backends[0]);
    require(ggml_backend_sched_alloc_graph(sched.get(),graph),"explicit graph allocation");
    require(ggml_backend_sched_get_tensor_backend(sched.get(),result)==backends[0],"requested placement changed");
    std::vector<float> expected(width*heads*tokens),actual(expected.size());
    for(size_t h=0;h<heads;++h) {
        require(spin8_query_v3_controller_apply(layer->cpu[h],SPIN8_F32,input.data()+h*stride,
            (input.size()-h*stride)*4,stride*heads,expected.data()+h*width,
            (expected.size()-h*width)*4,width*heads,tokens)==SPIN8_OK,"reference execution");
    }
    for(int repeat=0;repeat<3;++repeat) {
        require(ggml_backend_sched_graph_compute(sched.get(),graph)==GGML_STATUS_SUCCESS,"graph execution");
        require(ggml_spin8_state_check(state.get())==0,"backend invariant");
        ggml_backend_tensor_get(result,actual.data(),0,actual.size()*4);
        double max_error=0;
        for(size_t i=0;i<actual.size();++i) { require(std::isfinite(actual[i]),"nonfinite output");max_error=std::max(max_error,std::abs(double(actual[i])-expected[i])); }
        require(identity?memcmp(actual.data(),expected.data(),actual.size()*4)==0:max_error<=2e-6,"numerical agreement");
        // Non-block tails participate in controller, but copy bitwise.
        for(size_t r=0;r<heads*tokens;++r) for(size_t i=width-width%8;i<width;++i) {
            require(memcmp(&actual[r*width+i],&input[r*stride+i],4)==0,"tail changed");
        }
    }
    std::cout << "dispatch CPU=" << state->cpu_calls.load() << " CUDA=" << state->cuda_calls.load() << std::endl;
    require(cuda?state->cuda_calls.load()==3:state->cpu_calls.load()==3,"actual dispatch counter");
    require(cuda?state->cpu_calls.load()==0:state->cuda_calls.load()==0,"hidden fallback");
    std::cout << "bridge device=" << (cuda?"CUDA":"CPU") << " width=" << width << " identity=" << identity << " passed\n";
    // Real backend fault on a source row; the sticky backend state survives reuse.
    const float nan=std::numeric_limits<float>::quiet_NaN();
    ggml_backend_tensor_set(storage,&nan,0,4);
    require(ggml_backend_sched_graph_compute(sched.get(),graph)==GGML_STATUS_SUCCESS,"fault graph scheduling");
    require(ggml_spin8_state_check(state.get())!=0,"nonfinite source accepted");
    const float finite=1.0f;ggml_backend_tensor_set(storage,&finite,0,4);
    require(ggml_backend_sched_graph_compute(sched.get(),graph)==GGML_STATUS_SUCCESS,"sticky graph scheduling");
    require(ggml_spin8_state_check(state.get())!=0,"backend fault was reset");
    ggml_backend_sched_synchronize(sched.get());
}
int main() {
    try {
        ggml_backend_load_all();
        for(bool cuda : {false,true}) for(bool identity : {false,true}) for(size_t width : {size_t(13),size_t(256)}) { run(cuda,identity,width); }
        return 0;
    } catch(const std::exception & error) { std::cerr << error.what() << '\n';return 1; }
}
