#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <spin8/query.h>
#include <spin8/query_v3.h>
#include <spin8/spin8.h>
#include <string>
#include <vector>

namespace {

constexpr double kPi = 3.14159265358979323846;

struct Jw {
  std::FILE *f;
  int field;
  bool first = true;
  explicit Jw(std::FILE *file) : f(file) {}
  void key(const char *k) {
    if (k == nullptr) {
      return;
    }
    std::fprintf(f, "\"%s\":", k);
  }
  void comma() { std::fputc(',', f); }
  void obj_open(const char *k) {
    comma_if_needed();
    key(k);
    std::fputc('{', f);
    first = true;
  }
  void obj_close() {
    std::fputc('}', f);
    first = false;
  }
  void arr_open(const char *k) {
    comma_if_needed();
    key(k);
    std::fputc('[', f);
    first = true;
  }
  void arr_close() {
    std::fputc(']', f);
    first = false;
  }
  void lit(const char *k, bool v) {
    comma_if_needed();
    key(k);
    std::fprintf(f, v ? "true" : "false");
    field = 0;
  }
  void lit(const char *k, const char *v) {
    comma_if_needed();
    key(k);
    std::fprintf(f, "\"%s\"", v);
    field = 0;
  }
  void lit(const char *k, double v) {
    comma_if_needed();
    key(k);
    std::fprintf(f, "%.17g", v);
    field = 0;
  }
  void lit(const char *k, uint64_t v) {
    comma_if_needed();
    key(k);
    std::fprintf(f, "%llu", static_cast<unsigned long long>(v));
    field = 0;
  }
  void lit(int v) {
    comma_if_needed();
    std::fprintf(f, "%d", v);
  }
  void lit(double v) {
    comma_if_needed();
    std::fprintf(f, "%.17g", v);
  }
  void item_comma() { first = false; }
  void comma_if_needed() {
    if (!first) {
      std::fputc(',', f);
    }
    first = false;
  }
};

[[noreturn]] void fail(const char *what, const char *detail = "") {
  std::fprintf(stdout, "FAIL %s %s\n", what, detail);
  std::exit(2);
}

void must(spin8_status s, const char *what) {
  if (s != SPIN8_OK) {
    std::fprintf(stdout, "FAIL status %s code=%d\n", what, static_cast<int>(s));
    std::exit(2);
  }
}

double u01(std::mt19937_64 &rng) {
  std::uniform_real_distribution<double> d(0.0, 1.0);
  return d(rng);
}

void write_audit_report(Jw &w, const spin8_audit_report &r) {
  w.obj_open("audit");
  w.arr_open("views");
  for (int i = 0; i < 3; ++i) {
    w.obj_open(nullptr);
    w.lit("ef_normalized", r.views[i].ef_normalized);
    w.lit("max_error", r.views[i].max_error);
    w.lit("log_abs_det", r.views[i].log_abs_det);
    w.lit("det_sign", static_cast<double>(r.views[i].det_sign));
    w.obj_close();
  }
  w.arr_close();
  w.lit("triality_max_error", r.triality_max_error);
  w.obj_close();
}

void write_audit(Jw &w, const spin8_matrix_audit &a) {
  w.lit("ef_normalized", a.ef_normalized);
  w.lit("max_error", a.max_error);
  w.lit("log_abs_det", a.log_abs_det);
  w.lit("det_sign", static_cast<double>(a.det_sign));
}

void write_plan(Jw &w, const spin8_plan *plan, const spin8_plane *planes,
                size_t count, bool include_planes) {
  double mat[64];
  spin8_audit_report audit;
  if (include_planes) {
    w.arr_open("planes");
    for (size_t i = 0; i < count; ++i) {
      w.lit(static_cast<int>(planes[i].a));
      w.lit(static_cast<int>(planes[i].b));
      w.lit(planes[i].angle);
    }
    w.arr_close();
  }
  w.arr_open("vector");
  must(spin8_plan_matrix(plan, SPIN8_VECTOR, mat), "plan_matrix_vector");
  for (double x : mat) {
    w.lit(x);
  }
  w.arr_close();
  w.arr_open("plus");
  must(spin8_plan_matrix(plan, SPIN8_SPIN_PLUS, mat), "plan_matrix_plus");
  for (double x : mat) {
    w.lit(x);
  }
  w.arr_close();
  w.arr_open("minus");
  must(spin8_plan_matrix(plan, SPIN8_SPIN_MINUS, mat), "plan_matrix_minus");
  for (double x : mat) {
    w.lit(x);
  }
  w.arr_close();
  must(spin8_plan_audit(plan, &audit), "plan_audit");
  write_audit_report(w, audit);
}

void write_square_block(Jw &w, const spin8_plan *plan, spin8_view view) {
  double mat[64];
  must(spin8_plan_matrix(plan, view, mat), "plan_matrix");
  for (double x : mat) {
    w.lit(x);
  }
}

struct LoopBuffers {
  std::vector<double> src;
  std::vector<double> fwd;
  std::vector<double> inv;
  double max_err = 0.0;
};

LoopBuffers run_f64_loopback(const spin8_plan *plan, spin8_view view,
                             size_t rows, size_t cols, std::mt19937_64 &rng) {
  LoopBuffers lb;
  lb.src.assign(rows * cols, 0.0);
  lb.fwd.assign(rows * cols, 0.0);
  lb.inv.assign(rows * cols, 0.0);
  for (double &x : lb.src) {
    x = 2.0 * u01(rng) - 1.0;
  }
  double cap = static_cast<double>(rows * cols * sizeof(double));
  must(spin8_transform(plan, view, SPIN8_F64, lb.src.data(), cols,
                       lb.fwd.data(), cols, rows, cols, 0),
       "transform_f64_fwd");
  must(spin8_transform(plan, view, SPIN8_F64, lb.fwd.data(), cols,
                       lb.inv.data(), cols, rows, cols, 1),
       "transform_f64_inv");
  for (size_t i = 0; i < rows * cols; ++i) {
    double e = std::fabs(lb.src[i] - lb.inv[i]);
    if (e > lb.max_err) {
      lb.max_err = e;
    }
  }
  (void)cap;
  return lb;
}

} // namespace

