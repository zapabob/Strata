// src/kernels/cpu/nvfp4_avx2.cpp - see include/strata/kernels/cpu/nvfp4_avx2.hpp.
//
// Per 64-value block, once: its E2M1 values in element order as two 32-byte registers (ggml's reordering: sub-block
// s keeps value j in the low nibble of qs[8 s + j] and value j + 8 in the high one), their magnitudes, and the four
// sub-block scales. Per token, as ggml_vec_dot_nvfp4_q8_0's AVX2 path: vpsignb moves the sign onto the activation,
// vpmaddubsw + vpmaddwd give 8 int32 lanes (four per 16-value sub-block), one FMA per 32 values applies
// ue4m3(d[s]) * d_q8, and hsum_float_8's order sums the lanes.
//
// Needs AVX2, FMA and F16C - what cpu_avx2_ok() checks before anything here is called.
#include "strata/kernels/cpu/nvfp4_avx2.hpp"

#define GGML_COMMON_DECL_CPP
#define GGML_COMMON_IMPL_CPP
#include "ggml-common.h"

#include <immintrin.h>

#include <cmath>
#include <cstdlib>
#include <cstring>

namespace strata::kernels::cpu {
namespace {

// A compile-time table, not a constructor: this file is compiled for a wide ISA, and a namespace-scope object with a
// constructor runs at program start on EVERY CPU - the compiler vectorises the loop with AVX/FMA, and a CPU without them
// (Westmere, Sandy Bridge, ...) died with an illegal instruction before main (#2324).  Powers of two: exact.
constexpr float pow2i(int e) {
    float r = 1.0f;
    for (; e > 0; --e) r *= 2.0f;
    for (; e < 0; ++e) r *= 0.5f;
    return r;
}
struct Ue4m3Table {   // ggml_ue4m3_to_fp32 (ggml-impl.h): halved for the doubled kvalues_fp4, 0x7F read as 0
    float v[256];
    constexpr Ue4m3Table() : v() {
        for (int x = 0; x < 256; ++x) {
            if (x == 0 || x == 0x7F) { v[x] = 0.0f; continue; }
            const int e = (x >> 3) & 0xF, m = x & 0x7;
            const float raw = e == 0 ? (float) m * pow2i(-9) : (1.0f + (float) m / 8.0f) * pow2i(e - 7);
            v[x] = raw * 0.5f;
        }
    }
};
constexpr Ue4m3Table kUe4m3;

// software prefetch distance in bytes (STRATA_NVFP4_PREFETCH, 0 = off), as the AVX-512 rows
// (read on first use, behind the CPU check: a static initialiser here would run on every CPU, see above)
inline int prefetch_distance() {
    static const int v = [] {
        const char* e = std::getenv("STRATA_NVFP4_PREFETCH");
        return e ? std::atoi(e) : 2048;
    }();
    return v;
}

inline float h2f(uint16_t h) { return _mm_cvtss_f32(_mm_cvtph_ps(_mm_cvtsi32_si128((int) h))); }

// sub-blocks 2 h and 2 h + 1 (16 bytes of qs) as their 32 signed doubled E2M1 values, in element order
inline __m256i values32(const uint8_t* qs, const __m128i kv) {
    const __m128i q = _mm_loadu_si128((const __m128i*) qs);
    const __m128i m4 = _mm_set1_epi8(0x0F);
    const __m128i lo = _mm_shuffle_epi8(kv, _mm_and_si128(q, m4));
    const __m128i hi = _mm_shuffle_epi8(kv, _mm_and_si128(_mm_srli_epi16(q, 4), m4));
    return _mm256_set_m128i(_mm_unpackhi_epi64(lo, hi), _mm_unpacklo_epi64(lo, hi));
}

inline float hsum8(const __m256 x) {   // ggml's hsum_float_8
    __m128 res = _mm256_extractf128_ps(x, 1);
    res = _mm_add_ps(res, _mm256_castps256_ps128(x));
    res = _mm_add_ps(res, _mm_movehl_ps(res, res));
    res = _mm_add_ss(res, _mm_movehdup_ps(res));
    return _mm_cvtss_f32(res);
}

constexpr int kMaxBlocks = 64;   // rows of up to 4096 values (n_embd 2560)
// tokens per pass: the pool's MAXT, so a window is one pass. Spilled accumulators cost less than another pass over
// the weights: one expert's gate+up, 8 tokens, 0.415 ms in passes of 4 + 4, 0.352 in one of 8 (5 6 7 alike)
constexpr int kMaxW = 8;

struct Acts {   // per token and block, the two Q8_0 blocks' scales; built once per call, reused by every row
    int nt = 0, nb = 0;
    const block_q8_0* y[kMaxW] = {};
    float dy[kMaxW * kMaxBlocks * 2];
    Acts(const void* const* act, int nt_, int nb_) : nt(nt_), nb(nb_) {
        for (int t = 0; t < nt; ++t) {
            y[t] = (const block_q8_0*) act[t];
            for (int ib = 0; ib < 2 * nb; ++ib) dy[(size_t) t * 2 * nb + ib] = h2f(y[t][ib].d);
        }
    }
};

template <int NT>
inline void row_dot(const uint8_t* row, const Acts& a, float* res) {
    const __m128i kv = _mm_loadu_si128((const __m128i*) kvalues_fp4);
    const __m256i ones = _mm256_set1_epi16(1);
    __m256 acc[NT];
    for (int t = 0; t < NT; ++t) acc[t] = _mm256_setzero_ps();
    const block_nvfp4* x = (const block_nvfp4*) row;
    const int prefetch_ahead = prefetch_distance();
    for (int ib = 0; ib < a.nb; ++ib) {
        if (prefetch_ahead > 0) _mm_prefetch((const char*) (x + ib) + prefetch_ahead, _MM_HINT_NTA);
        const __m256i v01 = values32(x[ib].qs, kv), v23 = values32(x[ib].qs + 16, kv);
        const __m256i a01 = _mm256_sign_epi8(v01, v01), a23 = _mm256_sign_epi8(v23, v23);
        // lanes 0-3 ue4m3(d[0]), 4-7 d[1] (and d[2], d[3]): times a broadcast d_q8, each lane is ggml's scalar
        // ue4m3(d[s]) * d_q8, rounded the same
        const __m256 u01 = _mm256_set_m128(_mm_set1_ps(kUe4m3.v[x[ib].d[1]]), _mm_set1_ps(kUe4m3.v[x[ib].d[0]]));
        const __m256 u23 = _mm256_set_m128(_mm_set1_ps(kUe4m3.v[x[ib].d[3]]), _mm_set1_ps(kUe4m3.v[x[ib].d[2]]));
        for (int t = 0; t < NT; ++t) {
            const block_q8_0* yb = a.y[t] + 2 * ib;
            const __m256i q01 = _mm256_loadu_si256((const __m256i*) yb[0].qs);
            const __m256i q23 = _mm256_loadu_si256((const __m256i*) yb[1].qs);
            const __m256i p1 = _mm256_madd_epi16(_mm256_maddubs_epi16(a01, _mm256_sign_epi8(q01, v01)), ones);
            const __m256i p2 = _mm256_madd_epi16(_mm256_maddubs_epi16(a23, _mm256_sign_epi8(q23, v23)), ones);
            const float* dy = a.dy + (size_t) t * 2 * a.nb + 2 * ib;
            const __m256 s01 = _mm256_mul_ps(u01, _mm256_broadcast_ss(dy));
            const __m256 s23 = _mm256_mul_ps(u23, _mm256_broadcast_ss(dy + 1));
            acc[t] = _mm256_fmadd_ps(s01, _mm256_cvtepi32_ps(p1), acc[t]);
            acc[t] = _mm256_fmadd_ps(s23, _mm256_cvtepi32_ps(p2), acc[t]);
        }
    }
    for (int t = 0; t < NT; ++t) res[t] = hsum8(acc[t]);
}

static inline __m128 nvfp4_fast_tanh4_ps(__m128 x) noexcept {
    const __m128 lo = _mm_set1_ps(-5.0f), hi = _mm_set1_ps(5.0f);
    const __m128 xc = _mm_min_ps(hi, _mm_max_ps(lo, x));
    const __m128 x2 = _mm_mul_ps(xc, xc);
    __m128 num = _mm_fmadd_ps(x2, _mm_add_ps(_mm_set1_ps(378.0f), x2), _mm_set1_ps(17325.0f));
    num = _mm_mul_ps(xc, _mm_fmadd_ps(x2, num, _mm_set1_ps(135135.0f)));
    __m128 den = _mm_fmadd_ps(x2, _mm_fmadd_ps(x2, _mm_set1_ps(28.0f), _mm_set1_ps(3150.0f)), _mm_set1_ps(62370.0f));
    den = _mm_fmadd_ps(x2, den, _mm_set1_ps(135135.0f));
    __m128 r = _mm_rcp_ps(den);
    r = _mm_mul_ps(r, _mm_fnmadd_ps(den, r, _mm_set1_ps(2.0f)));
    __m128 res = _mm_mul_ps(num, r);
    res = _mm_blendv_ps(res, _mm_set1_ps(1.0f), _mm_cmpgt_ps(x, hi));
    res = _mm_blendv_ps(res, _mm_set1_ps(-1.0f), _mm_cmplt_ps(x, lo));
    return res;
}

// Gen-L T==1 dual-row NVFP4 dot: reads Q8_0 activation ONCE for two weight rows (2x ILP, NTA L3-bypass, bit-exact).
inline void row_dot2_t1(const uint8_t* row0, const uint8_t* row1, const Acts& a, float& out0, float& out1) {
    const __m128i kv = _mm_loadu_si128((const __m128i*) kvalues_fp4);
    const __m256i ones = _mm256_set1_epi16(1);
    __m256 acc0 = _mm256_setzero_ps();
    __m256 acc1 = _mm256_setzero_ps();
    const block_nvfp4* x0 = (const block_nvfp4*) row0;
    const block_nvfp4* x1 = (const block_nvfp4*) row1;
    const block_q8_0* y0 = a.y[0];
    const float* dy_base = a.dy;
    const int nb = a.nb;
    for (int ib = 0; ib < nb; ++ib) {
        if (ib + 4 < nb) {
            _mm_prefetch((const char*) (x0 + ib + 4), _MM_HINT_NTA);
            _mm_prefetch((const char*) (x1 + ib + 4), _MM_HINT_NTA);
        }
        const block_q8_0* yb = y0 + 2 * ib;
        const __m256i q01 = _mm256_loadu_si256((const __m256i*) yb[0].qs);
        const __m256i q23 = _mm256_loadu_si256((const __m256i*) yb[1].qs);
        const __m256 dy0 = _mm256_broadcast_ss(dy_base + 2 * ib);
        const __m256 dy1 = _mm256_broadcast_ss(dy_base + 2 * ib + 1);

        const __m256i v0_01 = values32(x0[ib].qs, kv), v0_23 = values32(x0[ib].qs + 16, kv);
        const __m256i a0_01 = _mm256_sign_epi8(v0_01, v0_01), a0_23 = _mm256_sign_epi8(v0_23, v0_23);
        const __m256 u0_01 = _mm256_set_m128(_mm_set1_ps(kUe4m3.v[x0[ib].d[1]]), _mm_set1_ps(kUe4m3.v[x0[ib].d[0]]));
        const __m256 u0_23 = _mm256_set_m128(_mm_set1_ps(kUe4m3.v[x0[ib].d[3]]), _mm_set1_ps(kUe4m3.v[x0[ib].d[2]]));
        const __m256i p0_1 = _mm256_madd_epi16(_mm256_maddubs_epi16(a0_01, _mm256_sign_epi8(q01, v0_01)), ones);
        const __m256i p0_2 = _mm256_madd_epi16(_mm256_maddubs_epi16(a0_23, _mm256_sign_epi8(q23, v0_23)), ones);
        acc0 = _mm256_fmadd_ps(_mm256_mul_ps(u0_01, dy0), _mm256_cvtepi32_ps(p0_1), acc0);
        acc0 = _mm256_fmadd_ps(_mm256_mul_ps(u0_23, dy1), _mm256_cvtepi32_ps(p0_2), acc0);

        const __m256i v1_01 = values32(x1[ib].qs, kv), v1_23 = values32(x1[ib].qs + 16, kv);
        const __m256i a1_01 = _mm256_sign_epi8(v1_01, v1_01), a1_23 = _mm256_sign_epi8(v1_23, v1_23);
        const __m256 u1_01 = _mm256_set_m128(_mm_set1_ps(kUe4m3.v[x1[ib].d[1]]), _mm_set1_ps(kUe4m3.v[x1[ib].d[0]]));
        const __m256 u1_23 = _mm256_set_m128(_mm_set1_ps(kUe4m3.v[x1[ib].d[3]]), _mm_set1_ps(kUe4m3.v[x1[ib].d[2]]));
        const __m256i p1_1 = _mm256_madd_epi16(_mm256_maddubs_epi16(a1_01, _mm256_sign_epi8(q01, v1_01)), ones);
        const __m256i p1_2 = _mm256_madd_epi16(_mm256_maddubs_epi16(a1_23, _mm256_sign_epi8(q23, v1_23)), ones);
        acc1 = _mm256_fmadd_ps(_mm256_mul_ps(u1_01, dy0), _mm256_cvtepi32_ps(p1_1), acc1);
        acc1 = _mm256_fmadd_ps(_mm256_mul_ps(u1_23, dy1), _mm256_cvtepi32_ps(p1_2), acc1);
    }
    out0 = hsum8(acc0);
    out1 = hsum8(acc1);
}

template <bool SITU>
void gu_rows_t1(const uint8_t* blob, size_t gu_row, size_t up_off, const Acts& a, float* ff0, int r0, int r1,
                float sg, float su, float beta = 4.f, float lb = 25.f) {
    const float inv_beta = SITU ? (1.0f / beta) : 0.0f;
    const float inv_lb = (SITU && lb > 0.f) ? (1.0f / lb) : 0.0f;
    for (int r = r0; r < r1; ++r) {
        if (r + 2 < r1) {
            _mm_prefetch((const char*) (blob + (size_t) (r + 2) * gu_row), _MM_HINT_NTA);
            _mm_prefetch((const char*) (blob + up_off + (size_t) (r + 2) * gu_row), _MM_HINT_NTA);
        }
        float g = 0.f, u = 0.f;
        row_dot2_t1(blob + (size_t) r * gu_row, blob + up_off + (size_t) r * gu_row, a, g, u);
        const float gs = g * sg, us = u * su;
        if constexpr (SITU) {
            const __m128 vin = _mm_set_ps(0.0f, 0.5f * gs, lb > 0.f ? (us * inv_lb) : 0.0f, gs * inv_beta);
            const __m128 tv = nvfp4_fast_tanh4_ps(vin);
            const float tv0 = _mm_cvtss_f32(tv);
            const float tv1 = _mm_cvtss_f32(_mm_shuffle_ps(tv, tv, 0x55));
            const float tv2 = _mm_cvtss_f32(_mm_movehl_ps(tv, tv));
            const float tg = beta * tv0;
            const float tu = lb > 0.f ? (lb * tv1) : us;
            const float sig = 0.5f * (1.0f + tv2);
            ff0[r] = (tg * sig) * tu;
        } else {
            ff0[r] = (gs / (1.f + std::exp(-gs))) * us;
        }
    }
}

void dot_rows_t1(const uint8_t* w, size_t row_bytes, const Acts& a, float* out0, int r0, int r1, float scale) {
    int r = r0;
    for (; r + 1 < r1; r += 2) {
        if (r + 4 < r1) {
            _mm_prefetch((const char*) (w + (size_t) (r + 4) * row_bytes), _MM_HINT_NTA);
            _mm_prefetch((const char*) (w + (size_t) (r + 5) * row_bytes), _MM_HINT_NTA);
        }
        float s0 = 0.f, s1 = 0.f;
        row_dot2_t1(w + (size_t) r * row_bytes, w + (size_t) (r + 1) * row_bytes, a, s0, s1);
        out0[r]     = s0 * scale;
        out0[r + 1] = s1 * scale;
    }
    for (; r < r1; ++r) {
        float res[1];
        row_dot<1>(w + (size_t) r * row_bytes, a, res);
        out0[r] = res[0] * scale;
    }
}

template <int NT, bool SITU = false>
void gu_rows(const uint8_t* blob, size_t gu_row, size_t up_off, const Acts& a, float* const* ff, int r0, int r1,
             float sg, float su, float beta = 4.f, float lb = 25.f) {
    float g[NT], u[NT];
    for (int r = r0; r < r1; ++r) {
        row_dot<NT>(blob + (size_t) r * gu_row, a, g);
        row_dot<NT>(blob + up_off + (size_t) r * gu_row, a, u);
        for (int t = 0; t < NT; ++t) {   // native_gu_rows' ggml path, operation for operation
            const float gs = g[t] * sg, us = u[t] * su;
            if constexpr (SITU) {
                const float tg = beta * std::tanh(gs / beta);
                const float tu = lb > 0.f ? lb * std::tanh(us / lb) : us;
                ff[t][r] = (tg / (1.f + std::exp(-gs))) * tu;
            } else {
                ff[t][r] = (gs / (1.f + std::exp(-gs))) * us;
            }
        }
    }
}

template <int NT>
void dot_rows(const uint8_t* w, size_t row_bytes, const Acts& a, float* const* out, int r0, int r1, float scale) {
    float res[NT];
    for (int r = r0; r < r1; ++r) {
        row_dot<NT>(w + (size_t) r * row_bytes, a, res);
        for (int t = 0; t < NT; ++t) out[t][r] = res[t] * scale;
    }
}

// windows wider than kMaxW (not from the pool) run in balanced slices of at most kMaxW
template <typename F>
inline void slices(int nt, F&& run) {
    const int k = (nt + kMaxW - 1) / kMaxW;
    for (int i = 0, t0 = 0; i < k; ++i) {
        const int w = nt / k + (i < nt % k ? 1 : 0);
        run(t0, w);
        t0 += w;
    }
}

}  // namespace

bool nvfp4_256_fits(int n) { return n % QK_NVFP4 == 0 && n / QK_NVFP4 <= kMaxBlocks; }

void nvfp4_256_gu_rows(const uint8_t* blob, size_t gu_row, size_t up_off, int n, const void* const* act, int nt,
                       float* const* ff, int r0, int r1, float s_gate, float s_up) {
    slices(nt, [&](int t0, int w) {
        const Acts a(act + t0, w, n / QK_NVFP4);
        float* const* f = ff + t0;
        switch (w) {
            case 1: gu_rows_t1<false>(blob, gu_row, up_off, a, f[0], r0, r1, s_gate, s_up); break;
            case 2: gu_rows<2, false>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up); break;
            case 3: gu_rows<3, false>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up); break;
            case 4: gu_rows<4, false>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up); break;
            case 5: gu_rows<5, false>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up); break;
            case 6: gu_rows<6, false>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up); break;
            case 7: gu_rows<7, false>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up); break;
            default: gu_rows<8, false>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up); break;
        }
    });
}

