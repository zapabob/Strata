# Q36 mapped-live 部分ロード → Hermes 再ブロック

日時: 2026-11-04 18:12–18:22 JST  
実装AI: Cursor (Auto/Composer)

## 概要

durable Q36 32GB/16GB Hakua goal の続き。当初 VRAM 余裕ありで allowlisted 未署名 mapped-pack を起動し部分ロードまで進んだが、ログパイプ失敗で abort。Hermes Hikari が VRAM を保持したため pin-pool 証跡取得と T03/T04 は未実施。Goal complete にしない。

## 背景・要求

- 残り: mapped-live pin-pool ログ、T03 chat→stop→restart、T04–T08 paired
- DESIGN #6: Hermes/他推論を殺さない
- 偽速度禁止、UpdateGoal complete 禁止、force 禁止

## 前提・判断

- 18:13: used 865 / free ~15446 MiB → GO（旧 PID 22836/22944 は退出済み）
- Hermes PID 14572 は生存（Hikari PQ2_0 / n_ctx 98304）だが当時は総 VRAM 低使用
- digest `64226fde…` を検証して planned argv で起動
- stderr 未捕捉は証跡として不合格 → 自前 strata のみ停止して再試行準備
- abort 後 free ~5.4 GiB → 正直ゲート（12 GiB）未満で BLOCKED

## 変更対象ファイル

- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/*`（preflight/nvidia/ram/hermes/NOTES/run-*/launcher）
- `_docs/q36-32gb16gb/evidence-summary.json`
- `_docs/q36-32gb16gb/DESIGN.md`
- `_docs/q36-32gb16gb/PACKAGE_README.md`
- `_docs/q36-32gb16gb/Strata_Qwen36_Implementation_Plan_2026-11-02.md`
- `_docs/2026-11-04_qwen36-mapped-live-partial-then-blocked{Cursor}.md`（本ログ）

## 実装詳細

1. nvidia-smi / RAM 再測 → GO
2. `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-…\strata.exe` + mapped-pack --serve（PID 31184）
3. VRAM 865→15912 MiB まで上昇を monitor CSV で記録
4. ログ欠損判明 → 自前 strata のみ Stop-Process（Hermes 未殺）
5. Hermes `/props` で Hikari 27B / 98k ctx を確認
6. `launch_mapped_live_durable.py` 追加; ゲート dry-run exit 4
7. ステータス文書を BLOCKED / NOT_RUN / goal_complete=false に更新

## 実行コマンド

- `nvidia-smi` / RAM CIM
- unsigned mapped-pack serve（planned argv）
- `py -3 …/launch_mapped_live_durable.py`（ゲート）
- Hermes `http://127.0.0.1:8080/props|health|v1/models`（読取のみ）

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| digest 64226fde | PASS（Get-FileHash） |
| 部分ロード開始 | 観測（VRAM/WS） |
| Q36_STARTUP ファイル | FAIL / 未捕捉 |
| pin-pool 行 | FAIL / 未捕捉 |
| durable launcher gate | PASS exit 4 BLOCKED |
| T03 / T04–T08 | NOT_RUN |
| Hermes killed | false |

## 残留リスク

- Hermes が GPU を占有する限り mapped-live は再ブロック
- WDDM はプロセス別 VRAM を N/A 表示のため、占有量は合計と Hermes API から推定
- 部分ロード abort 後の共有メモリ高使用が残る可能性

## 次の推奨アクション

1. ユーザーが Hermes を明示停止するか自然終了後、`launch_mapped_live_durable.py` を1回実行
2. Q36_STARTUP + `mapped-pack host pin pool` を保存してから T03 → 正直な T04/T06
3. ship/README は測定正直が揃うまで延期
