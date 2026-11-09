# CUDA resource investigation — compiler reproduction and bounded candidates

## Latest result: resumed compiler-only investigation

The parent explicitly obtained permission to Stop/unload its active model and reported successful unload. This owner resumed after fresh telemetry admitted work (25087316 KiB free physical memory, 14778 MiB GPU free). No model or installed-app action was taken by this owner. **GPU parity and GPU timing remain NOT RUN, explicitly held for parent sequencing.** The earlier resource blocker and all failed attempts below are retained as history.

All three full frozen TUs compiled serially. Their **602 entry resource records match the preserved original objects exactly**, after normalizing only the compiler-generated anonymous-namespace hash: DFlash 83, QSA 29, IQ 490. All resource columns were compared, not just the four failures. Selected original-versus-recompiled SASS instruction strings also match exactly: DFlash 2416 instructions across its two failures, QSA 7552, IQ 7504. This is instruction-text comparison after anonymous-name normalization, not a claim of whole-object byte equality. The four resource failures were reproduced exactly before candidate edits.

### Proven allocation mechanism and measured candidates

Every selected baseline PTX entry has **zero `.local` declarations and zero local load/store operations**. Thus these four frames are introduced by PTXAS register spilling, not source arrays left addressable in PTX and not a bulk copy of the by-value parameter struct. PTXAS independently reports nonzero spill stores/loads and SASS contains the matching STL/LDL operations. The source arrays can still create register pressure; absence of PTX locals does not mean their scalarized values cannot spill later.

| Failed instance | Baseline REG / STACK | Baseline PTXAS spill stores / loads | Tested change | Candidate REG / STACK | Disposition |
|---|---:|---:|---|---:|---|
| `expdec_down_kernel<20,4>` | 64 / 152 | 240 / 384 bytes | A: schedule one row's IQ4_NL helper work at a time | 64 / 672 | REJECT; spills grew to 1868 / 4008 bytes |
| `gemm4_rows_kernel<8,1,8>` | 80 / 24 | 24 / 40 bytes | B: load each activation-column scale in column scope, only this and unroll-4 instance | 90 / 0 | Compiler-resource candidate; 0 / 0 spill bytes |
| `gemm4_rows_kernel<8,1,4>` | 80 / 16 | 16 / 16 bytes | Same B change | 79 / 0 | Compiler-resource candidate; 0 / 0 spill bytes |
| `block_topk_reg_kernel<33>` | 64 / 96 | 184 / 272 bytes | A: unroll the four fixed radix passes | 64 / 216 | REJECT; spills grew to 244 / 1216 bytes |

LOCAL stays zero throughout. EXPDEC's baseline PTX declares `.maxntid 256` and `.minnctapersm 4`, and PTXAS uses 64 registers. Its scalarized row/entry partials, decoded IQ4_NL values and loop/address state compete under that launch-bound allocation. The SASS frame contains both loop/group state spills near the prologue (`STL [R1+0x6c]` at 0x00b0, additional slots 0x64/0x68/0x70, later corresponding LDL) and spills throughout the arithmetic branches (for example 0x6290, 0x62e0, 0x6340 and later reloads). The experiment demonstrates that source-level row serialization with full unrolling is not a working live-range fix: it worsens PTXAS scheduling/allocation. Precise attribution of every EXPDEC slot to a named C++ value is still unresolved; it would require richer debug mapping or a more surgical follow-up. The proven root mechanism is backend spills under the retained launch-bound register budget, not an unpromoted `s[R][NC]` array or an 88-byte `NativeExpertLayout` copy.

