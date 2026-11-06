# Q36 bounded expert working storage — OpenCode

## Scope and requirements

Worktree `H:/Strata/worktrees/native-32gb16gb-20261106`, branch `fix/native-32gb16gb-20261106`, base `ca3ab40a9397c28a388ca042bf964f4aae541de7`. Requested log filename retained; this continuation runs on 2026-11-07. Goal: a small opt-in, testable reduction of Q36 expert backing pressure on this 32 GB RAM / 16 GB VRAM PC, followed by parent review before a source-bound engine build and real-model qualification.

R1: retain model bytes, KV types, context, router/top-k, token grouping, arithmetic and existing integrity checks. R2: bound CPU expert working buffers as well as H2D staging; do not mistake mapped address space or the pin budget for total physical RAM. R3: refuse unsupported geometry/configuration or insufficient observed headroom before the new allocations. R4: consume each staged CPU batch synchronously before reuse, retain CUDA completion-event ownership for H2D. R5: unchanged default path; an explicit candidate mode and separate versioned memory marker. R6: no installed-app/profile/model changes, heavy engine build, release, push or unrelated process control.

## Standards and plan

Applied the compatible canonical `CLAUDE-FABLE-5.md` instructions, worktree AGENTS, common/start-gate/skill-selection/security/DeepResearch/LLMOps/C++/Python SOPs, and the already-loaded MILSPECLLMOps and DeepResearch baselines. Selected systematic-debugging and test-driven-development. No subdelegation or available Goal API. No formal compliance claim.

Sequence: trace actual allocations and ownership; add failing CPU/lifetime/admission tests; implement the production helper and opt-in engine wiring; run bounded serial unit verification and review the diff; hand off exact integration and qualification requirements. Full CUDA/HIP/SYCL builds and real inference are deferred for parent review.

## Findings before implementation

`place_experts()` allocates all experts with `cudaHostAlloc` then `malloc` in legacy mode. Historical `_docs/q36-32gb16gb/DESIGN.md` records 18.75 GiB for that arena, in addition to the original mapped GGUF and GPU copies. This is not a new measurement.

Mapped-pack avoids that arena, but `moe_hybrid_cpu()` passes `L.hblobs + expert * stride` directly to CPU jobs. `h2d_from_host()` also defaults to memcpy from the mapped payload. The existing `STRATA_Q36_FILE_STAGING=1` changes GPU transfer only; its inference reader uses buffered ReadFile. Thus a 64 MiB pin pool bounds neither CPU payload residency nor the OS file-data cache. The GGUF mapping is already dropped after placement; repeating that repair would not solve CPU payload reads. Existing pin-pipeline events wait on each slot's last copy, including copies on another stream; these waits must be retained.

VRAM is a separate ledger: dense weights, prompt activations/MMQ scratch, 256 MiB float attention scores plus 128 MiB half probabilities, F32-to-F16 prompt KV scratch when applicable, persistent typed KV across attention states/sessions, recurrent state, expert slots, and two max-layer GPU staging buffers. Historical staging is 1.10 GiB. Hybrid CPU output/activation buffers are sized to tmax, although smaller hybrid batches are common. This unit targets expert backing residency, not a fabricated total-RAM/VRAM fit estimate or a math-changing scratch optimisation.

The sibling `cuda135-kv-20261106/.superpowers/sdd/2026-11-06-strata-cuda135-rtx5060ti-implementation-plan/task-P0-A-memory-abort-audit.md` identifies a guarded compile stop near the IQ2_S frontend: available RAM 3,193,729,024 bytes below 3 GiB, commit still above 4 GiB. It is not native runtime OOM evidence, nor a reason to prune formats or weaken build guards. Its progress log retains this distinction.

Initial fresh snapshot: physical available 11.60 GiB of 31.87 GiB, system commit headroom 40.49 GiB; RTX 5060 Ti free VRAM 14,752 MiB of 16,311 MiB, driver process use 1,299 MiB. Hermes and strata-desktop were present, no matching native/llama/compiler process. Disk C 8.17 GiB, H 317.40 GiB. Availability differs from the earlier user sample and must be sampled again before execution.

## Design boundary

