# NKAT–URT Predictive Weight Streaming (PWS)

Status: **Opt-in audit, replay, and certification layer (`tools/pws/`, `tools/pws_bench.py`)** · **`releaseQualified=false`**

Predictive Weight Streaming (PWS) extends Strata's existing four-tier GPU / RAM / CPU / SSD MoE architecture with rigorous bandwidth modelling, multi-tier Roofline analysis, non-commutative expert prediction, deadline-aware prefetch simulation, NKAT common-basis factorisation, and TSI joint efficiency certification.

---

## 1. Existing Strata 4-Tier Pipeline Audit (Baseline `21473cc9b`)

Direct source inspection confirms that Strata already provides strong native building blocks which PWS audits and extends rather than duplicates:

| Existing File | Verified Capability | Identified Research Gap for PWS |
|---|---|---|
| `engine/include/strata/platform/direct_file.hpp` (`DirectFile`) | Windows `FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED` IOCP thread pool (`STRATA_IO_THREADS`, dynamic $\ge 4096\text{ B}$ sector alignment), bypassing OS page cache. | Physical vs page-cache byte telemetry per token is not yet exposed to TSI/PWS JSON reports. |
| `engine/include/strata/core/ssd_stream_scheduler.hpp` (`TwoPriorityExpertScheduler`) | Demand preemption over 512 KiB chunked speculative prefetch, late slot binding, `drop_stale()`, `promote_to_demand()`, 3-projection readiness `proj_ready[3]`, `VramCopybackQueue`, `IdlePreloader`. | Prefetch currently relies on static/layer heuristics without order-sensitive NKAT sequence predictors or adaptive deadline throttling. |
| `engine/include/strata/core/expert_cache.hpp` (`ExpertCache`) | VRAM-resident expert arena with `--vram-elastic` CUDA VMM resize and `STRP` frequency profiles (`tools/make_profile.py`). | `ExpertCache::admit` does not evict online; policy selection is offline/windowed. |
| `engine/include/strata/core/ink_expert_policy.hpp` (`InkExpertPolicy`) | Decayed-frequency hot-expert swap planner with 25% pinned slots and low-VRAM swap caps. | Uses scalar frequency rather than latency-per-byte priority $p[e] t[e] / w[e]$. |
| `tools/bench_eviction.py` & `tools/replay_cache_policy.py` | Replays native `--dump-routing` traces (`layer, k, ids, weights`) across `fill-only`, `lru`, `lfu-decay`, and Belady's `oracle`. | Evaluates expert-count hit rate only; lacks byte-weighted hit rate, Markov/NKAT/TSI predictors, EDF deadline scheduling, and physical read-amplification telemetry. |

---

## 2. Physical Bandwidth Limits and Multi-Tier Roofline

- **Dense full-weight streaming upper bound** (`tools/pws/bandwidth_model.py`): for $N$ parameters at $b$ effective bits per weight ($W = N b / 8$), streaming all weights every token obeys $\text{decode\_rate} \le B_{\mathrm{SSD}} / W$. For a $27\text{B}$ model at $3.69\text{ bpw}$ ($W = 12.45375\text{ GB}$), idealised ceilings are $0.281$, $0.562$, and $1.124\text{ tok/s}$ at $3.5$, $7.0$, and $14.0\text{ GB/s}$ respectively. Avoiding full-weight transfer is physically mandatory.
- **MoE active-weight bound**: for active weight volume $W_a$ and byte-weighted VRAM+RAM hit rate $h$, ideal demand is $W_{\mathrm{SSD}} = (1 - h) W_a$, requiring $h \ge \max(0, 1 - B_{\mathrm{SSD}} / (v W_a))$ to sustain target decode speed $v$. For a theoretical $3\text{B}$-active $2\text{ bpw}$ model ($W_a = 750\text{ MB}$) at $3.5\text{ GB/s}$ and $30\text{ tok/s}$, allowable demand is $116.67\text{ MB/token}$ ($h \ge 84.44\%$); at $90\%$ hit rate, demand is $75\text{ MB/token}$ (SSD-only ceiling $46.67\text{ tok/s}$). Actual physical reads additionally include unused prefetch, alignment padding, read amplification, and repeated reads.
- **Multi-tier Roofline vs DAG critical path** (`tools/pws/roofline.py`): idealised parallel throughput is bounded by $\min(P_{\mathrm{GPU}}/F, B_{\mathrm{VRAM}}/W_{\mathrm{VRAM}}, B_{\mathrm{RAM}}/W_{\mathrm{RAM}}, B_{\mathrm{PCIe}}/W_{\mathrm{PCIe}}, B_{\mathrm{SSD}}/W_{\mathrm{SSD}})$, whereas realised throughput is governed by the serial residual/GDN/attention/CPU-expert DAG critical path.

---

## 3. Predictive Caching, EDF Prefetch, Factorisation, and Negative Controls

- **Seven-policy cache comparison (`tools/pws/cache_policy.py`)**: compares `lru`, `lfu`, `layer_aware`, `markov`, `nkat_seq` (order-sensitive non-commutative sequence predictor), `tsi_task` (task-category aware), and `offline_oracle` (Belady's MIN — strictly an offline upper bound, never deployable online) using greedy knapsack priority $p[e] t[e] / w[e]$.
- **Deadline-aware EDF scheduler (`tools/pws/deadline_scheduler.py`)**: tracks $t_{\mathrm{io}}[e]$ and exposed stall $\max(0, t_{\mathrm{io}}[e] - t_{\mathrm{lead}}[e])$, demand preemption, double/triple buffering, dynamic bandwidth EMA, and safe lookahead throttling when precision collapses.
- **NKAT common-basis factorisation and $\mathrm{Spin}(8)$ comparison (`tools/pws/factorisation.py`)**: audits $W[e] = W_{\mathrm{shared}} + U[e]V[e]^\top + E[e]$ via exact SVD, URT operator-norm error $\|W[e] - W_{\mathrm{approx}}[e]\|_2 \le \varepsilon[e]$, Section 10 transfer-bit AND critical-path timing condition ($\text{saved exposed I/O} > \text{reconstruction + sync}$), and compares no-rotation, Sylvester $\mathrm{SO}(8)/\mathrm{Spin}(8)$, and generic Givens $\mathrm{SO}(8)$ rotations empirically without assuming automatic triality advantage.
- **Negative controls (Section 18)**: uniform random routing (`generate_random_negative_control_trace`), insufficient SSD bandwidth, high reconstruction overhead, and dense full-weight streaming are explicitly tested to show where PWS speedup disappears.
- **Windows direct transfer note (Section 13)**: GPUDirect Storage / DirectStorage CUDA weight paths are not assumed available on consumer Windows WDDM; overlapped unbuffered reads (`DirectFile`) into pinned host RAM followed by asynchronous H2D `cudaMemcpyAsync` remain the primary supported path.