DFlash baseline SASS directly loads selected `Df2Seg` q/d pointers from constant parameter storage and spills the two 64-bit values: unroll-8 has `LDC.64` at 0x03d0/0x03e0, `STL.64` at 0x0410/0x0450, and later `LDL.64` at 0x4520/0x4530. Its additional 8 bytes hold scalar state. Unroll-4 has `LDC.64` at 0x0390/0x03b0, `STL.64` at 0x03e0/0x0420, then `LDL.64` at 0x2690/0x26b0. These are selected pointer values spilling under scheduling pressure, not the 104-byte segment struct being copied for dynamic array indexing. Moving the eight preloaded scales to their column-use scopes eliminates those spills. The unroll-8 compiler chooses 90 registers instead of 80; therefore this is not proof of lower register use or faster execution.

QSA baseline SASS allocates **22 ordered-key values to 88 bytes of stack slots** (0x00..0x54) during the `order_key` initialization, plus an 8-byte live-address spill at 0x58, explaining STACK 96. For example the score load and ordering at 0x13d0..0x1440 end in a predicated `STL [R1]` at 0x1450; histogram evaluation reloads it at 0x4200, and later selection/emission reload the same slots. PTX scalarizes `key[33]` and declares `.maxntid 1024`; PTXAS nevertheless spills keys plus address state at the observed 64-register allocation. This differs from the old guard comment saying the key array stays in registers. Unrolling radix passes increases pressure and is not a viable candidate.

### Candidate scope, source proof, and guard

Candidate A had one conceptual change per TU, each copied independently from `frozen/`. Its DFlash scale-scope edit applied to all rows-kernel instances: it solved the two targets but the unchanged guard found three **new** disallowed stacks (`<1,1,8>` 24 bytes, `<2,4,2>` and `<4,4,2>` 32 bytes each). That broad candidate is rejected. EXPDEC and QSA A candidates are also rejected by the measurements above. No A change is proposed for production.

Candidate B starts again from frozen DFlash and narrows the scale-scope change with `constexpr bool scoped_scale = WARPS == 8 && R == 1 && (UNR == 4 || UNR == 8)`. For those two instances it loads `xd[c*nb + st*16 + lane/2]` into a scalar inside the column loop; every other instance keeps the original preloaded `xs[8]` expression. The source diff is `H:/Strata/validation/cuda-resource-20261109/candidate-B-dflash2.diff`; full TU is `candidate-B/src/kernels/cuda/dflash2.cu`, SHA-256 `1aa3c485fa747a4e3f5cd0721968f91eb966ca35ad396a0a84c185404b7c809e`. Diff SHA-256 is `8b6c60c5276ec8b741a93623188f8239a5d5f8464c8e02a1c772446bad924be2`.

Per-output source arithmetic is unchanged: the same column/step weight and activation addresses, the same four xsum DP4A operations, the same four weight-dot DP4A operations, the same `dw*scale` multiplication and explicit `fmaf`, and the same final shuffle-reduction tree. Step order and ncols output predicates are unchanged. The only changed scheduling request is when each read-only scale becomes live; each scale is read once per column and step as before. This source-level argument requires normal immutable, non-overlapping input/output buffers; it is not executed numerical proof.

**The unchanged `tools/check_cuda_spills.py` passes candidate B's complete `dflash2.obj`: 83 entries, two stack-using entries already covered by existing allowances, zero violations, exit 0.** Only the two intended full resource records differ from original; the other 81 are equal. Selected B SASS has no STL/LDL operations. No allowance or baseline was modified. This is a TU-local resource pass, not a whole-engine qualification: original IQ and QSA still fail.

### Execution, failures, and evidence

Installed `nvcc --version`, `nvcc --help`, `ptxas --help` and `cuobjdump --help` were invoked through the owned Job and retained locally. Main's original `.cu.cache` flags were translated to direct full-TU Release compiles: C++20, compute_120+sm_120, O2, static cudart, x64, original defines and MSVC EHsc/Ob2/MT/W4. Only source/output/include relocation and diagnostic `--keep`/`-Xptxas=-v,-warn-spills` were added. Full command vectors are in `baseline-*.cmd`, `candidate-*.cmd` and matching JSON/log records. No original build directory was used for output. The baseline's all-column resource equality and exact selected instruction equality provide the reproduction check for this translation. Diagnostic tool help, rather than web or model memory, was the primary source for these flags.

