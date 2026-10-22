#include "llama-spin8.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <cstdio>
#include <cstdlib>

static void require(bool ok, const char * what) {
    if (!ok) { std::fprintf(stderr, "FAIL: %s\n", what); std::exit(1); }
}

int main(int argc, char ** argv) {
    require(argc == 2, "profile argument");
    double max_error = 0;
    for (int mode = 1; mode <= 4; ++mode) {
        auto cfg = llama_spin8::load(mode, argv[1]);
        for (int64_t d : {8, 16, 128, 256}) {
            ggml_context * ctx = ggml_init({64*1024*1024, nullptr, false});
            require(ctx != nullptr, "context allocation");
            constexpr int64_t nq = 2, nk = 3, heads = 4, kvheads = 2, streams = 2;
            auto * q = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, d, nq, heads, streams);
            auto * k = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, d, nk, kvheads, streams);
            std::array<ggml_tensor *, 3> matrices{};
            for (int v = 0; v < 3; ++v) {
                matrices[v] = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, 8, 8);
                std::copy(cfg->matrices[v].begin(), cfg->matrices[v].end(), static_cast<float *>(matrices[v]->data));
            }
            for (int64_t i = 0; i < ggml_nelements(q); ++i) { static_cast<float *>(q->data)[i] = std::sin(float(i)*0.17f); }
            for (int64_t i = 0; i < ggml_nelements(k); ++i) { static_cast<float *>(k->data)[i] = std::cos(float(i)*0.23f); }
            auto * scores = llama_spin8_scores(ctx, q, k, matrices, cfg->weights);
            auto * rotated = llama_spin8_rotate(ctx, matrices[1], q);
            auto * mask = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, nk, nq, 1, streams);
            std::fill_n(static_cast<float *>(mask->data), ggml_nelements(mask), 0.0f);
            static_cast<float *>(mask->data)[nk - 1] = -INFINITY;
            auto * probabilities = ggml_soft_max_ext(ctx, scores, mask, 1.0f/std::sqrt(float(d)), 0.0f);
            constexpr int64_t dv = 5;
            auto * v = ggml_new_tensor_4d(ctx, GGML_TYPE_F32, nk, dv, kvheads, streams);
            for (int64_t i = 0; i < ggml_nelements(v); ++i) { static_cast<float *>(v->data)[i] = std::sin(float(i)*0.11f); }
            auto * output = ggml_mul_mat(ctx, v, probabilities);
            auto * graph = ggml_new_graph(ctx);
            ggml_build_forward_expand(graph, output);
            ggml_build_forward_expand(graph, rotated);
            require(ggml_graph_compute_with_ctx(ctx, graph, 1) == GGML_STATUS_SUCCESS, "GGML compute");
            int softmax_count = 0;
            for (int i = 0; i < ggml_graph_n_nodes(graph); ++i) {
                softmax_count += ggml_graph_node(graph, i)->op == GGML_OP_SOFT_MAX;
            }
            require(softmax_count == 1, "one softmax");
            std::vector<float> expected_rot(size_t(ggml_nelements(q)));
            require(spin8_transform(cfg->plan.get(), SPIN8_SPIN_PLUS, SPIN8_F32, q->data, d,
                expected_rot.data(), d, size_t(ggml_nelements(q)/d), d, 0) == SPIN8_OK, "core transform");
            for (size_t i = 0; i < expected_rot.size(); ++i) {
                require(std::abs(expected_rot[i] - static_cast<float *>(rotated->data)[i]) < 2e-6, "core/GGML transform orientation");
            }
            for (int64_t s = 0; s < streams; ++s) for (int64_t h = 0; h < heads; ++h) for (int64_t qi = 0; qi < nq; ++qi) {
                const float * qr = static_cast<float *>(q->data) + d*(qi + nq*(h + heads*s));
                const float * kr = static_cast<float *>(k->data) + d*nk*(h/(heads/kvheads) + kvheads*s);
                std::array<float, nk> expected{};
                double weights[3];
                for (int view = 0; view < 3; ++view) { weights[view] = mode == 4 ? 1.0/3.0 : double(cfg->weights[view]); }
                require(spin8_matmul_f32(cfg->plan.get(), qr, 1, kr, nk, d, weights, expected.data()) == SPIN8_OK, "core scores");
                std::array<float, nk*dv> vr{};
                for (int64_t ki = 0; ki < nk; ++ki) for (int64_t vi = 0; vi < dv; ++vi) {
                    vr[ki*dv + vi] = static_cast<float *>(v->data)[ki + nk*(vi + dv*(h/(heads/kvheads) + kvheads*s))];
                }
                std::array<float, dv> expected_out{};
                std::array<uint8_t, nk> allowed{1,1,1};
                if (s == 0 && qi == 0) { allowed[nk-1] = 0; }
                require(spin8_attention_f32(cfg->plan.get(), qr, 1, kr, nk, vr.data(), dv, d,
                    allowed.data(), weights, expected_out.data()) == SPIN8_OK, "core attention");
                for (int64_t vi = 0; vi < dv; ++vi) {
                    const float actual = static_cast<float *>(output->data)[vi + dv*(qi + nq*(h + heads*s))];
                    require(std::abs(expected_out[vi] - actual) < 1e-5, "shared V attention");
                }
                for (int64_t ki = 0; ki < nk; ++ki) {
                    const float actual = static_cast<float *>(scores->data)[ki + nk*(qi + nq*(h + heads*s))];
                    max_error = std::max(max_error, double(std::abs(expected[ki] - actual)));
                    require(std::abs(expected[ki] - actual) < 5e-5, "GQA/multistream scalar scores");
                }
            }
            require(static_cast<float *>(probabilities->data)[nk-1] == 0.0f, "causal mask preserved");
            ggml_free(ctx);
        }
        cfg->audit(1024);
        cfg->matrices[0][0] = 9;
        bool failed = false;
        try { cfg->audit(1024); } catch (const std::runtime_error &) { failed = true; }
        require(failed, "audit invalidates corrupted matrix");
        failed = false;
        try { cfg->audit(1); } catch (const std::runtime_error &) { failed = true; }
        require(failed, "sticky invalidation");
    }
    std::printf("PASS strict core/GGML graph: modes=4 dimensions=8,16,128,256 GQA=4:2 streams=2 one-softmax mask audit; max_score_error=%.9g\n", max_error);
}
