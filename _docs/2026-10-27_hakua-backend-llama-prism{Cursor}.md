# 2026-10-27 Hakua/Strata バックエンドを llama-prism b10826 に切替{Cursor}

実施時刻：2026-10-27 19:15 JST 前後。

## 概要

Hakua チャットボット（Strata Host の llama.cpp 推論経路）のバックエンドを、CUDA 13.3 の `llama-prism-b10826-c9c34bc` に切り替えた。

## 背景・要求

直前作業で Downloads の prism zip を llama-server として整備済み。今回はそのバイナリを Strata/Hakua 側のエンジン解決先にする。

## 前提・判断

- Host `supervisor.findBinary()` は優先順：`STRATA_LLAMA_SERVER` → `components/generic-gguf/active.json` → その他
- 旧 active は `0.3.2-preview.20261027.1`（build **10787**）
- 新 active は `prism-b10826-c9c34bc`（build **10826**, commit `c9c34bc9c`）
- **Hakua memory chat**（`/api/native/hakua-chat`）は引き続き **native Strata instance** 必須。今回の切替は llama.cpp / generic-gguf 経路
- 稼働中 Hermes 8080（Hikari via prism）は停止していない

## 変更対象

| 項目 | 内容 |
|------|------|
| `...\components\generic-gguf\prism-b10826-c9c34bc\` | prism bin 72+ BUILD.json を新規配置 |
| `...\components\generic-gguf\active.json` | folder → `prism-b10826-c9c34bc`（bak 作成） |
| User env `STRATA_LLAMA_SERVER` | 上記 `llama-server.exe` を指す |

## 検証

- `--version` → `0.2.0-dev (build 10826, commit c9c34bc9c)`
- `--list-devices` → RTX 5060 Ti
- `STRATA_LLAMA_SERVER` と active ポインタが同一 exe
- 8080 は引き続き prism + Hikari（未改変）
- strata-desktop は未起動（再起動後に新 env が効く）

## 残留リスク

- 既に起動中の Host があれば再起動が必要（User env は新規プロセスから）
- native `component:strata-engine` プロファイル（q2_0 等）は未変更
- memory harness 付き Hakua 試験は未実施

## 次の推奨アクション

- Strata / Hakua GUI を起動し直し、Engine 解決先が prism であることを UI/ログで確認
- GGUF を llama.cpp 経路でロードするスモーク
- memory 試験が必要なら native instance を別途用意
