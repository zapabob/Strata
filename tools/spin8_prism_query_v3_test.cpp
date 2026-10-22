#include "ggml-cpu.h"
#include "spin8_prism_query_v3_graph.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace qv3 = strata_prism_query_v3;
namespace {
void require(bool condition, const char *message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}
template <typename F> void rejects(F action, const char *fragment) {
  try {
    action();
  } catch (const std::invalid_argument &error) {
    require(std::string(error.what()).find(fragment) != std::string::npos,
            "fault must have a descriptive exception");
    return;
  }
  throw std::runtime_error("invalid payload was accepted");
}
using context_ptr = std::unique_ptr<ggml_context, decltype(&ggml_free)>;
using controller_ptr =
    std::unique_ptr<spin8_query_v3_controller,
                    decltype(&spin8_query_v3_controller_free)>;
int maximum_nodes = 0;

struct fixture {
  context_ptr ctx{ggml_init({128 * 1024 * 1024, nullptr, false}), ggml_free};
  int64_t d, heads, tokens;
  ggml_tensor *q = nullptr;
  qv3::parameters parameters{};
  std::vector<float> win, bin, wout, bout;
  std::array<float, 448> generators = qv3::audited_generators_f32();

  fixture(int64_t width, int64_t h, int64_t t, bool strided = false,
          bool identity = false, bool near_bound = false)
      : d(width), heads(h), tokens(t), win(size_t(d * 8 * heads)),
        bin(size_t(8 * heads)), wout(size_t(56 * heads)),
        bout(size_t(7 * heads)) {
    require(bool(ctx), "GGML context allocation");
    auto *backing = ggml_new_tensor_3d(ctx.get(), GGML_TYPE_F32,
                                       strided ? d * 2 : d, heads, tokens);
    q = strided ? ggml_view_3d(ctx.get(), backing, d, heads, tokens,
                               backing->nb[1], backing->nb[2], 0)
                : backing;
    for (int64_t t0 = 0; t0 < tokens; ++t0) {
      for (int64_t h0 = 0; h0 < heads; ++h0) {
        for (int64_t i = 0; i < d; ++i) {
          at(i, h0, t0) = float(std::sin(double(i + 3 * h0 + 7 * t0) * .19) +
                                .11 * double(t0 + 1));
        }
        // Exercise bit-preserving copying of a negative-zero tail.
        if (d % 8 != 0) {
          at(d - 1, h0, t0) = -0.0f;
        }
      }
    }
    for (size_t i = 0; i < win.size(); ++i) {
      win[i] = float(.09 * std::sin(double(i + 1) * .31));
    }
    for (size_t i = 0; i < bin.size(); ++i) {
      bin[i] = float(.07 * std::cos(double(i + 2)));
    }
    for (size_t i = 0; i < wout.size(); ++i) {
      wout[i] = identity ? 0.0f : float(.13 * std::sin(double(i + 2) * .47));
    }
    for (size_t i = 0; i < bout.size(); ++i) {
      bout[i] = identity ? 0.0f
                         : float((near_bound ? 1.e8 : .03) *
                                 std::cos(double(i + 1) * .37));
    }
    parameters.win =
        tensor(ggml_new_tensor_3d(ctx.get(), GGML_TYPE_F32, d, 8, heads), win);
    parameters.bin =
        tensor(ggml_new_tensor_2d(ctx.get(), GGML_TYPE_F32, 8, heads), bin);
    parameters.wout =
        tensor(ggml_new_tensor_3d(ctx.get(), GGML_TYPE_F32, 8, 7, heads), wout);
    parameters.bout =
        tensor(ggml_new_tensor_2d(ctx.get(), GGML_TYPE_F32, 7, heads), bout);
    for (size_t j = 0; j < 7; ++j) {
      parameters.j[j] = ggml_new_tensor_2d(ctx.get(), GGML_TYPE_F32, 8, 8);
      std::copy_n(generators.data() + j * 64, 64,
                  static_cast<float *>(parameters.j[j]->data));
    }
  }
  ggml_tensor *tensor(ggml_tensor *target, const std::vector<float> &values) {
    std::copy(values.begin(), values.end(), static_cast<float *>(target->data));
    return target;
  }
  float &at(int64_t i, int64_t h, int64_t t) {
    auto *row = static_cast<unsigned char *>(q->data) + size_t(h) * q->nb[1] +
                size_t(t) * q->nb[2];
    return reinterpret_cast<float *>(row)[i];
  }
  qv3::host_parameters host() const {
    return {{win.data(), win.size() * sizeof(float)},
            {bin.data(), bin.size() * sizeof(float)},
            {wout.data(), wout.size() * sizeof(float)},
            {bout.data(), bout.size() * sizeof(float)},
            {generators.data(), generators.size() * sizeof(float)}};
  }
  qv3::host_query query() const {
    return {static_cast<const float *>(q->data),
            ggml_nbytes(q),
            d,
            heads,
            tokens,
            q->nb[1],
            q->nb[2]};
  }
  std::vector<double> reference() {
    std::vector<double> expected(size_t(d * heads * tokens));
    for (int64_t h = 0; h < heads; ++h) {
      // F64 reference receives exactly the deployed, F32-rounded weights.
      std::vector<double> wi(win.begin() + h * d * 8,
                             win.begin() + (h + 1) * d * 8);
      std::vector<double> bi(bin.begin() + h * 8, bin.begin() + (h + 1) * 8);
      std::vector<double> wo(wout.begin() + h * 56,
                             wout.begin() + (h + 1) * 56);
      std::vector<double> bo(bout.begin() + h * 7, bout.begin() + (h + 1) * 7);
      spin8_query_v3_controller *raw = nullptr;
      require(spin8_query_v3_controller_create(
                  3, size_t(d), wi.data(), wi.size() * 8, bi.data(),
                  bi.size() * 8, wo.data(), wo.size() * 8, bo.data(),
                  bo.size() * 8, &raw) == SPIN8_OK,
              "F64 controller create");
      controller_ptr controller(raw, spin8_query_v3_controller_free);
      for (int64_t t = 0; t < tokens; ++t) {
        std::vector<double> row(size_t(d), 0.0);
        for (int64_t i = 0; i < d; ++i) {
          row[size_t(i)] = at(i, h, t);
        }
        require(spin8_query_v3_controller_apply(
                    controller.get(), SPIN8_F64, row.data(), row.size() * 8,
                    size_t(d), expected.data() + d * (h + heads * t),
                    row.size() * 8, size_t(d), 1) == SPIN8_OK,
                "F64 controller apply");
      }
    }
    return expected;
  }
  ggml_tensor *compute() {
    const auto limits = qv3::conservative_f32_limits();
    qv3::admit_host_payload(host(), query(), limits);
    auto *out = qv3::build_pre_rope(ctx.get(), q, parameters, limits, true);
    auto *graph = ggml_new_graph_custom(ctx.get(), 16384, false);
    ggml_build_forward_expand(graph, out);
    maximum_nodes = std::max(maximum_nodes, ggml_graph_n_nodes(graph));
    require(ggml_graph_n_nodes(graph) < 256,
            "batched query-v3 graph node count must be independent of "
            "heads/blocks");
    for (int n = 0; n < ggml_graph_n_nodes(graph); ++n) {
      const auto *node = ggml_graph_node(graph, n);
      require(
          node->op != GGML_OP_MAP_CUSTOM1 && node->op != GGML_OP_MAP_CUSTOM2 &&
              node->op != GGML_OP_MAP_CUSTOM3 && node->op != GGML_OP_RMS_NORM,
          "graph must have no CPU custom op or additional RMS norm");
    }
    require(ggml_graph_compute_with_ctx(ctx.get(), graph, 1) ==
                GGML_STATUS_SUCCESS,
            "GGML CPU graph compute");
    qv3::admit_host_output(
        {static_cast<const float *>(out->data), ggml_nbytes(out)},
        size_t(d * heads * tokens));
    return out;
  }
};

double maximum_error = 0.0;
void compare_case(int64_t d, int64_t heads, int64_t tokens, bool strided,
                  bool identity, bool near_bound) {
  fixture f(d, heads, tokens, strided, identity, near_bound);
  const auto expected = f.reference();
  auto *out = f.compute();
  require(out->ne[0] == d && out->ne[1] == heads && out->ne[2] == tokens &&
              out->ne[3] == 1,
          "output shape matches Q");
  const auto *actual = static_cast<const float *>(out->data);
  double total_change = 0.0;
  for (int64_t t = 0; t < tokens; ++t) {
    for (int64_t h = 0; h < heads; ++h) {
      double before = 0.0, after = 0.0;
      for (int64_t i = 0; i < d; ++i) {
        const size_t at = size_t(i + d * (h + heads * t));
        const double error = std::abs(double(actual[at]) - expected[at]);
        maximum_error = std::max(maximum_error, error);
        require(error < 3.e-5, "F32 graph versus F64 rounded-weight oracle");
        before += double(f.at(i, h, t)) * f.at(i, h, t);
        after += double(actual[at]) * actual[at];
        total_change += std::abs(double(actual[at]) - f.at(i, h, t));
        if (i >= d - d % 8) {
          require(std::memcmp(&actual[at], &f.at(i, h, t), sizeof(float)) == 0,
                  "tail copied bitwise, including negative zero");
        }
      }
      require(std::abs(before - after) < 3.e-5 * std::max(1.0, before),
              "each head and token preserves its own norm");
      for (int64_t block = 0; block + 8 <= d; block += 8) {
        double dot = 0.0, norm2 = 0.0;
        for (int64_t i = 0; i < 8; ++i) {
          const double x = f.at(block + i, h, t);
          dot += x * actual[size_t(block + i + d * (h + heads * t))];
          norm2 += x * x;
        }
        const double angle = std::acos(std::clamp(dot / norm2, -1.0, 1.0));
        require(angle < .3926990816987242 + 2.e-5,
                "isoclinic angle bounded by pi/8");
        if (near_bound) {
          require(std::abs(angle - .3926990816987242) < 2.e-5,
                  "large tangent approaches the angle bound");
        }
      }
    }
  }
  if (!identity && d >= 8) {
    require(total_change > .001, "nonzero controller must change Q");
  }
}

// A concrete position-dependent rotation of coordinates 0/1. Its unequal
// angles at each token do not commute with the query-dependent v3 transform.
void position_rotate(std::vector<double> &values, int64_t d, int64_t heads,
                     int64_t tokens) {
  for (int64_t t = 0; t < tokens; ++t) {
    for (int64_t h = 0; h < heads; ++h) {
      const size_t base = size_t(d * (h + heads * t));
      const double x = values[base], y = values[base + 1];
      const double angle = .41 * double(t + 1);
      values[base] = std::cos(angle) * x - std::sin(angle) * y;
      values[base + 1] = std::sin(angle) * x + std::cos(angle) * y;
    }
  }
}
void ordering_and_tail_dependence() {
  fixture before(15, 2, 3);
  auto expected = before.reference();
  auto *out = before.compute();
  std::vector<double> actual(size_t(15 * 2 * 3), 0.0);
  std::transform(static_cast<float *>(out->data),
                 static_cast<float *>(out->data) + actual.size(),
                 actual.begin(), [](float x) { return double(x); });
  position_rotate(expected, 15, 2, 3);
  position_rotate(actual, 15, 2, 3);
  for (size_t i = 0; i < actual.size(); ++i) {
    require(std::abs(actual[i] - expected[i]) < 3.e-5,
            "adapter then position rotation");
  }
  fixture after(15, 2, 3);
  std::vector<double> rotated(actual.size(), 0.0);
  for (int64_t t = 0; t < 3; ++t) {
    for (int64_t h = 0; h < 2; ++h) {
      for (int64_t i = 0; i < 15; ++i) {
        rotated[size_t(i + 15 * (h + 2 * t))] = after.at(i, h, t);
      }
    }
  }
  position_rotate(rotated, 15, 2, 3);
  for (int64_t t = 0; t < 3; ++t) {
    for (int64_t h = 0; h < 2; ++h) {
      for (int64_t i = 0; i < 15; ++i) {
        after.at(i, h, t) = float(rotated[size_t(i + 15 * (h + 2 * t))]);
      }
    }
  }
  auto *wrong_order = after.compute();
  double difference = 0.0;
  for (size_t i = 0; i < actual.size(); ++i) {
    difference +=
        std::abs(actual[i] - static_cast<float *>(wrong_order->data)[i]);
  }
  require(difference > .01, "test must detect inserting adapter after RoPE");

  fixture tail_a(9, 1, 1), tail_b(9, 1, 1);
  tail_a.at(8, 0, 0) = -1.5f;
  tail_b.at(8, 0, 0) = 1.5f;
  auto *a = tail_a.compute();
  auto *b = tail_b.compute();
  double first_block_difference = 0.0;
  for (size_t i = 0; i < 8; ++i) {
    first_block_difference += std::abs(static_cast<float *>(a->data)[i] -
                                       static_cast<float *>(b->data)[i]);
  }
  require(first_block_difference > .001,
          "copied tail must still feed controller");
}

void faults_and_off() {
  fixture f(15, 2, 3, true);
  const auto limits = qv3::conservative_f32_limits();
  const size_t used = ggml_used_mem(f.ctx.get());
  require(qv3::build_pre_rope(nullptr, f.q, {}, {}, false) == f.q,
          "off returns original Q without requiring configuration");
  require(ggml_used_mem(f.ctx.get()) == used, "off allocates no GGML nodes");
  auto bad = f.parameters;
  bad.win = ggml_new_tensor_3d(f.ctx.get(), GGML_TYPE_F32, 14, 8, 2);
  rejects([&] { qv3::build_pre_rope(f.ctx.get(), f.q, bad, limits, true); },
          "Win");
  bad = f.parameters;
  bad.bout = ggml_new_tensor_2d(f.ctx.get(), GGML_TYPE_F16, 7, 2);
  rejects([&] { qv3::build_pre_rope(f.ctx.get(), f.q, bad, limits, true); },
          "F32");
  bad = f.parameters;
  bad.j[3] = nullptr;
  rejects([&] { qv3::build_pre_rope(f.ctx.get(), f.q, bad, limits, true); },
          "J");
  auto *q4 = ggml_new_tensor_4d(f.ctx.get(), GGML_TYPE_F32, 15, 2, 3, 2);
  rejects(
      [&] { qv3::build_pre_rope(f.ctx.get(), q4, f.parameters, limits, true); },
      "Q");
  auto *qh = ggml_new_tensor_3d(f.ctx.get(), GGML_TYPE_F16, 15, 2, 3);
  rejects(
      [&] { qv3::build_pre_rope(f.ctx.get(), qh, f.parameters, limits, true); },
      "F32");
  auto invalid_q = *f.q;
  invalid_q.ne[0] = 0;
  rejects(
      [&] {
        qv3::build_pre_rope(f.ctx.get(), &invalid_q, f.parameters, limits,
                            true);
      },
      "positive");
  auto invalid_parameter = *f.parameters.win;
  invalid_parameter.nb[1] += sizeof(float);
  bad = f.parameters;
  bad.win = &invalid_parameter;
  rejects([&] { qv3::build_pre_rope(f.ctx.get(), f.q, bad, limits, true); },
          "contiguous");
  auto bad_host = f.host();
  bad_host.win.bytes -= sizeof(float);
  rejects([&] { qv3::admit_host_payload(bad_host, f.query(), limits); }, "Win");
  auto bad_query = f.query();
  bad_query.bytes -= sizeof(float);
  rejects([&] { qv3::admit_host_payload(f.host(), bad_query, limits); },
          "capacity");
  bad_query = f.query();
  bad_query.head_stride_bytes = 1;
  rejects([&] { qv3::admit_host_payload(f.host(), bad_query, limits); },
          "stride");
  f.win[2] = std::numeric_limits<float>::quiet_NaN();
  rejects([&] { qv3::admit_host_payload(f.host(), f.query(), limits); },
          "finite");
  f.win[2] = -.25f; // Negative finite weights are valid, not clamped.
  qv3::admit_host_payload(f.host(), f.query(), limits);
  for (float *value : {&f.bin[0], &f.wout[0], &f.bout[0], &f.generators[0]}) {
    const float saved = *value;
    *value = -std::numeric_limits<float>::infinity();
    rejects([&] { qv3::admit_host_payload(f.host(), f.query(), limits); },
            "finite");
    *value = saved;
  }
  f.at(0, 1, 2) = std::numeric_limits<float>::infinity();
  rejects([&] { qv3::admit_host_payload(f.host(), f.query(), limits); },
          "finite");
  f.at(0, 1, 2) = 1.0f;
  f.generators[1] += .5f;
  rejects([&] { qv3::admit_host_payload(f.host(), f.query(), limits); },
          "audited");
  f.generators = qv3::audited_generators_f32();
  f.bout[0] = std::numeric_limits<float>::max();
  rejects([&] { qv3::admit_host_payload(f.host(), f.query(), limits); },
          "tangent");
  f.bout[0] = 0.0f;
  auto restricted = limits;
  restricted.query_l1 = .01;
  rejects([&] { qv3::admit_host_payload(f.host(), f.query(), restricted); },
          "query");
  restricted = limits;
  restricted.hidden_l1 = .01;
  rejects([&] { qv3::admit_host_payload(f.host(), f.query(), restricted); },
          "hidden");
  restricted = limits;
  restricted.query_l1 = std::numeric_limits<double>::infinity();
  rejects(
      [&] {
        qv3::build_pre_rope(f.ctx.get(), f.q, f.parameters, restricted, true);
      },
      "limits");
  bad_query = f.query();
  bad_query.token_stride_bytes = std::numeric_limits<size_t>::max() - 3;
  rejects([&] { qv3::admit_host_payload(f.host(), bad_query, limits); },
          "overflow");
  std::array<float, 2> invalid_output{0.0f,
                                      std::numeric_limits<float>::infinity()};
  rejects(
      [&] {
        qv3::admit_host_output({invalid_output.data(), sizeof(invalid_output)},
                               2);
      },
      "finite");
}
} // namespace

int main() {
  try {
    for (const int64_t d : {1, 7, 8, 9, 15, 23, 128, 256}) {
      compare_case(d, 1, 1, false, false, false);
      compare_case(d, 2, 3, true, false, false);
      compare_case(d, 2, 3, false, true, false);
    }
    compare_case(23, 2, 3, true, false, true);
    compare_case(256, 24, 2, false, false, false);
    compare_case(256, 24, 2, true, false, false);
    ordering_and_tail_dependence();
    faults_and_off();
    std::printf("PASS query-v3 GGML CPU: per-head/token F64 oracle, norms, "
                "tails, pre-RoPE order, off, admission; max_abs_error=%.9g "
                "max_graph_nodes=%d\n",
                maximum_error, maximum_nodes);
  } catch (const std::exception &error) {
    std::fprintf(stderr, "FAIL query-v3 GGML: %s\n", error.what());
    return 1;
  }
}
