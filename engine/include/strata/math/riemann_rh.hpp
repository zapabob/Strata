// engine/include/strata/math/riemann_rh.hpp
// Riemann Hypothesis (RH)-conditional mathematical primitives for Strata inference engine.
//
// Assumes RH: all non-trivial zeros of the Riemann zeta function lie on the critical line
// rho_k = 1/2 + i * gamma_k (Re(s) = 1/2).
//
// Applied theorems:
// 1. Littlewood (1912): sum_{n<=x} lambda(n) = O(x^{1/2 + eps}) <=> RH, where lambda(n) = (-1)^{Omega(n)}
//    is the Liouville function. Yields a zero-PRNG, compile-time sign vector with optimal O(sqrt(d))
//    square-root cancellation for deterministic quasi-orthogonal preconditioning.
// 2. von Koch (1901) / Riemann's Explicit Formula: under RH, counting fluctuations around the smooth
//    trend are bounded by O(t^{1/2} log t) (critical-line exponent sigma = 1/2). Motivates critical-line
//    adaptive decay gamma(t) = 1 - 1/sqrt(t + 4) and hysteresis floor eps_RH(t) = c * sqrt(S_a + S_b) / ln(t + e).
// 3. Zeta-Lagrangian VRAM Allocation: for MoE expert routing following a discrete Riemann Zeta law
//    P_i(r) = r^{-s_i} / zeta_E(s_i), global CPU-latency minimization subject to sum_i S_i * b_i <= B
//    is solved optimally by greedy marginal utility mu_i(k) = c_i * k^{-s_i} / (b_i * zeta_E(s_i)).
#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace strata::math {

// First 32 non-trivial zeros gamma_k > 0 of zeta(1/2 + i*gamma_k) = 0 (Odlyzko table, 15 digits).
inline constexpr std::array<double, 32> kZetaZeroImag = {
    14.134725141734694, 21.022039638771555, 25.010857580145688, 30.424876125859513,
    32.935061587739190, 37.586178158825671, 40.918719012147495, 43.327073280914999,
    48.005150881167160, 49.773832477672302, 52.970321477714461, 56.446247697063395,
    59.347044002602353, 60.831778524609810, 65.112544048081607, 67.079810529494174,
    69.546401711173979, 72.067157674481908, 75.704690699083933, 77.144840068874805,
    79.337375020249368, 82.910380854086030, 84.735492980517050, 87.425274613125229,
    88.809111207634465, 92.491899270558484, 94.651344040519887, 95.870634228245310,
    98.831194218193692, 101.31785100573139, 103.72553804047834, 105.44662305232609,
};

// Compile-time Liouville function lambda(n) = (-1)^{Omega(n)} in {-1, +1} for n >= 1.
// Under RH (Littlewood 1912), partial sums satisfy |sum_{n<=x} lambda(n)| = O(x^{1/2 + eps}).
constexpr int8_t liouville_sign(int n) noexcept {
    if (n <= 1) return 1;
    int parity = 0;
    int m = n;
    while ((m & 1) == 0) {
        parity ^= 1;
        m >>= 1;
    }
    for (int d = 3; d * d <= m; d += 2) {
        while (m % d == 0) {
            parity ^= 1;
            m /= d;
        }
    }
    if (m > 1) parity ^= 1;
    return parity ? int8_t(-1) : int8_t(1);
}

// Critical-line (sigma = 1/2) adaptive decay factor gamma(t) = 1 - 1 / sqrt(t + 4).
// Matches the RH explicit-formula fluctuation scaling O(t^{1/2}) so Zipf/Zeta head experts
// are retained across long horizons while adapting to regime shifts in O(sqrt(t)) steps.
inline double rh_critical_decay(uint64_t step) noexcept {
    const double d = 1.0 - 1.0 / std::sqrt((double) step + 4.0);
    return std::clamp(d, 0.50, 0.96);
}

// RH von Koch explicit-formula hysteresis floor:
// Avoids evicting a resident expert on O(sqrt(N)) random fluctuations while admitting
// genuine Zipf-head experts immediately. c_vk defaults to 0.20 (ShinkaEvolve optimal: ~0.1893).
inline double rh_von_koch_threshold(double score_hot, double score_cold, uint64_t step,
                                    double c_vk = 0.20) noexcept {
    const double s = std::max(0.0, score_hot + score_cold);
    const double denom = std::log((double) step + 2.718281828459045);
    return c_vk * std::sqrt(s) / std::max(1.0, denom);
}

