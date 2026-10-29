# 2026-10-29 NSIS post-release path fix + publish (Cursor)

## 概要

`makensis` lzma 成功後の `post-nsis-release.ps1` が cargo-target 側の誤パスを見ていたため、
release ディレクトリ上の実 setup.exe を正本にするよう修正し、サイレント上書きインストール・
DisplayVersion 確認・tag push・GitHub Release アップロード・GH Pages 公開まで完走した。

## 背景・要求

- 製品版: `0.3.2-preview.20261029.2`（.1 へダウングレード禁止）
- 実体: `H:\Strata\releases\0.3.2-preview.20261029.2\Strata_0.3.2-preview.20261029.2_x64-setup.exe`
- サイズ: `117663238` bytes
- スクリプト誤期待: `H:\Strata\cargo-target\desktop\release\bundle\nsis\...`

## 前提・判断

- setup を cargo-target にコピーするより、release 直下を `$setupSrc` / `$setupDst` 正本にする方が正しい。
- レジストリ `InstallLocation` が引用符付き `"C:\..."` のため `Join-Path` が失敗 → Trim('"') を追加。
- `$ErrorActionPreference='Stop'` 下で `gh release view` の stderr が終了扱いになる → try/存在確認後 create/upload。

## 変更対象ファイル

- `H:\Strata\releases\0.3.2-preview.20261029.2\post-nsis-release.ps1`（リリース作業スクリプト）
- 本ログ: `_docs/2026-10-29_nsis-post-release_Cursor.md`

## 実装詳細

1. `$setupSrc` を release 直下の setup に変更（legacy cargo-target はフォールバックのみ）
2. InstallLocation の引用符除去
3. Release 既存時は `gh release upload --clobber` + notes 更新、無ければ `gh release create`
4. `tools/publish_gh_pages.ps1` は維持

## 実行コマンド

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "H:\Strata\releases\0.3.2-preview.20261029.2\post-nsis-release.ps1"
```

再実行ログ: `H:\Strata\releases\0.3.2-preview.20261029.2\post-nsis-release.run3.log`（EXIT 0）

## テスト・検証結果（証拠）

| 項目 | 結果 |
|------|------|
| setup size | `117663238` |
| SHA256 | `1CF23A43D92932164C672DA4EA0A949D2079E1F5548A7D956D2B660E7137EC30` |
| installer exit | `0` |
| DisplayVersion | `0.3.2-preview.20261029.2`（HKCU Uninstall Strata） |
| InstallLocation | `C:\Users\downl\AppData\Local\Programs\Strata` |
| marker | `True` → `...\host\hakua-chatbot.enabled` |
| tag local/remote | `v0.3.2-preview.20261029.2` → `c552dedea5fbeb5c37a7cb4965e0646ee175e1d4` |
| Release URL | https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261029.2 |
| asset | `Strata_0.3.2-preview.20261029.2_x64-setup.exe` size `117663238` |
| GH Pages push | `f5038bc3..4c1e9df7` → `gh-pages`（`[Docs] refresh Pages for 0.3.2-preview.20261029.2`） |
| live Pages | `https://zapabob.github.io/Strata/` status 200、本文に `0.3.2-preview.20261029.2` YES / `20261028.2` NO |
| README EN/JA/zh-CN | いずれも product / download / tag が `0.3.2-preview.20261029.2` |
| `VERSION` file | `0.3.2-preview.20261029.2` |
| `main` / `origin/main` | 同一 `c552dede` |

### 主要検証コマンド抜粋

```powershell
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' |
  Where-Object { $_.DisplayName -like 'Strata*' } |
  Select-Object DisplayName, DisplayVersion, InstallLocation
Test-Path 'C:\Users\downl\AppData\Local\Programs\Strata\host\hakua-chatbot.enabled'
git ls-remote --tags origin v0.3.2-preview.20261029.2
gh release view v0.3.2-preview.20261029.2 --repo zapabob/Strata
Invoke-WebRequest https://zapabob.github.io/Strata/ -UseBasicParsing
```

## 残留リスク / Goal 残ギャップ（親監査向け）

ハード証拠で揃ったもの: DisplayVersion / marker / tag push / Release asset / Pages live / README 同版 / main HEAD 同期。

軽微・非ブロッカー候補:

1. 作業ツリー dirty: `apps/desktop/src-tauri/Cargo.toml` で preview 用に `lto=false` / `codegen-units=16`（未コミット）。installer ビルド時のローカル調整であり、`origin/main` の VERSION/README とは別件。
2. README 一部文言に「planned tag / 予定タグ」が残存（リンク先バージョン自体は正しい）。
3. Goal「Hakua memory wiring already on main」は本スクリプトでは再検証していない（先行ログ `_docs/2026-10-29_hakua-hermes-soul-memory-wire{Cursor}.md` 等に依存）。親が配線コミットを再監査する場合はその証跡を参照。

**本エージェントは Goal 完了マークを付けない。** 親が上記ギャップ有無を最終判定すること。

## 次の推奨アクション

- 親 Goal 監査: wiring on main / DisplayVersion / Release / Pages を横断確認
- 必要なら README の「planned」文言を「published」に直す docs PR
- 必要なら preview LTO 無効を意図的にコミットするか、作業ツリーを破棄してクリーンにする
