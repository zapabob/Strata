// Compile against the pristine pinned header, load only the preserved baseline
// DLLs, and emit real off-path logits for comparison with the integration build.
#include "llama.h"
#include "ggml-backend.h"
#include <windows.h>
#include <algorithm>
#include <cctype>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool ok, const char * text) { if (!ok) { throw std::runtime_error(text); } }
static HMODULE load_module(std::string path) {
    std::replace(path.begin(),path.end(),'/','\\');
    auto module=LoadLibraryExA(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);
    if(!module) { throw std::runtime_error("DLL load failed "+path+" winerror="+std::to_string(GetLastError())); }
    return module;
}
static void write(const std::string & path, const std::vector<float> & values) {
    std::ofstream file(path, std::ios::binary);
    file.write(reinterpret_cast<const char *>(values.data()), values.size()*sizeof(float));
    require(bool(file), "write logits");
}
int main(int argc, char ** argv) {
    try {
        require(argc==5,"usage: probe BASELINE_DLL_DIR MODEL OUTPUT_DIR CUDA_RUNTIME_DIR");
        const std::string bin=argv[1], output=argv[3];
        auto cublas=load_module(std::string(argv[4])+"/cublas64_13.dll");
        require(cublas,"load explicit CUDA runtime");
        auto library=load_module(bin+"/llama.dll"); require(library,"load baseline llama");
        auto ggml=load_module(bin+"/ggml.dll"); require(ggml,"load baseline ggml");
        char loaded[MAX_PATH]{};require(GetModuleFileNameA(library,loaded,MAX_PATH)>0,"loaded DLL path");
        std::cout << "loaded=" << loaded << '\n';
        auto load_backends=reinterpret_cast<decltype(&ggml_backend_load_all)>(GetProcAddress(ggml,"ggml_backend_load_all"));
        require(load_backends,"backend entry"); load_backends();
        auto normalize=[](std::string path) {
            std::replace(path.begin(),path.end(),'\\','/');
            std::transform(path.begin(),path.end(),path.begin(),[](unsigned char c) { return char(std::tolower(c)); });
            return path;
        };
        for(const char * name : {"llama.dll","ggml.dll","ggml-base.dll","ggml-cpu.dll","ggml-cuda.dll"}) {
            auto module=GetModuleHandleA(name);require(module,"baseline dependency missing");
            require(GetModuleFileNameA(module,loaded,MAX_PATH)>0,"dependency path");
            require(normalize(loaded)==normalize(bin+"/"+name),"mixed baseline DLL provenance");
            std::cout << "dependency=" << loaded << '\n';
        }
#define BIND(name) auto name=reinterpret_cast<decltype(&::name)>(GetProcAddress(library,#name)); require(name,#name)
        BIND(llama_backend_init); BIND(llama_model_default_params); BIND(llama_context_default_params);
        BIND(llama_model_load_from_file); BIND(llama_init_from_model); BIND(llama_model_get_vocab);
        BIND(llama_vocab_n_tokens); BIND(llama_tokenize); BIND(llama_batch_get_one); BIND(llama_decode);
        BIND(llama_get_logits_ith); BIND(llama_free); BIND(llama_model_free);
        llama_backend_init();
        auto mp=llama_model_default_params();mp.n_gpu_layers=999;
        auto * model=llama_model_load_from_file(argv[2],mp);require(model,"baseline model");
        auto cp=llama_context_default_params();cp.n_ctx=512;cp.n_batch=64;cp.n_ubatch=64;
        cp.n_seq_max=1;cp.n_threads=4;cp.n_threads_batch=4;
        cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_ENABLED;cp.type_k=GGML_TYPE_F16;cp.type_v=GGML_TYPE_F16;
        auto * ctx=llama_init_from_model(model,cp);require(ctx,"baseline context");
        const auto * vocab=llama_model_get_vocab(model);const int nv=llama_vocab_n_tokens(vocab);
        const std::string prompt="A short test: one, two, three. The next number is";
        std::vector<llama_token> tokens(128);
        const int nt=llama_tokenize(vocab,prompt.data(),int(prompt.size()),tokens.data(),int(tokens.size()),true,true);
        require(nt>1,"token count");tokens.resize(nt);
        require(llama_decode(ctx,llama_batch_get_one(tokens.data(),nt))==0,"baseline prefill");
        auto * logits=llama_get_logits_ith(ctx,-1);require(logits,"prefill logits");
        std::vector<float> prefill(logits,logits+nv);write(output+"/baseline-prefill.f32",prefill);
        auto token=llama_token(std::max_element(prefill.begin(),prefill.end())-prefill.begin());
        require(llama_decode(ctx,llama_batch_get_one(&token,1))==0,"baseline decode");
        logits=llama_get_logits_ith(ctx,-1);require(logits,"decode logits");
        write(output+"/baseline-decode.f32",std::vector<float>(logits,logits+nv));
        llama_free(ctx);llama_model_free(model);
        std::cout << "baseline passed prefill=" << nt << " vocabulary=" << nv << " greedy=" << token << '\n';
        return 0;
    } catch(const std::exception & error) { std::cerr << error.what() << '\n';return 1; }
}