Seven full-TU compiles completed successfully: baseline three, A three, B DFlash one. They were serial, with a 600-second per-compile owned-Job deadline and preflight resource checks. No GPU test binary was built or run. All completed compile receipts report containment before resume and zero active Job descendants after cleanup. Failed initial command-line quoting is retained in `baseline-dflash2.log/.json`; the actual compiler never started in that attempt. A scratch `.cmd` invocation fixed the quoting, and `baseline-dflash2-r2` is the successful retry. An initial cuobjdump function substring matched nothing; it was corrected to full mangled identities discovered in the object resource table. An initial resource parser expected a different `Function` delimiter; the failed attempt is retained, with subsequent successful output under distinct labels.

One **extra disassembly of the already-rejected A IQ candidate** was interrupted by the outer tool's 30-second deadline after its resource dump had completed. Its partial SASS log is retained and lacks a completion receipt; it is not used as evidence. Completed baseline/original SASS and B SASS have their own successful receipts. A later process check found no nvcc/ptxas/cicc/cuobjdump process, but this is not substituted for the missing A-disassembly cleanup receipt. No other process was stopped. The controlling script's owned Job has kill-on-close; the missing receipt remains explicitly incomplete.

`compiler-summary.json` is the final machine-readable comparison; `baseline-analysis.json`, `candidate-A-analysis.json`, the full resource tables, kept PTX and selected SASS remain in scratch. `summarize.py` asserted original/baseline resource equality, selected instruction equality, no PTX locals in all four selected entries, exactly two B resource changes, STACK/LOCAL=0 for both B targets, and no B STL/LDL. `investigate.py verify` rechecked all 290 manifest entries successfully after the experiments. No previous failed evidence was deleted or relabeled as a pass.

### Handoff and remaining work

GPU parity count **0**, timing count **0**, measured numerical error **unknown**. Parent can now sequence a tiny DFlash test of variants 18/21 using the inspected independent CPU reference and exact frozen baseline. Include K values that exercise full unroll and remainder steps, ncols 1..8, and 1/2/3 segment boundaries, with total explicit GPU allocations below 256 MiB. Unroll-8's 80→90-register change may affect occupancy/performance; no throughput guarantee is made.

Next minimal production proposal, only after parent SPEC/QUALITY and GPU parity: a default-off compile-time opt-in for this **two-instance DFlash scale-scope change**, with the original source expression retained when off. The scratch B source is an experiment, not that production opt-in patch. Require byte-identical off-path device code against the frozen default and rerun the whole-engine unchanged resource guard when integrating. EXPDEC and QSA need a separate bounded follow-up; their tested A changes must not be integrated. Overall native resource qualification remains **FAIL / unresolved**.

Self-review-event: `qa_defect` for rejected broad DFlash changes and interrupted redundant A disassembly. The unchanged guard caught the new spills; narrow B was then independently compiled and gated. No governance/allowance weakening was accepted. Compile-only evidence is kept separate from the intentionally unrun GPU checks.

---

## Historical first attempt — resource-blocked checkpoint

## Objective and disposition

Investigate the four native 0.5.2 r3 CUDA resource violations, demonstrate their cause using the exact preserved objects and a frozen same-input compile, then test a minimal isolated candidate against the unchanged resource guard before bounded GPU parity. This owner covers `iq_kernels.cu`, `dflash2.cu`, `qsa_select.cu` and their relevant helpers/tests. Parent long-input QA is separate.

**BLOCKED / NOT VERIFIED.** Resource preflight rejected the first diagnostic child before creation. No PTXAS/SASS root cause has been demonstrated, no candidate source change has been made, and no production patch is ready for review. The four existing violations remain failures.

