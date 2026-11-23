# 3x benchmark suite on the latest Gen-I/J engines (2026-11-23)

## Objective
User asked to run each benchmark 3 times. Used the freshly rebuilt CUDA 13.5 /
SM120 engines (Gen-I/J: strata.exe `6ac28c84`, strata-inkling2.exe `17759a44`,
strata-q38.exe `ab87e2e6`, strata-hy4.exe `cd2f36e5`). The originally planned
"DS4-9B" target was corrected by the user to **Qwen3.5-9B** — the GGUF is named
`DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf` on H: (the
Japanese folder name and `[` required `Get-ChildItem` + literal path; a
hard-coded mojibake path caused three EXIT=2 usage failures, fixed in the
separate qwen35-9b script).

## Method
- Script: H:/Strata/evidence/bench-3x.ps1 (+ bench-qwen35-9b-3x.ps1).
- Raw logs: H:/Strata/evidence/bench-3x/<target>-run{1,2,3}.txt.
- Summary: H:/Strata/evidence/final-bench-summary.py (joins wrapped log lines).
- All 15 runs exit 0.

## Results (3 runs each)

### Sakura-Inkling-2 Q4_K_M @ 98K (`--expert-vram 7.3`, chunk 512, 16-tok prefill)
| Run | Prefill | Decode | hits/misses | cpu_ms |
| ---: | --- | --- | --- | ---: |
| 1 | 11.86 t/s | 20.25 t/s | 10088/4024 | 936.9 |
| 2 | 11.86 t/s | 19.48 t/s | 10088/4024 | 967.6 |
| 3 | 11.89 t/s | 25.06 t/s | 10088/4024 | 698.5 |

### Inkling-2 UD Q4_K_M @ 16K (`--expert-vram 7.3`)
| Run | Prefill | Decode | cpu_ms |
| ---: | --- | --- | ---: |
| 1 | 14.21 t/s | 14.25 t/s | 672.5 |
| 2 | 14.14 t/s | 16.23 t/s | 1223.9 |
| 3 | 14.39 t/s | 29.26 t/s | 449.9 |

### Qwen3.5-9B Q4_K_M (`strata.exe`, ctx 4096, 64 decode)
| Run | Prefill | Decode | E2E |
| ---: | --- | --- | ---: |
| 1 | 59.1 ms | 58.11 t/s | 1183.8 ms |
| 2 | 57.8 ms | 61.56 t/s | 1113.5 ms |
| 3 | 57.0 ms | 63.39 t/s | 1081.2 ms |

### Hikari-LoRA PQ2_0 (`strata.exe`, ctx 4096, 31 decode)
| Run | Prefill | Decode | E2E |
| ---: | --- | --- | ---: |
| 1 | 3888.3 ms | 20.30 t/s | 5438.1 ms |
| 2 | 1167.7 ms | 20.40 t/s | 2705.0 ms |
| 3 | 767.5 ms | 20.20 t/s | 2320.5 ms |

### Qwen3.8-27B MTP (`strata-q38.exe`, ctx 4096, 31 decode)
| Run | Prefill | Decode | E2E |
| ---: | --- | --- | ---: |
| 1 | 394.5 ms | 29.24 t/s | 1474.5 ms |
| 2 | 380.1 ms | 29.38 t/s | 1455.5 ms |
| 3 | 394.2 ms | 29.24 t/s | 1475.3 ms |

## Qwen3.5-9B from C: (user noted a C: copy; 3 more runs)
Model: `C:/Users/downl/AppData/Local/Temp/opencode/ds4-model/DeepSeek-9B-Q4_K_M.gguf`
(the same 5.24 GB Qwen3.5-9B architecture under a clean path).
| Run | Prefill | Decode | E2E |
| ---: | --- | --- | ---: |
| 1 | 57.6 ms | 59.77 t/s | 1145.2 ms |
| 2 | 57.3 ms | 60.66 t/s | 1129.5 ms |
| 3 | 58.5 ms | 58.94 t/s | 1163.8 ms |
H: and C: copies agree within run-to-run noise (pp 57-59 ms, tg 59-63 t/s),
confirming the earlier H: path with the Japanese folder name was the only issue.

## Notes
- Decode varies run-to-run on the MoE targets (19.5-25.1 t/s Sakura,
  14.3-29.3 t/s UD) because expert cache warmth differs; `cpu_ms` tracks it
  inversely. Prefill and hits/misses are stable.
- The Qwen3.5-9B numbers (pp ~57-59 ms, tg 58-63 t/s) are in the same range as
  the earlier DS4-9B measurements (pp 63 ms, tg 53-65 t/s), so the renamed
  target behaves consistently.
- No HY4 model is present locally, so strata-hy4.exe was not benchmarked.
- `releaseQualified=false` unchanged: these are single-machine (RTX 5060 Ti,
  CUDA 13.5 / sm_120) measurements, not cross-GPU qualification.
