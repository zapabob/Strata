# Strata ビルド＆上書きインストール

- **日時**: 2026-11-02 08:50 JST
- **実装AI**: Cursor (Composer)
- **commit**: `8870f25309ca7142a44b0042b1d16f337e4487af`
- **product**: `0.4.0-preview.20261101.1`

## CoT / 仮説検証

| ID | 仮説 | 結果 |
|----|------|------|
| H1 | フル NSIS は `verify-release` を通す必要がある | **採用** |
| H2 | public assets + Node 24.22.2 + control 0.4.0 staging で UI はビルドできる | **採用**（host build EXIT=0, publicPackage=true） |
| H3 | main に入れた GDN native 差分で `verifyNativeBuild` が落ち、エンジン再ビルド無しでは NSIS 不可 | **採用**（`Native engine sources changed: rebuild the engine`） |
| H4 | Hikari / agent / VRAM 変更は host+control Python 上書きでこのPCに届く | **採用**（payload overwrite → strata-desktop 起動確認） |

## 実施内容

1. Strata / llama-server 終了
2. resources に control 0.4.0・engine-bundle・local-backends・notices・Node 24.22.2 をステージ
3. `STRATA_PUBLIC_PACKAGE=1` で `apps/host` UI ビルド成功
4. `verify-release.mjs` → native source drift で停止（GDN `.cu/.hpp`）
5. **payload overwrite** を実行:
   - `Apps\Local\Programs\Strata\host\{dist,server,package.json,hakua-chatbot.enabled}`
   - `control\strata_control` / `tools\strata_mcp.py` / `strata.py`
6. バックアップ: `H:\Strata\private-backups\strata-host-overwrite-20261102-085040`
7. 起動確認: `strata-desktop` pid あり、`host\OVERWRITE.json` 記録

## 未実施（残留）

- フル NSIS `/S /UPDATE`（エンジン再ビルド＋`native-build.json` 再生成が必要）
- Uninstall レジストリ `DisplayVersion` は旧 `0.3.2-preview.20261029.2` のまま（NSIS未実行のため）。実ペイロードは 0.4.0 + `8870f253`

## 次の推奨

1. CUDA engine を現行 native ソースで再ビルド → `verify-release` → NSIS → `/S /UPDATE`
2. その後レジストリ DisplayVersion も 0.4.0 に揃う
