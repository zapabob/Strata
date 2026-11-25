// Record unmodified greedy decisions and the full-normaliser probabilities of Inkling's delimiters.
#include "llama.h"
#include "ggml-backend.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using Tokens = std::vector<llama_token>;
static constexpr int eos = 200006, eot = 200010, visible = 200004, user = 200000;

static Tokens read_ids(const fs::path &path, bool empty_ok = false) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    auto bytes = in.tellg();
    if (!in || bytes < 0 || (!empty_ok && bytes == 0) || bytes % 4 || bytes > 4*131072)
        throw std::runtime_error("Invalid token ID file: " + path.string());
    Tokens ids(size_t(bytes)/4);
    in.seekg(0); in.read(reinterpret_cast<char*>(ids.data()), bytes);
    if (!in) throw std::runtime_error("Truncated ID stream");
    return ids;
}

struct Context {
    llama_context *ctx;
    llama_batch batch;
    Context(llama_model *model, int capacity) : ctx(nullptr), batch(llama_batch_init(512, 0, 1)) {
        auto cp = llama_context_default_params();
        cp.n_ctx = capacity; cp.n_batch = 512; cp.n_ubatch = 128;
        cp.n_threads = 5; cp.n_threads_batch = 5;
        ctx = llama_init_from_model(model, cp);
        if (!ctx) { llama_batch_free(batch); throw std::runtime_error("Context allocation failed"); }
    }
    ~Context() { llama_batch_free(batch); llama_free(ctx); }
    void input(const llama_token *tokens, int n, int pos, bool all) {
        batch.n_tokens = n;
        for (int j = 0; j < n; ++j) {
            batch.token[j] = tokens[j]; batch.pos[j] = pos+j; batch.n_seq_id[j] = 1;
            batch.seq_id[j][0] = 0; batch.logits[j] = all || j+1 == n;
        }
        if (llama_decode(ctx, batch) != 0) throw std::runtime_error("Decoder rejected a token batch");
    }
};

