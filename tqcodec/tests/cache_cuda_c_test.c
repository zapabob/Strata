#include "tqcodec/cache_cuda.h"
int main(void) {
  tqc_cache_cuda_config c = {0};
  tqc_cache_cuda_plan *p = 0;
  c.version = 1;
  c.size = sizeof(c);
  c.precision = TQC_D_F32;
  c.columns = 128;
  c.kv_heads = 1;
  c.q_heads = 2;
  c.capacity = 4;
  c.max_queries = 2;
  c.max_append_rows = 2;
  c.alpha[0] = c.alpha[1] = c.alpha[2] = 1.0 / 3.0;
  c.view_mask = 7;
  c.k_dialect = 3;
  c.v_dialect = 1;
  c.model[0] = 1;
  c.adapter[0] = 1;
  c.position[0] = 1;
  if (tqc_cache_cuda_create(&c, &p) != TQC_D_OK || !p)
    return 1;
  tqc_cache_cuda_free(p);
  return 0;
}
