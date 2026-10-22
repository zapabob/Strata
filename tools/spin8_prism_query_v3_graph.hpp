#pragma once

#include "ggml.h"
#include "spin8/query_v3.h"

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>

// Private reference adapter for pinned Prism GGML 73bfe6cc. This is not a
// public llama API, a custom CPU op, or the fused Spin8 CUDA controller.
namespace strata_prism_query_v3 {

struct parameters {
  ggml_tensor *win = nullptr;       // [d,8,heads], source coordinate first
  ggml_tensor *bin = nullptr;       // [8,heads]
  ggml_tensor *wout = nullptr;      // [8,7,heads], hidden coordinate first
  ggml_tensor *bout = nullptr;      // [7,heads]
  std::array<ggml_tensor *, 7> j{}; // [8,8], row-major J_a as exported by core
};

struct host_span {
  const float *data = nullptr;
  size_t bytes = 0;
};
struct host_parameters {
  host_span win, bin, wout, bout, j; // j: seven consecutive row-major matrices
};
struct host_query {
  const float *data = nullptr;
  size_t bytes = 0;
  int64_t width = 0, heads = 0, tokens = 0;
  size_t head_stride_bytes = 0, token_stride_bytes = 0;
};

// Explicit numerical admission budgets, not model defaults. Unlike the FP64
// CPU/CUDA core, this F32 reference graph does not accept all finite profiles.
// Admission checks conservative absolute sums, including cancellation cases.
struct f32_limits {
  double query_l1 = 0.0;
  double hidden_l1 = 0.0;
  double tangent_l1 = 0.0;
};
inline f32_limits conservative_f32_limits() {
  const double maximum = std::numeric_limits<float>::max();
  return {maximum / 64.0, maximum / 64.0, std::sqrt(maximum / 64.0)};
}

namespace detail {
[[noreturn]] inline void invalid(const std::string &message) {
  throw std::invalid_argument("Prism query-v3: " + message);
}
inline size_t mul(size_t a, size_t b, const char *name) {
  if (b != 0 && a > std::numeric_limits<size_t>::max() / b) {
    invalid(std::string(name) + " byte/shape multiplication overflow");
  }
  return a * b;
}
inline size_t add(size_t a, size_t b, const char *name) {
  if (a > std::numeric_limits<size_t>::max() - b) {
    invalid(std::string(name) + " byte/shape addition overflow");
  }
  return a + b;
}
inline size_t dimension(int64_t value, const char *name) {
  if (value <= 0 || uint64_t(value) > std::numeric_limits<size_t>::max()) {
    invalid(std::string(name) + " dimensions must be positive and fit size_t");
  }
  return size_t(value);
}
inline void limits(const f32_limits &value) {
  const auto maximum = conservative_f32_limits();
  if (!std::isfinite(value.query_l1) || value.query_l1 <= 0.0 ||
      value.query_l1 > maximum.query_l1 || !std::isfinite(value.hidden_l1) ||
      value.hidden_l1 <= 0.0 || value.hidden_l1 > maximum.hidden_l1 ||
      !std::isfinite(value.tangent_l1) || value.tangent_l1 <= 0.0 ||
      value.tangent_l1 > maximum.tangent_l1) {
    invalid("explicit F32 admission limits must be finite, positive and within "
            "safe budgets");
  }
}
inline void host_buffer(host_span span, size_t count, const char *name) {
  const size_t bytes = mul(count, sizeof(float), name);
  const auto address = reinterpret_cast<uintptr_t>(span.data);
  if (!span.data || address % alignof(float) != 0 || bytes > span.bytes ||
      address > std::numeric_limits<uintptr_t>::max() - bytes) {
    invalid(std::string(name) + " alignment/capacity/address range is invalid");
  }
  for (size_t i = 0; i < count; ++i) {
    if (!std::isfinite(span.data[i])) {
      invalid(std::string(name) + " payload must be finite");
    }
  }
}
inline size_t query_layout(const host_query &q) {
  const size_t width = dimension(q.width, "Q"), heads = dimension(q.heads, "Q");
  const size_t tokens = dimension(q.tokens, "Q");
  const size_t row_bytes = mul(width, sizeof(float), "Q");
  const size_t head_span =
      add(mul(heads - 1, q.head_stride_bytes, "Q"), row_bytes, "Q");
  if (q.head_stride_bytes % sizeof(float) != 0 ||
      q.head_stride_bytes < row_bytes ||
      q.token_stride_bytes % sizeof(float) != 0 ||
      q.token_stride_bytes < head_span) {
    invalid("Q stride must describe disjoint F32 head/token rows");
  }
  const size_t bytes =
      add(mul(tokens - 1, q.token_stride_bytes, "Q"), head_span, "Q");
  const auto address = reinterpret_cast<uintptr_t>(q.data);
  if (!q.data || address % alignof(float) != 0 || bytes > q.bytes ||
      address > std::numeric_limits<uintptr_t>::max() - bytes) {
    invalid("Q capacity/alignment/address range is invalid");
  }
  return bytes;
}
inline void tensor(ggml_tensor *value, int64_t a, int64_t b, int64_t c,
                   const char *name) {
  if (!value) {
    invalid(std::string(name) + " tensor is missing");
  }
  if (value->type != GGML_TYPE_F32) {
    invalid(std::string(name) + " requires F32");
  }
  if (value->ne[0] != a || value->ne[1] != b || value->ne[2] != c ||
      value->ne[3] != 1) {
    invalid(std::string(name) + " tensor shape mismatch");
  }
  size_t bytes = sizeof(float);
  const int64_t shape[] = {a, b, c, 1};
  for (size_t i = 0; i < 4; ++i) {
    if (value->nb[i] != bytes) {
      invalid(std::string(name) +
              " parameter tensor must have contiguous F32 layout");
    }
    bytes = mul(bytes, dimension(shape[i], name), name);
  }
  if (bytes != ggml_nbytes(value)) {
    invalid(std::string(name) + " tensor byte count mismatch");
  }
}
inline ggml_tensor *mm(ggml_context *ctx, ggml_tensor *a, ggml_tensor *b) {
  auto *out = ggml_mul_mat(ctx, a, b);
  ggml_mul_mat_set_prec(out, GGML_PREC_F32);
  return out;
}
} // namespace detail

// Converts only the audited core's actual convention. No caller-selected or
// independently invented Clifford basis is accepted by host admission.
inline std::array<float, 448> audited_generators_f32() {
  spin8_query_v3_basis_report report{};
  std::array<double, 448> source{};
  if (spin8_query_v3_basis_audit(&report) != SPIN8_OK ||
      spin8_query_v3_generators(source.data()) != SPIN8_OK) {
    throw std::runtime_error("Prism query-v3: core J basis audit failed");
  }
  std::array<float, 448> result{};
  for (size_t i = 0; i < result.size(); ++i) {
    result[i] = static_cast<float>(source[i]);
    if (!std::isfinite(result[i]) || double(result[i]) != source[i]) {
      throw std::runtime_error(
          "Prism query-v3: audited J is not exactly representable in F32");
    }
  }
  return result;
}

// Mandatory BEFORE executing an enabled graph on this exact host payload.
// The caller uploads exactly these admitted parameter/J bytes and Q values,
// preserves them until execution finishes, and serializes any updates.
// A graph-produced GPU Q needs an equivalent device admission/error boundary;
// this standalone helper does not implement that future engine plumbing.
inline void admit_host_payload(const host_parameters &p, const host_query &q,
                               const f32_limits &limits) {
  detail::limits(limits);
  detail::query_layout(q);
  const size_t width = size_t(q.width), heads = size_t(q.heads),
               tokens = size_t(q.tokens);
  const size_t head_win = detail::mul(width, 8, "Win");
  detail::host_buffer(p.win, detail::mul(head_win, heads, "Win"), "Win");
  detail::host_buffer(p.bin, detail::mul(8, heads, "bin"), "bin");
  detail::host_buffer(p.wout, detail::mul(56, heads, "Wout"), "Wout");
  detail::host_buffer(p.bout, detail::mul(7, heads, "bout"), "bout");
  detail::host_buffer(p.j, 448, "J");
  const auto expected_j = audited_generators_f32();
  for (size_t i = 0; i < expected_j.size(); ++i) {
    if (p.j.data[i] != expected_j[i]) {
      detail::invalid("J payload differs from the audited core basis");
    }
  }
  for (size_t h = 0; h < heads; ++h) {
    double tangent_l1 = 0.0;
    for (size_t axis = 0; axis < 7; ++axis) {
      tangent_l1 += std::abs(double(p.bout.data[h * 7 + axis]));
      for (size_t k = 0; k < 8; ++k) {
        tangent_l1 += std::abs(double(p.wout.data[h * 56 + axis * 8 + k]));
      }
    }
    // tanh is bounded by one, so this is independent of the hidden values.
    if (!std::isfinite(tangent_l1) || tangent_l1 > limits.tangent_l1) {
      detail::invalid(
          "tangent absolute-sum bound exceeds admitted F32 chart budget");
    }
    for (size_t t = 0; t < tokens; ++t) {
      const auto *row = reinterpret_cast<const float *>(
          reinterpret_cast<const unsigned char *>(q.data) +
          h * q.head_stride_bytes + t * q.token_stride_bytes);
      double query_l1 = 0.0;
      for (size_t i = 0; i < width; ++i) {
        if (!std::isfinite(row[i])) {
          detail::invalid("Q payload must be finite, including copied tails");
        }
        query_l1 += std::abs(double(row[i]));
      }
      if (!std::isfinite(query_l1) || query_l1 > limits.query_l1) {
        detail::invalid(
            "query absolute-sum bound exceeds admitted F32 rotation budget");
      }
      for (size_t k = 0; k < 8; ++k) {
        double hidden_l1 = std::abs(double(p.bin.data[h * 8 + k]));
        for (size_t i = 0; i < width; ++i) {
          hidden_l1 += std::abs(
              double(p.win.data[h * head_win + k * width + i]) * row[i]);
        }
        if (!std::isfinite(hidden_l1) || hidden_l1 > limits.hidden_l1) {
          detail::invalid("hidden absolute-sum bound exceeds admitted F32 "
                          "controller budget");
        }
      }
    }
  }
}

// Mandatory before consuming output. A failed admission rejects the complete
// evaluation; partial graph results must not enter attention or a KV cache.
inline void admit_host_output(host_span output, size_t elements) {
  if (elements == 0) {
    detail::invalid("output must contain at least one F32 element");
  }
  detail::host_buffer(output, elements, "output");
}

// Contract: Q is ALREADY model-normalized [d,heads,tokens] and has NOT
// undergone RoPE/MRoPE. Call immediately after Q normalization, then apply the
// model's original RoPE. No K/V, cache, mask, softmax, gate or position tensor
// is touched. Q and parameters are borrowed; their GGML contexts/buffers
// outlive this graph. Enabled graph: structural checks only; caller MUST
// perform payload admission for every evaluation and reject nonfinite
// execution/output via the above contract. GGML itself does not provide this
// adapter's semantic error flag. Enabled zero Wout/bout is numerical identity;
// only OFF is pointer/bit exact.
inline ggml_tensor *build_pre_rope(ggml_context *ctx, ggml_tensor *q,
                                   const parameters &p,
                                   const f32_limits &limits, bool enabled) {
  if (!enabled) {
    return q;
  }
  detail::limits(limits);
  if (!ctx || !q) {
    detail::invalid("enabled graph requires context and Q");
  }
  if (q->type != GGML_TYPE_F32) {
    detail::invalid("Q requires F32");
  }
  if (q->ne[3] != 1 || q->nb[0] != sizeof(float)) {
    detail::invalid(
        "Q must have [d,heads,tokens] shape with contiguous F32 coordinates");
  }
  const int64_t width = q->ne[0], heads = q->ne[1], tokens = q->ne[2];
  // No data access: graph nodes may not yet have allocated backing storage.
  const auto row_bytes =
      detail::mul(detail::dimension(width, "Q"), sizeof(float), "Q");
  const auto head_span =
      detail::add(detail::mul(detail::dimension(heads, "Q") - 1, q->nb[1], "Q"),
                  row_bytes, "Q");
  if (q->nb[1] % sizeof(float) != 0 || q->nb[1] < row_bytes ||
      q->nb[2] % sizeof(float) != 0 || q->nb[2] < head_span) {
    detail::invalid("Q stride must describe disjoint F32 head/token rows");
  }
  const size_t span_bytes = detail::add(
      detail::mul(detail::dimension(tokens, "Q") - 1, q->nb[2], "Q"), head_span,
      "Q");
  if (span_bytes != ggml_nbytes(q) ||
      span_bytes > size_t(std::numeric_limits<int64_t>::max())) {
    detail::invalid("Q tensor byte span mismatch or exceeds GGML index range");
  }
  detail::tensor(p.win, width, 8, heads, "Win");
  detail::tensor(p.bin, 8, heads, 1, "bin");
  detail::tensor(p.wout, 8, 7, heads, "Wout");
  detail::tensor(p.bout, 7, heads, 1, "bout");
  for (auto *j : p.j) {
    detail::tensor(j, 8, 8, 1, "J");
  }

  constexpr float tau = 0.4142135623730950488f;
  // GGML batch dimensions preserve distinct heads and tokens. Broadcasting
  // parameters over tokens and J over every block avoids per-head/block graph
  // expansion: node count stays bounded as head count and width grow.
  auto *qc = ggml_reshape_4d(ctx, ggml_cont(ctx, q), width, 1, heads, tokens);
  auto *bin = ggml_reshape_4d(ctx, p.bin, 8, 1, heads, 1);
  auto *bout = ggml_reshape_4d(ctx, p.bout, 7, 1, heads, 1);
  auto *hidden = ggml_tanh(ctx, ggml_add(ctx, detail::mm(ctx, p.win, qc), bin));
  auto *a = ggml_add(ctx, detail::mm(ctx, p.wout, hidden), bout);
  // Admission leaves a factor 64 of range for squares/reductions.
  auto *radius =
      ggml_sqrt(ctx, ggml_scale_bias(ctx, ggml_sum_rows(ctx, ggml_sqr(ctx, a)),
                                     1.0f, tau * tau));
  auto *u = ggml_scale(ctx, ggml_div(ctx, a, radius), tau);
  auto *norm =
      ggml_sqrt(ctx, ggml_scale_bias(ctx, ggml_sum_rows(ctx, ggml_sqr(ctx, u)),
                                     1.0f, 1.0f));
  auto *one = ggml_scale_bias(ctx, norm, 0.0f, 1.0f);
  auto *c0 = ggml_div(ctx, one, norm);
  auto *c = ggml_mul(ctx, u, c0);
  const int64_t full = width - width % 8;
  ggml_tensor *transformed = nullptr;
  if (full != 0) {
    auto *active = ggml_view_4d(ctx, qc, full, 1, heads, tokens, qc->nb[1],
                                qc->nb[2], qc->nb[3], 0);
    auto *blocks = ggml_reshape_4d(ctx, ggml_cont(ctx, active), 8, full / 8,
                                   heads, tokens);
    auto *rotated = ggml_mul(ctx, blocks, c0);
    for (size_t axis = 0; axis < 7; ++axis) {
      auto *coefficient =
          ggml_view_4d(ctx, c, 1, 1, heads, tokens, c->nb[1], c->nb[2],
                       c->nb[3], axis * sizeof(float));
      auto *term =
          ggml_mul(ctx, detail::mm(ctx, p.j[axis], blocks), coefficient);
      rotated = ggml_add(ctx, rotated, term);
    }
    transformed = ggml_reshape_4d(ctx, rotated, full, 1, heads, tokens);
  }
  if (width % 8 != 0) {
    auto *tail =
        ggml_view_4d(ctx, qc, width % 8, 1, heads, tokens, qc->nb[1], qc->nb[2],
                     qc->nb[3], size_t(full) * sizeof(float));
    transformed = transformed ? ggml_concat(ctx, transformed, tail, 0)
                              : ggml_cont(ctx, tail);
  }
  auto *result = ggml_reshape_3d(ctx, transformed, width, heads, tokens);
  ggml_set_name(result, "spin8_query_v3_pre_rope_reference");
  return result;
}
} // namespace strata_prism_query_v3
