# 2026-11-05 Hakua 0.4.0-preview.20261103.7 ship finish {Composer}

## 概要

前 ship agent 停滞後の仕上げ。版上げ push → NSIS setup → gh release → DisplayVersion/exe 確認 → README/HAKUA 正直化。Goal complete しない。`Programs\Strata` の wipe/`rmdir` は禁止して修復。

## 背景・要求

- Product `0.4.0-preview.20261103.7`、verify-release PASS 済み
- Q36 digest `907341c7…`、native-build.json `cd235fdf…`、signed CUDA `b5e4d525…` 非接触
- commit+push → build → overwrite install → GitHub release → README
- STOP wiping install dir; exit 2 時は empty managed dirs + ONE `/S`

## 前提・判断（CoT）

1. 仮説: bare empty tree の `/S` は NSIS exit 2。検証: managed 空フォルダ precreate 後 `/S` で EXIT=0 を一度観測。
2. 仮説: InstallLocation が `%LOCALAPPDATA%\Programs\Strata` 固定。検証: 製造者キー復元で `H:\Programs\Strata-0.4.0-preview.20261103.7`。
3. 仮説: 同時 setup/`rmdir` がロック破壊。検証: leftover setup PID と不完全ツリーを観測。以後 wipe 禁止。
4. README は別コミット `03190c98` で `.7` 済み。本作業は HAKUA silent-install 注記と実装ログ。

## 変更対象ファイル

- `docs/HAKUA_RELEASE.md` / `docs/HAKUA_INSTALL.md`（silent-install precreate・InstallLocation 正直化）
- 先行: `622517a0` version bump、`03190c98` README rewrite
- 本実装ログ

## 実装詳細

1. Version bump commit+push `622517a0`
2. NSIS: `CARGO_TARGET_DIR=H:\Strata\releases\hakua040-nsis-cargo-20261103-7`、`RUSTC_WRAPPER` unset
3. Setup SHA-256 `5e8b8fff…` / 113064953 bytes → `gh release create v0.4.0-preview.20261103.7 --latest=false`
4. Install repair: precreate managed dirs、ONE `/S`、DisplayVersion `.7`、exe ProductVersion `.7`
5. node 欠落時は cargo `release\node` を robocopy `/E`（親 wipe なし）
6. HAKUA に exit 2 / precreate / no-wipe を記録

## 実行コマンド

```powershell
git push origin main   # 622517a0, 03190c98
# tauri build --bundles nsis (RUSTC_WRAPPER unset)
Get-FileHash ...\Strata_0.4.0-preview.20261103.7_x64-setup.exe
gh release create v0.4.0-preview.20261103.7 --latest=false --repo zapabob/Strata ...
# precreate managed folders; ONE /S; no rmdir
```

## テスト・検証結果

| Item | Result |
|------|--------|
| verify-release | PASS（Hakua `.7`, engine 0.4.0） |
| Setup | 113064953 bytes; SHA-256 `5e8b8fff82b6e63dea48bf5c1907950911700c9bf30673444e5d2489a87c0336` |
| gh release | https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.7 ; assets setup+SHA256SUMS; Latest は `.20261101.1` |
| DisplayVersion | `0.4.0-preview.20261103.7` |
| exe | present; ProductVersion `.7`; SHA-256 `58426441dcd64fddcbca565d64f59841cbedcb8c972c8dd7b44d294071010b4a` |
| signed `b5e4d525…` | untouched |
| q36 side `907341c7…` | present |
| `/S /UPDATE` after races | NOT relied on (exit -1/2 observed); do not wipe |
| Goal complete | false |

## 残留リスク

- InstallLocation が H: 版パス。Local leftover 空ツリーは未削除（意図的）
- 追加 `/S` が DisplayVersion を瞬間的に `.6` に戻した例あり（レジストリ手直しで `.7` に復帰）
- Private Node は robocopy 補完。再 `/S` 乱打は禁止
- T06 BLOCKED; T08 measured FP16 NOT_RUN; spill guard 不合格のまま
- unsigned ≠ signed

## 次の推奨アクション

1. InstallLocation を通常の `%LOCALAPPDATA%\Programs\Strata` に戻すなら、wipe せず計画的な一度きりの移行
2. NSIS exit 2 / empty-tree を upstream マクロで恒久修正
3. UpdateGoal complete しない
