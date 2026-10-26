# Windows inference preview, 27 October 2026

This preview accepts working text inference on the measured Windows PC. It does
not claim scientific quality, comparative performance or full-length certification.
The README and PERF131K record contain the exact scope and measurements.

The engine source checkpoint is
`56c4613be8e5f63868f8dbd52e41ab644a324aba`. The tested executable SHA-256 is
`20373ca6b9b16b9d220820a902b584d604a64e068d383a26ba11dd4e43f85d93`.
GUI request/import changes are in `411d5b63`; the recovery and overlay helper
changes are in `29725f68`. These are separate from the engine source identity.
The spin8 and tqcodec directories are tracked repository trees; this build's
CMake cache points to those directories in its source checkout.

With capacity 131072, Qwen3.8 Q2_0, spec4 + MTP and k8v4, exact 4096- and
32768-token inputs completed first and repeated requests, each generating 52
tokens. Four synthetic sentinel recall checks passed. Both runs confirmed zero
remaining Job processes. The separately authorized Job cap was 32,010,928,128
bytes; earlier 10 GiB failures remain recorded. The 64K stage was intentionally
cancelled when the acceptance scope changed, and has no capacity verdict.

Local verification includes the CUDA build, 36 focused GUI/host regressions,
four real Harness cases and seven overlay-helper cases. Three focused no-child
recovery cases passed. The broader Node and runtime suites are not all green;
no full-suite pass is claimed. A tiny pinned GGUF completed generation through
the actual host API with an isolated synthetic profile and explicit FP16.
Interactive desktop testing was unavailable.

The local quiet-turn allowance is now 30 minutes, with separate remote/tool
limits and cancellation. Generic text GGUF import reports actual compatibility
errors. An unsupported native import offers the generic backend. Missing cache
metadata remains unknown; unsupported quantized cache settings require explicit
FP16 selection. Missing runtime child ownership still stops automatic recovery.

The existing legacy state responsible for the test PC's lost-host error was
preserved after checking its exact hash, absent host and listener, unheld lease
and empty process registry, while holding the profile start lock. No unrelated
service was stopped. Future hosts publish a no-child marker before state.

The native R2 archive has 26 verified payload files and SHA-256
`4d2d744a532ebd70154220dad1e6605ddfde9d043ca7494153f163a8cc434755`.
Its extracted manifest, required PE dependencies and native help invocation
were verified. Previous components and rollback backups are retained. The
legacy vision executable is unchanged; image inference is unqualified.

Full input 126000 with output reserve 1024 and at least 512 generated steps,
PPL/KL, paired statistics, 32-turn/two-hour stability, HIP/SYCL and native
multiuser-memory resource qualification remain open. Memory is disabled by
default. Same-source GitHub CI has no passing check run; repository safeguards
were not bypassed. Local evidence and independent Astra xhigh review do not
substitute for those missing qualifications.
