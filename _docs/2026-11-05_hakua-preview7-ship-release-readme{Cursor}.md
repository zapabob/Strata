# 2026-11-05 Hakua 0.4.0-preview.20261103.7 ship / release / README {Cursor}

## 概要

前エージェント（Ship build install release README）の resume 停滞から引き継ぎ、製品 `.7` の版上げ commit+push、NSIS setup 完成、上書き導入、`gh release create --latest=false`、README/HAKUA 正直化、docs commit+push まで完了。UpdateGoal complete はしない。

## 背景・要求

- Product `0.4.0-preview.20261103.7`、verify-release 済み
- Q36 digest `907341c7…`；`native-build.json` `cd235fdf…` はメタデータ
- 署名 CUDA `b5e4d525…` 非接触
- T04 KEEP_DEFAULT；T07 profile done；T06 BLOCKED；T08 refuse PASS / measured NOT_RUN；unsigned≠signed

## 前提・判断（CoT）

1. 版上げ未コミット差分を先に main へ載せる
2. 既存 cargo dir `H:\Strata\releases\hakua040-nsis-cargo-20261103-7` を再利用、`RUSTC_WRAPPER` 解除
3. 空の `Programs\Strata` への素の `/S` が exit 2 になる事象を観測。managed フォルダを空作成してから `/S` で INSTALL_EXIT=0
4. `/S /UPDATE` 再実行は exit -1 で Uninstall キーが消えたが、EXE ProductVersion は `.7` のまま → キーを修復
5. Goal complete 禁止

## 変更対象ファイル

- 版上げ: `VERSION`, packages, Cargo, `full_installer.nsi`, `PRODUCT_VERSION`, bump tool, `AGENTS.md`, `README.zh-CN.md`（途中）
- Docs: `README.md` / 七言語、`docs/HAKUA_RELEASE.md`, `docs/HAKUA_INSTALL.md`, `packaging/README.md`, `AGENTS.md`
- 本実装ログ

## 実装詳細

1. Commit `622517a0` `[Other] bump Hakua product to 0.4.0-preview.20261103.7` → push main
2. NSIS retry 完了: setup `113064953` bytes, SHA-256 `5e8b8fff82b6e63dea48bf5c1907950911700c9bf30673444e5d2489a87c0336`
3. 導入検証: DisplayVersion / ProductVersion `.7`；signed CUDA `b5e4d525…`；q36 side `907341c7…`
4. Release: https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.7 （setup + SHA256SUMS, `--latest=false`）
5. README/HAKUA を `.7` ハッシュ・T 状態で再書

## 実行コマンド

```powershell
git commit / git push origin main   # 622517a0
# CARGO_TARGET_DIR=H:\Strata\releases\hakua040-nsis-cargo-20261103-7 ; RUSTC_WRAPPER unset
tauri build --bundles nsis
setup /S   # after precreating managed folders
gh release create v0.4.0-preview.20261103.7 --latest=false ...
py -3 _docs/_tmp_sync_readme_7.py
```

## テスト・検証結果

| Item | Result |
|------|--------|
| verify-release | PASS（先行ログ） |
| Setup SHA/bytes | `5e8b8fff…` / 113064953 |
| `/S` fresh after folder prep | INSTALL_EXIT=0；DisplayVersion `.7` |
| signed `b5e4d525…` | untouched |
| q36 `907341c7…` | side-by-side 一致 |
| Release assets | setup + SHA256SUMS uploaded |
| `/S /UPDATE` 再実行 | EXIT=-1（キー消失→修復）。残留リスク |
| Goal complete | しない |

## 残留リスク

- 空ディレクトリへの素の `/S` が exit 2 になる再現条件が未解明（フォルダ事前作成で回避）
- `/S /UPDATE` が不安定（exit -1 / Uninstall キー消失）
- T06 BLOCKED；T07 kernel opt-in NOT_RUN；T08 measured FP16 NOT_RUN
- アプリ installer は CUDA 非同梱
- EU/zh README は機械同期；ネイティブレビューなし

## 次の推奨アクション

1. NSIS StrataRemove / fresh-install exit 2 を再現し修正
2. `/S /UPDATE` 安定化
3. UpdateGoal complete しない
