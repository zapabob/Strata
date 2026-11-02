# Qwen3.6 起動段階と RAM 入場

- 日時: 2026-11-02 23:40 JST
- 実装AI: Cursor (Grok 4.7)
- ブランチ: `feat/q36-32gb16gb`
- ゴール: 計画の完成、ビルド、上書きインストール、リリース、README書き換え。このログの時点では未完了。

## 概要

T02 の起動段階行と、UD-Q4_K_XL の legacy expert arena が物理RAMに載らないときの起動前拒否を入れた。mapped expert store、CUDAビルド、NSIS、上書きインストール、GitHubリリース、README書き換えは未実施。

## 背景・要求

`/goal` は計画T00–T09の完成と、ビルド、上書きインストール、リリース、READMEを一つの完了条件にしている。今回進めたのは、今のエンジンが 19195 MiB の host arena を確保して落ちる経路を、起動前に止めることと、段階を stderr で区別すること。

## 前提・判断

- 18.75 GiB 級の拒否はファイル名が `q4_k_xl` のときだけ。他のQwen3.6のexpert容量は作らない。
- 予備は 4 GiB と RAM の 20% の大きい方。
- 段階行は stderr の `Q36_STARTUP`。stdout の READY プロトコルは変えていない。
- エラー段階のあとの progress は要約を loading に戻さない。
- 配布中の strata-q36 は、このソースをビルドするまで段階行を出さない。RAM拒否は Host 側なので、アプリを入れ替えれば旧エンジンでも効く。

## 変更対象ファイル

- `include/strata/qwen35/startup_trace.hpp`
- `src/qwen35/q36_engine.cu`
- `apps/host/server/q36-startup-events.mjs`
- `apps/host/server/q36-run-contract.mjs`
- `apps/host/server/native-control.mjs`
- `apps/host/tests/q36-progress.test.mjs`
- `apps/host/tests/q36-run-contract.test.mjs`

## 実行コマンド

```powershell
node --test tests/q36-progress.test.mjs tests/q36-run-contract.test.mjs tests/q36-capabilities.test.mjs tests/resource-ram.test.mjs
```

## テスト・検証結果

- 上記 node --test: 最終再実行の progress は 2 pass。その前の一式は admission の余裕計算を直す前に 19 pass / 1 fail。直し後の progress は 2 pass。
- CUDA コンパイル: NOT_RUN
- NSIS、上書きインストール、リリース、GUI: NOT_RUN

## 残留リスク

- 空き物理RAMは commit headroom ではない。ページファイルがあれば OS は確保できることがある。拒否は「載らない起動を避ける」側。
- 段階の経過ミリ秒は各段階の steady clock であり、プロセス開始からの単一時計ではない。
- GEMM probe は prefill 終了と decode 開始の間にあり、独立段階としては出していない。

## 次の推奨アクション

1. T05 の opt-in mapped expert store（既定は legacy）。
2. sm_120 のエンジン再ビルドと、Host を含む NSIS。
3. `/S /UPDATE` の上書きインストール、実測を NOT_RUN のまま書いた README、リリース。
