// Dump per-expert scales from the loaded runtime and verify recurrent pointer/packed-header identity.
#include <array>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#ifdef STRATA_SCALE_AUDIT
#include "ink_manifest.h"
#else
#include "llama-model.h"
#include "ggml-backend.h"
#endif

using Values = std::array<float,128>;
static void emit(std::ofstream &out,int slot,int layer,int proj,const Values &v) {
    const int ids[3]={slot,layer,proj};
    for(float x:v) if(!std::isfinite(x) || x<0) throw std::runtime_error("Invalid scale value");
    out.write(reinterpret_cast<const char*>(ids),sizeof(ids));
    out.write(reinterpret_cast<const char*>(v.data()),sizeof(v));
}

int main(int argc,char** argv) {
    if(argc!=3)return 2;
    try {
        std::ofstream out(argv[2],std::ios::binary);
        if(!out)throw std::runtime_error("Cannot open output");
#ifdef STRATA_SCALE_AUDIT
        ink2::InkModelFile mf;std::string error;
        if(!mf.open(argv[1],error,false) || !mf.gguf_adapter)throw std::runtime_error(error);
        if(mf.m.c.n_phys!=24 || mf.m.c.n_experts!=128 || mf.m.c.core_start!=6 || mf.m.c.core_end!=18)
            throw std::runtime_error("Unexpected recurrent topology");
        std::array<std::array<Values,2>,24> scales{};
        std::vector<uint8_t> body;
        for(int layer=0;layer<24;++layer) {
            const auto &meta=mf.gguf_adapter->layers.at(layer);
            for(int e=0;e<128;++e) {
                if(!mf.read_expert_body(mf.dir_index_of.at(layer*128+e),body,error))throw std::runtime_error(error);
                float gate,up,down;
                if(meta.is_nvfp4_to_sf4) {
                    float header[4];std::memcpy(header,body.data(),sizeof(header));
                    gate=up=header[0];down=header[2];
                } else {
                    strata::quant::sk::GgufExpertHeader header;
                    std::memcpy(&header,body.data(),sizeof(header));
                    gate=header.gate_scale;up=header.up_scale;down=header.dn_scale;
                }
                if(gate!=meta.gate_scale.at(e) || up!=meta.up_scale.at(e) || down!=meta.dn_scale.at(e))
                    throw std::runtime_error("Native expert-body scales differ");
                scales[layer][0][e]=gate;scales[layer][1][e]=down;
            }
        }
        for(int visit=0;visit<48;++visit) {
            int layer=visit<6?visit:(visit<42?6+(visit-6)%12:visit-24);
            for(int i=0;i<2;++i)emit(out,visit,layer,i,scales[layer][i]);
        }
#else
        ggml_backend_load_all();llama_backend_init();
        auto p=llama_model_default_params();p.n_gpu_layers=0;
        auto *m=llama_model_load_from_file(argv[1],p);
        if(!m || m->layers.size()!=48)throw std::runtime_error("Missing expanded runtime layers");
        for(int visit=0;visit<48;++visit) {
            int layer=visit<6?visit:(visit<42?6+(visit-6)%12:visit-24);
            int slot=visit<18?layer:(visit<42?24+visit-18:layer);
            const auto &v=m->layers.at(slot),&base=m->layers.at(layer);
            if(v.ffn_up_exps_s!=base.ffn_up_exps_s || v.ffn_down_exps_s!=base.ffn_down_exps_s ||
               v.ffn_gate_up_exps!=base.ffn_gate_up_exps || v.ffn_down_exps!=base.ffn_down_exps ||
               v.ffn_up_exps_in_s!=base.ffn_up_exps_in_s || v.ffn_down_exps_in_s!=base.ffn_down_exps_in_s)
                throw std::runtime_error("Repeated slot is missing its physical expert tensor or scale");
            for(int proj=0;proj<2;++proj) {
                auto *w=proj?v.ffn_down_exps:v.ffn_gate_up_exps;
                auto *s=proj?v.ffn_down_exps_s:v.ffn_up_exps_s;
                if(!w || (w->type==GGML_TYPE_NVFP4 && !s))throw std::runtime_error("Missing NVFP4 scale");
                Values values;values.fill(1);
                if(s) {
                    if(s->type!=GGML_TYPE_F32 || ggml_nelements(s)!=128)throw std::runtime_error("Scale shape");
                    ggml_backend_tensor_get(s,values.data(),0,sizeof(values));
                }
                emit(out,visit,layer,proj,values);
            }
        }
        llama_model_free(m);llama_backend_free();
#endif
        out.close();if(!out)throw std::runtime_error("Incomplete scale file");
        return 0;
    } catch(const std::exception &e) { std::cerr<<e.what()<<"\n"; return 1; }
}
