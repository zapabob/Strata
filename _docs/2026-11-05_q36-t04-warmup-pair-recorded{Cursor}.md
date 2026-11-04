# 2026-11-05_q36-t04-warmup-pair-recorded{Cursor}

## 概要

Q36 mapped-pack T04（warmup vs `--no-warmup`）ペア計測を引き継ぎ監視し、`PAIR_RECORDED` まで完走。NOTES / evidence-summary / 本実装ログを確定し main に push。

## 背景・要求

- Prior monitor agent `7b40159f` が stall。terminal `756900.txt` の `py -3 t04_warmup_cost_pair.py`（23:20 開始）を継続監視。
- armA は既に PASS（partial `t04-report.json`）。armB pid 41008 を READY+gens まで待つ。Hermes は殺さない。UpdateGoal complete しない。

## 前提・判断

- CoT: armB stderr 沈黙は `expert_host_alloc` 中の正常パターン（armA も同様）。WS 増加・VRAM 占有を進行証拠として WAIT を選択。abort せず。
- 完了時刻（ローカル）: 2026-11-05 00:16:57+09:00（report `ended_at`）。シェル確認日時: 2026-11-05 00:18:30 +09:00。

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-23-20-t04/`（計測成果物）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t04_warmup_cost_pair.py`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-23-20.md`
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/2026-11-05_q36-t04-warmup-pair-recorded{Cursor}.md`（本ファイル）
- 関連: `nvidia-smi-*-23-18.*`（起動前ゲート証拠）

意図的に除外: `_docs/intake/`、`_docs/2026-11-02_qwen36-engine-died-host-experts{Cursor}.md`

## 実装詳細

1. PID 26832 / 41008 生存確認 → armB 進捗ポーリング。
2. 端末 footer で `PAIR_RECORDED` + `exit_code: 0` を確認。
3. NOTES に正直な解釈を記載: READY は armB の方が遅い（expert_host_alloc 分散）。READY→first T は +20.5 s（コスト移動）。
4. evidence-summary の `plan_execution_status` / session ブロックを更新。goal_complete は false のまま。

## 実行コマンド

```text
Get-Process -Id 26832,41008
# poll armB logs / nvidia-smi
# (pair script already running in terminal 756900)
```

## テスト・検証結果

| Check | Result |
|-------|--------|
| Pair result | **PAIR_RECORDED** |
| armA / armB | PASS / PASS |
| Hermes killed | false |
| Invented speeds | false |
| Goal complete | false |

Key timings: armA load→READY 1480524 ms; armB 1705414 ms; READY→first T 13603.8 → 34108.1 ms (+20504.3).

## 残留リスク

- T06–T08 未実施。READY デルタはホスト alloc ノイズ大。
- 1 ペアのみ — 採用判断禁止（report `adoption: NOT_DECIDED`）。

## 次の推奨アクション

- T06–T08 は別ゲート（VRAM≥12 GiB、Hermes 非殺）で計画。必要なら同日リピートで stage 正規化。
- 製品デフォルトは触らない。

## 追記（親からの進捗確認 00:21+）

- `9b56549a` は T03 完了済み（`turn_ended` success）。再起動不要。
- T04 shell `756900` は `PAIR_RECORDED` / exit 0 で完了済みを再確認。strata 残骸なし、free ~14820 MiB。
- T06 は engine 候補+RED 前提のため本 turn では起動しない。
