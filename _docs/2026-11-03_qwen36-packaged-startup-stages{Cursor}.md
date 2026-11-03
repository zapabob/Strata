# Packaged Q36_STARTUP stages → 20261103.4

- **日時**: 2026-11-03 23:16 JST
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。起動時間とトークン速度は未計測。T04 / T06 / T07 と対の速度計測も未計測。

## 概要

Control 経由の packaged load がエンジン log の `Q36_STARTUP` を拾い、loading / warming / ready / error を報告するようにした。ホストだけの変更なので新しい `strata.exe` は作らない。許可リストの digest は `.3` のまま。製品版は `0.4.0-preview.20261103.4`。GitHub リリースは latest にしない。

## 背景・要求

T09 の穴: packaged は `control.start` でエンジンを上げるため、stderr を直接読めない。非 packaged の `spawnProcess(serve/server.py)` だけが段階を見ていた。未計測の速度方針は既定にしない。22GB モデルは起動しない。

## 前提・判断

- `strata_control/runtime.py` の `_paths` は `{profile}.host.log`（owner）と、サーバは `{profile}.server.log` を書く。エンジンの stderr は run config の `log`（例: `%LOCALAPPDATA%\Strata\install\strata-qwen36-ud-q4_k_xl.log`）。
- 未知の stage 名は拒否。error のあとの progress では error を消さない。
- STOP でプロセスを終了させない（既存どおり stdin EOF）。
- 署名・spill guard 合格・速度向上は主張しない。

## 変更対象ファイル

- `apps/host/server/q36-startup-events.mjs`（`q36ReportPhase` / `q36EngineLogPath` / `pushEngineLogChunk`）
- `apps/host/server/native-control.mjs`（packaged 時に `cfg.log` を poll）
- `apps/host/tests/packaged-control.test.mjs`
- `apps/host/tests/q36-progress.test.mjs`
- `VERSION` ほか製品版文字列 → `0.4.0-preview.20261103.4`
- `docs/HAKUA_RELEASE.md`（stash 衝突を `.3` 側で解消したうえで `.4` に更新）
- README 8 本、`docs/HAKUA_INSTALL.md`、`packaging/README.md`

## 実装詳細

`watchQ36EngineLog` が `cfg.log` を読み、`pushEngineLogChunk` で段階を畳む。`notePackagedStartup` が instance.phase と job.summary を更新する。テストは start をホールドして log に追記し、GPU なしで loading → warming → ready を確認する。

## 実行コマンド

```text
node --test tests/packaged-control.test.mjs tests/q36-progress.test.mjs tests/q36-run-contract.test.mjs tests/q36-capabilities.test.mjs tests/native-control.test.mjs
npm run build   # apps/host, with STRATA_PUBLIC_ASSETS + RECEIPT
node apps/desktop/scripts/verify-release.mjs
apps\desktop\node_modules\.bin\tauri.cmd build --bundles nsis
setup.exe /S /UPDATE
gh release create v0.4.0-preview.20261103.4 --latest=false
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| host 5 本（上記） | 55 pass / 0 fail |
| `verify-release.mjs` | exit 0 |
| NSIS | exit 0。114979368 bytes。SHA-256 `9bf5f4c9090484a35a8e3534d310840303cd7d3b1684ebbce272e01fd9937724` |
| `/S /UPDATE` | `INSTALL_EXIT=0` |
| DisplayVersion | `0.4.0-preview.20261103.4` |
| PrismML | 上書き前後とも `90428627933e0c4120fe0bcaa6a3cc7803dd5fe5846102eeacf4cf1298807a8d` |
| 署名 | なし。`signature` は null |
| spill guard | 不合格のまま。合格とは書かない |
| 速度 | 未計測 |

## 残留リスク

- T04、T06、T07、対になる速度計測は未計測。
- GUI クリックでの chat/stop/restart は本ログでは未実施。
- 実モデル起動はしていない。

## 次の推奨アクション

1. リリース https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.4 （`--latest=false`）。
2. T04 / T06 / T07 は対の計測なしに既定化しない。