## Baseline and preservation

Main was clean at entry, HEAD `ceffaf8511937460ae939a5d185fac937dc96275`. `git diff --stat 4a171bde HEAD -- src/kernels/cuda include third_party/ggml` returned no differences. The r3 source receipt identifies `4a171bdeb33675963edcca51f423519863fb7127`. Dependency HEAD was independently queried as `3cf03257f219afbe7334045ff7c6a06ac68c627d`.

Existing primary local evidence is `H:/Strata/releases/personal-052-local2-20261107/followup-r3/{build-source.json,resource-origin.json,resource-correlation.json}` and the original CMake-generated `native-build/strata_kernels.dir/Release/*.cu.cache` files. The origin receipt records CUDA 13.3.73, MSVC 19.44.35224.0, Release sm_120, no fast math or relocatable device code. These compiler versions have not been independently rerun in this session. The actual compiler path in the recipe is `C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/nvcc.exe`; the executable was located with the file tool.

The isolated directory `H:/Strata/validation/cuda-resource-20261109/` now contains a tracked-input snapshot of `include`, `third_party/ggml`, and `src/kernels/cuda` under `frozen/`, plus copies of the three original `.obj` files and CUDA compile-cache records. `manifest.json` records SHA-256 hashes for the snapshot and copied original objects. Old source/build outputs and dependencies were not modified. No installed package, process, service, environment setting, Git configuration, release, or default was changed.

## Existing failures, not new measurements

The following values come from the supplied resource-correlation evidence, not from a fresh compiler run in this session. Every instance has LOCAL=0.

| Instance | REG | STACK | Existing permitted STACK | Fresh before/after |
|---|---:|---:|---:|---|
| `expdec_down_kernel<20,4>` | 64 | 152 | 136 | NOT RUN |
| `gemm4_rows_kernel<8,1,8>` | 80 | 24 | 0, unlisted | NOT RUN |
| `gemm4_rows_kernel<8,1,4>` | 80 | 16 | 0, unlisted | NOT RUN |
| `block_topk_reg_kernel<33>` | 64 | 96 | 88 | NOT RUN |

The existing evidence correlates exact full demangled signatures and sm_120 across preserved 0.5.1/r3 executable/library artifacts and finds equal resource values. This establishes pre-existence, not an acceptable resource verdict or the reason for stack allocation. `tools/check_cuda_spills.py` explicitly gates STACK as well as LOCAL. LOCAL=0 is insufficient to distinguish arrays from spills.

## Source findings and use conditions

These are static-analysis findings; they do not prove the compiler allocation cause or that a particular installed-app request launched these instances.

`iq_kernels.cu:2767–2820` instantiates the down kernel with `TD=20` (IQ4_NL), `R=4`. Dispatch at approximately lines 4080–4213 requires EXPDEC enabled, EXPDEC down enabled, IQ4_NL down enabled, `n_ff=640`, and positive `n_embd` divisible by 128. `STRATA_OLD_IQ_MMVQ` bypasses EXPDEC. The default down row count selects R=4. A block has 256 threads, 32 eight-lane subwarps, and 128 rows per pass; `rb` controls passes. It stages four entries at a time and specializes NC=1/2/3/4. Helpers `ed_d20_rows`, `Split<20>::load/apply_u`, and `ed_stage_entry` were read. `Split<20>::W` has two `int2` values and a float scale. The helper keeps independent per-row/per-entry partials and preserves explicit sum-tree additions. Register pressure from these overlapping values is a hypothesis; the exact contribution of `s`, `s8`, `w`, row pointers, parameter fields and compiler temporaries remains unknown without PTX/SASS and PTXAS.

