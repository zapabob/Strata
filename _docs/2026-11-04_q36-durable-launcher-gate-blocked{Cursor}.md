# 2026-11-04 Q36 durable launcher gate BLOCKED {Cursor}

## 概要

Q36 mapped-live 引き継ぎを継続。未コミット durable launcher（OS ファイルリダイレクト＋stdin babysitter）をレビュー・`py_compile`・コミットし、VRAM ゲートを実測したところ **BLOCKED**（free ~331 MiB < 12000）。Hermes は殺していない。Goal complete にしていない。

## 背景・要求

- 引き継ぎ: `_docs/2026-11-04_qwen36-handover-plan{Cursor}.md`（`b331b258`）
- 18:14 PIPE abort 再発防止の launcher 改修を完成させコミット
- free VRAM 十分なら mapped-live；不足ならタイムスタンプ付き証跡のみ
- DESIGN #6 / 偽速度禁止 / UpdateGoal complete 禁止

## 前提・判断

- ゲート下限 12000 MiB（ランチャー既定）を維持
- 署名済み `b5e4d525…` 非接触；未署名期待 digest `64226fde…` を検証済み
- intake / engine-died はコミット skip

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py`（`f4504a3d`）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-20-56.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-20-56-gate/`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-*-20-56.*`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/ram-recheck-20-56.json`
- `_docs/q36-32gb16gb/evidence-summary.json`
- 本実装ログ

## 実装詳細

1. launcher 差分レビュー: PIPE+tee → Popen の OS ファイル stdout/stderr、stdin keepalive スレッド、マーカーはログ tail、timeout 後も既定で babysit 継続。
2. `py -3 -m py_compile` 成功後、launcher のみコミット。
3. `nvidia-smi` / RAM 実測 → free VRAM 164–331 MiB。
4. durable launcher 実行 → exit **4** BLOCKED。子プロセス未起動のため Q36_STARTUP / pin-pool なし。
5. T03 / T04 / T06 は serve 未成立のため NOT_RUN。

## 実行コマンド

```text
py -3 -m py_compile _docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/launch_mapped_live_durable.py
Get-FileHash …\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe  → 64226fde…
nvidia-smi --query-gpu=… --format=csv
py -3 …/launch_mapped_live_durable.py --out-dir …/run-20-56-gate
git push origin main   # no force
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| py_compile | PASS |
| unsigned digest | `64226fde…` MATCH |
| gate | exit 4 BLOCKED（free 331 MiB） |
| Hermes killed | false（PIDs 3108 / 19816 生存） |
| mapped-live READY | NOT_RUN |
| invented speeds | false |

## 残留リスク

- Hermes VRAM 占有が続く限り live / T03–T08 は進まない
- launcher の OS ファイル経路はゲート通過後の初回 live で未実証（今回は起動前拒否）
- コミット `f4504a3d` のメッセージ末尾に PowerShell heredoc 由来の余分な `EOF` 行が残存（機能影響なし）

## 次の推奨アクション

1. ユーザーが Hermes を止めるか自然終了を待つ（無断 kill 禁止）
2. free ≥ 12000 MiB で durable launcher 再実行し Q36_STARTUP + pin-pool をファイル捕捉
3. READY 後 T03 → paired T04/T06
4. Goal は完了条件揃うまで complete にしない
