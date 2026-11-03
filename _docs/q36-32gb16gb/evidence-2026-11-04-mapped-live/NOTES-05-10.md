# mapped-live preflight 2026-11-04 05:10–05:12 JST

- Purpose: remeasure headroom; if VRAM free run mapped-live; else timestamp blocker and take a real non-GPU forward step (docs/code honesty), DESIGN #6: do not kill Hermes.
- GPU: RTX 5060 Ti — used 15182 MiB / free 869 MiB / util 96%.
- Hermes: PIDs 22836 / 22944 still alive (WS ~5665 MiB + ~139 MiB; large commit). Not killed.
- RAM: total 31.87 GiB, free ~9.45 GiB.
- Disk: H: FreeGB **78.74** (docs that still said ~14.2 after 04:20 reclaim were stale — corrected this turn). C: FreeGB ~3.02 (tight for npm/caches; not the live blocker).
- Unsigned engine `0.4.0-q36-…\strata.exe` SHA-256 `6fe11065…` present. Signed `b5e4d525…` untouched.
- Model + pack present: GGUF 22853663008 bytes; `.q36epk` 20127612928 bytes.
- Decision: **mapped-live remains BLOCKED**. No serve / no Q36_STARTUP capture / no T03 restart / no T04–T08 this turn. No invented speeds. Goal complete = false.

## Honesty gaps closed this turn (non-GPU)

1. **Stale H: FreeGB** in DESIGN / plan / PACKAGE_README / evidence-summary (said ~14.2; now ~78.74).
2. **`--help` omitted `--q36-expert-store`**. Family switch only accepts it after `--native`/`--model` selects qwen35moe; without that path, `unknown argument: --q36-expert-store`. Source now documents the flag in `generate.cpp` usage, `engine.hpp`, and q36 usage string. **Installed unsigned binary still omits the help line until the next q36 engine rebuild** — do not claim the shipped EXE already shows it.
3. Binary ASCII markers (no model load): `Q36_STARTUP` true, `q36-expert-store` true, `mapped-pack` true, `pin pool` true, `ExpertPinPool` false (C++ symbol not required in ASCII).

## Planned live command (do not run while Hermes holds VRAM)

```text
%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe ^
  --native H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf ^
  --max-context 65536 --prefill auto --mtp 2 --q36-expert-store mapped-pack --serve
```

Expected stderr markers (not speed claims):

- `Q36_STARTUP` JSON stages
- `strata-q36: mapped-pack host pin pool … MiB x2` (or pageable-fallback lines from `q36_engine.cu`)
- Never claim 18.75 GiB legacy arena on mapped-pack success path

## Status

| Item | Result |
|------|--------|
| mapped-live | **BLOCKED** |
| T03 chat→stop→restart | **NOT_RUN** |
| T04 / T06 / T07 / T08 | **NOT_RUN** |
| invented speeds | **false** |
| Hermes killed | **false** |
| goal complete | **false** |
