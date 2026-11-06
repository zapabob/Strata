// Exercise the production Qwen3.6 kernels and session operations, without loading a model.
// Including the driver here keeps this test out of the public engine protocol.
#include "../../src/qwen35/q36_engine.cu"
#include <stdexcept>

namespace {
struct Allocations {
    std::vector<void*> pointers;
    ~Allocations() { for (void* p : pointers) cudaFree(p); }
    template<class T> T* make(size_t n) {
        T* p = nullptr;
        CK(cudaMalloc((void**)&p, n * sizeof(T)));
        CK(cudaMemset(p, 0, n * sizeof(T)));
        pointers.push_back(p);
        return p;
    }
    template<class T> T* upload(const std::vector<T>& v) {
        T* p = make<T>(v.size());
        CK(cudaMemcpy(p, v.data(), v.size() * sizeof(T), cudaMemcpyHostToDevice));
        return p;
    }
};
template<class T> std::vector<T> read_device(const T* p, size_t n) {
    std::vector<T> v(n);
    CK(cudaMemcpy(v.data(), p, n * sizeof(T), cudaMemcpyDeviceToHost));
    return v;
}
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

template<class KT, class VT> void kernel_case() {
    constexpr int H = 4, HKV = 2, HD = 256, T = 257, CTX = 513, NC = 2;
    constexpr size_t COUNT = HKV * CTX * HD;
    Allocations a;
    std::vector<float> hqg(T * H * HD * 2), hx(T * HKV * HD), hv(hx.size()), weights(HD, 1.f);
    for (size_t i = 0; i < hqg.size(); ++i) hqg[i] = float(int(i % 83) - 41) / 37.f;
    for (size_t i = 0; i < hx.size(); ++i) {
        hx[i] = float(int(i % 71) - 35) / 31.f;
        hv[i] = float(int(i % 97) - 48) / 29.f;
    }
    auto qg = a.upload(hqg), x = a.upload(hx), v = a.upload(hv), w = a.upload(weights);
    auto q = a.make<float>(T * H * HD), gate = a.make<float>(T * H * HD);
    auto k32 = a.make<float>(COUNT), v32 = a.make<float>(COUNT);
    auto kc = a.make<KT>(COUNT);
    auto vc = a.make<VT>(COUNT);
    auto pos = a.upload<int32_t>({0});
    k_attn_prep<float, float><<<dim3(H + HKV, T), 256>>>(qg, x, v, w, w, q, gate, k32, v32,
        H, HKV, HD, 64, pos, CTX, 1000000.f, 1e-6f, nullptr, nullptr, {});
    k_attn_prep<KT, VT><<<dim3(H + HKV, T), 256>>>(qg, x, v, w, w, q, gate, kc, vc,
        H, HKV, HD, 64, pos, CTX, 1000000.f, 1e-6f, nullptr, nullptr, {});
    CK(cudaDeviceSynchronize());
    auto hk32 = read_device(k32, COUNT), hv32 = read_device(v32, COUNT);
    auto hk = read_device(kc, COUNT); auto hvc = read_device(vc, COUNT);
    for (size_t i = 0; i < COUNT; ++i) {
        require(float(hk[i]) == float(KT(hk32[i])), "K storage or untouched suffix differs");
        require(float(hvc[i]) == float(VT(hv32[i])), "V storage or untouched suffix differs");
    }
    auto k16 = a.make<__half>(HKV * T * HD), v16 = a.make<__half>(HKV * T * HD);
    k_kv_f16<KT, VT><<<grid1(HKV * T * HD), 256>>>(kc, vc, k16, v16, CTX, T, HD, HKV);
    auto compact_k = read_device(k16, HKV * T * HD), compact_v = read_device(v16, HKV * T * HD);
    for (int h = 0; h < HKV; ++h) for (int i = 0; i < T * HD; ++i) {
        require(float(compact_k[h * T * HD + i]) == float(__half(float(hk[h * CTX * HD + i]))), "prefill K compaction");
        require(float(compact_v[h * T * HD + i]) == float(__half(float(hvc[h * CTX * HD + i]))), "prefill V compaction");
    }
    // The prefill GEMMs may read FP16 cache heads directly, including the second head and unused suffix.
    constexpr bool KH = std::is_same_v<KT, __half>, VH = std::is_same_v<VT, __half>;
    k_kv_f16<KT, VT><<<grid1(HKV * T * HD), 256>>>(kc, vc, KH ? nullptr : k16, VH ? nullptr : v16, CTX, T, HD, HKV);
    cublasHandle_t blas;
    require(cublasCreate(&blas) == CUBLAS_STATUS_SUCCESS, "create test cuBLAS");
    auto operand = a.upload(std::vector<__half>(T * 3, __half(0.125f)));
    auto direct = a.make<float>(T * 3), reference = a.make<float>(T * 3);
    const float one = 1.f, zero = 0.f;
    for (int head = 0; head < HKV; ++head) for (bool key : {true, false}) {
        const __half* base = key ? k16 : v16;
        const __half* actual = kv_half_head(key ? KH : VH, key ? (void*)kc : (void*)vc, base, head, CTX, T, HD);
        const __half* expected = base + head * T * HD;
        const int rows = key ? T : HD, inner = key ? HD : T;
        auto gemm = [&](const __half* input, float* output) {
            require(cublasGemmEx(blas, key ? CUBLAS_OP_T : CUBLAS_OP_N, CUBLAS_OP_N,
                rows, 3, inner, &one, input, CUDA_R_16F, HD, operand, CUDA_R_16F, inner,
                &zero, output, CUDA_R_32F, rows, CUBLAS_COMPUTE_32F, CUBLAS_GEMM_DEFAULT) == CUBLAS_STATUS_SUCCESS, "prefill operand GEMM");
        };
        gemm(actual, direct); gemm(expected, reference);
        auto got = read_device(direct, rows * 3), want = read_device(reference, rows * 3);
        for (size_t i = 0; i < got.size(); ++i) require(std::isfinite(got[i]) && std::abs(got[i] - want[i]) < 1e-6f, "direct FP16 prefill differs from compact operands");
    }
    require(cublasDestroy(blas) == CUBLAS_STATUS_SUCCESS, "destroy test cuBLAS");
    auto acc = a.make<float>(H * NC * HD), mx = a.make<float>(H * NC), sum = a.make<float>(H * NC);
    auto out = a.make<float>(T * H * HD);
    k_attn_part<KT, VT><<<dim3(NC, H), 256>>>(q, kc, vc, pos, T - 1, H, HKV, CTX, 1.f / 16.f, NC, acc, mx, sum, {});
    k_attn_merge<<<H, HD>>>(acc, mx, sum, gate, pos, T - 1, H, NC, out, {});
    auto hq = read_device(q, T * H * HD), hg = read_device(gate, T * H * HD), ho = read_device(out, T * H * HD);
    double max_error = 0;
    for (int h = 0; h < H; ++h) {
        std::vector<double> scores(T);
        double peak = -INFINITY, denom = 0;
        for (int p = 0; p < T; ++p) {
            double score = 0;
            for (int d = 0; d < HD; ++d) score += double(hq[((T - 1) * H + h) * HD + d]) * float(hk[((h / 2) * CTX + p) * HD + d]);
            scores[p] = score / 16.; peak = std::max(peak, scores[p]);
        }
        for (double& s : scores) { s = std::exp(s - peak); denom += s; }
        for (int d = 0; d < HD; ++d) {
            double ref = 0;
            for (int p = 0; p < T; ++p) ref += scores[p] * float(hvc[((h / 2) * CTX + p) * HD + d]);
            const size_t i = ((T - 1) * H + h) * HD + d;
            ref = ref / denom / (1. + std::exp(-double(hg[i])));
            require(std::isfinite(ho[i]), "non-finite attention output");
            max_error = std::max(max_error, std::abs(ref - ho[i]));
        }
    }
    require(max_error < 2e-5, "attention differs from double CPU reference");
    // Address two sessions through RowSel; only the selected cell may change.
    auto other_k = a.make<KT>(COUNT);
    auto other_v = a.make<VT>(COUNT);
    RowSel rs;
    rs.kc = a.upload<void*>({other_k, kc}); rs.vc = a.upload<void*>({other_v, vc});
    rs.slot = a.upload<int32_t>({0, 1}); rs.cell = a.upload<int32_t>({CTX - 1, CTX - 2});
    k_attn_prep<KT, VT><<<dim3(H + HKV, 2), 256>>>(qg, x, v, w, w, q, gate, nullptr, nullptr,
        H, HKV, HD, 64, pos, CTX, 1000000.f, 1e-6f, nullptr, nullptr, rs);
    auto other = read_device(other_v, COUNT); auto selected = read_device(vc, COUNT);
    for (int h = 0; h < HKV; ++h) for (int p = 0; p < CTX; ++p) for (int d = 0; d < HD; ++d) {
        const size_t i = (h * CTX + p) * HD + d;
        const float want_other = p == CTX - 1 ? float(VT(hv[h * HD + d])) : 0.f;
        const float want_selected = p == CTX - 2 ? float(VT(hv[(HKV + h) * HD + d])) : float(hvc[i]);
        require(float(other[i]) == want_other && float(selected[i]) == want_selected, "session addressing");
    }
    std::printf("PASS kernels K=%zu V=%zu max_abs_error=%.9g\n", sizeof(KT), sizeof(VT), max_error);
}

void session_case(bool key_half, bool value_half) {
    Model m{};
    m.g.n_head_kv = 2; m.g.head_dim = 256; m.g.n_embd = 16;
    m.g.ssm_conv_channels = 4; m.g.ssm_d_conv = 3; m.g.ssm_v_heads = 2; m.g.ssm_state_size = 4;
    m.layers.resize(2); m.layers[0].attn = true; m.layers[1].attn = false; m.has_mtp = true;
    Engine e{};
    e.m = &m; e.ctx = 513; e.kv_k_f16 = key_half; e.kv_v_f16 = value_half;
    e.sess.resize(2); e.cur = 0; e.private_cache = true;
    for (auto& ss : e.sess) e.alloc_session(ss);
    e.load_cur(); e.pos = 3;
    const size_t count = size_t(e.ctx) * m.g.n_head_kv * m.g.head_dim;
    for (size_t layer : {size_t(0), size_t(2)}) {
        CK(cudaMemset(e.sess[0].kc[layer], 0x3c, count * e.kv_element_bytes(true)));
        CK(cudaMemset(e.sess[0].vc[layer], 0x3d, count * e.kv_element_bytes(false)));
    }
    e.copy_session(0, 1);
    for (size_t layer : {size_t(0), size_t(2)}) for (bool key : {true, false}) {
        const size_t width = m.g.head_dim * e.kv_element_bytes(key);
        auto bytes = read_device(static_cast<unsigned char*>(key ? e.sess[1].kc[layer] : e.sess[1].vc[layer]), count * e.kv_element_bytes(key));
        for (size_t i = 0; i < bytes.size(); ++i)
            require(bytes[i] == ((i % (e.ctx * width) < 3 * width) ? (key ? 0x3c : 0x3d) : 0), "session prefix copy or suffix boundary");
    }
    e.clear_private_cache();
    for (size_t layer : {size_t(0), size_t(2)}) for (bool key : {true, false}) {
        auto bytes = read_device(static_cast<unsigned char*>(key ? e.kc[layer] : e.vc[layer]), count * e.kv_element_bytes(key));
        require(std::all_of(bytes.begin(), bytes.end(), [](unsigned char b) { return b == 0; }), "private wipe must include speculative suffix and MTP");
    }
    for (auto& ss : e.sess) {
        for (auto p : ss.kc) if (p) CK(cudaFree(p));
        for (auto p : ss.vc) if (p) CK(cudaFree(p));
        for (auto p : ss.conv) if (p) CK(cudaFree(p));
        for (auto p : ss.S) if (p) CK(cudaFree(p));
        CK(cudaFree(ss.hlast));
    }
    std::printf("PASS sessions K=%s V=%s copy/private/MTP\n", key_half ? "f16" : "f32", value_half ? "f16" : "f32");
}
}

int main() {
    try {
        size_t free = 0, total = 0;
        CK(cudaMemGetInfo(&free, &total));
        require(free > 512ull * 1024 * 1024, "requires 512 MiB free VRAM");
        kernel_case<float, float>(); kernel_case<__half, __half>();
        kernel_case<float, __half>(); kernel_case<__half, float>();
        for (bool k : {false, true}) for (bool v : {false, true}) session_case(k, v);
        CK(cudaDeviceSynchronize());
        return 0;
    } catch (const std::exception& e) { std::fprintf(stderr, "FAIL %s\n", e.what()); return 1; }
}
