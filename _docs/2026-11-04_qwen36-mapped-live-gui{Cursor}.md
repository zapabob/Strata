# Qwen3.6 mapped-live / GUI resume（VRAM blocked）

- **日時**: 2026-11-04 00:52–01:03 JST
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB（ユーザー環境）。速度主張なし。

## 概要

前エージェント（1595747a）停滞後を再開。Hermes `llama-server` が VRAM を占有したままなので mapped-pack live は **BLOCKED** のまま更新証跡を残し、フル GPU ロードなしで T03 GUI/API の private-cache 拒否を確定した。durable Q36 goal は完了にしない。

## 背景・要求

DESIGN 非交渉 #6（他アプリ推論 server を kill しない）と #4（private-cache 制約を外して成功扱いにしない）。予定コマンドは allowlisted unsigned `0.4.0-q36-...` + `--q36-expert-store mapped-pack --serve`。VRAM/RAM が空くまで実行しない。

## 前提・判断

- 再測定: used VRAM ≈15.4–15.6 GiB、free ≈0.5–0.7 GiB、free RAM しばしば <4 GiB。Hermes PID 22836 / 22944 存続。
- `hakua-chatbot.enabled` あり → packaged Qwen3.6 は privacyRequired で拒否される（意図どおり）。
- mapped-live（Q36_STARTUP / ExpertPinPool）は headroom 不足のため未実行。速度は捏造しない。

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/preflight-blocker.json`（再測定で更新）
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/nvidia-smi-recheck.txt`
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/ram-recheck.json`
- `_docs/q36-32gb16gb/evidence-2026-11-04-gui/*`（DisplayVersion・Models refuse UI・API）
- `_docs/q36-32gb16gb/evidence-summary.json`（正直な PARTIAL / BLOCKED）
- `_docs/2026-11-04_qwen36-mapped-live-gui{Cursor}.md`（本ログ）

コード変更なし。

## 実装詳細

1. nvidia-smi / RAM / process 再確認 → Hermes 維持、mapped-live ABORT。
2. Strata `.5` 起動済み確認（pid 15168）。`/api/setup` → `app.version=0.4.0-preview.20261103.5`。
3. GUI: dashboard（favorite Hf·PQ2_0）→ Models で `Qwen3.6-35B-A3B` / `UD-Q4_K_XL` 選択。赤帯拒否と再試行ボタンをスクショ。
4. API: `POST /api/native/operations` `kind=load` `model=qwen36-ud-q4_k_xl` → job `538f2458-…` state=error、同一文言。約9秒で終了、GPU ロードなし。Hermes 未殺。

## 実行コマンド

```text
nvidia-smi --query-gpu=...
Get-CimInstance Win32_OperatingSystem
Get-Process llama-server,strata-desktop,Hermes
Invoke-RestMethod http://127.0.0.1:47831/api/setup
Invoke-RestMethod .../api/native/plan  body family=qwen36 model=UD-Q4_K_XL
Invoke-RestMethod .../api/native/operations  body kind=load model=qwen36-ud-q4_k_xl
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| DisplayVersion `.5` | 確認（registry / FileVersion / API） |
| T03 GUI refuse | 確認（スクショ + API job） |
| mapped-live pin-pool log | BLOCKED（未実行） |
| T04 / T06 / T07 / T08 | NOT_RUN |
| Hermes kill | なし |
| 速度数値 | なし（捏造なし） |

## 監査表（本ターン）

| ID | 状態 | 証拠 |
|----|------|------|
| mapped-live | BLOCKED | `evidence-2026-11-04-mapped-live/preflight-blocker.json` |
| T03 GUI | PARTIAL | `evidence-2026-11-04-gui/` refuse UI。chat/stop/restart 未 |
| T04–T08 | NOT_RUN | 対計測なし |
| T09 | PARTIAL | `.5` + refuse UI。フル E2E 未 |

## 残留リスク

- chatbot 有効時は Qwen3.6 packaged 起動が拒否のまま（設計どおり）。mapped-pack の実機ログは別セッションで VRAM 空き後。
- GUI の GPU 名表示が誤読されやすい（実測は nvidia-smi の RTX 5060 Ti を正とする）。
- chat→stop→restart は headroom なしのため未実施。

## 次の推奨アクション

1. Hermes が自然終了／ユーザーが明示停止したあと、planned unsigned mapped-pack コマンドを1回だけ実行し cfg.log の Q36_STARTUP + ExpertPinPool を保存。
2. T04–T08 は対計測計画が揃うまで既定化しない。
3. durable Q36 goal は完了にしない。
