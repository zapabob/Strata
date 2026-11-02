# setup.exe / SHA を GitHub Release へアップロード

- **日時**: 2026-11-02 18:59 JST
- **実装AI**: Cursor (Composer)
- **tag**: `v0.4.0-preview.20261101.1`（`zapabob/Strata`）
- **workspace**: `8870f25309ca7142a44b0042b1d16f337e4487af`

## 背景・要求

正式 NSIS で作った `setup.exe` と SHA を release 資産として保管し、公開済みタグへアップロードする。

## 前提・判断

1. 署名済み engine / Control / feed は 2026-11-01 公開物を再利用（ダイジェスト不変）。
2. 差し替え対象は app installer 系3点のみ: setup.exe / 外装7z / SHA256SUMS.txt。
3. 同一タグ `--clobber` で上書き。フルスイート再資格は本アップロードでは未実施と明記。

## 変更対象

| パス | 内容 |
|------|------|
| `H:\Strata\releases\hakua040-nsis-publication-20261102\` | ステージ一式 |
| GitHub release assets (3) | clobber upload |
| `docs/HAKUA_RELEASE.md` | 公開ダイジェスト更新 |

## 実装詳細

### ステージ

- setup SHA256 `9682b59774fa1b552d9ba09c7d0baed0028f0b7b104cfeec4c9b0a3d7eda2a26` / 113758075 bytes
- 7z SHA256 `7d02e384a502600b0e2b2143cbb73ebc8c71893af8a2fd8532b74ad823bb6fbe` / 113749050 bytes（INSTALL.md + SHA256SUMS-installer.txt + EXE、`7z t` / 再展開 hash OK）
- SHA256SUMS.txt SHA256 `411ab24fd7579daca3a1f73d240de65718399b1de3511b5f416988a32e7c73f6` / 720 bytes

### アップロード

```powershell
gh release upload v0.4.0-preview.20261101.1 `
  Strata_0.4.0-preview.20261101.1_x64-setup.exe `
  Hakua-Strata-0.4.0-preview.20261101.1-windows-x64-sm120.7z `
  SHA256SUMS.txt `
  --repo zapabob/Strata --clobber
```

`UPLOAD_OK=2026-11-02T18:51:48+09:00`

### 匿名検証

`curl.exe -L` で3資産を再取得。size/sha すべて match。`ANON_VERIFY_OK` at 2026-11-02T09:58:59Z。

## 残留リスク

- 本 rebuild では Host/Python フルスイートと 13 self-tests を再実行していない。
- 同一 product 版番号のまま EXE バイトが変わったため、旧 SHA を保持している利用者は再照合が必要。
- ローカル再ビルド engine (`d7f459a1…`) は公開署名 engine コンポーネント (`39722537…`) とは別物。公開 feed が指すエンジンは旧署名パッケージのまま。

## 次の推奨

1. 必要なら docs 変更を main に commit/push
2. Hikari Load with Strata を公開 EXE 経路で一度確認
3. GDN 再ビルド engine を署名コンポーネントとして出すなら別フィード更新が必要