`dflash2.cu:503–561` is the Q4_0 rows-per-warp GEMM. Dispatch at lines 1034–1047 maps failing `<8,1,4>` to variant 18 and `<8,1,8>` to variant 21. Both have 256 threads and one output row per warp, eight activation-column accumulators, with reduction-step unroll factors 4 or 8. The Q4 default variant in this CUDA source is 17, not either failing variant. Variants 18/21 are reachable through the existing per-process tuning or bench setter. Matrices require `n_in` divisible by 512, output rows divisible by 16, and 1–8 columns. Unlike the old dynamic segment-picker pattern, `df2_pick` already accesses the three by-value parameter segments at constant indices. It would be unjustified to label these failures a dynamic `Df2Segs` parameter copy solely from the old guard comments. Candidate pressure sources include the eight preloaded column scales `xs`, weights, accumulators, and unrolled-step temporaries. Both failing instances need separate PTXAS attribution.

`qsa_select.cu:739–845` keeps 33 ordered score keys per thread across radix passes and selection. It has `__launch_bounds__(1024)` and per-warp histograms. Dispatch at lines 2930–2994 normally uses capacity on CUDA sm_120; when `reach <= 1024*33`, this `<33>` kernel is reachable without an opt-in. Wider reach uses another kernel. Per-thread `per=ceil((n_bid+1)/1024)` must stay <=33. `key[33]` is statically indexed by unrolled loops, but a fixed 64-register compiled result plus live selection state may spill. Whether keys themselves or other live values spill is not established. The source has 64-bit range/index state and sequential radix passes; shortening live ranges or unrolling the four fixed radix passes would require a same-input measurement before any recommendation.

## Containment, attempted command, and blocker

Selected standards were the canonical `CLAUDE-FABLE-5.md` context, PC/project AGENTS, Common Engineering, Implementation Start Gate, Skill Selection, DeepResearch (local-primary-source scope), Application Development, CPP and Python SOPs. Baseline skills already in context were applied, with `systematic-debugging` loaded for this task. No delegation was used. No web research or package changes were needed.

An isolated `investigate.py` stages inputs and prepares serial commands. It reuses a scratch copy of the existing `tools/perf131k/windows_job.py`: atomic job assignment, suspended creation, membership readback before resume, kill-on-close, owned-Job-only cleanup, output bound and deadline. Planned compile containment is one invocation at a time, 600-second deadline, 6 GiB Job commit cap and 16 maximum child processes. Resource floors are RAM 3 GiB, available commit 4 GiB, C: 5 GiB, H: 10 GiB and GPU free 1 GiB. TEMP/TMP are passed only to owned children and point to H: scratch. No child from this harness was actually launched, so containment execution has not been freshly validated here. GPU parity additionally needs an absent model-server process and explicit total allocations below 256 MiB; no parity executable exists yet.

Commands actually executed included:

```text
git status --short
git rev-parse HEAD
git diff --stat 4a171bde HEAD -- src/kernels/cuda include third_party/ggml
git -C H:/Strata/deps/ggml-3cf03257 rev-parse HEAD
uv python find --offline
uv run --no-project --offline --python 3.13 python H:/Strata/validation/cuda-resource-20261109/investigate.py init
uv run --no-project --offline --python 3.13 python investigate.py tool cuobjdump-help "C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v13.3/bin/cuobjdump.exe" --help
```

The initialization completed. The diagnostic command failed in preflight with `available_ram=2960244736`, `commit_headroom=27342483456`, `H_free=250939920384`, `C_free=9010393088` bytes. Available RAM was already below 3 GiB. This happened before GPU telemetry, Job creation, or cuobjdump invocation. The controller traceback is in the session tool output; there is no successful cuobjdump log or child receipt to cite. A subsequent passive check found `strata` PID 17648 alongside the idle desktop PID 26844; no process was stopped or controlled. GPU free was 1459 MiB at that check.

Further passive checks saw FreePhysicalMemory fall to 259208 KiB, later 222068 KiB after a 60-second bounded wait. The final pre-log check was 891544 KiB free physical, 27809052 KiB free virtual reported by CIM, and 1479 MiB GPU free. These are ambient observations, not parent-QA results. System-memory headroom never recovered to the required floor during these checks. Compilation and tests were therefore held.

