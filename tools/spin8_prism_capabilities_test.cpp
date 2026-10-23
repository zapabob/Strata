// Model-free capability test, run separately against CPU-only and CUDA builds.
#include "llama.h"
#include "ggml-backend.h"
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool value, const char * reason) {
    if (!value) { throw std::runtime_error(reason); }
}
int main(int argc, char ** argv) {
    try {
        require(argc==2 && (std::string(argv[1])=="0" || std::string(argv[1])=="1"),"expected CUDA build 0 or 1");
        ggml_backend_load_all();
        const size_t size=llama_spin8_query_info(nullptr,nullptr,0);
        require(size>1,"missing capability query");
        char sentinel='X';
        require(llama_spin8_query_info(nullptr,&sentinel,1)==size && sentinel=='X',"undersized output changed");
        std::vector<char> text(size);
        require(llama_spin8_query_info(nullptr,text.data(),text.size())==size,"unstable capability size");
        const std::string json=text.data();
        const auto contains=[&](const std::string & value) { return json.find(value)!=std::string::npos; };
        require(contains(std::string("\"compiled\":{\"cpu\":true,\"cuda\":")+(argv[1][0]=='1'?"true}":"false}")),"wrong compiled support");
        size_t cpus=0,gpus=0;
        for(size_t i=0;i<ggml_backend_dev_count();++i) {
            const auto reg=ggml_backend_dev_backend_reg(ggml_backend_dev_get(i));
            if(std::strcmp(ggml_backend_reg_name(reg),"CPU")==0) { ++cpus; }
            if(std::strcmp(ggml_backend_reg_name(reg),"CUDA")==0) { ++gpus; }
        }
        require(contains("\"runtime\":{\"cpuDevices\":"+std::to_string(cpus)+",\"cudaDevices\":"+std::to_string(gpus)+"}"),"wrong runtime availability");
        require(contains("\"cpuCalls\":0,\"cudaCalls\":0"),"availability mistaken for execution");
        require(contains("\"bindings\":null"),"model-free query fabricated bindings");
        std::cout << json << '\n';
        return 0;
    } catch(const std::exception & error) { std::cerr << error.what() << '\n'; return 1; }
}
