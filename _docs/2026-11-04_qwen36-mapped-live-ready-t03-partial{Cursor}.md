# Q36 mapped-live READY + T03 PARTIAL

- **日時**: 2026-11-04 21:04–22:18 JST（壁時計 `Get-Date` / UTC `2026-11-04T13:18:02Z`）
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。偽速度なし。UpdateGoal complete しない。Hermes 未殺（DESIGN #6）。

## 概要

ユーザーが VRAM を空けたため出荷ルートを中断し、nvidia-smi 再測定 → durable mapped-live を実行。`64226fde…` で **READY** と pin-pool 行を取得。続けて T03 GEN は成功、再起動は `warmup_prefill` で `0xC0000409` により失敗。インストーラ出荷は deferred。

## 背景・要求

durable Q36 Hakua。force なし。偽速度なし。Hermes 無断殺禁止。mapped-live を優先し、成功または新ゲート失敗のあとにのみ ship 再開。

## 前提・判断（CoT）

1. free ≥ 12000 → live 優先 → **採用**（free ~14972 MiB、llama-server 不在）。
2. ship 継続 → **棄却**（ユーザー指示で出荷停止）。
3. Hermes desktop 残存を kill → **棄却**（DESIGN #6；llama-server は既に無い）。

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/NOTES-21-05.md`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-21-05/**`（live 証跡）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/run-21-05-t03/**`（T03）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/t03_chat_stop_restart.py`
- `_docs/q36-32gb16gb/{PACKAGE_README,DESIGN,evidence-summary,計画書}`
- 本実装ログ

## 実行コマンド

```text
nvidia-smi …
py -3 …/launch_mapped_live_durable.py --out-dir …/run-21-05
py -3 …/t03_chat_stop_restart.py
# launch2 restart half after STOP/EOF cleanup
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| Headroom preflight | free **14982 MiB** → GO |
| digest `64226fde…` | MATCH |
| pin-pool line | **PASS** `cudaHostAlloc 32 MiB x2 (64.00 MiB committed)` |
| mapped-live READY | **PASS** (`READY 65536 stop`) |
| T03 GEN | **PASS** (`DONE 7 …`) |
| T03 restart READY | **FAIL** exit `3221226505` / `0xC0000409` at warmup_prefill begin |
| T04–T08 | **NOT_RUN** |
| Hermes killed | **false** |
| invented speeds | **false** |
| goal complete | **false** |
| installer ship | **deferred** |

## 残留リスク

- T03 再起動クラッシュの根因未特定（fast-fail / stack buffer overrun 系コード）。
- serve は idle 時 `STOP` だけでは終了せず stdin EOF が必要（ドライバに反映）。
- 二重 launch が短時間発生した（重複 strata を停止；Hermes 非対象）。
- paired speed は未計測。

## 次の推奨アクション

1. restart クラッシュを `warmup_prefill` 境界で再現・診断（Compute Sanitizer / 最小 ctx は別 arm）。
2. T03 を STOP+EOF 固定ドライバで再試行。
3. T04/T06 は対測定なしに既定化しない。
4. live 安定後にのみ help-honesty EXE を次プレビューへ載せる。
