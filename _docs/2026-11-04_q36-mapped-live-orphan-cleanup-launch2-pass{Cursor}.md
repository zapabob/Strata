# 2026-11-04 Q36 mapped-live orphan cleanup → launch2 PASS {Cursor}

## 概要

残骸の mapped-pack `strata.exe` / T03 babysitter を掃除したあと、T03 launch2 をクリーン再試行し **READY PASS** まで到達した。Hermes / llama-server は未接触。Goal complete は false のまま。

## 背景・要求

ユーザー確認: 「残骸掃除してから再試行や」。

- 先行 launch2 は pin-pool 後 `warmup_prefill` で exit `3221226505` (`0xC0000409`)、READY false。
- 別試行は PARTIAL で旧 strata PID 生存のまま開始していた。
- DESIGN #6: Hermes/他アプリの llama-server は殺さない。自前 orphan のみ。

## 前提・判断

- CoT 仮説: 残骸プロセスの VRAM/状態汚染が `warmup_prefill` クラッシュ原因。クリーン起動なら READY 到達する。
- 検証結果: 仮説一致。クリーン pid **37524** で warmup_prefill 完走 → READY。

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/cleanup_orphans.ps1`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/cleanup-killed-pids.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/preflight-go-cleanup-22-24.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-*-cleanup-22-24.*`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-*-after-launch2-pass-22-55.*`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-21-05.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-21-05-t03/launch2-ready.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-21-05-t03/t03-final-status.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-21-05-t03/t03-report.json`
- `_docs/q36-32gb16gb/PACKAGE_README.md`

## 実装詳細

### 1. 残骸特定とキル

| PID | Name | 判定 | 結果 |
|-----|------|------|------|
| 4024 | strata.exe | cmdline に `qwen36-UD-Q4` + `mapped-pack` | killed |
| 28188 | py.exe | `t03_launch2_only.py` | killed |
| 22204 | python.exe | 同上 | already_gone |

Hermes 系 python / Hermes.exe: **未接触**。

### 2. Headroom

- 掃除後: used **869 MiB** / free **15182 MiB**（gate ≥12000 → GO）
- 成功後 STOP: used **~903 MiB** / free **~15148 MiB**; strata 残存 0

### 3. launch2 クリーン再試行

- 開始: 2026-11-04T22:25:39+09:00, pid **37524**
- pin-pool: `cudaHostAlloc 32 MiB x2 (64.00 MiB committed)`
- expert_host_alloc end: **1219344 ms**
- warmup_prefill end: **334239 ms**（前回クラッシュ地点を通過）
- READY: `READY 65536 stop` @ 22:52:29+09:00
- STOP lifetime: STOP + stdin EOF → 正常終了（残骸なし）
- `t03-report.json` result: **PASS**

## 実行コマンド

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ...\cleanup_orphans.ps1
nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv
py -3 t03_launch2_only.py   # Q36_T03_READY_TIMEOUT_SEC=2400
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| orphan kill（自前のみ） | PASS |
| Hermes untouched | PASS (`hermes_killed: false`) |
| VRAM headroom ≥12000 | PASS (15182) |
| Q36_STARTUP + pin-pool | PASS |
| launch2 READY | PASS |
| STOP + EOF exit | PASS |
| T03 overall | PASS |
| UpdateGoal complete | **not done** (goal_complete false) |

## 残留リスク

- 前回の `0xC0000409` は残骸競合で再現しなかったが、同条件以外での再発は未証明。
- T04–T08 paired speed は未実施（偽速度なし）。
- 並行で別 `t03_launch2_only` が先に起動し、こちら側の Tee ラップ起動は一瞬 `BLOCKED_VRAM_BEFORE_RESTART` になった。成功したのは先に走ったクリーン babysitter（pid 37524）。

## 次の推奨アクション

- T04/T06 等は別セッションで、クリーン状態から計測。
- installer ship は live 証拠優先のまま deferred。
- Goal complete は人間確認後。
