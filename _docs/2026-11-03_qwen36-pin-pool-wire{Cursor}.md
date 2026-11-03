# mapped-pack host pin pool をエンジンへ接続

- **日時**: 2026-11-03 23:55 JST
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。対の速度計測は未実施。T04 / T06 / T07 は NOT_RUN。

## 概要

`ExpertPinPool`（既定 2×32 MiB）を mapped-pack の H2D 経路に接続した。legacy 既定は不変。`cudaHostAlloc` 失敗時は縮小再試行のあと pageable staging を明示し、18.75 GiB arena へは戻さない。

## 変更

- `expert_store.hpp/.cpp`: 外部バッファ（非所有）コンストラクタ
- `q36_engine.cu`: mapped-pack 時に pin pool 確保、`h2d_from_host` で stream / slot 置換 / 初回 upload
- `q36-run-contract.mjs`: 新 `strata.exe` digest `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29` を allowlist に追加（旧 digest 維持）
- `q36_transfer_lifetime_test`: 外部バッファケース

## 検証

| 項目 | 結果 |
|------|------|
| `q36_transfer_lifetime_test` | exit 0 |
| `strata_qwen35` Release | exit 0（-j 2） |
| `strata` Release | exit 0 |
| `strata.exe` | 114187264 bytes、SHA-256 `6fe11065…` |
| 実モデル起動 / paired 速度 | NOT_RUN |
| `.5` インストーラ | 未出荷（コードと allowlist を先に main へ） |

## 残留リスク

- pin pool 経由の H2D は slot ごとに同期する保守的実装。速いとは主張しない。
- 全 `-j 8` 再ビルドは strata_mmq で OOM した。差分ビルドは成功。
- T04/T06/T07 未計測。

## 次

1. 未署名エンジンパッケージ更新 → `0.4.0-preview.20261103.5` NSIS / 上書き / `--latest=false`
2. mapped-pack 1 回の起動ログで pin pool 行を確認（速度比較ではない）
