// Real-model integration test. One immutable loaded model, sequential contexts.
// Private access inspects owned test state and corrupts an ephemeral test bank.
#include "llama.h"
#include "llama-context.h"
#include "llama-sampler.h"
#include "ggml-backend.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#include <cctype>
#endif

static void require(bool ok, const char * what) {
    if (!ok) { throw std::runtime_error(what); }
}
static int sampler_initializations=0;
static int constructor_sampler_initializations=0;
static bool trap_constructor_sampler_init(llama_sampler *, ggml_backend_buffer_type_t, uint32_t) {
    ++constructor_sampler_initializations;
    return true;
}
static bool trap_sampler_init(llama_sampler *, ggml_backend_buffer_type_t, uint32_t) {
    ++sampler_initializations;
    return true;
}
static void trap_sampler_apply(llama_sampler *, ggml_context *, ggml_cgraph *, llama_sampler_data *) {
    throw std::runtime_error("rejected sampler executed");
}
static void record_libraries() {
#ifdef _WIN32
    char filename[32768]{};
    require(GetModuleFileNameA(nullptr,filename,sizeof(filename))>0,"executable path");
    auto normalize=[](std::string path) {
        std::replace(path.begin(),path.end(),'\\','/');
        std::transform(path.begin(),path.end(),path.begin(),[](unsigned char c) { return char(std::tolower(c)); });
        return path;
    };
    const auto executable=normalize(filename);
    const auto directory=executable.substr(0,executable.find_last_of('/')+1);
    for(const char * name : {"llama.dll","ggml.dll","ggml-base.dll","ggml-cpu.dll","ggml-cuda.dll"}) {
        const auto module=GetModuleHandleA(name);require(module,"candidate dependency missing");
        require(GetModuleFileNameA(module,filename,sizeof(filename))>0,"candidate dependency path");
        require(normalize(filename)==directory+name,"mixed candidate DLL provenance");
        std::cout << "dependency=" << filename << std::endl;
    }
#endif
}
using context_ptr = std::unique_ptr<llama_context, decltype(&llama_free)>;
static std::string info(llama_context * ctx) {
    std::vector<char> text(llama_spin8_query_info(ctx, nullptr, 0));
    require(!text.empty(), "diagnostic info unavailable");
    require(llama_spin8_query_info(ctx, text.data(), text.size()) == text.size(), "diagnostic size changed");
    return text.data();
}
static void save_text(const std::string & path, const std::string & value) {
    std::ofstream out(path, std::ios::binary); out << value << '\n'; require(bool(out), "write evidence");
}
static void save_logits(const std::string & path, const std::vector<float> & values) {
    std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<const char *>(values.data()),values.size()*sizeof(float));
    require(bool(out),"write logits");
}
static std::vector<float> decode(llama_context * ctx, std::vector<llama_token> tokens, int vocab) {
    auto batch = llama_batch_get_one(tokens.data(), int32_t(tokens.size()));
    require(llama_decode(ctx, batch) == 0, "decode failed");
    const auto * logits = llama_get_logits_ith(ctx, -1); require(logits, "missing logits");
    std::vector<float> result(logits, logits+vocab);
    for (float value : result) { require(std::isfinite(value), "nonfinite logits"); }
    return result;
}
static float max_error(const std::vector<float> & a, const std::vector<float> & b) {
    float result=0; for (size_t i=0;i<a.size();++i) { result=std::max(result,std::abs(a[i]-b[i])); } return result;
}
int main(int argc, char ** argv) {
    try {
        require(argc == 3, "usage: test MODEL OUTPUT_DIR");
        const std::string output=argv[2];
        ggml_backend_load_all(); llama_backend_init();
        record_libraries();
        auto mp=llama_model_default_params(); mp.n_gpu_layers=999; mp.spin8_hash_model=true;
        auto direct_io=mp; direct_io.load_mode=LLAMA_LOAD_MODE_DIRECT_IO;
        std::unique_ptr<llama_model, decltype(&llama_model_free)> rejected(
            llama_model_load_from_file(argv[1],direct_io),llama_model_free);
        require(!rejected,"explicit direct-I/O hashing mode accepted");
        std::cout << "SPIN8_DIRECT_IO_REJECTED" << std::endl;
        std::unique_ptr<llama_model, decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1],mp),llama_model_free);
        require(bool(model),"model load failed");
        auto cp=llama_context_default_params(); cp.n_ctx=512; cp.n_batch=64; cp.n_ubatch=64;
        cp.n_seq_max=1; cp.n_threads=4; cp.n_threads_batch=4;
        cp.flash_attn_type=LLAMA_FLASH_ATTN_TYPE_ENABLED; cp.type_k=GGML_TYPE_F16; cp.type_v=GGML_TYPE_F16;
        cp.spin8_query_inspect=true;
        auto make=[&](const char * sidecar) {
            cp.spin8_query_sidecar=sidecar;
            return context_ptr(llama_init_from_model(model.get(),cp),llama_free);
        };
        auto off=make(nullptr); require(bool(off),"inspection context failed");
        save_text(output+"/bindings.json",info(off.get()));
        std::cout << "SPIN8_BINDINGS_READY" << std::endl;
        std::string ready; require(bool(std::getline(std::cin,ready)) && ready=="SIDECARS_READY","sidecar handshake");
        const auto * vocab=llama_model_get_vocab(model.get()); const int nv=llama_vocab_n_tokens(vocab);
        const std::string prompt="A short test: one, two, three. The next number is";
        std::vector<llama_token> tokens(128);
        const int nt=llama_tokenize(vocab,prompt.data(),int(prompt.size()),tokens.data(),int(tokens.size()),true,true);
        require(nt>1,"prefill token count"); tokens.resize(nt);
        auto off_prefill=decode(off.get(),tokens,nv);
        const auto next=llama_token(std::max_element(off_prefill.begin(),off_prefill.end())-off_prefill.begin());
        auto off_decode=decode(off.get(),{next},nv);
        save_logits(output+"/off-prefill.f32",off_prefill);save_logits(output+"/off-decode.f32",off_decode);
        std::vector<uint8_t> off_state(llama_state_get_size(off.get()));
        require(llama_state_get_data(off.get(),off_state.data(),off_state.size())==off_state.size(),"off state save");
        off.reset();
        const std::string zero_path=output+"/zero.sp8q", nonzero_path=output+"/nonzero.sp8q";
        auto zero=make(zero_path.c_str()); require(bool(zero),"zero context failed");
        auto zero_prefill=decode(zero.get(),tokens,nv); auto zero_decode=decode(zero.get(),{next},nv);
        // Declared contract: exact F32 logits and greedy token for zero adapter.
        require(memcmp(off_prefill.data(),zero_prefill.data(),nv*sizeof(float))==0,"zero prefill logits differ");
        require(memcmp(off_decode.data(),zero_decode.data(),nv*sizeof(float))==0,"zero decode logits differ");
        std::vector<uint8_t> full(llama_state_get_size(zero.get()));
        require(full.size()>off_state.size(),"enabled provenance absent");
        require(llama_state_get_data(zero.get(),full.data(),full.size())==full.size(),"enabled state save");
        const size_t sequence_size=llama_state_seq_get_size(zero.get(),0);
        std::vector<uint8_t> sequence(sequence_size);
        require(llama_state_seq_get_data(zero.get(),sequence.data(),sequence.size(),0)==sequence.size(),"sequence save");
        require(llama_state_save_file(zero.get(),(output+"/full.state").c_str(),tokens.data(),tokens.size()),"full file save");
        require(llama_state_seq_save_file(zero.get(),(output+"/sequence.state").c_str(),0,tokens.data(),tokens.size())>0,"sequence file save");
        auto continuation=decode(zero.get(),{next},nv);
        require(llama_state_set_data(zero.get(),full.data(),full.size())==full.size(),"full restore");
        require(max_error(continuation,decode(zero.get(),{next},nv))==0,"full restored logits differ");
        llama_memory_clear(llama_get_memory(zero.get()),true);
        require(llama_state_seq_set_data(zero.get(),sequence.data(),sequence.size(),0)==sequence.size(),"sequence restore");
        require(max_error(continuation,decode(zero.get(),{next},nv))==0,"sequence restored logits differ");
        std::vector<llama_token> loaded_tokens(128); size_t loaded_count=0;
        require(llama_state_load_file(zero.get(),(output+"/full.state").c_str(),loaded_tokens.data(),loaded_tokens.size(),&loaded_count),"full file restore");
        require(loaded_count==tokens.size() && std::equal(tokens.begin(),tokens.end(),loaded_tokens.begin()),"file token roundtrip");
        require(max_error(continuation,decode(zero.get(),{next},nv))==0,"full file logits differ");
        llama_memory_clear(llama_get_memory(zero.get()),true);
        require(llama_state_seq_load_file(zero.get(),(output+"/sequence.state").c_str(),0,loaded_tokens.data(),loaded_tokens.size(),&loaded_count)>0,"sequence file restore");
        require(max_error(continuation,decode(zero.get(),{next},nv))==0,"sequence file logits differ");
        save_text(output+"/zero-info.json",info(zero.get()));
        require(zero->spin8_query->state->cuda_calls.load()>=16*5,"missing CUDA dispatch");
        require(zero->spin8_query->state->cpu_calls.load()==0,"unexpected CPU fallback");
        require(zero->spin8_query->layers.size()==16,"regular attention layer coverage");
        for (const auto & entry : zero->spin8_query->layers) {
            require(entry.second->cuda_calls.load()==7 && entry.second->cpu_calls.load()==0,"per-layer CUDA coverage");
        }
        // Rejection is before reading even an invalid adapter pointer or mutating state.
        std::vector<uint8_t> before_refusal(llama_state_get_size(zero.get()));
        require(llama_state_get_data(zero.get(),before_refusal.data(),before_refusal.size())==before_refusal.size(),"pre-refusal state");
        require(llama_set_adapters_lora(zero.get(),nullptr,1,nullptr)==-1,"runtime LoRA accepted");
        require(llama_set_adapter_cvec(zero.get(),nullptr,0,0,0,0)==-1,"runtime cvec accepted");
        // Keep the genuine chain interface so the upstream constructor would
        // accept it. Instrument its child, and inspect the chain's init state.
        auto * construction_sampler=llama_sampler_chain_init(llama_sampler_chain_default_params());
        auto * construction_child=llama_sampler_init_greedy();
        auto * child_iface=construction_child->iface;
        auto construction_iface=*child_iface;
        construction_iface.backend_init=trap_constructor_sampler_init;
        construction_iface.backend_apply=trap_sampler_apply;
        construction_child->iface=&construction_iface;
        llama_sampler_chain_add(construction_sampler,construction_child);
        const auto * construction_chain=static_cast<const llama_sampler_chain *>(construction_sampler->ctx);
        const auto chain_before=*construction_chain;
        llama_sampler_seq_config config{0,construction_sampler};
        auto refused_params=cp;
        refused_params.n_samplers=1; refused_params.samplers=&config;
        refused_params.spin8_query_inspect=false; // sidecar request alone
        context_ptr refused_sidecar(llama_init_from_model(model.get(),refused_params),llama_free);
        require(!refused_sidecar,"constructor accepted backend sampler with sidecar");
        refused_params.spin8_query_sidecar=nullptr; refused_params.spin8_query_inspect=true;
        context_ptr refused_inspect(llama_init_from_model(model.get(),refused_params),llama_free);
        require(!refused_inspect,"constructor accepted backend sampler with inspection");
        require(constructor_sampler_initializations==0,"constructor initialized sampler before rejection");
        require(construction_chain->is_init==chain_before.is_init && !construction_chain->is_init &&
                construction_chain->n_nodes==chain_before.n_nodes &&
                construction_chain->samplers.size()==1 &&
                construction_chain->samplers[0].ptr==construction_child &&
                construction_chain->samplers[0].is_backend==chain_before.samplers[0].is_backend &&
                construction_chain->cur.empty() &&
                construction_chain->t_sample_us==chain_before.t_sample_us &&
                construction_chain->n_sample==chain_before.n_sample &&
                construction_child->iface==&construction_iface,
                "constructor refusal mutated caller-owned sampler");
        // Prove the count/request guard also precedes configuration dereference.
        refused_params.samplers=reinterpret_cast<llama_sampler_seq_config *>(uintptr_t(1));
        context_ptr refused_pointer(llama_init_from_model(model.get(),refused_params),llama_free);
        require(!refused_pointer,"constructor dereferenced unsupported sampler configuration");
        construction_child->iface=child_iface;
        llama_sampler_free(construction_sampler);
        save_text(output+"/constructor-refusal-result.json","{\"sidecarRejected\":true,\"inspectionRejected\":true,\"invalidConfigRejected\":true,\"samplerInitializations\":0,\"samplerUnchanged\":true}");
        auto * sampler=llama_sampler_chain_init(llama_sampler_chain_default_params());
        llama_sampler_chain_add(sampler,llama_sampler_init_greedy());
        auto * original_iface=sampler->iface;
        auto trap_iface=*original_iface;
        trap_iface.backend_init=trap_sampler_init;
        trap_iface.backend_apply=trap_sampler_apply;
        sampler->iface=&trap_iface;
        require(!llama_set_sampler(zero.get(),0,sampler),"runtime sampler accepted by public API");
        require(!llama_set_sampler(zero.get(),0,nullptr),"sampler removal accepted on unsupported context");
        require(sampler_initializations==0,"sampler initialized before rejection");
        sampler->iface=original_iface;
        llama_sampler_free(sampler);
        require(!zero->spin8_query->failed,"rejected runtime adapter mutated context");
        std::vector<uint8_t> after_refusal(llama_state_get_size(zero.get()));
        require(llama_state_get_data(zero.get(),after_refusal.data(),after_refusal.size())==after_refusal.size(),"post-refusal state");
        require(before_refusal==after_refusal,"refusal mutated hybrid state");
        require(llama_state_set_data(zero.get(),full.data(),full.size())==full.size(),"post-refusal restore");
        require(max_error(continuation,decode(zero.get(),{next},nv))==0,"context unusable after refusal");
        save_text(output+"/refusal-result.json","{\"loraRejected\":true,\"samplerRejected\":true,\"samplerInitializations\":0,\"stateUnchanged\":true,\"continuedExactly\":true}");
        zero.reset();
        auto nonzero=make(nonzero_path.c_str()); require(bool(nonzero),"nonzero context failed");
        auto nz_prefill=decode(nonzero.get(),tokens,nv); auto nz_decode=decode(nonzero.get(),{next},nv);
        const float prefill_effect=max_error(off_prefill,nz_prefill),decode_effect=max_error(off_decode,nz_decode);
        require(prefill_effect>1e-5f && decode_effect>1e-5f,"nonzero effect absent");
        save_text(output+"/nonzero-info.json",info(nonzero.get()));
        require(llama_state_set_data(nonzero.get(),full.data(),full.size())==0,"cross-adapter state accepted");
        auto retry=llama_batch_get_one(tokens.data(),nt);
        require(llama_decode(nonzero.get(),retry)!=0,"failed context reused"); nonzero.reset();
        nonzero=make(nonzero_path.c_str()); require(bool(nonzero),"mismatch file context");
        require(llama_state_seq_load_file(nonzero.get(),(output+"/sequence.state").c_str(),0,loaded_tokens.data(),loaded_tokens.size(),&loaded_count)==0,"cross-adapter sequence file accepted");
        require(llama_decode(nonzero.get(),retry)!=0,"sequence file mismatch reused"); nonzero.reset();
        off=make(nullptr); require(bool(off),"off reconstruction failed");
        require(llama_state_seq_set_data(off.get(),sequence.data(),sequence.size(),0)==0,"enabled sequence accepted by off");
        require(llama_state_set_data(off.get(),off_state.data(),off_state.size())==off_state.size(),"legacy state regression"); off.reset();
        for(size_t truncated : {size_t(0),size_t(7),size_t(16),full.size()-1}) {
            auto ctx=make(zero_path.c_str()); require(bool(ctx),"truncated context creation");
            require(llama_state_set_data(ctx.get(),full.data(),truncated)==0,"truncated state accepted");
            require(llama_decode(ctx.get(),retry)!=0,"truncated failure reused");
        }
        auto fault=make(zero_path.c_str()); require(bool(fault),"fault context creation");
        const float nan=std::numeric_limits<float>::quiet_NaN();
        ggml_backend_tensor_set(fault->spin8_query->banks.begin()->second,&nan,0,sizeof(nan));
        require(llama_decode(fault.get(),retry)!=0,"actual device parameter fault accepted");
        require(llama_get_logits(fault.get())==nullptr,"failed logits exposed");
        require(fault->spin8_query->state->cuda_calls.load()>0,"fault did not execute CUDA");
        require(llama_decode(fault.get(),retry)!=0,"device fault context reused");
        require(llama_memory_seq_pos_max(llama_get_memory(fault.get()),0)==-1,"failed hybrid memory not cleared");
        save_text(output+"/fault-info.json",info(fault.get())); fault.reset();
        auto device_state=make(zero_path.c_str()); require(bool(device_state),"device-state rejection context");
        require(llama_state_seq_get_size_ext(device_state.get(),0,LLAMA_STATE_SEQ_FLAGS_ON_DEVICE)==0,"unsupported device state accepted");
        require(llama_decode(device_state.get(),retry)!=0,"device-state failure reused"); device_state.reset();
        auto incompatible=make(zero_path.c_str()); require(bool(incompatible),"off-state rejection context");
        require(llama_state_set_data(incompatible.get(),off_state.data(),off_state.size())==0,"off state accepted by enabled");
        require(llama_decode(incompatible.get(),retry)!=0,"off-state failure reused"); incompatible.reset();
        for(size_t truncated : {size_t(0),size_t(7),size_t(20),sequence.size()-1}) {
            auto ctx=make(zero_path.c_str()); require(bool(ctx),"sequence truncated context");
            require(llama_state_seq_set_data(ctx.get(),sequence.data(),truncated,0)==0,"truncated sequence accepted");
            require(llama_decode(ctx.get(),retry)!=0,"truncated sequence reused");
        }
        auto cancelled=make(zero_path.c_str()); require(bool(cancelled),"invalid batch context");
        decode(cancelled.get(),tokens,nv);
        llama_batch empty{};
        require(llama_decode(cancelled.get(),empty)!=0,"invalid batch accepted");
        require(llama_memory_seq_pos_max(llama_get_memory(cancelled.get()),0)==-1,"failed decode hybrid memory retained");
        require(llama_decode(cancelled.get(),retry)!=0,"failed decode reused"); cancelled.reset();
        for(const auto * invalid : {"wrong-binding","wrong-profile","wrong-position","wrong-geometry"}) {
            auto mismatch=make((output+"/"+invalid+".sp8q").c_str()); require(!mismatch,"wrong binding accepted");
        }
        save_text(output+"/result.json","{\"passed\":true,\"prefillTokens\":"+std::to_string(nt)+
            ",\"zeroLogitContract\":\"bitwise\",\"nonzeroPrefillMaxDelta\":"+std::to_string(prefill_effect)+
            ",\"nonzeroDecodeMaxDelta\":"+std::to_string(decode_effect)+"}");
        std::cout << "SPIN8_MODEL_PASS" << std::endl;
        return 0;
    } catch(const std::exception & error) { std::cerr << "SPIN8_MODEL_FAIL: " << error.what() << std::endl; return 1; }
}
