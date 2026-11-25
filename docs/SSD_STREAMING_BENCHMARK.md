# SSD Streaming Benchmark Protocol

Status: **Measurement protocol (`research/tsi-verified-evaluation`)** · **`releaseQualified=false`**

This document specifies reproducible storage and streaming benchmarks for `tools/pws_bench.py` and Strata's four-tier MoE engine.

---

## 1. Separating OS Page Cache from Physical SSD Reads

Standard buffered file reads (`mmap` / cached `ReadFile`) can be served from Windows standby RAM at $>10\text{ GB/s}$, masking true SSD limits. Every storage report must distinguish:

1. **Physical unbuffered SSD reads**: measured via `tools/pws_bench.py ssd-probe <existing_readonly_file>` using Windows `CreateFileW(..., FILE_FLAG_NO_BUFFERING)` with page-aligned `VirtualAlloc` buffers (zero writes or modifications to model files).
2. **OS page-cache / warm-cache reads**: reported separately; never conflated with physical SSD bandwidth.
3. **Cold-cache discipline**: destructive OS cache flushes are avoided. When a true cold-cache state cannot be guaranteed without destructive operations, the condition is recorded explicitly as `cold_cache_unverified`.

Furthermore, a motherboard or GPU supporting PCIe 5.0 never implies that an installed NVMe or SATA drive operates at PCIe 5.0 speed; every drive's actual model (`FriendlyName`), bus type (`NVMe` vs `SATA`), sector sizes, and measured unbuffered sequential and random 64 KiB read bandwidths must be recorded directly.

---

## 2. Benchmark Arms and Negative Controls

Same model, same prompt, same quantisation, and identical resource floors must be held fixed across arms:

- Existing Strata baseline (warm and cold where verifiable)
- Demand-only SSD streaming vs async I/O + double buffering
- Predictive cache policies (`lru`, `lfu`, `layer_aware`, `markov`, `nkat_seq`, `tsi_task`, and `offline_oracle` upper bound)
- Deadline-aware EDF prefetch vs demand-only
- Lossless layout/caching changes (requiring **bit-exact parity** on fixed-token decode) vs lossy approximations (`Spin(8)` quantisation, NKAT common-basis factorisation — requiring full-vocab/top-$k$ KL, top-1 agreement, and TSI verified success evaluation)
- Mandatory negative controls: uniform random routing, tight SSD bandwidth, excessive lookahead, and high reconstruction overhead.

Unmeasured telemetry fields (`ssd_queue_depth`, `pcie_transfer_ms_per_token`, etc.) must be written as `null`, never `0`.
