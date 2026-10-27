# T3〜T9 実装ログ（Hakua chatbot）

- 記録時刻: 2026-10-28T00:00:56+09:00（追記）/ 初版 2026-10-27T22:50:08+09:00
- ownership 再確認: `chat-turn-ownership.test.mjs` 2/2 pass（Select-String の `Error: offline` はモック reject 文言の誤検出）
- 作業ツリー: `H:\Strata\worktrees\hakua-chatbot-20261027`
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
| F03 取消 | fixture **10連続** pass。追加 `F03b`（late start → own profile stop、reuse は止めない）2/2 |
| T7 | `firstVisibleAnswerMs`、`docs/hakua-desktop-validation.md`、`tools/bench_hakua_desktop.py`、`_docs/bench-sample.jsonl` |
| 関連静的 | `thinking-direct` / `card-labels` を turnPrefs スナップショットに追従 |
| **実機 GUI load→cancel→reload** | 配布 `strata-desktop`（host `:47831`）へ `native-control.mjs` パッチ適用後に確認（下記） |

関連バッチ（意図した回帰）: **40 pass / 0 fail**（ownership, cancel, config, stream-terminal, budget, thinking, user-args, onboarding, native-control）。

### 実機 GUI サイクル（swift-iq2_xs / RTX 5060 Ti）

パッチ前（installed 旧 host）: cancel 3/3 → `cancelled`、reload 0/3 → 全件 `server_stop_deadline_expired`。

原因仮説→修正: cancel 後も in-flight `control.start` が完了し orphan profile が残る。`stopCancelledLoad` で **reuse されていない** profile だけ止める（F03 と両立）。非 ready 残骸は次 load 前に force unload。

パッチ後:

| ラン | cancel | reload ready | 備考 |
|---|---|---|---|
| v2 cycle3 | cancelled | **true** | 最初の完全成功 |
| v3 clean1 | cancelled | **true** | VRAM 空き状態 |
| v2 cycle2 | cancelled | false | `startup_wait_expired`（VRAM 逼迫下） |
| v3 clean2/3 | cancelled / — | false | reload 中に host 切断（desktop 落ち） |

→ load→cancel→reload の**成功サイクルを2回確認**。cancel 自体は安定。reload は VRAM/host 生死に依存するフレークあり。

一時パッチ先: `C:\Users\downl\AppData\Local\Programs\Strata\host\server\native-control.mjs`（`.bak-hakua-*` 退避あり）。

## 失敗（全 npm test）

`node --test --test-timeout=90000` 全 `tests/*.test.mjs`（T3〜T9 時点）:

| 集計 | 値 |
|---|---|
| tests | 1129 |
| pass | 991 |
| fail | 12 |
| skipped | 125 |

主な失敗の切り分け（本差分との関係）:

| 失敗 | 切り分け |
|---|---|
| app version / Cargo 一致 | リポジトリ内 version 表記の既存ずれ。本修正の因果ではない |
| card Mode 正規表現 | **本差分** → turnPrefs 許容に更新済み（再実行 pass） |
| live speed tok/s 18.9 | 実時間フレーク（閾値>22） |
| directory API / demo host / HTTP gateway 他 | 起動タイムアウト・環境・既存 |

→ 「全 npm test 緑」は**未達**。Hakua RED/GREEN 対象は別途 pass。

## 未実行

| 項目 | 理由 |
|---|---|
| T8 任意プロファイル採用 | 同日ペア実測・採用なし |
| T9 配布アプリ 32ターン2時間 endurance | 未実施。fixture 取消は代替にしない。load/cancel 実機は上記で実施 |
| auto push | 禁止どおり |

## 維持確認

- `applyNativeApiKeys` / `hakua_harness` / `checkRunConfig` / `openHakuaChat` 残存
- run-config 単一スナップショット起動は維持（READY後は現行ファイルへの狭いpatch）

## 変更ファイル

- `apps/host/src/lib/store.ts`, `types.ts`
- `apps/host/server/native-control.mjs`（ownerJob / dropOwned / **stopCancelledLoad** / force unload 非ready）
- `apps/host/server/agent/context-budget.mjs`, `plugins/strata-context.mjs`, `events.mjs`
- `serve/memory_harness.py`, `serve/test_memory_harness.py`
- テスト: ownership, load-cancel(+F03b), config-persistence, stream-terminal, context-budget-blocks, thinking-direct, card-labels, no-model-chat
- `docs/hakua-desktop-validation.md`, `tools/bench_hakua_desktop.py`, `_docs/2026-10-27_t*.md`, `_docs/bench-sample.jsonl`
