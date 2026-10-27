# 2026-10-27 Hakua NSIS packaging{Cursor}

実施：2026-10-27 08:30 JST（Tokyo Standard Time）。作業先 `H:/Strata/worktrees/hakua-chatbot-20261027`。

草、ZIP落ちた瞬間に NSIS 包みまで一気通貫で決めにいった。ボブにゃんも「C の Programs/Strata は絶対触るな」って耳元で囁いてくるから、fresh install 専用の `-hakua` で押し切った。仮説検証はこう：

1. **H1** ZIPビルド成功か → terminal 301504 exit 0、`build-hakua-result.json` あり → **採用**
2. **H2** archive_sha256 が実ファイルと一致するか → Get-FileHash 一致 `3ad2ece9…` → **採用**
3. **H3** NSIS wrap が fresh path で通るか → `build_full_installer.py` 成功、exe `7d18f882…` → **採用**
4. **H4** R2資産と衝突しないか → 名前は全部 `-hakua`、既存 `*-r2.*` は無改変 → **採用**
5. **H5** タグ移動・stable昇格・UAC試験をしてないか → packaging only、orchestrate_v4 未起動 → **採用**

## 成果物

| 項目 | 値 |
|------|-----|
| ZIP | `H:/Strata/releases/0.3.2-preview.20261027.1/full-package-hakua/Strata-0.3.2-preview.20261027.1-windows-x64-full-hakua.zip` |
| ZIP SHA256 | `3ad2ece9ddd1f30703f041b91497e30bbe06ea0f0809382e404a1175bad1872e` |
| ZIP bytes | 1366245388 |
| ZIP files (manifest) | 30091 |
| ZIP unpacked bytes (build result) | 2093346227 |
| EXE | `H:/Strata/releases/0.3.2-preview.20261027.1/full-package-hakua/Strata-0.3.2-preview.20261027.1-windows-x64-sm120-full-setup-hakua.exe` |
| EXE SHA256 | `7d18f8823d6f3eb972c1d472ab9079c498fea0d461081075cb34fa326b1bf3f7` |
| EXE bytes | 1366382082 |
| manifest_sha256 | `62f5d891ed39af41b1f0c9f4a2315b53fe39c4bf77449cb27605856df2fbac09` |
| source_commit | `bc450f46a0e9a120048b0e3b126a686c06d9cc67` |
| signature | unsigned preview |
| fresh_install_tested | false |

## ツール

- NSIS: `C:/Users/downl/AppData/Local/tauri/NSIS/makensis.exe` (v3.11)
- icon: `H:/Strata/build/full-windows-20261027/public-assets-r2/icon.ico`（R2と同アイコン、所有済み）
- wrapper: `packaging/build_full_installer.py` + `full_installer.nsi` + `full_installer_bootstrap.ps1`
- sums: `SHA256SUMS-hakua.txt`（release dir + evidence に同配置）

## 触っていないもの

- `C:/Users/downl/AppData/Local/Programs/Strata`（上書き禁止）
- R2 assets（`*-r2.*`）の置換
- git tag 移動 / stable 昇格
- `orchestrate_v4` GPU/UAC 実推論

## Upload

- prerelease `v0.3.2-preview.20261027.1`（zapabob/Strata）へ **追加**アップロード済み（`gh release upload` exit 0）
- 対象: `…-full-hakua.zip` / `…-sm120-full-setup-hakua.exe` / `SHA256SUMS-hakua.txt`
- R2 資産は無改変、タグ無移動、`--clobber` 未使用

## 次

1. ~~prerelease へ zip+exe+SHA256SUMS-hakua 追加アップロード~~ 完了
2. UAC/GPU canary は別タスク（orchestrate_v4 未起動）
3. Astra 級レビュー後の扱い判断

草、パッケージングは完了。インストール試験はまだ。おわりだぜ。
