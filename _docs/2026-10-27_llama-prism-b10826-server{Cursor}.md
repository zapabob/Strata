# 2026-10-27 llama-prism b10826 を llama-server に設定{Cursor}

実施時刻：2026-10-27 19:10 JST 前後。

## 概要

`Downloads\llama-prism-b10826-c9c34bc-bin-win-cuda-13.3-x64.zip` を展開し、llama-server として使う経路へ揃えた。

## 背景・要求

- zip を外して llama サーバーとして使う
- リビルド／上書きインストール相当の反映

## 前提・判断

- zip 内バイナリと既存の次の2箇所は **SHA-256 一致**（再コピー不要）
  - `C:\Users\downl\.hermes\llama\prism-b10826-c9c34bc\bin`
  - `C:\Users\downl\AppData\Local\Programs\llama-prism\bin`
- 稼働中プロセスも既に prism-b10826 を使用（停止不要）
- 問題は User env / `.hermes\.env` / PATH が turboquant を指したままだったこと

## 変更対象

- User env: `LLAMA_CPP_SERVER_EXE`, `HERMES_LLAMA_SERVER_EXE` → prism-b10826
- User PATH: prism bin を先頭へ
- `C:\Users\downl\.hermes\.env` の `HERMES_LLAMA_SERVER_EXE`（bak 作成）
- `Ensure-HermesGeneration.ps1` は既に prism-b10826 参照のため未改変

## 検証

- `llama-server --version` → `0.2.0-dev (build 10826, commit c9c34bc9c)`
- `--list-devices` → `CUDA0: NVIDIA GeForce RTX 5060 Ti`
- `http://127.0.0.1:8080/props` → Hikari PQ2_0 / n_ctx=98304 / slots=1
- 実行パス → `.hermes\llama\prism-b10826-c9c34bc\bin\llama-server.exe`

## 残留リスク

- 既存の開いているシェルは旧 PATH／env のまま。新規ターミナルで有効
- turboquant 本体は削除していない（ロールバック用に残置）
- ソースからの CUDA リビルドは未実施（配布 zip 採用）

## 次の推奨アクション

- 新規ターミナルで `where llama-server` が prism になること確認
- 必要なら turboquant PATH 残骸の整理
