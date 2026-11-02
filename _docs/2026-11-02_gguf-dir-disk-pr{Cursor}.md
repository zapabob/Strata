# Free space is measured on the drive that receives the files

- **Date**: 2026-11-02 18:00 JST
- **Author**: Cursor
- **Base**: Niko1221/Strata `main` at `c62d5e3a`
- **Branch**: `fix/gguf-dir-disk-on-data-dir` (`9cf18021`), worktree `H:\Strata\worktrees\gguf-dir-disk-check`
- **Pull request**: https://github.com/Niko1221/Strata/pull/4989

## What was wrong

`--gguf-dir` is a folder of files already in hand. Setup nevertheless judged free space on that folder.

- Qwen3.6 charged a missing pinned file to that drive, then said the file was missing.
- Flash-Next charged the pack and the draft layer to that drive, though they are written under `--data-dir`.
- DeepSeek did the same for a missing shard, which is not downloaded there, and for shared files, which are fetched into the data folder.

## What was done

The free-space check follows the bytes that will be written. A source folder that will not receive them is not asked to hold them.

## Tests

`py -3 -m unittest tools.test_setup_qwen36 tools.test_setup_dsv41 tools.test_setup_unsloth`

198 passed. Five failures of `test_no_engine_stops_before_the_download` occurred because the signed DeepSeek engine feed was reachable and installed engine 0.1.55. That assertion is about the engine, not about disk space.