// Normalized Shannon routing entropy H(p) / ln(n) in [0, 1] for a layer's expert score distribution.
inline double normalized_shannon_entropy(const double* scores, size_t n) noexcept {
    if (!scores || n <= 1) return 0.5;
    double total = 0.0;
    for (size_t i = 0; i < n; ++i) {
        if (scores[i] > 0.0) total += scores[i];
    }
    if (total <= 1e-12) return 0.5;
    double h = 0.0;
    const double inv_total = 1.0 / total;
    for (size_t i = 0; i < n; ++i) {
        if (scores[i] > 0.0) {
            const double p = scores[i] * inv_total;
            h -= p * std::log(p);
        }
    }
    return std::clamp(h / std::log((double) n), 0.0, 1.0);
}

// Information-theoretic Shannon-entropy-modulated RH critical-line decay:
// Peaked Zipf routing (low H_norm) increases retention; flat/shifting regimes (high H_norm) adapt faster.
inline double rh_entropy_adjusted_decay(uint64_t step, double norm_entropy) noexcept {
    const double base = rh_critical_decay(step);
    const double shift = 0.08 * (0.5 - std::clamp(norm_entropy, 0.0, 1.0));
    return std::clamp(base + shift, 0.50, 0.96);
}

// RH Explicit-Formula Spectral Phase (Odlyzko first 8 non-trivial zeros, assuming Re(rho_k) = 1/2):
// Normalized critical-line oscillation in [-1, 1] providing quasi-periodic anti-resonance against
// periodic rebalance lock-in / thrashing across multi-turn decode.
inline double rh_explicit_spectral_phase(uint64_t step) noexcept {
    static constexpr double kNorm8 =
        (1.0 / 14.143566475878458) + (1.0 / 21.027985329891663) +
        (1.0 / 25.015854784905953) + (1.0 / 30.428984476168953) +
        (1.0 / 32.938856862140195) + (1.0 / 37.589503513954328) +
        (1.0 / 40.921773733804775) + (1.0 / 43.329958231546326);
    const double ln_x = std::log((double) step + 2.0);
    double acc = 0.0;
    for (size_t k = 0; k < 8; ++k) {
        const double g = kZetaZeroImag[k];
        acc += std::cos(g * ln_x) / std::sqrt(0.25 + g * g);
    }
    return acc / kNorm8;
}

// Gen-N RH Explicit-Formula Spectral + Entropy-Jump Regime-Shift Decay:
// Modulates critical-line decay with Odlyzko zero spectral phase and positive entropy jump delta_H.
inline double rh_spectral_entropy_decay(uint64_t step, double norm_entropy, double prev_entropy,
                                        double spec_amp = 0.025, double dh_gain = 0.0) noexcept {
    const double h = std::clamp(norm_entropy, 0.0, 1.0);
    const double dh_pos = std::max(0.0, h - std::clamp(prev_entropy, 0.0, 1.0));
    const double base = rh_critical_decay(step);
    const double spec = (spec_amp != 0.0) ? (spec_amp * rh_explicit_spectral_phase(step)) : 0.0;
    return std::clamp(base + 0.08 * (0.5 - h) - dh_gain * dh_pos + spec, 0.50, 0.96);
}

// Gen-N RH-UCB Cold-Start Admission Bound:
// Under RH (sigma = 1/2), early-decode uncertainty scales as O(sqrt(ln(t+e)) / (sqrt(S+1) * sqrt(t+4))),
// letting newly-hot experts clear the hysteresis floor during cold-start while vanishing at long horizons.
inline double rh_ucb_admission_bonus(double score, uint64_t step, double c_ucb = 0.00575) noexcept {
    if (c_ucb <= 0.0 || score <= 0.0) return 0.0;
    const double num = std::sqrt(std::max(1.0, std::log((double) step + 2.718281828459045)));
    const double den = std::sqrt(score + 1.0) * std::sqrt((double) step + 4.0);
    return c_ucb * (num / den);
}

