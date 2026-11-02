# Qwen3.6 / RAM 32GB / VRAM 16GB baseline slot

This directory holds the workload contract and the machine binding for the
Qwen3.6 startup plan. It is not a measured speed result.

The compared run, when it is later taken, uses one Qwen3.6-35B-A3B UD-Q4_K_XL,
context 65536, MTP 2, parallel 1, FP32 KV, and the effective prefill the engine
prints. A shorter context, a lower KV precision, or another model is a different arm.

`bindings/host.json` records the PC and the source commit that were read while
this slot was created. `windows_gpu_baseline` stays `NOT_RUN` until a paired
load on that PC writes a result file under `results/`. The historical 28.6 s /
266.0 s / 306.6 s figures live in `_docs/q36-32gb16gb/evidence-summary.json`.
They are one past observation, not this slot's median.

Log parsing rules are checked by `tests/qwen36/test_startup_log_analysis.py`.
The original stderr is not stored here.