After writing this log, `git diff --check` exited successfully and `git status --short` listed only this new log. A final passive check still found the same model process, with 313632 KiB free physical memory. The blocker remained active at handoff.

## Verification and numerical claims

No production kernel edits, candidate TU edits, CUDA compilations, PTXAS runs, SASS disassemblies, resource-table reruns, GPU launches, GPU timing repetitions or numerical comparisons were executed. Parity/timing counts are **zero**. Numerical error versus the exact baseline is **unknown**, not zero. No candidate math-preservation proof or compiler-resource improvement is claimed.

Existing reusable tests were inspected: `src/core/dflash2_q4_parity.cpp` (independent CPU dequantized/integer-dot reference), `src/kernels/qsa_topk_parity.cpp` (reference radix kernel with tied/equal/continuous scores), `src/kernels/native_expert_parity.cpp` (independent ggml dequantization/CPU reference), and `src/kernels/expdec_bench.cpp` (default-vs-EXPDEC bitwise check). Their unmodified broad runs are not suitable substitutes for the requested tiny instance-specific tests. DFlash's current CPU test does not explicitly select failing variants 18/21. The EXPDEC bench includes a rotating >=96 MB blob pool and many cases; a bounded direct-down harness is preferable for this investigation. No test result from another owner is adopted as this owner's result.

## Next minimal work after parent frees headroom

Resume the existing H: snapshot, retain the preflight failure, and independently verify snapshot/original hashes. Query the installed tool help inside the owned Job for the exact PTXAS and cuobjdump options. Disassemble the copied original objects for all four full mangled identities. Compile each full frozen TU separately with Release-equivalent original flags plus diagnostic reporting/kept intermediates, then require resource reproduction before changing source. The prepared wrapper's compile recipe has not run and needs comparison to the original full MSBuild command; do not treat its mere presence as exact compiler reproduction.

Classify each failure using PTX local declarations, parameter-to-local stores, PTXAS stack/spill-store/spill-load counts, and actual SASS local load/store sites. Only then create one-variable candidate TU copies with diff/hash records. A plausible DFlash experiment, if spills are confirmed, is to load each column scale in its column scope rather than holding `xs[8]` across columns: per-output integer-dot/FMA order need not change, but this has not been compiled or proved here. No EXPDEC or QSA change is selected until allocation sites are known. Do not reduce formats, remove failing instantiations, change defaults or widen guard/baseline limits.

After the unchanged resource gate passes, explicitly exercise the matching instances on bounded independent inputs. DFlash should cover variants 18/21, unroll-full and remainder reductions, 1–8 columns, and 1/2/3 matrix segments with small row counts. IQ4_NL down should cover NC=1..4, an entry count crossing four, and multipass `rb`, with `n_ff=640` and a valid divisible-by-128 embedding. QSA should cover the 33-key reach boundary, partial tail cells, identity selection and equal/tied/continuous scores. Keep GPU allocation accounting below 256 MiB and wait for the parent model process to disappear; compilation alone can resume when CPU/disk/GPU-floor headroom is adequate. Report actual launch geometry, bitwise mismatches, numerical error and bounded timing counts. Parent SPEC/QUALITY review remains necessary before any production opt-in patch.

## Self-review and residual risk

Self-review-event: `qa_defect`, verification blocked by resource admission. Review-only: the floor correctly prevented an owned child from starting; changing admission or stopping the other owner's process was rejected. No governance or guard change is warranted. The initialization sample ran successfully; the diagnostic attempt exercised the preflight failure path, not the compiler or Job path. Source/allocation hypotheses are explicitly separated from proven causes. The exact runtime use of the four instances in installed-app requests is unknown. Resource failure and native release qualification remain unresolved.
