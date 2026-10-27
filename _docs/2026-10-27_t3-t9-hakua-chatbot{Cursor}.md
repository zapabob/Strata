# T3〜T9 実装ログ（Hakua chatbot）

- 記録時刻: 2026-10-27T22:50:08+09:00
- ownership 再確認: `chat-turn-ownership.test.mjs` 2/2 pass（Select-String の `Error: offline` はモック reject 文言の誤検出）
- 作業ツリー: `H:\Strata\worktrees\hakua-chatbot-20261027`
- HEAD基点: `bc450f46`
- 実装AI: Cursor
- auto push: なし

## 成功

| 項目 | 証拠 |
|---|---|
| T3 F04/F05 | `native-config-persistence.test.mjs` 3/3。READYは**現行ディスク設定**へ狭いpatchのみ。保存失敗はREADY維持 |
| T4 F06/F07 | `chat-stream-terminal.test.mjs` 2/2 |
| T5 F08 | `context-budget-blocks.test.mjs` 2/2 + strata-context 同一fingerprint打ち切り |
| T6 F09 | `unittest` 日本語「コーヒー」+ 英語 coffee（repo root） |
| T1/T2 回帰 | ownership / load-cancel / user-args / native-onboarding 関連 pass |
| F03 取消 | fixture **10連続** pass |
| T7 | `firstVisibleAnswerMs`、`docs/hakua-desktop-validation.md`、`tools/bench_hakua_desktop.py`、`_docs/bench-sample.jsonl` |
| 関連静的 | `thinking-direct` / `card-labels` を turnPrefs スナップショットに追従 |

関連バッチ（意図した回帰）: **40 pass / 0 fail**（ownership, cancel, config, stream-terminal, budget, thinking, user-args, onboarding, native-control）。

## 失敗（全 npm test）

`node --test --test-timeout=90000` 全 `tests/*.test.mjs`:

| 集計 | 値 |
|---|---|
| tests | 1129 |
| pass | 991 |
| fail | 12 |
| skipped | 125 |

主な失敗の切り分け（本差分との関係）:

| 失敗 | 切り分け |
|---|---|
| app version / Cargo 一致 | リポジトリ内 version 表記の既存ずれ（0.3.0/0.3.1/preview）。本修正の因果ではない |
| card Mode 正規表現 | **本差分** → `card-labels.test.mjs` を turnPrefs 許容に更新済み（再実行 pass） |
| live speed tok/s 18.9 | `inference.mjs` 実時間フレーク（閾値>22）。events の firstVisible 追加とは別経路 |
| directory API / demo host / HTTP gateway / skill / file handover / spy download / native file/weights | 起動タイムアウト・環境・既存。本差分の load/store/memory 経路外 |

→ 「全 npm test 緑」は**未達**。製品失敗と環境失敗が混在。Hakua 計画の RED/GREEN 対象ケースは別途 pass。

## 未実行

| 項目 | 理由 |
|---|---|
| T8 任意プロファイル採用 | 同日ペア実測・採用なし。センサーサンプルのみ（VRAM free は時点により 1.2〜14 GiB） |
| T9 配布アプリ GUI 一連＋32ターン2時間 | 未実施。fixture 取消は代替にしない |
| 実機 GUI load→cancel→reload | strata-desktop プロセスは確認したが、自動化した実機サイクルは未実施 |
| auto push | 禁止どおり |

## 維持確認

- `applyNativeApiKeys` / `hakua_harness` / `checkRunConfig` / `openHakuaChat` 残存
- run-config 単一スナップショット起動は維持（READY後は現行ファイルへの狭いpatch）

## 変更ファイル

- `apps/host/src/lib/store.ts`, `types.ts`
- `apps/host/server/native-control.mjs`, `agent/context-budget.mjs`, `agent/plugins/strata-context.mjs`, `agent/events.mjs`
- `serve/memory_harness.py`, `serve/test_memory_harness.py`
- 新規/更新テスト多数（ownership, load-cancel, config-persistence, stream-terminal, context-budget-blocks, thinking-direct, card-labels, no-model-chat）
- `docs/hakua-desktop-validation.md`, `tools/bench_hakua_desktop.py`, `_docs/2026-10-27_t*.md`, `_docs/bench-sample.jsonl`