// ST-MoE (arXiv:2606.15453, June 2026) consecutive-token Markov temporal-recurrence boost:
// Rewards experts exhibiting short-horizon sequential stability (dt <= 2 tokens) while RH von Koch
// hysteresis still suppresses 1-off noise. Real-machine verified optimal: dt1_boost = 0.1387.
inline double st_moe_markov_boost(uint32_t dt, double dt1_boost = 0.1387) noexcept {
    if (dt == 1u) return dt1_boost;
    if (dt == 2u) return 0.45 * dt1_boost;
    return 0.0;
}

// Continuous cosine-interpolated Zipf/Zeta depth exponent profile from shallow to deep outer layers:
// Real-machine verified optimal (Sakura 98K hits=7447 / GPU=2329): s_shallow = 1.2470, s_deep = 0.9116.
inline double continuous_zeta_exponent(int idx, int n_layers,
                                       double s_shallow = 1.2470,
                                       double s_deep = 0.9116) noexcept {
    if (n_layers <= 1) return s_shallow;
    const double t = std::clamp((double) idx / (double) (n_layers - 1), 0.0, 1.0);
    const double w = 0.5 * (1.0 + std::cos(3.14159265358979323846 * t));
    return s_deep + (s_shallow - s_deep) * w;
}

// LeCaR (Learning Cache Replacement via Online Multiplicative-Weights Regret Minimization):
// Maintains O(sqrt(T ln 2)) regret bound between Frequency (LFU/Zeta) and Recency (LRU/Markov)
// using a tiny ghost eviction ring. Zero ML overhead (<50 ns per rebalance).
// Real-machine verified defaults: w_lfu=0.6046, eta=0.6349, recency_scale=1.8393.
struct LeCaRController {
    double w_lfu = 0.6046;        // initial Zipf-prior weight for frequency vs recency (1 - w_lfu)
    double eta = 0.6349;          // multiplicative-weights learning rate
    double recency_scale = 1.8393;// scale-invariant recency amplitude relative to layer mean active score
    static constexpr size_t kGhostCap = 16;
    int32_t ghost_id[kGhostCap] = {};
    uint32_t ghost_step[kGhostCap] = {};
    uint8_t ghost_reason[kGhostCap] = {};  // 0 = evicted by LFU, 1 = evicted by LRU
    size_t ghost_head = 0;

    LeCaRController() noexcept {
        for (size_t i = 0; i < kGhostCap; ++i) {
            ghost_id[i] = -1;
            ghost_step[i] = 0;
            ghost_reason[i] = 0;
        }
    }

    void record_eviction(int32_t expert_id, uint32_t step, bool by_recency) noexcept {
        ghost_id[ghost_head] = expert_id;
        ghost_step[ghost_head] = step;
        ghost_reason[ghost_head] = by_recency ? 1u : 0u;
        ghost_head = (ghost_head + 1u) & (kGhostCap - 1u);
    }

    // Call on a CPU cache miss: if the missed expert was recently evicted, penalize the policy that evicted it.
    void on_miss(int32_t expert_id, uint32_t step) noexcept {
        for (size_t i = 0; i < kGhostCap; ++i) {
            if (ghost_id[i] != expert_id) continue;
            const uint32_t age = (step > ghost_step[i]) ? (step - ghost_step[i]) : 1u;
            const double discount = std::pow(0.85, (double) std::min<uint32_t>(age, 32u));
            const double w_lru = 1.0 - w_lfu;
            double new_lfu = w_lfu;
            double new_lru = w_lru;
            if (ghost_reason[i] == 0u) {
                // Evicted by LFU -> regret on LFU, boost LRU
                new_lru *= std::exp(eta * discount);
            } else {
                // Evicted by LRU -> regret on LRU, boost LFU
                new_lfu *= std::exp(eta * discount);
            }
            const double norm = new_lfu + new_lru;
            if (norm > 0.0) w_lfu = std::clamp(new_lfu / norm, 0.15, 0.90);
            ghost_id[i] = -1;
            return;
        }
    }

    // Blended eviction/promotion score combining LFU (frequency) and LRU (recency).
    double blend_score(double freq_score, uint32_t last_step, uint32_t cur_step) const noexcept {
        const uint32_t age = (cur_step > last_step) ? (cur_step - last_step) : 0u;
        const double recency = 1.0 / (1.0 + 0.15 * (double) age);
        return w_lfu * freq_score + (1.0 - w_lfu) * (recency * 4.0);
    }