int main(int argc, char **argv) {
  uint64_t seed = 20261023;
  long trials_total = 5000;
  long python_check = 1000;
  const char *out_path = nullptr;
  if (argc % 2 == 0) {
    fail("arguments-require-values");
  }
  for (int i = 1; i + 1 < argc; i += 2) {
    std::string a = argv[i];
    if (a == "--out") {
      out_path = argv[i + 1];
    } else if (a == "--trials") {
      trials_total = std::atol(argv[i + 1]);
    } else if (a == "--python-check") {
      python_check = std::atol(argv[i + 1]);
    } else if (a == "--seed") {
      seed = std::strtoull(argv[i + 1], nullptr, 10);
    } else {
      fail("unknown-argument", argv[i]);
    }
  }
  if (out_path == nullptr || trials_total < 1 || python_check < 1 ||
      python_check > trials_total) {
    fail("argument-range");
  }

  std::FILE *f = std::fopen(out_path, "w");
  if (!f) {
    fail("open-output");
  }
  Jw w(f);

  spin8_capabilities caps;
  must(spin8_get_capabilities(&caps), "capabilities");
  double gens[2048];
  must(spin8_clifford_generators(gens), "clifford_generators");

  std::mt19937_64 rng(seed);

  w.obj_open(nullptr);
  w.lit("schema", "gateA-spin8-probe-v1");
  w.lit("seed", seed);
  w.lit("trials_total", static_cast<uint64_t>(trials_total));
  w.lit("python_check", static_cast<uint64_t>(python_check));
  w.obj_open("capabilities");
  w.lit("abi_version", static_cast<uint64_t>(caps.abi_version));
  w.lit("cpu_dtype_mask", static_cast<uint64_t>(caps.cpu_dtype_mask));
  w.lit("representation_dimension",
        static_cast<uint64_t>(caps.representation_dimension));
  w.lit("hadamard_max_block", static_cast<uint64_t>(caps.hadamard_max_block));
  w.obj_close();

  w.arr_open("generators");
  for (double x : gens) {
    w.lit(x);
  }
  w.arr_close();

  w.arr_open("trials");
  for (long t = 0; t < trials_total; ++t) {
    std::vector<spin8_plane> planes;
    planes.reserve(12);
    bool python_checked = t < python_check;
    for (int k = 0; k < 12; ++k) {
      uint64_t ra = rng() % 8;
      uint64_t rb = rng() % 7;
      if (rb >= ra) {
        ++rb;
      }
      double mag = 0.05 + u01(rng) * (kPi - 0.05);
      double sgn = (rng() % 2 == 0) ? 1.0 : -1.0;
      planes.push_back(
          {static_cast<uint32_t>(ra), static_cast<uint32_t>(rb), sgn * mag});
    }
    spin8_plan *plan = nullptr;
    must(spin8_plan_create(planes.data(), planes.size(), &plan),
         "plan_create_trial");
    if (python_checked) {
      double src[24];
      double fwd[24];
      double inv[24];
      for (double &x : src) {
        x = 2.0 * u01(rng) - 1.0;
      }
      must(spin8_transform(plan, SPIN8_VECTOR, SPIN8_F64, src, 8, fwd, 8, 3, 8,
                           0),
           "transform_trial_vector");
      must(spin8_transform(plan, SPIN8_VECTOR, SPIN8_F64, fwd, 8, inv, 8, 3, 8,
                           1),
           "transform_trial_vector_inv");
      double maxerr = 0.0;
      for (int i = 0; i < 24; ++i) {
        maxerr = std::max(maxerr, std::fabs(src[i] - inv[i]));
      }
      float fsrc[24];
      float fbase[24];
      float finv[24];
      for (int i = 0; i < 24; ++i) {
        fsrc[i] = static_cast<float>(src[i]);
        fbase[i] = fsrc[i];
      }
      must(spin8_transform(plan, SPIN8_VECTOR, SPIN8_F32, fsrc, 8, fsrc, 8, 3,
                           8, 0),
           "transform_trial_f32_fwd");
      must(spin8_transform(plan, SPIN8_VECTOR, SPIN8_F32, fsrc, 8, finv, 8, 3,
                           8, 1),
           "transform_trial_f32_inv");
      double f32err = 0.0;
      for (int i = 0; i < 24; ++i) {
        f32err = std::max(f32err, std::fabs(static_cast<double>(fbase[i]) -
                                            static_cast<double>(finv[i])));
      }
      w.obj_open(nullptr);
      write_plan(w, plan, planes.data(), planes.size(), true);
      w.arr_open("f64_src");
      for (double x : src) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("f64_fwd");
      for (double x : fwd) {
        w.lit(x);
      }
      w.arr_close();
      w.lit("f64_loopback_max", maxerr);
      w.lit("f32_loopback_max", f32err);
      w.obj_close();
    } else {
      w.obj_open(nullptr);
      write_plan(w, plan, planes.data(), planes.size(), false);
      w.obj_close();
    }
    spin8_plan_free(plan);
  }
  w.arr_close();

  {
    spin8_plane two{0, 1, 2.0 * kPi};
    spin8_plane four{0, 1, 4.0 * kPi};
    spin8_plan *p2 = nullptr;
    spin8_plan *p4 = nullptr;
    must(spin8_plan_create(&two, 1, &p2), "plan_2pi");
    must(spin8_plan_create(&four, 1, &p4), "plan_4pi");
    w.obj_open("two_pi");
    write_plan(w, p2, &two, 1, true);
    w.obj_close();
    w.obj_open("four_pi");
    write_plan(w, p4, &four, 1, true);
    w.obj_close();
    spin8_plan_free(p2);
    spin8_plan_free(p4);
  }
  {
    spin8_plan *pid = nullptr;
    must(spin8_plan_create(nullptr, 0, &pid), "plan_identity");
    w.obj_open("identity_plan");
    write_plan(w, pid, nullptr, 0, false);
    w.obj_close();
    spin8_plan_free(pid);
  }

  {
    std::vector<spin8_plane> tp{{0, 3, 0.9}, {1, 6, -0.55}, {4, 7, 2.1}};
    spin8_plan *tool = nullptr;
    must(spin8_plan_create(tp.data(), tp.size(), &tool), "plan_tool");
    LoopBuffers lb = run_f64_loopback(tool, SPIN8_VECTOR, 64, 20, rng);
    bool tail_equal = true;
    for (size_t r = 0; r < 64; ++r) {
      tail_equal = tail_equal && (lb.src[r * 20 + 16] == lb.fwd[r * 20 + 16]);
      tail_equal = tail_equal && (lb.src[r * 20 + 19] == lb.fwd[r * 20 + 19]);
    }
    w.obj_open("extended_loopback");
    w.arr_open("planes");
    for (const spin8_plane &p : tp) {
      w.lit(static_cast<int>(p.a));
      w.lit(static_cast<int>(p.b));
      w.lit(p.angle);
    }
    w.arr_close();
    w.arr_open("src");
    for (double x : lb.src) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("fwd");
    for (double x : lb.fwd) {
      w.lit(x);
    }
    w.arr_close();
    w.lit("loopback_max", lb.max_err);
    w.lit("tail_byte_equal", tail_equal);
    w.obj_close();
    spin8_plan_free(tool);
  }

  w.arr_open("hadamard_masks");
  for (uint32_t mask = 0; mask < 256; ++mask) {
    double fm[64];
    double im[64];
    spin8_matrix_audit aud;
    must(spin8_hadamard_matrix(static_cast<uint8_t>(mask), 0, fm),
         "hadamard_fwd");
    must(spin8_hadamard_matrix(static_cast<uint8_t>(mask), 1, im),
         "hadamard_inv");
    must(spin8_audit_matrix(fm, &aud), "hadamard_audit");
    w.obj_open(nullptr);
    w.lit("mask", static_cast<uint64_t>(mask));
    w.arr_open("f");
    for (double x : fm) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("i");
    for (double x : im) {
      w.lit(x);
    }
    w.arr_close();
    w.obj_open("audit");
    write_audit(w, aud);
    w.obj_close();
    w.obj_close();
  }
  w.arr_close();

  w.arr_open("hadamard_blocks");
  const size_t blocks[4] = {8, 16, 64, 128};
  for (size_t block : blocks) {
    for (int is_f32 = 0; is_f32 < 2; ++is_f32) {
      spin8_dtype dt = is_f32 ? SPIN8_F32 : SPIN8_F64;
      size_t elems_per = block * 3;
      std::vector<double> src(elems_per);
      std::vector<double> fwd(elems_per);
      std::vector<double> inv(elems_per);
      for (double &x : src) {
        x = 2.0 * u01(rng) - 1.0;
      }
      std::vector<float> fsrc(elems_per);
      std::vector<float> fbase(elems_per);
      std::vector<float> finv(elems_per);
      double max_err = 0.0;
      if (is_f32) {
        for (size_t i = 0; i < elems_per; ++i) {
          fsrc[i] = static_cast<float>(src[i]);
          fbase[i] = fsrc[i];
        }
        must(spin8_hadamard_block(dt, fsrc.data(), block, fsrc.data(), block, 3,
                                  block, block, nullptr, 0),
             "hadamard_f32_fwd");
        must(spin8_hadamard_block(dt, fsrc.data(), block, finv.data(), block, 3,
                                  block, block, nullptr, 1),
             "hadamard_f32_inv");
        for (size_t i = 0; i < elems_per; ++i) {
          max_err = std::max(max_err, std::fabs(static_cast<double>(fbase[i]) -
                                                static_cast<double>(finv[i])));
        }
      } else {
        must(spin8_hadamard_block(dt, src.data(), block, fwd.data(), block, 3,
                                  block, block, nullptr, 0),
             "hadamard_f64_fwd");
        must(spin8_hadamard_block(dt, fwd.data(), block, inv.data(), block, 3,
                                  block, block, nullptr, 1),
             "hadamard_f64_inv");
        for (size_t i = 0; i < elems_per; ++i) {
          max_err = std::max(max_err, std::fabs(src[i] - inv[i]));
        }
      }
      spin8_matrix_audit a64;
      spin8_matrix_audit a32;
      must(spin8_hadamard_block_audit(SPIN8_F64, block, nullptr, &a64),
           "hadamard_block_audit_f64");
      must(spin8_hadamard_block_audit(SPIN8_F32, block, nullptr, &a32),
           "hadamard_block_audit_f32");
      w.obj_open(nullptr);
      w.lit("block", static_cast<uint64_t>(block));
      w.lit("dtype", is_f32 ? "f32" : "f64");
      w.lit("loopback_max", max_err);
      w.obj_open("audit_f64");
      write_audit(w, a64);
      w.obj_close();
      w.obj_open("audit_f32");
      write_audit(w, a32);
      w.obj_close();
      w.obj_close();
    }
  }
  w.arr_close();

  {
    const size_t rows = 5;
    const size_t cols = 7;
    std::vector<double> v[3];
    std::vector<double> outd(rows * cols);
    std::vector<double> outc(rows * cols);
    const double *views[3];
    for (int k = 0; k < 3; ++k) {
      v[k].assign(rows * cols, 0.0);
      for (double &x : v[k]) {
        x = 2.0 * u01(rng) - 1.0;
      }
      views[k] = v[k].data();
    }
    const double custom[3] = {0.2, 0.3, 0.5};
    const void *const views_cp[3] = {views[0], views[1], views[2]};
    must(spin8_reduce(SPIN8_F64, views_cp, cols, outd.data(), cols, rows, cols,
                      nullptr),
         "reduce_default");
    must(spin8_reduce(SPIN8_F64, views_cp, cols, outc.data(), cols, rows, cols,
                      custom),
         "reduce_custom");
    w.obj_open("reduce");
    w.lit("rows", static_cast<uint64_t>(rows));
    w.lit("cols", static_cast<uint64_t>(cols));
    w.arr_open("views");
    for (int k = 0; k < 3; ++k) {
      for (double x : v[k]) {
        w.lit(x);
      }
    }
    w.arr_close();
    w.arr_open("out_default");
    for (double x : outd) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("out_custom");
    for (double x : outc) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("custom");
    w.lit(custom[0]);
    w.lit(custom[1]);
    w.lit(custom[2]);
    w.arr_close();
    w.obj_close();
  }

  std::vector<spin8_plane> tp{{0, 3, 0.9}, {1, 6, -0.55}, {4, 7, 2.1}};
  spin8_plan *mplan = nullptr;
  must(spin8_plan_create(tp.data(), tp.size(), &mplan), "plan_matmul");
  w.obj_open("matmul");
  {
    const size_t m = 6;
    const size_t n = 5;
    const size_t k = 8;
    std::vector<double> A(m * k);
    std::vector<double> B(n * k);
    for (double &x : A) {
      x = 2.0 * u01(rng) - 1.0;
    }
    for (double &x : B) {
      x = 2.0 * u01(rng) - 1.0;
    }
    std::vector<double> outd(m * n);
    std::vector<double> outc(m * n);
    const double custom[3] = {0.25, 0.35, 0.4};
    must(spin8_matmul_f64(mplan, A.data(), m, B.data(), n, k, nullptr,
                          outd.data()),
         "matmul_default");
    must(spin8_matmul_f64(mplan, A.data(), m, B.data(), n, k, custom,
                          outc.data()),
         "matmul_custom");
    w.arr_open("planes");
    for (const spin8_plane &p : tp) {
      w.lit(static_cast<int>(p.a));
      w.lit(static_cast<int>(p.b));
      w.lit(p.angle);
    }
    w.arr_close();
    w.arr_open("matrices");
    write_square_block(w, mplan, SPIN8_VECTOR);
    write_square_block(w, mplan, SPIN8_SPIN_PLUS);
    write_square_block(w, mplan, SPIN8_SPIN_MINUS);
    w.arr_close();
    w.arr_open("A");
    for (double x : A) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("B");
    for (double x : B) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("out_default");
    for (double x : outd) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("out_custom");
    for (double x : outc) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("custom");
    w.lit(custom[0]);
    w.lit(custom[1]);
    w.lit(custom[2]);
    w.arr_close();
  }
  w.obj_close();

  w.obj_open("attention");
  {
    const size_t nq = 8;
    const size_t nk = 12;
    const size_t d = 8;
    const size_t dv = 6;
    std::vector<double> q(nq * d);
    std::vector<double> k(nk * d);
    std::vector<double> v(nk * dv);
    std::vector<uint8_t> mask(nq * nk, 1);
    for (double &x : q) {
      x = 2.0 * u01(rng) - 1.0;
    }
    for (double &x : k) {
      x = 2.0 * u01(rng) - 1.0;
    }
    for (double &x : v) {
      x = 2.0 * u01(rng) - 1.0;
    }
    for (size_t i = 0; i < nq; ++i) {
      uint64_t a = rng() % nk;
      uint64_t b = rng() % (nk - 1);
      if (b >= a) {
        ++b;
      }
      mask[i * nk + a] = 0;
      mask[i * nk + b] = 0;
    }
    std::vector<double> out(nq * dv);
    must(spin8_attention_f64(mplan, q.data(), nq, k.data(), nk, v.data(), dv, d,
                             mask.data(), nullptr, out.data()),
         "attention_f64");
    w.arr_open("planes");
    for (const spin8_plane &p : tp) {
      w.lit(static_cast<int>(p.a));
      w.lit(static_cast<int>(p.b));
      w.lit(p.angle);
    }
    w.arr_close();
    w.lit("nq", static_cast<uint64_t>(nq));
    w.lit("nk", static_cast<uint64_t>(nk));
    w.lit("d", static_cast<uint64_t>(d));
    w.lit("dv", static_cast<uint64_t>(dv));
    w.arr_open("q");
    for (double x : q) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("k");
    for (double x : k) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("v");
    for (double x : v) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("mask");
    for (double x : mask) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("out");
    for (double x : out) {
      w.lit(x);
    }
    w.arr_close();
  }
  w.obj_close();
  spin8_plan_free(mplan);

  w.obj_open("query1");
  {
    const size_t rows = 3;
    const size_t width = 20;
    w.arr_open("cases");
    for (int c = 0; c < 16; ++c) {
      double h[7];
      double spinor[8];
      double mat[64];
      spin8_matrix_audit aud;
      std::vector<double> src(rows * width);
      std::vector<double> dst(rows * width);
      for (double &x : h) {
        x = 4.0 * u01(rng) - 2.0;
      }
      must(spin8_query_spinor_from_tangent(h, spinor), "q1_spinor");
      must(spin8_query_matrix(spinor, mat), "q1_matrix");
      must(spin8_query_matrix_audit(spinor, &aud), "q1_matrix_audit");
      for (double &x : src) {
        x = 2.0 * u01(rng) - 1.0;
      }
      must(spin8_query_transform(spinor, SPIN8_F64, src.data(),
                                 rows * width * sizeof(double), width,
                                 dst.data(), rows * width * sizeof(double),
                                 width, rows, width),
           "q1_transform");
      w.obj_open(nullptr);
      w.arr_open("h");
      for (double x : h) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("spinor");
      for (double x : spinor) {
        w.lit(x);
      }
      w.arr_close();
      w.obj_open("audit");
      write_audit(w, aud);
      w.obj_close();
      w.arr_open("matrix");
      for (double x : mat) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("src");
      for (double x : src) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("dst");
      for (double x : dst) {
        w.lit(x);
      }
      w.arr_close();
      w.obj_close();
    }
    w.arr_close();
    {
      double h[7] = {0, 0, 0, 0, 0, 0, 0};
      double spinor[8];
      double mat[64];
      std::vector<double> src(rows * width);
      std::vector<double> dst(rows * width);
      for (double &x : src) {
        x = 2.0 * u01(rng) - 1.0;
      }
      must(spin8_query_spinor_from_tangent(h, spinor), "q1_identity_spinor");
      must(spin8_query_matrix(spinor, mat), "q1_identity_matrix");
      must(spin8_query_transform(spinor, SPIN8_F64, src.data(),
                                 rows * width * sizeof(double), width,
                                 dst.data(), rows * width * sizeof(double),
                                 width, rows, width),
           "q1_identity_transform");
      bool exact_identity_matrix = true;
      for (int i = 0; i < 8; ++i) {
        for (int j = 0; j < 8; ++j) {
          double expect = (i == j) ? 1.0 : 0.0;
          if (mat[i * 8 + j] != expect) {
            exact_identity_matrix = false;
          }
        }
      }
      bool byte_equal = std::memcmp(src.data(), dst.data(),
                                    rows * width * sizeof(double)) == 0;
      w.obj_open("identity");
      w.arr_open("spinor");
      for (double x : spinor) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("matrix");
      for (double x : mat) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("src");
      for (double x : src) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("dst");
      for (double x : dst) {
        w.lit(x);
      }
      w.arr_close();
      w.lit("byte_identical", byte_equal);
      w.lit("matrix_is_identity", exact_identity_matrix);
      w.obj_close();
    }
    {
      double h[7];
      double spinor[8];
      double mat[64];
      std::vector<double> src(rows * width);
      std::vector<double> dst(rows * width);
      for (int i = 0; i < 7; ++i) {
        h[i] = 0.37 * static_cast<double>(i + 1);
      }
      for (double &x : src) {
        x = 2.0 * u01(rng) - 1.0;
      }
      std::vector<float> fsrc(rows * width);
      std::vector<float> fdst(rows * width);
      for (size_t i = 0; i < rows * width; ++i) {
        fsrc[i] = static_cast<float>(src[i]);
      }
      must(spin8_query_spinor_from_tangent(h, spinor), "q1_f32_spinor");
      must(spin8_query_matrix(spinor, mat), "q1_f32_matrix");
      must(spin8_query_transform(spinor, SPIN8_F32, fsrc.data(),
                                 rows * width * sizeof(float), width,
                                 fdst.data(), rows * width * sizeof(float),
                                 width, rows, width),
           "q1_f32_transform");
      w.obj_open("f32_case");
      w.arr_open("h");
      for (double x : h) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("spinor");
      for (double x : spinor) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("matrix");
      for (double x : mat) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("src");
      for (double x : src) {
        w.lit(x);
      }
      w.arr_close();
      w.arr_open("dst");
      for (float x : fdst) {
        w.lit(static_cast<double>(x));
      }
      w.arr_close();
      w.obj_close();
    }
  }
  w.obj_close();

  w.obj_open("query3");
  {
    double g3[448];
    must(spin8_query_v3_generators(g3), "query3_generators");
    spin8_query_v3_basis_report basis;
    must(spin8_query_v3_basis_audit(&basis), "query3_basis_audit");
    w.arr_open("generators");
    for (double x : g3) {
      w.lit(x);
    }
    w.arr_close();
    w.obj_open("basis_audit");
    w.lit("normed_max_error", basis.normed_max_error);
    w.lit("polarization_max_error", basis.polarization_max_error);
    w.lit("skew_max_error", basis.skew_max_error);
    w.lit("clifford_max_error", basis.clifford_max_error);
    w.obj_close();

    const size_t rows = 4;
    const size_t width = 20;
    const size_t elems = rows * width;
    std::vector<double> q(elems);
    for (double &x : q) {
      x = 2.0 * u01(rng) - 1.0;
    }
    std::vector<double> qdst(elems);
    std::vector<double> qspin(rows * 8);

    spin8_query_v3_controller *zc = nullptr;
    {
      std::vector<double> zwin(8 * width, 0.0);
      std::vector<double> zbin(8, 0.0);
      std::vector<double> zwout(7 * 8, 0.0);
      std::vector<double> zbout(7, 0.0);
      must(spin8_query_v3_controller_create(
               SPIN8_QUERY_V3_VERSION, width, zwin.data(),
               zwin.size() * sizeof(double), zbin.data(),
               zbin.size() * sizeof(double), zwout.data(),
               zwout.size() * sizeof(double), zbout.data(),
               zbout.size() * sizeof(double), &zc),
           "query3_zero_create");
    }
    must(spin8_query_v3_controller_apply(
             zc, SPIN8_F64, q.data(), elems * sizeof(double), width,
             qdst.data(), elems * sizeof(double), width, rows),
         "query3_zero_apply");
    must(spin8_query_v3_controller_spinors(
             zc, SPIN8_F64, q.data(), elems * sizeof(double), width,
             qspin.data(), qspin.size() * sizeof(double), 8, rows),
         "query3_zero_spinors");
    bool zero_byte_equal =
        std::memcmp(q.data(), qdst.data(), elems * sizeof(double)) == 0;
    bool zero_spinors_exact_e0 = true;
    for (size_t r = 0; r < rows; ++r) {
      if (qspin[r * 8] != 1.0) {
        zero_spinors_exact_e0 = false;
      }
      for (int j = 1; j < 8; ++j) {
        if (qspin[r * 8 + j] != 0.0) {
          zero_spinors_exact_e0 = false;
        }
      }
    }
    w.obj_open("zero");
    w.arr_open("src");
    for (double x : q) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("spinors");
    for (double x : qspin) {
      w.lit(x);
    }
    w.arr_close();
    w.lit("byte_identical", zero_byte_equal);
    w.lit("spinors_exact_e0", zero_spinors_exact_e0);
    w.obj_close();

    double dy[20];
    {
      std::vector<double> dyv(20);
      for (double &x : dyv) {
        x = 2.0 * u01(rng) - 1.0;
      }
      std::memcpy(dy, dyv.data(), sizeof(dy));
    }

    spin8_query_v3_gradients_f64 zg;
    std::vector<double> zdq(20), zdwin(160), zdbin(8), zdwout(56), zdbout(7);
    zg.dq = zdq.data();
    zg.dq_bytes = zdq.size() * sizeof(double);
    zg.dwin = zdwin.data();
    zg.dwin_bytes = zdwin.size() * sizeof(double);
    zg.dbin = zdbin.data();
    zg.dbin_bytes = zdbin.size() * sizeof(double);
    zg.dwout = zdwout.data();
    zg.dwout_bytes = zdwout.size() * sizeof(double);
    zg.dbout = zdbout.data();
    zg.dbout_bytes = zdbout.size() * sizeof(double);
    must(spin8_query_v3_controller_vjp_f64(zc, q.data(), width * sizeof(double),
                                           dy, sizeof(dy), &zg),
         "query3_zero_vjp");

    w.obj_open("vjp_zero");
    w.arr_open("q");
    for (size_t i = 0; i < width; ++i) {
      w.lit(q[i]);
    }
    w.arr_close();
    w.arr_open("dy");
    for (double x : dy) {
      w.lit(x);
    }
    w.arr_close();
    w.obj_open("grads");
    w.arr_open("dq");
    for (double x : zdq) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dwin");
    for (double x : zdwin) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dbin");
    for (double x : zdbin) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dwout");
    for (double x : zdwout) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dbout");
    for (double x : zdbout) {
      w.lit(x);
    }
    w.arr_close();
    w.obj_close();
    w.obj_close();

    std::vector<double> win(8 * width);
    std::vector<double> bin(8);
    std::vector<double> wout(7 * 8);
    std::vector<double> bout(7);
    for (double &x : win) {
      x = 0.5 * u01(rng) - 0.25;
    }
    for (double &x : bin) {
      x = 0.5 * u01(rng) - 0.25;
    }
    for (double &x : wout) {
      x = 0.5 * u01(rng) - 0.25;
    }
    for (double &x : bout) {
      x = 0.5 * u01(rng) - 0.25;
    }
    spin8_query_v3_controller *nc = nullptr;
    must(spin8_query_v3_controller_create(
             SPIN8_QUERY_V3_VERSION, width, win.data(),
             win.size() * sizeof(double), bin.data(),
             bin.size() * sizeof(double), wout.data(),
             wout.size() * sizeof(double), bout.data(),
             bout.size() * sizeof(double), &nc),
         "query3_nonzero_create");
    std::vector<double> ndst(elems);
    std::vector<double> nspin(rows * 8);
    must(spin8_query_v3_controller_apply(
             nc, SPIN8_F64, q.data(), elems * sizeof(double), width,
             ndst.data(), elems * sizeof(double), width, rows),
         "query3_nonzero_apply");
    must(spin8_query_v3_controller_spinors(
             nc, SPIN8_F64, q.data(), elems * sizeof(double), width,
             nspin.data(), nspin.size() * sizeof(double), 8, rows),
         "query3_nonzero_spinors");
    double case0mat[64];
    must(spin8_query_v3_matrix(nspin.data(), case0mat), "query3_case0_matrix");
    spin8_query_v3_gradients_f64 ng;
    std::vector<double> ndq(20), ndwin(160), ndbin(8), ndwout(56), ndbout(7);
    ng.dq = ndq.data();
    ng.dq_bytes = ndq.size() * sizeof(double);
    ng.dwin = ndwin.data();
    ng.dwin_bytes = ndwin.size() * sizeof(double);
    ng.dbin = ndbin.data();
    ng.dbin_bytes = ndbin.size() * sizeof(double);
    ng.dwout = ndwout.data();
    ng.dwout_bytes = ndwout.size() * sizeof(double);
    ng.dbout = ndbout.data();
    ng.dbout_bytes = ndbout.size() * sizeof(double);
    must(spin8_query_v3_controller_vjp_f64(nc, q.data(), width * sizeof(double),
                                           dy, sizeof(dy), &ng),
         "query3_nonzero_vjp");

    w.obj_open("nonzero");
    w.arr_open("params_win");
    for (double x : win) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("params_bin");
    for (double x : bin) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("params_wout");
    for (double x : wout) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("params_bout");
    for (double x : bout) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("src");
    for (double x : q) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dst");
    for (double x : ndst) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("spinors");
    for (double x : nspin) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("case0_matrix");
    for (double x : case0mat) {
      w.lit(x);
    }
    w.arr_close();
    w.obj_close();
    w.obj_open("vjp");
    w.arr_open("dy");
    for (double x : dy) {
      w.lit(x);
    }
    w.arr_close();
    w.obj_open("grads");
    w.arr_open("dq");
    for (double x : ndq) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dwin");
    for (double x : ndwin) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dbin");
    for (double x : ndbin) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dwout");
    for (double x : ndwout) {
      w.lit(x);
    }
    w.arr_close();
    w.arr_open("dbout");
    for (double x : ndbout) {
      w.lit(x);
    }
    w.arr_close();
    w.obj_close();
    w.obj_close();

    spin8_query_v3_controller_free(nc);
    spin8_query_v3_controller_free(zc);
  }
  w.obj_close();

  std::fputc('}', f);
  std::fputc('\n', f);
  std::fclose(f);
  std::fprintf(stdout, "PASS probe wrote %s (trials=%ld, python_check=%ld)\n",
               out_path, trials_total, python_check);
  return 0;
}
