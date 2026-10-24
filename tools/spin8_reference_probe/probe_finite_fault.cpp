// Exercise the real probe's output checks, with SPIN8_OK results poisoned only
// in this test executable. The ordinary probe and library contain no injector.
#include <limits>
#include <spin8/spin8.h>
#include <string>

namespace {
std::string fault_scope;
double fault_value = 0.0;

void poison(const std::string &scope, spin8_dtype dtype, void *dst,
            size_t stride, size_t rows, size_t cols) {
  if (scope != fault_scope) {
    return;
  }
  const size_t last = (rows - 1) * stride + cols - 1;
  if (dtype == SPIN8_F32) {
    static_cast<float *>(dst)[last] = static_cast<float>(fault_value);
  } else {
    static_cast<double *>(dst)[last] = fault_value;
  }
}

spin8_status fault_transform(const spin8_plan *plan, spin8_view view,
                             spin8_dtype dtype, const void *src,
                             size_t src_stride, void *dst, size_t dst_stride,
                             size_t rows, size_t cols, int inverse) {
  auto status = spin8_transform(plan, view, dtype, src, src_stride, dst,
                                dst_stride, rows, cols, inverse);
  if (status == SPIN8_OK) {
    std::string scope = cols == 20 ? "extended" : "trial";
    scope += dtype == SPIN8_F32 ? "-f32" : "-f64";
    scope += inverse ? "-inverse" : "-forward";
    poison(scope, dtype, dst, dst_stride, rows, cols);
  }
  return status;
}

spin8_status fault_block(spin8_dtype dtype, const void *src, size_t src_stride,
                         void *dst, size_t dst_stride, size_t rows, size_t cols,
                         size_t block, const int8_t *signs, int inverse) {
  auto status = spin8_hadamard_block(dtype, src, src_stride, dst, dst_stride,
                                     rows, cols, block, signs, inverse);
  if (status == SPIN8_OK) {
    std::string scope = "block-" + std::to_string(block);
    scope += dtype == SPIN8_F32 ? "-f32" : "-f64";
    scope += inverse ? "-inverse" : "-forward";
    poison(scope, dtype, dst, dst_stride, rows, cols);
  }
  return status;
}
} // namespace

#define spin8_transform fault_transform
#define spin8_hadamard_block fault_block
#define main reference_probe_main
#include "probe_spin8.cpp"
#undef main
#undef spin8_hadamard_block
#undef spin8_transform

int main(int argc, char **argv) {
  if (argc < 3) {
    return 3;
  }
  fault_scope = argv[1];
  const std::string value = argv[2];
  if (value == "nan") {
    fault_value = std::numeric_limits<double>::quiet_NaN();
  } else if (value == "inf") {
    fault_value = std::numeric_limits<double>::infinity();
  } else {
    return 3;
  }
  return reference_probe_main(argc - 2, argv + 2);
}
