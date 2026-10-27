# 2026-10-28 NSIS overwrite install + GitHub release attach {Cursor}

- **When**: 2026-10-28 00:33 +09:00
- **Workspace**: `H:\Strata\worktrees\hakua-chatbot-20261027`
- **Tip**: `origin/main` / HEAD `4cf0cf1ea3f0e97204d6171c6ed200236099fd7f`
- **Tag**: `v0.3.2-preview.20261027.2`
- **Goal**: overwrite-install + release asset + README 3 langs → **UpdateGoal complete**

## Artifact

| Item | Value |
|------|-------|
| NSIS path | `apps/desktop/src-tauri/target/release/bundle/nsis/Strata_0.3.2-preview.20261027.2_x64-setup.exe` |
| Size | 176610345 bytes (~168.4 MiB) |
| SHA-256 | `839029112EF655466BDC04E92E5A97325B3BA03E05B5F92F4DCB96D015E4A0DF` |
| Signed | **No** (expected; no keys on build PC) |

## Overwrite install

1. Quit `strata-desktop` if running; silent upgrade: `…setup.exe /S /UPDATE` (Tauri NSIS; exit 0).
2. Install location: `C:\Users\downl\AppData\Local\Programs\Strata`
3. Registry: DisplayName=Strata, DisplayVersion=`0.3.2-preview.20261027.2`
4. `strata-desktop.exe` SHA-256 matches release build binary:
   - built & installed: `9F81AE3EF247964FAA1CD29B258877E1BFE600D32672B407F09603D5E0F3156E` (size 9566208)
5. `host/server/native-control.mjs` tip vs install: size **95225**, SHA match
   `BB91FF66DDF552FEAC4E181D9A9A1110DDAA1AFE19CB44A775375CC65B0C788F`
   → no temp `.bak` patch needed (old bak files remain unused).
6. User data kept: `%USERPROFILE%\.strata\models`, `%LOCALAPPDATA%\strata`, `%APPDATA%\strata` present.

## GitHub Release

- Release already existed as **prerelease**; `gh release create` → duplicate; then `gh release upload --clobber` ensured asset.
- URL: https://github.com/zapabob/Strata/releases/tag/v0.3.2-preview.20261027.2
- Asset: `Strata_0.3.2-preview.20261027.2_x64-setup.exe` (176610345), digest sha256 matches local.
- Companion: `SHA256SUMS.txt`
- Body notes unsigned preview (existing release notes).

## README (EN / JA / ZH)

| File | Status |
|------|--------|
| `README.md` | Present; fork lockup + EN copy current |
| `README.ja.md` | Present; rewritten JA (mtime ~2026-10-27 23:34) |
| `README.zh-CN.md` | Present; rewritten ZH (mtime ~2026-10-27 23:34) |

No additional README commit/push required.

## Goal status

| Gate | Result |
|------|--------|
| Overwrite install verified | **PASS** |
| Release NSIS asset up | **PASS** |
| README 3 langs present | **PASS** |
| UpdateGoal | **complete** |

## Hypothesis / CoT

- H1: Silent `/S /UPDATE` works on Tauri NSIS → confirmed exit 0.
- H2: Same-version reinstall may keep older FS mtime → binary SHA still matches tip build; treat SHA as ground truth.
- H3: Release may already exist from parallel agent → upload/clobber path is correct; asset digest matches integrated-build SHA.
