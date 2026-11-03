# Qwen3.6 unsigned help rebuild（mapped-live は引き続き BLOCKED）

- **日時**: 2026-11-04 05:15–05:22 JST（壁時計 `Get-Date` / UTC `2026-11-03T20:22:13Z`）
- **実装AI**: Cursor
- **GPU**: RTX 5060 Ti 16GB。速度主張なし。UpdateGoal complete しない。Hermes 未殺（DESIGN #6）。

## 概要

nvidia-smi 再確認で Hermes `llama-server` PID 22836/22944 が VRAM ~15.2 GiB を占有 → mapped-live 不可。代わりに現行 source（`--q36-expert-store` help 追記込み）で未署名 q36 Windows CUDA エンジンを差分ビルドし、`H:\Strata\releases\…` へ梱包、`0.4.0-q36-windows-x86_64-cuda-cuda13` のみ置換、allowlist / host 試験 / ドキュメント正直さを更新した。署名エンジンと GitHub latest は触っていない。

## 背景・要求

durable Q36 Hakua。force なし。偽速度なし。Hermes を殺さない。C: 逼迫時は H: へ build/cache。署名 `b5e4d525…` 非上書き。新 GitHub latest は作らない（フル NSIS+README 検証なし）。

## 前提・判断（CoT）

1. Hermes 消えていれば mapped-live 優先 → **棄却**: used 15178–15185 MiB / free ~873 MiB。
2. 再計測だけ → **棄却**: help 正直化の EXE 反映が残課題。
3. 署名コンポーネントを差し替え → **棄却**: q36 横置きのみ。
4. 新 preview リリース → **棄却**: verify+NSIS+README まで未実施。ローカル component + allowlist + docs で止める。

## 変更対象ファイル

- `apps/host/server/q36-run-contract.mjs` — digest `64226fde…` を allowlist に追加（旧維持）
- `apps/host/tests/q36-run-contract.test.mjs` — 同上
- `docs/HAKUA_RELEASE.md` / `packaging/README.md` / `_docs/q36-32gb16gb/{DESIGN,PACKAGE_README,計画書,NOTES-05-22-rebuild}`
- 本実装ログ
- 成果物（git 外）: `H:\Strata\releases\hakua040-q36-engine-20261104-help\`、`%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-…`、staged engine-bundle（gitignore）

## 実装詳細

- Build dir: `H:\Strata\releases\hakua040-native-sync-20261103`（VS2022 / CUDA 13.3 / sm_120 / `STRATA_NATIVE_EXPERTS=ON`）
- `native-build.json` を現 checkout source hash で再記録（spill baseline なし）
- `package_engine.py` → rename to `0.4.0-q36-…` → verify ok
- 旧 unsigned を `.bak-6fe11065` に退避してから robocopy 置換
- staged engine-bundle を同一 payload で同期（次インストーラ用ローカル一貫性；今回は NSIS しない）

## 実行コマンド

```text
nvidia-smi
cmake --build H:\Strata\releases\hakua040-native-sync-20261103 --config Release --target strata --target strata-q36 --parallel 2
py -3 packaging/package_engine.py ... --out H:\Strata\releases\hakua040-q36-engine-20261104-help
py -3 packaging/package_engine.py --verify ...\0.4.0-q36-windows-x86_64-cuda-cuda13
robocopy → %LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13
node --test tests/q36-*.test.mjs   # TMP/npm-cache on H:
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| Headroom | VRAM free ~873 MiB; H ~77.31; C ~15.47 |
| Hermes | 生存・未殺 |
| mapped-live | **BLOCKED** |
| `cmake --build` strata/strata-q36 | exit 0 |
| new `strata.exe` SHA-256 | `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7` |
| installed `--help` | `--q36-expert-store` 行あり |
| signed `b5e4d525…` | 前後とも一致 |
| package verify | ok |
| host q36 node tests | **19 pass / 0 fail** |
| invented speeds | false |
| new GitHub latest / NSIS | **not done** |
| goal complete | false |

## 残留リスク

- mapped-live は Hermes 解放待ち。
- 製品 `.5` setup EXE は旧 digest `6fe11065…` のまま。allowlist は新旧併記。
- spill guard は不合格のまま。
- C: 空きは変動する。大型 npm/NSIS は引き続き H: 優先。

## 次の推奨アクション

1. Hermes 終了後に `64226fde…` で NOTES-05-10/05-22 の mapped-pack live を1回だけ。
2. Q36_STARTUP + pin-pool 行を保存 → T03 restart → 正直な T04/T06。
3. 必要なら `.6` 相当のフル verify+NSIS+README のあと `--latest=false` でプレビュー出荷（今回は未実施）。
