# 2026-10-27 Hakua 認証プリフライト（第1工程）{Cursor}

実施時刻：2026-10-27 06:22 JST 前後。作業先：`H:/Strata/worktrees/hakua-chatbot-20261027`（基点 `3c3c8fd3…`）。

## 目的

引き継ぎ計画書第1工程：Native Control の利用者専用キー保持と、Python の GPU 起動前認証検証。GUI 入口・実モデル試験・既存 Strata 上書き・フルパッケージ公開は対象外。

## 変更要約

1. `serve/memory_harness.py` — `configure_harness()` を追加。`require_private_engine` + `from_config` + API キー必須を一箇所にまとめ、エンジン起動前に呼ぶ契約にした。
2. `serve/server.py` — 上記を `StrataEngine` 起動前に実行し、結果を後段の `svc.memory_harness` に再利用。二重構築しない。
3. `apps/host/server/native-control.mjs` — `applyNativeApiKeys()`。`hakua_harness.enabled` 時のみ principal キー（`key_env`）を保持し、異なる Host 専用キーを追加。既定パスは従来どおり単一 Host キー上書き。
4. `run-config-check.mjs` — `hakua_harness` を既知キーに追加。
5. 文書・試験 — `MEMORY_HARNESS.md` 追記、Python/Node 試験追加。

## CPU 試験結果

| 試験 | 結果 |
| --- | --- |
| `py -3 -m unittest serve.test_memory_harness -v` | 30 OK（symlink 2 サブケース skip） |
| `node --test apps/host/tests/native-api-keys.test.mjs` | 4 OK |
| `node --test apps/host/tests/native-gateway.test.mjs` | 2 OK（共有 Host キーでの記憶転送拒否維持） |
| `node --test apps/host/tests/packaged-control.test.mjs` | 28 OK（Hakua キー保持の packaged load 含む） |

GPU・8080 切替・C 上書き・個人ファイル操作は未実施。

## 合格条件との対応

- 偽キー／共有キー／不正 persona／root 重複／キャッシュ設定不良 → GPU 前に拒否
- Host 専用キーは memory principal に割り当てない
- Host gateway の `strata_memory` 拒否は既存試験で維持
- 既定（harness 無効）の単一キー上書きパスは不変

## 未実施（次工程）

- 第2工程：GUI 入口、hakua-memory wheel 同梱
- 第3工程：Watchdog 正規権限経路と一回の実モデル記憶試験
- 第4工程：既存 Strata 上書き
- 第5工程：フル setup 公開・README/Pages

## 併記：NSIS

`nsis-r2-handoff-status.json` 確認済み。`INSTALL_SUCCESS_RUNTIME_NOT_RUN`、exit 0、CPU smoke / 公開は未実施、C 側と 8080 は未改変。本工程では NSIS 成果物を触っていない。

## 注意

未コミット。独立レビューは未依頼。公開物・個人キー・DB は含めていない。