static int execute(llama_model *model, const fs::path &work, int limit, int capacity, const std::string &mode) {
    const Tokens prompt = read_ids(work/"prompt.i32");
    const Tokens forced = read_ids(work/"prefix.i32", true);
    const bool restoring = fs::is_regular_file(work/"previous.state");
    const auto *vocab = llama_model_get_vocab(model);
    const int v = llama_vocab_n_tokens(vocab);
    auto valid = [v](llama_token i){return i >= 0 && i < v;};
    if (!std::all_of(prompt.begin(),prompt.end(),valid) || !std::all_of(forced.begin(),forced.end(),valid)
            || limit < int(forced.size()) || int(prompt.size())+limit > capacity)
        throw std::runtime_error("Invalid vocabulary, budget or context");
    if (std::string(llama_vocab_get_text(vocab,eos)) != "<|content_model_end_sampling|>" ||
        std::string(llama_vocab_get_text(vocab,eot)) != "<|end_message|>" ||
        std::string(llama_vocab_get_text(vocab,visible)) != "<|content_text|>" ||
        std::string(llama_vocab_get_text(vocab,user)) != "<|message_user|>")
        throw std::runtime_error("Model special tokens differ");
    Context c(model,capacity);
    Tokens sequence = prompt;
    std::ofstream log(work/"steps.tsv",std::ios::binary), raw(work/"ids.i32",std::ios::binary);
    if (!log || !raw) throw std::runtime_error("Cannot create output");
    log<<"index\tid\tgreedy\teos_probability\teog_probability\teot_probability\tvisible_probability\teos_margin\teot_margin\ttarget_nll\tforced\n"<<std::setprecision(15);
    std::vector<int> eogs;
    for (int i=0;i<v;++i) if (llama_vocab_is_eog(vocab,i)) eogs.push_back(i);
    auto record = [&](const float *z,int index,int target) {
        if (!z) throw std::runtime_error("Missing logits");
        int best=int(std::max_element(z,z+v)-z);
        double maximum=z[best], norm=0, second=-INFINITY;
        for(int i=0;i<v;++i) {
            if (!std::isfinite(z[i])) throw std::runtime_error("Non-finite logits");
            norm+=std::exp(double(z[i])-maximum);
            if(i!=best) second=std::max(second,double(z[i]));
        }
        const double lse=maximum+std::log(norm);
        auto prob=[&](int i){return std::exp(double(z[i])-lse);};
        auto margin=[&](int i){return double(z[i])-(i==best ? second : maximum);};
        double p_any=0;for(int i:eogs)p_any+=prob(i);
        int token=target<0?best:target;
        log<<index<<'\t'<<token<<'\t'<<best<<'\t'<<prob(eos)<<'\t'<<p_any<<'\t'<<prob(eot)
           <<'\t'<<prob(visible)<<'\t'<<margin(eos)<<'\t'<<margin(eot)<<'\t'<<(lse-z[token])<<'\t'<<(target>=0)<<'\n';
        if (index==1 || index==32 || index==128 || index==512 || index==1024 || index==2048 ||
            index==4096 || index==8192 || index==16384 || llama_vocab_is_eog(vocab,token) || token==eot) {
            std::ofstream dump(work/("logits-"+std::to_string(index)+".f32"),std::ios::binary);
            dump.write(reinterpret_cast<const char*>(z),std::streamsize(v)*4);
            if (!dump) throw std::runtime_error("Logit persistence failed");
        }
        raw.write(reinterpret_cast<const char*>(&token),4);
        return token;
    };
    size_t done=0;
    if (restoring) {
        if(forced.empty() || limit<=int(forced.size())) throw std::runtime_error("A restored KV state needs a pending token and a larger budget");
        sequence.insert(sequence.end(),forced.begin(),forced.end());
        Tokens saved(sequence.size());
        size_t count=0;
        if (!llama_state_seq_load_file(c.ctx,(work/"previous.state").string().c_str(),0,saved.data(),saved.size(),&count)
            || count!=sequence.size() || saved!=sequence) throw std::runtime_error("KV/token prefix mismatch");
        c.input(&sequence.back(),1,int(sequence.size()-1),false);
        raw.write(reinterpret_cast<const char*>(forced.data()),std::streamsize(forced.size())*4);
        done=forced.size();
    } else {
        for(int i=0;i<int(prompt.size());i+=512)
            c.input(prompt.data()+i,std::min(512,int(prompt.size())-i),i,false);
    }
    bool terminal=false;
    while (done<size_t(limit)) {
        // Teacher-forced replay uses the exact historical IDs. One-token decode reproduces decode shape.
        int target=done<forced.size()?forced[done]:-1;
        int emitted=record(llama_get_logits_ith(c.ctx,-1),int(done+1),target);
        sequence.push_back(emitted); ++done;
        terminal=llama_vocab_is_eog(vocab,emitted) || (mode=="legacy" && (emitted==eot || emitted==user));
        if (terminal && done<forced.size()) throw std::runtime_error("Historical trajectory crossed its stop policy");
        if (terminal || done==size_t(limit)) break;
        c.input(&sequence.back(),1,int(sequence.size()-1),false);
    }
    if(!terminal && mode!="teacher" && limit<16384) {
        auto tmp=work/"next.state.partial";
        if (!llama_state_seq_save_file(c.ctx,tmp.string().c_str(),0,sequence.data(),sequence.size()))
            throw std::runtime_error("KV save failed");
        fs::rename(tmp,work/"next.state");
    }
    log.close();raw.close();
    if(!log || !raw) throw std::runtime_error("Trajectory persistence failed");
    std::cout<<"TERMINATION "<<done<<" "<<terminal<<" "<<v<<" "<<restoring<<"\n";
    return 0;
}

int main(int argc,char **argv) {
    try {
        if(argc!=6) throw std::runtime_error("MODEL DIRECTORY LIMIT CAPACITY legacy|natural|teacher");
        std::string mode=argv[5];
        if(mode!="legacy" && mode!="natural" && mode!="teacher") throw std::runtime_error("Unknown protocol");
        ggml_backend_load_all();llama_backend_init();
        auto p=llama_model_default_params();p.n_gpu_layers=99;
        auto *model=llama_model_load_from_file(argv[1],p);
        if(!model)throw std::runtime_error("Model load failed");
        int rc=execute(model,argv[2],std::stoi(argv[3]),std::stoi(argv[4]),mode);
        llama_model_free(model);llama_backend_free();return rc;
    } catch(const std::exception &e) { std::cerr<<e.what()<<"\n"; return 1; }
}
