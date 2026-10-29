// Independent CPU GGML reference for the existing PLE capture format.
// Model operations follow ggml-org/llama.cpp 3cf03257, src/models/qwen4exp.cpp.
// No Strata headers, kernels, decoder or implementation are linked.
#include "ggml.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

static void require(bool ok, const char * why) { if (!ok) throw std::runtime_error(why); }
template<class T> static std::vector<T> read(std::istream & file, size_t count) {
    std::vector<T> result(count);
    file.read(reinterpret_cast<char *>(result.data()), static_cast<std::streamsize>(count*sizeof(T)));
    require(bool(file), "Truncated input");
    return result;
}
static std::vector<uint8_t> region(const char * path, uint64_t offset, size_t count) {
    std::ifstream file(path, std::ios::binary); require(bool(file), "Cannot open original GGUF");
    file.seekg(static_cast<std::streamoff>(offset)); return read<uint8_t>(file, count);
}
static void finite(const std::vector<float> & values) {
    for (float value : values) require(std::isfinite(value), "Non-finite input");
}
static void equal_decode(ggml_type type, const std::vector<uint8_t> & raw, const std::vector<float> & want) {
    const auto * traits=ggml_get_type_traits(type); require(traits && traits->to_float, "Missing upstream decoder");
    std::vector<float> got(want.size()); traits->to_float(raw.data(),got.data(),static_cast<int64_t>(got.size()));
    require(std::memcmp(got.data(),want.data(),got.size()*sizeof(float))==0,
            "Canonical weight planes differ from the original GGUF's upstream decode");
}
int main(int argc,char ** argv) try {
    require(argc==6,"usage: ple_capture_oracle INPUT OUTPUT ORIGINAL_GGUF KEY_ABSOLUTE_OFFSET VALUE_ABSOLUTE_OFFSET");
    std::ifstream input(argv[1],std::ios::binary); require(bool(input),"Cannot open capture input");
    auto h=read<int32_t>(input,5); auto epsilon=read<float>(input,1);
    const int64_t d=h[0],heads=h[1],tokens=h[2],taps=h[3],dilation=h[4],channels=d*heads,history=(taps-1)*dilation;
    require(d==2560&&heads==4&&tokens>=2&&tokens<=64&&taps==4&&dilation==3&&epsilon[0]==1e-6f,"Unexpected model geometry");
    auto embedding=read<float>(input,tokens*d),hidden=read<float>(input,tokens*channels);
    auto key_weight=read<float>(input,channels*d),value_weight=read<float>(input,d*d);
    auto nk=read<float>(input,channels),nq=read<float>(input,channels),nc=read<float>(input,channels);
    auto convolution=read<float>(input,channels*taps),past=read<float>(input,history*channels);
    require(input.peek()==std::char_traits<char>::eof(),"Unexpected capture input bytes");
    for (const auto * v : {&embedding,&hidden,&key_weight,&value_weight,&nk,&nq,&nc,&convolution,&past})finite(*v);
    const auto key_bytes=region(argv[3],std::stoull(argv[4]),static_cast<size_t>(ggml_row_size(GGML_TYPE_Q2_0,d)*channels));
    const auto value_bytes=region(argv[3],std::stoull(argv[5]),static_cast<size_t>(ggml_row_size(GGML_TYPE_BF16,d)*d));
    equal_decode(GGML_TYPE_Q2_0,key_bytes,key_weight); equal_decode(GGML_TYPE_BF16,value_bytes,value_weight);

    ggml_init_params parameters{512u*1024u*1024u,nullptr,false};
    std::unique_ptr<ggml_context,decltype(&ggml_free)> context(ggml_init(parameters),ggml_free);
    require(bool(context),"Cannot allocate GGML reference context"); auto * ctx=context.get();
    auto matrix=[&](const std::vector<float> & values,int64_t x,int64_t y) {
        auto * t=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,x,y); std::memcpy(t->data,values.data(),values.size()*sizeof(float)); return t;
    };
    auto * x=matrix(embedding,d,tokens),*residual=matrix(hidden,channels,tokens);
    // The capture contract includes an independent F32 stage check. Use the
    // original weights widened exactly, so activation quantization remains an
    // error measured in the CUDA path rather than contaminating its oracle.
    auto * kw=matrix(key_weight,d,channels),*vw=matrix(value_weight,d,d);
    auto * norm_key=matrix(nk,d,heads),*norm_query=matrix(nq,d,heads),*norm_conv=matrix(nc,d,heads);
    auto * conv_weights=matrix(convolution,taps,channels),*prior=matrix(past,history,channels);
    auto normalize=[&](ggml_tensor * data,ggml_tensor * weight) {
        auto * grouped=ggml_reshape_3d(ctx,data,d,heads,tokens);
        return ggml_mul(ctx,ggml_rms_norm(ctx,grouped,epsilon[0]),weight);
    };
    auto * projected_key=ggml_mul_mat(ctx,kw,x),*value=ggml_mul_mat(ctx,vw,x);
    auto * key=normalize(projected_key,norm_key),*query=normalize(residual,norm_query);
    auto * score=ggml_scale(ctx,ggml_sum_rows(ctx,ggml_mul(ctx,key,query)),1.0f/std::sqrt(static_cast<float>(d)));
    auto * magnitude=ggml_sqrt(ctx,ggml_clamp(ctx,ggml_abs(ctx,score),1e-6f,INFINITY));
    auto * gate=ggml_sigmoid(ctx,ggml_mul(ctx,ggml_sgn(ctx,score),magnitude));
    auto * broadcast=ggml_repeat_4d(ctx,ggml_reshape_3d(ctx,value,d,1,tokens),d,heads,tokens,1);
    auto * gated=ggml_mul(ctx,broadcast,gate);
    auto * normalized=ggml_reshape_2d(ctx,normalize(ggml_reshape_2d(ctx,gated,channels,tokens),norm_conv),channels,tokens);
    auto * rows=ggml_cont(ctx,ggml_transpose(ctx,normalized));
    auto * padded=ggml_concat(ctx,prior,rows,0);
    ggml_tensor * sum=nullptr;
    for(int64_t tap=0;tap<taps;++tap) {
        auto * window=ggml_view_2d(ctx,padded,tokens,channels,padded->nb[1],tap*dilation*sizeof(float));
        auto * shifted=ggml_cont(ctx,ggml_transpose(ctx,window));
        auto * column=ggml_cont(ctx,ggml_view_2d(ctx,conv_weights,1,channels,conv_weights->nb[1],tap*sizeof(float)));
        auto * weights=ggml_reshape_1d(ctx,column,channels);
        auto * term=ggml_mul(ctx,shifted,weights);sum=sum?ggml_add(ctx,sum,term):term;
    }
    auto * conv=ggml_silu(ctx,sum);
    auto * result=ggml_add(ctx,residual,ggml_add(ctx,ggml_reshape_2d(ctx,gated,channels,tokens),conv));
    auto * graph=ggml_new_graph(ctx);ggml_build_forward_expand(graph,result);
    require(ggml_graph_compute_with_ctx(ctx,graph,2)==GGML_STATUS_SUCCESS,"GGML reference computation failed");
    std::ofstream output(argv[2],std::ios::binary);require(bool(output),"Cannot create reference output");
    const int32_t oh[]={static_cast<int32_t>(d),static_cast<int32_t>(channels),static_cast<int32_t>(tokens)};
    output.write(reinterpret_cast<const char *>(oh),sizeof(oh));
    for(auto * tensor : {key,value,gate,gated,normalized,conv,result}) {
        require(tensor->type==GGML_TYPE_F32&&ggml_is_contiguous(tensor),"Unexpected reference tensor layout");
        auto * values=ggml_get_data_f32(tensor);
        for(int64_t i=0;i<ggml_nelements(tensor);++i)require(std::isfinite(values[i]),"Non-finite reference output");
        output.write(reinterpret_cast<const char *>(values),static_cast<std::streamsize>(ggml_nbytes(tensor)));
    }
    require(bool(output),"Reference output write failed");
    std::cout<<"Original Q2_0/BF16 weights match upstream decode bit for bit; CPU GGML captured seven PLE stages.\n";
    return 0;
} catch(const std::exception & error) {std::cerr<<error.what()<<"\n";return 1;}
