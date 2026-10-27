# T1/T2 実装ログ：送信先固定とロード取消直列化

- 記録時刻（UTC）: 2026-10-27T13:09:05Z
- 作業ツリー: `H:\Strata\worktrees\hakua-chatbot-20261027`
- HEAD（着手時）: `bc450f46a0e9a120048b0e3b126a686c06d9cc67`
- ブランチ: `codex/strata-hakua-chatbot-20261027`
- 計画: `Strata_Hakua_Cursor_Implementation_Plan_20261027.md` の T0→T1/T2
- 実装AI: Cursor

## 概要

F01/F02（チャット送信の所有権すり替わり）と F03（キャンセルした古いロードが新しい ready を落とす）を RED→GREEN で直した。auto push なし。

## 背景・要求

- await をまたいで `state.remoteModel` / `activeWorkspace` / `activeSession` を再読しない
- queued-release の再送は owning session へ
- キャンセル済み load の遅延 start 完了が、ID/profile を再利用した新インスタンスを unload しない

## 前提・判断

- T0 ベースラインは `_docs/2026-10-27_t0-baseline-hakua-chatbot{Cursor}.md`
- Fork / run-config / Hakua キー分離は触っていない
- 性能デフォルト変更なし

## 変更対象ファイル

| ファイル | 内容 |
|---|---|
| `apps/host/src/lib/store.ts` | 送信スナップショット、`sessionId`/`workspaceId`/`remoteModel` 付き再送、`liveTurns.has` でキュー判定 |
| `apps/host/server/native-control.mjs` | `ownerJob`、`dropOwnedInstance`、`cancelling`、load cancel 時の所有 runtime 掃除、begin が cancelling 中は拒否 |
| `apps/host/tests/chat-turn-ownership.test.mjs` | F01/F02 RED→GREEN |
| `apps/host/tests/native-load-cancel.test.mjs` | F03 RED→GREEN |
| `apps/host/tests/no-model-chat.test.mjs` | ガード文言を previewRemote/previewModel に追従 |
| `_docs/2026-10-27_t0-baseline-hakua-chatbot{Cursor}.md` | T0 記録 |

## 実装詳細

### T1（F01/F02）

- 最初の await（履歴画像 / upload）より前に `turnRemote` / `turnWorkspace` / `turnModel` / prefs を固定
- `streamPost` 引数は await 済みの `history` / `imageIds` とスナップショットのみ
- `queued-release` は `{ text, workspaceId, remoteModel }` を session マップに保持し、`sendMessage(text, { sessionId, ... })` で再送
- 削除済み session への再送は破棄

### T2（F03）

- instance に `ownerJob`（job.id）
- キャンセル後の unload は `dropOwnedInstance` のみ（別 job が同じ id を所有していれば触らない）
- load の cancel は `cancelling` → 所有 instance を force unload → `cancelled`
- `begin` は `cancelling` 中の新規操作を拒否

## 実行コマンド

```text
node --test tests/chat-turn-ownership.test.mjs
node --test tests/native-load-cancel.test.mjs
node --test tests/native-control.test.mjs
node --test tests/no-model-chat.test.mjs tests/chat-turn-ownership.test.mjs tests/native-load-cancel.test.mjs tests/packaged-control.test.mjs
```

## テスト・検証結果

### 成功

- `chat-turn-ownership.test.mjs` … 2/2 pass（F01, F02）
- `native-load-cancel.test.mjs` … 1/1 pass（F03）
- `native-control.test.mjs` … 7/7 pass
- `no-model-chat.test.mjs` … pass（静的ガード + HTTP）
- `packaged-control.test.mjs` 含む一括 … **35 pass / 0 fail**

### 失敗

- なし（修正後）

### 未実行

- Windows GUI 実機でのチャット切替／ロード取消サイクル（目安10回）
- T3〜T9（設定保存分離、Stop/EOF、context budget、日本語記憶、計測、プロファイル、長時間運転）
- 全 `npm test`（apps/host 全ファイル）
- GPU 実測 before/after
- git commit / push（指示なしのため未実施）

## 残留リスク

- cancel と遅延 `control.start` の間に同一 profile 上で start が二重に完了し得る。unload の取りこぼし防止はできたが、孤児 runtime の完全保証は実機サイクル確認が必要
- composer 側の `state.streaming` UI 表示は activeSession 連動のまま（送信経路は `liveTurns` 基準に変更済み）
- VRAM/RAM 逼迫環境（T0 時点 free VRAM ~678 MiB）での実機ロード試験は未実施

## 次の推奨アクション

1. T3（READY と設定保存の分離 / F04・F05）へ RED から着手
2. 可能なら packaged 実機で load→cancel→reload を数サイクル
3. ユーザー指示があれば T1/T2 のみを小さな commit に分ける
