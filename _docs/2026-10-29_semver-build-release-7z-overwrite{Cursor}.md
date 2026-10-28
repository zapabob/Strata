# 2026-10-29 semver-build-release-7z-overwrite {Cursor}

- **When**: 2026-10-28 22:42 → 2026-10-29 02:19 +09:00
- **Workspace**: `C:\Users\downl\Documents\ChatGPT\Strata` (verified git root)
- **Resume**: failed subagent `4434843e` — version bump + host build done; NSIS died on OOM / CFA
- **実装AI**: Cursor
- **なんJ風**: 「ページング枯渇と Controlled Folder Access に殴られつつも NSIS まで押し切ったで」

## CoT / 仮説検証

| ID | 仮説 | 結果 |
|----|------|------|
| H1 | tip は既に `0.3.2-preview.20261028.2` バンプ済 → 再バンプ不要 | **採用**（`134b88a4` + BOM `37ea87d3`、後続 docs で tip `06612efb`） |
| H2 | 失敗原因は `embed-resource` ではなく pagefile/OOM + CFA | **採用**（os error 1455 / rust_oom → Defender Id=1123 が build-script を遮断） |
| H3 | `CARGO_TARGET_DIR` を H に置き、LTO=false でメモリ節約 | **採用**（preview OK、署名無し） |
| H4 | npm list が tauri CLI でハング → shim | **採用** |
| H5 | companion `strata-desktop.exe` は makensis 後に target 側が変化し得る → NSIS 抽出物が正 | **採用**（installed / NSIS payload 一致） |

## Version / Git

| Item | Value |
|------|-------|
| Version | `0.3.2-preview.20261028.2` |
| Tip / tag commit | `06612efbdef6c472c325354d091517a99b5311a8` |
| Tag | `v0.3.2-preview.20261028.2` |
| Push | FF `main`（バンプ時点 `49a23d0b..37ea87d3`、その後 tip は docs で前進） / tag push OK |
| Force-push | **なし** |

## Build

| Stage | Result |
|-------|--------|
| `apps/host` `npm run build` | **PASS**（先行エージェント / dist 再利用） |
| Desktop resources | node/control/harness を H stage + junction |
| `tauri build --bundles nsis` | **PASS**（`CARGO_TARGET_DIR=H:\Strata\cargo-target\desktop`, LTO=false, jobs=1） |
| NSIS path | `H:\Strata\cargo-target\desktop\release\bundle\nsis\Strata_0.3.2-preview.20261028.2_x64-setup.exe` |
| NSIS size | 116030388 bytes (~110.66 MiB) |
| Signing | **unsigned** |

## Archive + SHA-256

Dir: `H:\Strata\releases\0.3.2-preview.20261028.2\`

| File | SHA-256 |
|------|---------|
| `Strata_0.3.2-preview.20261028.2_x64-setup.exe` | `F0CDD5D84F3FADA7E084E4AEC0F65B558793834F58E2FEAF9F89456D5A0604FD` |
| `strata-desktop.exe`（NSIS payload / installed） | `A9E1139C18B5A29D51C7800F5911357CE10B94D9E902E9B483B2B70B1F2EF869` |
| `Strata_0.3.2-preview.20261028.2_windows-x64-nsis.7z` | `DE23C3DAC6EEAFA86D7A3A51581ABD7700E08832ADF47DD023A1DBF953411351`（121841990 bytes） |

Companion: `SHA256SUMS.txt`

## GitHub Release

- URL: https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261028.2
- Prerelease: **yes**
- Assets: NSIS + 7z + SHA256SUMS（digest 一致確認済）

## Overwrite install

1. Quit `strata-desktop` if running
2. `Strata_0.3.2-preview.20261028.2_x64-setup.exe /S /UPDATE` → **exit 0** (~240.7 s)
3. Install: `C:\Users\downl\AppData\Local\Programs\Strata`
4. Registry: DisplayName=Strata, DisplayVersion=`0.3.2-preview.20261028.2`
5. Installed exe SHA-256 = NSIS payload = `A9E1139C…` → **MATCH**
6. User data kept: `%USERPROFILE%\.strata\models`, `%LOCALAPPDATA%\strata`, `%APPDATA%\strata`

## Notes / blockers cleared

- C: free が一時 ~6GB、H: は draft `0.3.2-preview.20261027.1` full-package (~30GB) 削除で確保
- Windows **Controlled Folder Access** が `build-script-build.exe` をブロック → cargo/rustc を許可後に通過
- Hakua / proprietary は触っていない（version + build/release/install のみ）