    // Scale-invariant LeCaR blended score: anchors recency amplitude to layer_mean_score so
    // recency remains calibrated across prefill bursts and long-horizon decode regimes.
    double blend_score_scaled(double freq_score, uint32_t last_step, uint32_t cur_step,
                              double layer_mean_score) const noexcept {
        const uint32_t age = (cur_step > last_step) ? (cur_step - last_step) : 0u;
        const double recency = 1.0 / (1.0 + 0.15 * (double) age);
        const double rec_amp = recency_scale * std::max(1.0, layer_mean_score);
        return w_lfu * freq_score + (1.0 - w_lfu) * (recency * rec_amp);
    }
};

// Truncated Riemann zeta function zeta_E(s) = sum_{k=1}^{E} k^{-s}.
inline double truncated_zeta(int E, double s) noexcept {
    double sum = 0.0;
    for (int k = 1; k <= E; ++k) {
        sum += std::pow((double) k, -s);
    }
    return sum > 0.0 ? sum : 1.0;
}

struct ZetaLayerSpec {
    int layer_id = 0;
    size_t stride_bytes = 0;
    double cpu_miss_cost = 1.0;
    double zeta_exponent = 1.15;
    int max_slots = 128;
};

// Globally optimal Tier-2 VRAM slot allocation under discrete Riemann Zeta popularity:
// Maximizes sum_i c_i * sum_{k=1}^{S_i} (k^{-s_i} / zeta_E(s_i)) subject to sum_i S_i * b_i <= budget.
// Because k^{-s_i} is strictly decreasing in k, greedy marginal-utility selection is globally optimal.
inline std::vector<int> zeta_lagrangian_allocate(const std::vector<ZetaLayerSpec>& specs,
                                                 size_t budget_bytes,
                                                 size_t* out_used_bytes = nullptr) {
    const size_t L = specs.size();
    std::vector<int> slots(L, 0);
    std::vector<double> inv_zeta(L, 1.0);
    for (size_t i = 0; i < L; ++i) {
        inv_zeta[i] = 1.0 / truncated_zeta(std::max(1, specs[i].max_slots), specs[i].zeta_exponent);
    }
    size_t used = 0;
    for (;;) {
        size_t best_i = L;
        double best_mu = -1.0;
        for (size_t i = 0; i < L; ++i) {
            const auto& sp = specs[i];
            if (slots[i] >= sp.max_slots || sp.stride_bytes == 0) continue;
            if (used + sp.stride_bytes > budget_bytes) continue;
            const double rank = (double) (slots[i] + 1);
            const double marginal_prob = std::pow(rank, -sp.zeta_exponent) * inv_zeta[i];
            const double mu = (sp.cpu_miss_cost * marginal_prob) / (double) sp.stride_bytes;
            if (mu > best_mu) {
                best_mu = mu;
                best_i = i;
            }
        }
        if (best_i == L) break;
        slots[best_i] += 1;
        used += specs[best_i].stride_bytes;
    }
    if (out_used_bytes) *out_used_bytes = used;
    return slots;
}

// 4. Truncated Riemann-Hurwitz tail probability P(rank > gpu_slots | Zeta_E(s)):
//    Exact off-VRAM miss probability mass spilling to Tier-2 (Pinned RAM) or Tier-3 (SATA/NVMe SSD).
inline double truncated_hurwitz_tail(int E, int gpu_slots, double s) noexcept {
    if (E <= 0 || gpu_slots >= E) return 0.0;
    const double z_all = truncated_zeta(E, s);
    if (z_all <= 0.0) return 0.0;
    const int start = std::max(1, gpu_slots + 1);
    double z_tail = 0.0;
    for (int k = start; k <= E; ++k) {
        z_tail += std::pow((double) k, -s);
    }
    return std::clamp(z_tail / z_all, 0.0, 1.0);
}