Implemented `--q36-memory bounded-experts-v1`, requiring `--q36-expert-store mapped-pack` and an explicit positive decimal `--expert-slots N` smaller than the model's expert count. It uses an existing verified pack, fixed-capacity CPU waves and the existing two-slot H2D pipeline. Windows unbuffered reads use one aligned 1 MiB bounce buffer, locked until the copy to caller-owned staging completes. Unaligned expert ranges are read via aligned enclosing sectors, including short EOF; no fallback to mapped payload or buffered inference reads. Unsupported I/O fails explicitly. CPU wave jobs retain their original token grouping and output pointers; only the weight pointer changes. No model repack is allowed in the candidate mode.

This bounds application-owned expert working storage and avoids touching mapped expert payload. It does not cap total process/driver/OS memory, qualify a context, or promise throughput. Existing verification, dense load and non-expert scratch still need observed peak-memory evidence. Reads may be slower than a warm file cache.

Primary API references checked 2026-11-07: [Windows file buffering](https://learn.microsoft.com/en-us/windows/win32/fileio/file-buffering), [ReadFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile), [ReOpenFile](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-reopenfile). These establish unbuffered alignment, synchronous completion, short EOF reads and reopening the same file object. No package/dependency changes.

## Changed files and wiring review

`include/strata/qwen35/bounded_experts.hpp` provides the production CPU wave owner, strict candidate slot parser and overflow-safe physical/commit/VRAM admission predicates. CPU storage is `8 * align64(max_stride + 4096)` with a 64 MiB ceiling. Staging never mutates original job descriptors; failed reads never publish a partial wave. A synchronous consumer must finish its workers before return, matching `ExpertPool::run_split_multi_native()` / `run_phase()` and their parked-worker barrier.

`include/strata/qwen35/expert_store.hpp` and `src/qwen35/expert_store.cpp` add existing-pack-only bounded reads, the Windows physical/commit observation, a serialized 1 MiB aligned unbuffered reader reopened from the same file object, and model/pack read locks held from verification through pack destruction. Full model SHA-256, payload SHA-256, per-layer CRC, geometry and DPAPI/NTFS receipt code remain in use. A missing/corrupt/unreadable pack refuses before any build/repair. The pack view is destroyed before its lifetime lock; all synchronous reads finish before the bounce buffer is reused.

`src/qwen35/q36_engine.cu` wires the opt-in through CPU misses, initial slot uploads, streamed prefill and rebalancing H2D calls. `hblobs` remains an opaque address for range/offset lookup in this mode; CPU workers see staged weight bytes. All H2D pool-reuse waits and CUDA done events are retained. The optional pin pipeline and stream-resident switch are unchanged. Explicit slots keep the requested placement capacity; adaptive rebalancing remains unchanged. Model geometry rejects all-resident/invalid candidate slots before dense allocation. Candidate slot counts bypass legacy atoi and use the checked parser first.

Host admission includes the planned CPU stage, maximum H2D stage, I/O buffer and known hybrid host buffers, leaving 3 GiB physical and 4 GiB commit headroom. It is repeated before later host allocations and reads. Hybrid VRAM admission counts expert slots, GPU staging, CPU output/miss buffers and slot tables, with 768 MiB left; it samples again after verification so a minutes-old free-VRAM observation is not reused. Dense/init allocations, CPU worker scratch and driver memory are outside this ledger and remain a qualification limitation.

`include/strata/qwen35/engine.hpp` and the one-line `src/program/generate.cpp` change expose the separate memory capability from both help entrypoints. The strict K1 `Q36_KV_CAPABILITIES` schema is untouched. `docs/Q36_BOUNDED_EXPERTS.md` contains the exact host contract and scope. `CMakeLists.txt` only registers two CPU test targets; no format, build guard or compiler setting was removed. Tests are `q36_bounded_experts_test.cpp`, `q36_bounded_cpu_parity_test.cpp`, and expanded `q36_expert_store_test.cpp`; the existing transfer-lifetime test was also run.

Static review followed every `hblobs` consumer: initial H2D, streamed prefill, rebalance and CPU jobs. New behavior is behind `bounded_experts=false` by default; legacy arena, ordinary mapped pack, kernel arithmetic, routing, KV allocation/layout, precision, context, prompt chunk and warmup code are retained. Default numerical execution identity has not been measured in a newly built GPU engine. Help gains an additional capability line intentionally. Existing resource cleanup is process-oriented; this is not an in-process unload/reload RAII refactor.

## Header-only observation and allocation contract

`_docs/native-32gb16gb/pack-header-observed.json` records a read of only 5,376 header bytes from the user's existing expert pack. Model size: 22,853,663,008 bytes; pack size: 20,127,612,928; 41 layer records; expert payload: 20,127,604,736; max stride: 2,310,000. Observed type pairs are 12/13, 12/14, 13/14 (Q4_K/Q5_K, Q4_K/Q6_K, Q5_K/Q6_K), embedding 2048 and expert FF 512.

The resulting CPU stage is 18,512,896 bytes. Including H2D <=67,108,864 and I/O 1,048,576, the calculated expert-working budget is <=86,670,336 bytes (82.6553 MiB). General mode maximum is <=129 MiB for these three buffers. These are allocation calculations, not runtime peak RAM or model capacity measurements. The real pack payload was not scanned, hashed, changed, rebuilt or copied in this task.

## Execution and verification

RED preceded implementation: bounded helper tests failed to compile because `bounded_experts.hpp` did not exist; store tests failed C2039 on missing `enable_bounded_reads`, scratch reporting and the request flag. Subsequent mode/strict-slot/admission test additions also failed on the missing production APIs before implementation. These are **compile-RED** results for a new API, not a claimed real-model failure reproduction. The first shell attempt failed on cmd quoting before compilation and is not RED evidence. A scoped `.cmd` file then supplied the exact commands.

Final CPU results are PASS, with native exit 0 observed before cleanup and `job_active_after=0`:

| Test | Final receipt under `_docs/native-32gb16gb/` | Result |
| --- | --- | --- |
| CPU waves, lifetimes, failures, strict flags, admission | `bounded-compile-final5.json`, `bounded-run-final5.json` | 0 failures; original real job descriptor fields retained, worker joined before reuse, >8 jobs, duplicate expert groups, partial-read/consumer exceptions and budget/overflow boundaries |
| Expert pack / staged reader / existing integrity | `store-compile-final6.json`, `store-run-final6.json` | all checks passed; PAGE_NOACCESS payload, unaligned/chunk/EOF reads, concurrent readers, path replacement, moved ownership, bounded CPU helper + real file reader, lifetime writer exclusion, no rebuild on missing/corrupt pack; old hash/CRC/DPAPI tests retained |
| Existing pin-pool state lifetime | `lifetime-compile-green3.json`, `lifetime-run-green3.json` | passed; CPU state checks, **not CUDA event execution** |
| Actual CPU-pool numerical parity | `parity-compile-resume3.json`, `parity-run-resume3.json`, raw `.log` | byte-identical outputs for all three observed type pairs, N=2048/FF=512, 19 jobs, nt=1/4/8, two repetitions per pair |

The numerical test uses the newly compiled test and current production staging header with read-only prebuilt `strata_kernels_cpu.lib`, `ggml-cpu.lib`, `ggml-base.lib` from `H:/Strata/builds/cuda135-comparison-20261106/cuda-13.3`. Their recorded source is `594dfaa7c9b9f0fde840390dbe983820b84b9e3d`. `git diff 594dfaa7... HEAD -- src/kernels/cpu include/strata/kernels/cpu include/strata/platform/thread_name.hpp` was empty; the intervening CMake changes only added KV tests. No archive was rebuilt or modified. This is CPU wave parity, not a new engine build or a 13.3/13.5 comparison.

`source-unit-identities.json` records current source and test-binary hashes plus reused library hashes. The SHA-256 values are `8344f8e4a5b123c4017cecf232598c3be7881beb1f09df60a135d5d105d911dd` for strata_kernels_cpu, `b3f2e4d9a3ba692c3788d12a0203cbe054f649d89d9de118267e740480b3a132` for ggml-cpu, and `c4cb0ff36c89178b3583aeee10e5c52a9db76b25aac1f105d926b4c3b666b2c1` for ggml-base. The complete machine-readable identity record is authoritative for byte identities.

### Commands and containment

All commands ran in the owned worktree. The task-local `.cmd` calls Visual Studio 2022 `VsDevCmd.bat -arch=x64 -host_arch=x64`, then serial `cl /nologo /std:c++20 /EHsc /W4 /Iinclude`. Store/lifetime link `src/qwen35/expert_store.cpp`, `bcrypt.lib` and `crypt32.lib`. Numerical parity additionally uses `/MT /O2 /DSTRATA_NATIVE_EXPERTS=1 /DSTRATA_Q6K_EXPERTS=1`, the existing `H:/Strata/deps/ggml-3cf03257/ggml/include`, the three archived CPU libraries above and `advapi32.lib`. Outputs and TEMP/TMP are under `_docs/native-32gb16gb`.

Execution used `uv run --no-project --offline --python C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe _docs/native-32gb16gb/run-unit.py <test> <phase> <tag>`, with process-local `UV_CACHE_DIR` inside the owned evidence directory and `PYTHONDONTWRITEBYTECODE=1`. Exact final tuples are `bounded compile final5`, `bounded run final5`, `store compile final6`, `store run final6`, `lifetime compile green3`, `lifetime run green3`, `parity compile resume3`, `parity run resume3`. `inspect-pack.py` made the bounded header observation; `capture-evidence.py` captured streaming identities. These task-local runners/receipts remain in the ignored evidence directory; the test source and CMake targets are versioned.

The runner reuses `tools/perf131k/windows_job.py`: atomic owned Job membership before resume, kill-on-close, active-child limit 16, 2 GiB diagnostic Job cap, 90 s deadline, 2 MiB output cap, continuous RAM >=3 GiB / commit >=4 GiB / H >=10 GiB and C >=5 GiB. None of those floors was lowered. Final parity compile minimum sampled physical RAM was 3,587,584,000 bytes and run minimum 3,652,108,288; minimum commit was 6,128,377,856 / 6,149,197,824 respectively. Parity run Job peak commit was 42,237,952 bytes; this is a synthetic CPU test, not an engine measurement. All final owned Jobs drained to zero.

### Failures, blocks and warnings retained

`parity-compile-check1.json/.log` records exit 2, C2039/C3861: the test omitted `expert_layout.hpp`, where the existing `strata::kernels::cpu::cpu_avx1_ok()` is declared. Adding the declaration header fixed the test; no CPU feature API or ISA gate was replaced. The following attempt was refused at preflight; a separate fresh snapshot showed available RAM 1,855,123,456 bytes, commit 12,971,032,576, C free 6,843,056,128, H free 341,467,586,560. No child started for that refusal and no automatic retry followed. The later explicit user resume led to the successful `resume3` pair after a fresh admissible sample.

Existing MSVC C4324 alignment warnings from CPU pool headers and C4996 getenv warnings from the existing tracing/verification code remain recorded. uv reported pre-existing dangling `~astapi_users` / `~ip` metadata; no package repair/install was attempted. Earlier `--no-sync` with `--no-project` emitted an ineffectiveness warning and was omitted from later commands. `git diff --check` passed; Git's configured CRLF conversion warnings are retained.

## Parent integration and remaining gates

The exact opt-in/capability/effective-marker contract is in `docs/Q36_BOUNDED_EXPERTS.md`. Bind `Q36_MEMORY_CAPABILITIES` schema 1 to the freshly built executable digest and require the listed mode; leave K1's strict KV schema unchanged. `Q36_MEMORY_EFFECTIVE` reports actual CPU/H2D/I/O stage byte counts and `total_process_bound=0`, with startup generation. Unsupported platform/backend/CPU-pool builds advertise an empty mode list and refuse the flag. The installed native 0.5.1 `e75716a9...` has not been changed and is not evidence for this capability.

Full native compilation (including final `.cu` and `generate.cpp` linkage), CMake/CTest execution, CUDA/HIP/SYCL, actual help-probe parsing, CUDA done-event execution, real-model startup/generation/stop/restart, full-input consumption, quality, speed and total process peak memory remain **NOT_RUN**. Standalone MSVC CPU tests are not a full source-bound engine build. The next parent gate is review, freeze and fresh candidate build without pruning formats/guards, then the same CPU tests against freshly built libraries and CUDA/kernel/cache tests. Only then run the owned exact-flags model qualification; capacity and actual consumed input remain distinct.

During this task unrelated llama servers appeared and system memory changed substantially. No unrelated process was stopped. The user's later pause/restore authorization belongs to the parent maintenance operation, not this source unit. Parent must sample again and apply unchanged floors before any build or model test. Release/install/push and profile/model changes were not performed.

## Self-review

Self-review-event: `ticket_completed` (source unit), `qa_defect` (missing test declaration and blocked execution). Reviewed ownership, all expert byte-read paths, mode gating, stale VRAM observations, unsafe pre-validation atoi, integrity retention and evidence/claim boundaries. The narrow corrections are explicit header inclusion, checked candidate parsing before atoi, a refreshed post-verification VRAM sample, and accurate recorded NOT_RUN gates. No AGENTS/Skill/SOP change is justified by this evidence; baseline weakening, format pruning, changing precision/context and claiming total-RAM fit were rejected. Residual risks are the unbuilt GPU wiring and real-model lifecycle/peak-memory behavior listed above.
