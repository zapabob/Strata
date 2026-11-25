# Four engine types as separate components + C: disk usage (2026-11-23)

## Separate components installed
User asked for the four engines as separate Control components. Built from the
latest Gen-I/J binaries (0.6.9) under
`C:/Users/downl/AppData/Local/Strata/components/engine/`:

| Component id | version | files | entrypoint |
| --- | --- | --- | --- |
| strata-engine | 0.6.9 | 155 | strata.exe |
| strata-engine (separate, 0.6.9) | 0.6.9 | 7 | strata.exe |
| strata-inkling (shape inkling2) | 0.6.9 | 7 | strata-inkling2.exe |
| strata-hy4 (shape hy4) | 0.6.9 | 6 | strata-hy4.exe |
| strata-q38 (shape q38) | 0.6.9 | 6 | strata-q38.exe |

All manifests verified with `engine_component.verify(full=True)`. Shared DLLs
between the separate components are **hardlinks** to the canonical 0.6.9
component so the four packages do not each duplicate ~530 MB.

## C: disk usage root cause
C: was at 0.12 GB free (929 GB used). Measured top contributors:
- `AppData/Local/Strata/components/engine` = **21.57 GB** — nine historical
  engine generations (0.5.9, 0.6.0, 0.6.2, 0.6.3 x2, 0.6.4, 0.6.7, 0.6.8, 0.6.9),
  each ~2.1 GB because every folder carries its own copy of cublasLt64_13.dll
  (456 MB) + cublas64_13.dll (49 MB) + CRT DLLs.
- `AppData/Local/Temp/opencode` = **16.62 GB** — hikari-model 6.71 GB,
  ds4-model 5.24 GB (benchmark copies), v072-target 2.84 GB, syncstrata-013 1.81 GB.
- `C:/Strata/models` = 11.73 GB (qwen3.8-27b GGUF).
- `AppData/Local/Programs/Strata` = 0.59 GB; CrashDumps = 0.94 GB.

After hardlinking the separate components' DLLs, C: free rose from 0.12 GB to
3.03 GB.

## Cleanup performed (user approved "片付けたい")
- Verified SHA first: Temp `DeepSeek-9B-Q4_K_M.gguf` is byte-identical to the H:
  Qwen3.5-9B original (8cf793a3...), so it was safe to delete. Hikari's Temp copy
  had a **different SHA** from the H: original (18c2a2c4 vs 0ab2a1f2) — it is the
  actual benchmark entity, so it was kept.
- Removed 8 obsolete engine generations (0.5.9, 0.6.0, 0.6.2, 0.6.3 x2, 0.6.4,
  0.6.7, 0.6.8) and 3 stale Temp build copies (ds4-model, v072-target,
  syncstrata-013). Small metadata (engine-component.json / BUILD.json) was backed
  up to H:/Strata/evidence/cleanup-backup/manifests first.
- Result: C: free **0.12 GB -> 27.17 GB**; only 0.6.9 + the four separate 0.6.9
  components + hy4 0.1.64 remain; Temp keeps only hikari-model (6.71 GB).
- App relaunched and reported "Strata engine 0.6.9 is installed", no crash log.
- Receipt: H:/Strata/evidence/cleanup-report.json.

## Notes
- Frozen evidence (H:/Strata/evidence/*), all models and the active engine remain
  untouched; only obsolete installed generations and verified-duplicate Temp
  copies were removed.
- Scripts: H:/Strata/evidence/install-4-separate-components.py,
  finish-q38-component.py, dedupe-component-dlls.py.