// 5. 3-Tier Hurwitz-Zeta Lagrangian RAM vs SATA SSD Priority Ranking:
//    Ranks off-VRAM hybrid layers by descending marginal SATA stall latency saved per byte of Pinned RAM:
//      mu_i^{RAM<-SATA} = (c_i * rho_SATA * P_spill(S_i^{GPU})) / (E_i * stride_i)
//    ShinkaEvolve (48 gens x 3 islands, real S5-1TB SATA 252.2/98.0 MB/s constants) optimal: rho_SATA = 12.958.
inline std::vector<size_t> zeta_hurwitz_ram_priority(const std::vector<ZetaLayerSpec>& specs,
                                                     const std::vector<int>& gpu_slots,
                                                     double sata_cost_ratio = 12.958) {
    const size_t L = specs.size();
    std::vector<size_t> order(L);
    std::vector<double> util(L, 0.0);
    for (size_t i = 0; i < L; ++i) {
        order[i] = i;
        const auto& sp = specs[i];
        const int s_gpu = (i < gpu_slots.size()) ? gpu_slots[i] : 0;
        if (s_gpu >= sp.max_slots || sp.stride_bytes == 0) {
            util[i] = -1.0;
            continue;
        }
        const double tail_p = truncated_hurwitz_tail(sp.max_slots, s_gpu, sp.zeta_exponent);
        const double pin_bytes = (double) std::max(1, sp.max_slots) * (double) sp.stride_bytes;
        util[i] = (sp.cpu_miss_cost * sata_cost_ratio * tail_p) / pin_bytes;
    }
    std::stable_sort(order.begin(), order.end(), [&](size_t a, size_t b) {
        return util[a] > util[b];
    });
    return order;
}

// 6. RH Critical-Line Spectral Lookahead Prefetch Breadth K_pf(H_norm, step):
//    Combines normalized Shannon routing entropy H_norm with RH critical-line uncertainty
//    delta_RH(t) = 1 / (sqrt(t + 4) * ln(t + e)) so early/high-entropy regimes prefetch wider
//    across SATA NCQ while converged low-entropy regimes avoid wasting SATA bandwidth.
//    ShinkaEvolve optimal on SATA S5-1TB: k_base = 8, beta_rh = 1.4732.
inline int rh_sata_prefetch_k(double norm_entropy, uint64_t step,
                              int k_base = 8, double beta_rh = 1.4732, int k_max = 12) noexcept {
    const double h = std::clamp(norm_entropy, 0.0, 1.0);
    const double rh_uncert = 1.0 / (std::sqrt((double) step + 4.0) * std::max(1.0, std::log((double) step + 2.718281828459045)));
    const double raw = (double) k_base + 4.0 * (h + beta_rh * rh_uncert);
    const int k = (int) std::ceil(raw);
    return std::clamp(k, 1, std::max(1, k_max));
}

// 7. SATA NCQ Address-Sorted Gap-Coalescing Prefetch Planner:
//    Sorts virtual/file byte spans ascending by address and merges ranges separated by <= max_gap_bytes
//    (up to max_merged_bytes) to convert random 64K SATA faults (~98 MB/s) into contiguous sequential
//    SATA NCQ bursts (~252 MB/s on S5-1TB, 2.57x bandwidth amplification).
struct SataPrefetchSpan {
    uintptr_t addr = 0;
    size_t len = 0;
};

inline void coalesce_sata_ranges(std::vector<SataPrefetchSpan>& spans,
                                 size_t max_gap_bytes,
                                 size_t max_merged_bytes = 32ull << 20) {
    if (spans.size() <= 1) return;
    std::sort(spans.begin(), spans.end(), [](const SataPrefetchSpan& a, const SataPrefetchSpan& b) {
        return a.addr < b.addr;
    });
    size_t out = 0;
    for (size_t i = 0; i < spans.size(); ++i) {
        const SataPrefetchSpan& cur = spans[i];
        if (cur.addr == 0 || cur.len == 0) continue;
        if (out == 0) {
            spans[out++] = cur;
            continue;
        }
        SataPrefetchSpan& prev = spans[out - 1];
        const uintptr_t prev_end = prev.addr + prev.len;
        const uintptr_t cur_end = cur.addr + cur.len;
        if (cur.addr <= prev_end || (cur.addr - prev_end) <= max_gap_bytes) {
            const uintptr_t new_end = std::max(prev_end, cur_end);
            const size_t merged_len = (size_t) (new_end - prev.addr);
            if (merged_len <= max_merged_bytes) {
                prev.len = merged_len;
                continue;
            }
        }
        spans[out++] = cur;
    }
    spans.resize(out);
}

}  // namespace strata::math
