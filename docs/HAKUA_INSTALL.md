# Install Hakua / Strata on Windows

GUI/Product `0.3.3-preview.20261030.1` · native engine/Control `0.3.3` · Hakua-memory `0.3.5`.

Check the [qualification record](HAKUA_RELEASE.md) for publication status and measured limits. This is an unsigned manual-update preview for Windows x64 and NVIDIA CUDA sm_120, tested on an RTX 5060 Ti. Other GPUs and operating systems need their own qualified packages.

## Start

Download the [setup EXE](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Strata_0.3.3-preview.20261030.1_x64-setup.exe), or the [7z containing that same installer](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/Hakua-Strata-0.3.3-preview.20261030.1-windows-x64-sm120.7z). With the 7z, extract it before running the EXE. Compare the file with [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.3.3-preview.20261030.1/SHA256SUMS.txt).

Close the running app and unload models before updating. Back up the app's data directory first. Run the installer for your Windows account. Keep enough free disk space for extraction and model files; when C: is short of space, save the download and choose an installation directory on a drive with room.

Open Strata, select a compatible model and its storage folder, then load it. Node, Python, Hakua-memory and the Windows native engine are included. Full inference model weight packs are separate downloads and can be tens or hundreds of GB. Downloading, installing and loading take longer than the 30-second sequence of setup actions.

For native memory chat, open **Hakua memory** in the sidebar after loading a supported native model. Copy the profile key shown in its dialog. Select a memory checkbox on the local page, then paste the key into **About → Settings**. Choose read and/or save consent for each message. The app creates the local profile automatically and keeps ordinary chat credentials separate. See [the memory guide](../serve/MEMORY_HARNESS.md).

For local PQ2_0 GGUF files, choose **PrismML** in the model's advanced llama-server backend settings. For TurboQuant, choose **TurboQuant**, K=`FP16` and V=`TURBO2`, `TURBO3` or `TURBO4`, then reload. These are separate runtimes; their chat paths do not share the native memory sidebar. [Backend details and limits](LOCAL_LLAMA_BACKENDS.md).

This preview uses the fork's installer for updates. Source setup wrappers and upstream Terminal installation commands describe different distribution paths. The upstream Niko1221 installer does not contain Hakua's fork changes. [Build from source](SOURCE_INSTALL.md) is for developers.

## When C: has little free space

The extracted qualification payload is approximately 2.7 GB, before any full inference model weights. Keep additional space for temporary extraction. Choosing another installation drive does not automatically move Windows temporary files.

If needed, open PowerShell in the folder containing the downloaded EXE and use a temporary folder on a drive with room. Replace H: below with an existing drive on your PC. These environment settings apply to this PowerShell process and the installer it starts. Choose an installation directory with enough space in the installer.

```powershell
$installTemp = 'H:\Hakua-install-temp'
New-Item -ItemType Directory -Path $installTemp -Force | Out-Null
$env:TEMP = $installTemp
$env:TMP = $installTemp
Start-Process -FilePath (Join-Path $PWD 'Strata_0.3.3-preview.20261030.1_x64-setup.exe') -Wait
```

## 日本語の導入手順

上のEXEを取得して実行してください。7zを選んだ場合は、先に展開してから同梱EXEを実行します。両方を取得する必要はありません。未署名のプレビューですので、SHA256SUMS.txtとの照合をお願いします。

更新前にモデルをアンロードし、アプリを終了してデータをバックアップします。展開した検証用パッケージは約2.7 GBで、モデル重みと一時展開の容量は別途必要です。C:の空き容量が少ない場合は、保存先・インストール先に加えて一時ファイルの置き場所にも余裕が必要です。上のPowerShell例では、H:上の一時フォルダーを使ってEXEを起動します。H:は実際に存在し、空き容量のあるドライブへ置き換えてください。設定はそのPowerShellと、そこから起動するインストーラーに適用されます。

起動後は対応モデルを選んで読み込み、サイドバーのHakua memoryを開きます。表示された専用キーをコピーし、記憶ページのチェック欄を選択してからAbout → Settingsへ貼り付けます。記憶の参照・保存への同意は、送信ごとに選び直してください。

PQ2_0はPrismML、TurboQuantはKをFP16・VをTURBO2／TURBO3／TURBO4にして使用します。ネイティブの記憶チャットとは別の推論経路です。検証条件と未確認事項は[リリース検証記録](HAKUA_RELEASE.md)に記載します。
