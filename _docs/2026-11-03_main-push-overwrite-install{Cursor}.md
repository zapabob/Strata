# main への fast-forward と再上書き

- **日時**: 2026-11-03 00:41 JST（上書き終了 2026-11-02T15:41:58Z）
- **実装AI**: Cursor

## 概要

`feat/q36-32gb16gb` を `main` へ fast-forward して push した。force はしていない。同じ setup EXE で `/S /UPDATE` をやり直した。

## 結果

| 項目 | 結果 |
|------|------|
| main | `170e0d33..1d07f116` |
| push | `origin/main` へ通常 push |
| 上書き | `INSTALL_EXIT=0` |
| DisplayVersion | `0.4.0-preview.20261103.1` |
| host | `0.4.0-preview.20261103.1` |

未追跡の `_docs/intake/` と engine-died ログはコミットしていない。
