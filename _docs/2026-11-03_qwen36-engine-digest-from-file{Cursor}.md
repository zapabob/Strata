# mapped-pack は解決したエンジンファイルの SHA-256 だけで許可する

- **日時**: 2026-11-03 00:45 JST
- **実装AI**: Cursor

## 概要

モデル設定の `engine_sha256` では mapped-pack を開けないようにした。パッケージ版の起動は、Control が選んだ `strata.exe` を読んで SHA-256 を出し、allowlist と一致するときだけ `--q36-expert-store mapped-pack` を付ける。

## 判断

設定ファイルに allowlist の digest を書くと、別のエンジンへ新しい flag を送れてしまう。読めないファイルは null で、flag は付かない。速度は測っていない。

## 検証

`node --test tests/q36-run-contract.test.mjs tests/q36-capabilities.test.mjs tests/native-control.test.mjs` は 19 pass / 0 fail。

公開済み `v0.4.0-preview.20261103.1` の setup EXE にはこの変更は入っていない。