void nvfp4_256_gu_rows_situ(const uint8_t* blob, size_t gu_row, size_t up_off, int n, const void* const* act, int nt,
                            float* const* ff, int r0, int r1, float s_gate, float s_up, float beta, float lb) {
    slices(nt, [&](int t0, int w) {
        const Acts a(act + t0, w, n / QK_NVFP4);
        float* const* f = ff + t0;
        switch (w) {
            case 1: gu_rows_t1<true>(blob, gu_row, up_off, a, f[0], r0, r1, s_gate, s_up, beta, lb); break;
            case 2: gu_rows<2, true>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up, beta, lb); break;
            case 3: gu_rows<3, true>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up, beta, lb); break;
            case 4: gu_rows<4, true>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up, beta, lb); break;
            case 5: gu_rows<5, true>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up, beta, lb); break;
            case 6: gu_rows<6, true>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up, beta, lb); break;
            case 7: gu_rows<7, true>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up, beta, lb); break;
            default: gu_rows<8, true>(blob, gu_row, up_off, a, f, r0, r1, s_gate, s_up, beta, lb); break;
        }
    });
}

void nvfp4_256_rows(const uint8_t* w, size_t row_bytes, int n, const void* const* act, int nt, float* const* out,
                    int r0, int r1, float scale) {
    slices(nt, [&](int t0, int k) {
        const Acts a(act + t0, k, n / QK_NVFP4);
        float* const* o = out + t0;
        switch (k) {
            case 1: dot_rows_t1(w, row_bytes, a, o[0], r0, r1, scale); break;
            case 2: dot_rows<2>(w, row_bytes, a, o, r0, r1, scale); break;
            case 3: dot_rows<3>(w, row_bytes, a, o, r0, r1, scale); break;
            case 4: dot_rows<4>(w, row_bytes, a, o, r0, r1, scale); break;
            case 5: dot_rows<5>(w, row_bytes, a, o, r0, r1, scale); break;
            case 6: dot_rows<6>(w, row_bytes, a, o, r0, r1, scale); break;
            case 7: dot_rows<7>(w, row_bytes, a, o, r0, r1, scale); break;
            default: dot_rows<8>(w, row_bytes, a, o, r0, r1, scale); break;
        }
    });
}

}  // namespace strata::kernels::cpu
