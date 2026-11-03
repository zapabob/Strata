# Qwen3.6 mapped-live BLOCKED + help honesty

- **日時**: 2026-11-04 05:10–05:15 JST
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。速度主張なし。UpdateGoal complete しない。Hermes 未殺（DESIGN #6）。

## 概要

VRAM は Hermes 占有のまま mapped-live 不可。再計測だけで終わらせず、(1) タイムスタンプ付きブロッカー証跡、(2) 古くなった H: FreeGB 表記の訂正、(3) `--help` が `--q36-expert-store` を省略していた正直さの穴を source で塞いだ。

## 背景・要求

durable Q36 32GB/16GB Hakua。force なし。偽速度なし。他アプリ推論を殺さない。製品 `.5` / pin-pool wire は既出荷。残りは mapped-live ログ・T03 restart・T04–T08。

## 前提・判断（CoT）

1. Hermes が消えていれば live → **棄却**: PID 22836/22944 生存、VRAM used 15182 MiB / free 869 MiB、util 96%。
2. H: ENOSPC が二次ブロッカー → **棄却**: FreeGB ~78.74（04:20 の 14.2 表記は stale）。
3. 再計測のみは禁止 → **採択**: help/ドキュメント正直さギャップを閉じる。
4. 今すぐ engine rebuild / component 上書き → **棄却**: 署名 `b5e4d525…` 非接触、unsigned live は VRAM 待ち。source のみ先行。

## 変更対象ファイル

- `src/program/generate.cpp` — usage に `--q36-expert-store`
- `include/strata/qwen35/engine.hpp` — 家族フラグ一覧に追記
- `src/qwen35/q36_engine.cu` — 誤引数時 usage に同フラグ
- `_docs/q36-32gb16gb/evidence-2026-11-04-mapped-live/*-05-10.*` / `NOTES-05-10.md`
- `_docs/q36-32gb16gb/{DESIGN,PACKAGE_README,evidence-summary,計画書,gui/NOTES}`
- 本実装ログ

## 実装詳細

- ブロッカー JSON / nvidia-smi / RAM / EXE ASCII markers / planned argv + 期待 stderr を NOTES-05-10 に固定。
- installed unsigned `6fe11065…` の `--help` はまだ省略のまま（正直に明記）。次回 q36 rebuild で反映。

## 実行コマンド

```text
nvidia-smi --query-gpu=...
Get-Process -Id 22836,22944
Get-FileHash ...0.4.0-q36...\strata.exe
strata.exe --help | Select-String q36
strata.exe --q36-expert-store mapped-pack   # → unknown argument (family switch 前)
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| Headroom | VRAM free 869 MiB; RAM free ~9.45 GiB; H ~78.74; C ~3.02 |
| Hermes | 生存・未殺 |
| mapped-live | BLOCKED |
| T03 chat/stop/restart | NOT_RUN |
| T04–T08 | NOT_RUN |
| help honesty (source) | 追記済み |
| help honesty (installed EXE) | 未反映（次回 rebuild） |
| invented speeds | false |
| goal complete | false |

## 残留リスク

- mapped-live は Hermes 解放待ち。
- source help と shipped EXE の差が一時的に残る。
- C: FreeGB ~3 は npm / 一時ファイルに注意。

## 次の推奨アクション

1. Hermes 終了後に unsigned `6fe11065…` で NOTES-05-10 の planned command を1回だけ実行。
2. Q36_STARTUP + `mapped-pack host pin pool` 行を cfg/stderr に保存 → T03 restart → 正直な T04/T06。
3. 余裕があれば help 修正込みの差分 rebuild を unsigned q36 component へ反映（署名エンジンは触らない）。
