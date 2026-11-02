# 正式 NSIS（CUDA再ビルド → verify → setup.exe → /S /UPDATE）

- **日時**: 2026-11-02 10:52 JST（ローカル `Get-Date` + world-intel MCP `intel_status` 応答確認）
- **実装AI**: Cursor (Composer)
- **GPU**: RTX 5060 Ti 16GB（CUDA sm_120）
- **workspace commit**: `8870f25309ca7142a44b0042b1d16f337e4487af`
- **product**: `0.4.0-preview.20261101.1`

## 背景・要求

ペイロード上書きだけでは Uninstall レジストリの `DisplayVersion` が旧 `0.3.2` のまま。正式経路は CUDA エンジン再ビルド → `verify-release` → Tauri NSIS `setup.exe` → `/S /UPDATE`。

## CoT / 仮説検証

| ID | 仮説 | 結果 |
|----|------|------|
| H1 | GDN native 差分があるのでエンジン再ビルド無しでは `verifyNativeBuild` が落ちる | **採用**（先行ログで確認済み） |
| H2 | 再ビルド後 `native-build.json` sha `d7f459a1…` で verify 通過する | **採用** |
| H3 | NSIS `setup.exe` は cargo target `hakua040-nsis-cargo-20261102` に出る | **採用**（`NSIS_BUILD_EXIT=0`） |
| H4 | `/S /UPDATE` で DisplayVersion が `0.4.0-preview.20261101.1` になる | **採用**（INSTALL_EXIT=0） |
| H5 | インストール後 exe SHA は pre-bundle `release/strata-desktop.exe` と一致する | **棄却**（Tauri が NSIS バンドル時に binary patch。不一致は想定内） |

## 変更対象（成果物パス）

| 成果物 | パス |
|--------|------|
| Engine package | `H:\Strata\releases\hakua040-nsis-engine-pkg-20261102\0.4.0-windows-x86_64-cuda-cuda13\` |
| Native build meta | 同上 / `native-build.json`（`sha256=d7f459a11fca9716090fdadfab8c5f3dd54a34b28501156e33b6f5cd515180d9`） |
| setup.exe | `H:\Strata\releases\hakua040-nsis-cargo-20261102\release\bundle\nsis\Strata_0.4.0-preview.20261101.1_x64-setup.exe` |
| インストール先 | `%LOCALAPPDATA%\Programs\Strata` |

## 実装詳細 / 実行コマンド

1. CUDA sm_120 エンジン再ビルド + package（先行完了）
2. `verify-release` 通過（ログ: `H:\Strata\tmp\verify-release-nsis-20261102.log` → `Release payload verified: Hakua 0.4.0-preview.20261101.1, engine 0.4.0`）
3. Tauri NSIS（`RUSTC_WRAPPER` 無し、LTO=false 前提の cargo target）
   - `NSIS_BUILD_EXIT=0` at `2026-11-02T10:43:25+09:00`
   - setup size: `113758075` bytes（108.49 MiB）
   - setup SHA256: `9682B59774FA1B552D9BA09C7D0BAED0028F0B7B104CFEEC4C9B0A3D7EDA2A26`
4. 上書きインストール:
   ```powershell
   Start-Process -FilePath '...\Strata_0.4.0-preview.20261101.1_x64-setup.exe' -ArgumentList '/S','/UPDATE' -Wait -PassThru
   ```
   - `INSTALL_START=2026-11-02T10:45:17+09:00`
   - `INSTALL_EXIT=0` at `2026-11-02T10:52:02+09:00`

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| NSIS build exit | 0 |
| Install exit | 0 |
| HKCU Uninstall `DisplayName` | Strata |
| HKCU Uninstall `DisplayVersion` | `0.4.0-preview.20261101.1` |
| InstallLocation | `%LOCALAPPDATA%\Programs\Strata` |
| `host\package.json` version | `0.4.0-preview.20261101.1` |
| `host\hakua-chatbot.enabled` | 存在 |
| `control\VERSION` | `0.4.0` |
| `control\COMMIT` | `a684b50d5c149718fdc538d71c97c8389760347d` |
| installed `strata-desktop.exe` SHA256 | `A52B2EFF958EED250F43BB7FE5A21B384FF792DA59E5010AAA185033E8D60F4C` |
| pre-bundle release exe SHA256 | `9D5239178BF96ADE2AEC35BC818F0FB9B55E54E802826893550865EFCAD846AA`（patch 前・参照のみ） |

## 残留リスク

- GUI プロセス起動（`strata-desktop` pid 21868）までは確認。Hikari → Load with Strata → PrismML の実チャットは未再実行。
- エンジン本体はアプリ起動後の component/import 経路依存。NSIS 本体に常時フル CUDA エンジン同梱とは限らない。
- `control\COMMIT` は control バンドル由来で workspace `8870f253` とは別系統。

## 次の推奨アクション

1. Hikari → Load with Strata → PrismML 経路を一度通す
2. 必要なら setup.exe / SHA を release 資産として保管・公開手順へ
