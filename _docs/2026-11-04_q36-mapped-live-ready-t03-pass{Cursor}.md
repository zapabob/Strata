# Q36 mapped-live READY + T03 PASS（ship deferred）

- **日時**: 2026-11-04 21:01–22:55 JST（壁時計 `Get-Date` / UTC `2026-11-04T13:55:14Z`）
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。T04 合格速度は主張しない。UpdateGoal complete しない。Hermes 未殺（DESIGN #6）。

## 概要

ターン開始時は VRAM free ~264 MiB で ship 候補だったが、再計測で free ~14972 MiB・`llama-server` 消滅を確認し **live ルート**へ切替。durable launcher で mapped-pack pin-pool と READY を取得。続けて T03 chat→stop→restart を **PASS**。製品 next-preview 出荷は本ターン deferred。

## 背景・要求

durable Q36 Hakua。force なし。偽速度なし。Hermes 無断殺禁止。mapped-live 優先、だめなら ship。Goal complete しない。

## 前提・判断（CoT）

1. 21:01 free 264 → ship — **棄却**: 直後 free ≥12000 で live が本命。
2. Hermes desktop を殺して VRAM 空ける — **棄却**: DESIGN #6。llama-server は既に消えていた。
3. STOP だけで serve 終了 — **棄却**: protocol は STOP=生成停止。stdin EOF が必要（スクリプト修正）。
4. Cursor 付きシェルで長時間 load — **棄却傾向**: ~6 分で wrapper が死ぬ事例あり。launch2 成功は `Start-Process` デタッチ。

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-21-05.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t03_chat_stop_restart.py`（STOP+stdin close）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t03_launch2_only.py`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-21-05*` / `run-21-05-t03*`（証跡）
- `_docs/q36-32gb16gb/{DESIGN,PACKAGE_README,evidence-summary}.json/md`
- 本実装ログ

## 実装詳細

- digest `64226fde…` 検証、署名 `b5e4d525…` 非接触。
- `launch_mapped_live_durable.py` → `run-21-05` → pin-pool `cudaHostAlloc 32 MiB x2` → `READY 65536 stop`。
- T03: launch1 GEN/DONE PASS; launch2 detached READY PASS; report `result=PASS`。

## 実行コマンド

```text
nvidia-smi …
py -3 …/launch_mapped_live_durable.py --out-dir …/run-21-05
py -3 …/t03_chat_stop_restart.py
Start-Process py -ArgumentList '-3','t03_launch2_only.py' …   # detached
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| Path | **live**（ship deferred） |
| mapped-live pin-pool | **PASS** |
| mapped-live READY | **PASS** |
| T03 | **PASS** (`t03-report.json`) |
| T04–T08 | **NOT_RUN** |
| invented speeds | false |
| Hermes killed | false |
| goal complete | false |
| signed engine overwritten | false |

## 残留リスク

- expert_host_alloc は RAM thrash で 15–20 分級になり得る（32GB 機）。
- Cursor 対話シェルの長寿命子プロセスはデタッチ必須。
- T04 paired speed / GUI E2E / next installer（`64226fde` 製品同梱）は未実施。

## 次の推奨アクション

1. T04/T06 は対計測計画を立ててから（本ログの DONE tok/s を既定速度にしない）。
2. 余裕があれば `0.4.0-preview.20261104.1` に help-honesty EXE を乗せて `--latest=false` 出荷。
3. durable goal は完了にしない。
