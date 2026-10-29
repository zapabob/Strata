# 2026-10-29 Hakua enable marker restore{Cursor}

**完了時刻:** 2026-10-29T16:28+09:00（Tokyo）  
**実装AI:** Cursor  
**作業先:** `C:\Users\downl\Documents\ChatGPT\Strata`（branch `codex/strata-hakua-chatbot-20261027`）

草、バージョン上書きしたら Sidebar の Hakua が消えた件。コードは生きてるのにゲートだけ死んでた。仮説検証いこうぜ。

## 仮説検証（CoT）

| # | 仮説 | 結果 |
|---|------|------|
| H1 | Host コードから Hakua が消えた | **棄却** — `openHakuaChat` / `hakuaChatbot` / Sidebar / `hakua_harness` / `stopCancelledLoad` 残存 |
| H2 | `capabilities.hakuaChatbot` が false で UI が隠してる | **採用** — `hakuaChatbotEnabled()` が env も marker も無し |
| H3 | ROOT は install の `host/` | **採用** — `native-control.mjs` の `ROOT=…/server/..` → `<install>/host`。marker は `host/hakua-chatbot.enabled` |
| H4 | 配布 NSIS が marker を落としてる | **採用** — `Programs\Strata\host` に marker 無し。`tauri.conf.json` resources は dist/server/package.json のみで marker 未登録 |
| H5 | packaging allowlist はあるが必須でもコピーでもない | **採用** — `full_windows.py` は path 許可のみ、`required` 未追加、repo に marker ファイル無し |

## 根本原因（一行）

Hakua ゲートは `<install>/host/hakua-chatbot.enabled`（または `STRATA_HAKUA_CHATBOT`）依存なのに、Tauri resources / full package が marker を同梱せず、上書きインストールで消えた。

## 即時復旧（このマシン）

| 項目 | 値 |
|------|-----|
| 作成パス | `C:\Users\downl\AppData\Local\Programs\Strata\host\hakua-chatbot.enabled` |
| ROOT 期待 | `join(ROOT,'hakua-chatbot.enabled')` = 上記 |
| 他 proprietary marker | UI ゲートは本ファイルのみ。`hakua_harness` は config の `enabled` で別系統 |

**ユーザー作業:** Strata を一度終了して再起動（host 再読込で `capabilities.hakuaChatbot` が true になる）。

## 恒久修正（repo / packaging）

| ファイル | 変更 |
|----------|------|
| `apps/host/hakua-chatbot.enabled` | **新規** — Hakua fork default-on のソース marker |
| `apps/desktop/src-tauri/tauri.conf.json` | resources に `../../host/hakua-chatbot.enabled` → `host/hakua-chatbot.enabled` |
| `packaging/full_windows.py` | `required` に `programs/host/hakua-chatbot.enabled`（allowlist は既存） |
| `tests/terminal/test_full_windows.py` | fixture に marker を追加 |

次の Windows full / NSIS ビルドでは marker が必須同梱される。欠けると `full_windows` の manifest 検証が落ちる。

## 検証

| 項目 | 結果 |
|------|------|
| install marker 存在 | True（170 bytes） |
| repo marker 存在 | True |
| `_payload_name(...)` 許可 | `programs/host/hakua-chatbot.enabled` |
| `tauri.conf.json` resources | 登録済み |
| `pytest …::test_build_verify_zip_and_strict_membership` | **1 passed** |

未実施: 実アプリ再起動後の Sidebar 目視（host 再起動はユーザー側）、次ラウンドの実 NSIS 成果物ハッシュ確認。

## 残留リスク

1. 再起動前は UI に Hakua が出ない（マーカーはディスク済み）。
2. 旧インストーラ再実行で marker 無しパッケージに上書きすると再発 → 次ビルド以降で解消。
3. 上流 upstream 取り込み時に `tauri.conf.json` / `required` が戻ると再発しうる。merge 時に marker を守ること。

## 次の推奨

1. Strata 再起動 → Sidebar に Hakua が出るか確認  
2. 次の preview パッケージをビルドし、展開物に `host/hakua-chatbot.enabled` があることを manifest と実ファイルで確認  
3. 必要なら同内容を `main` へ取り込み（本作業は feature branch 上）

おわりだぜ。
