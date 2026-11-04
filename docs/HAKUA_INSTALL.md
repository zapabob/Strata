# Install Hakua / Strata on Windows

GUI/Product `0.4.0-preview.20261103.7` · native engine/Control `0.4.0` · Hakua-memory `0.3.5`. The app installer on this tag has no Windows code signature. Its Qwen3.6 engine package is separate, has no picture reader, and is not Ed25519-signed (`signature` is null). PrismML and TurboQuant stay in the signed component from `v0.4.0-preview.20261101.1`. Startup time and token speed for this build were not measured. The CUDA spill guard did not pass the reviewed baseline.

Use this fork's 0.4.0 preview packages below. See the [qualification record](HAKUA_RELEASE.md) for exact tests and supported limits.

Check the [qualification record](HAKUA_RELEASE.md) for publication status and measured limits. This is an unsigned manual-update preview for Windows x64 and NVIDIA CUDA sm_120, tested on an RTX 5060 Ti. Other GPUs and operating systems need their own qualified packages.

## Start

Download the [setup EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.7/Strata_0.4.0-preview.20261103.7_x64-setup.exe). Compare the file with [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.7/SHA256SUMS.txt). SHA-256 `5e8b8fff82b6e63dea48bf5c1907950911700c9bf30673444e5d2489a87c0336`, 113064953 bytes. The installer has no Windows code signature. Mapped expert pack stays off unless the launch asks for it and the resolved `strata.exe` SHA-256 is `907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150`, `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`, `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29`, `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5`, or `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046`. The older digest stays allowed. A local help-honesty rebuild `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7` is the unsigned Qwen3.6 component digest for this .6 preview (side-by-side 0.4.0-q36-…); older digests stay allowed. A digest written in model settings does not unlock it. The legacy host arena stays the default. The main line stays context 65536, FP32 KV, MTP 2, prefill auto.

Close the running app and unload models before updating. Back up the app's data directory first. Run the installer for your Windows account. Keep enough free disk space for extraction and model files; when C: is short of space, save the download and choose an installation directory on a drive with room.

With tray storage enabled, × only hides the window. Right-click the Strata tray icon and choose Quit Strata before updating.

Open Strata and install the compatible engine offered on its first-run preparation screen. The app downloads the separate signed Hakua engine component and checks its signature and file hashes before activation. If you have already downloaded its `.tar.gz` file from this fork's release, use the engine file-import option instead. Then select a compatible model and its storage folder and load it.

The installer follows the official app architecture: it carries private Node, Python/Control and Hakua-memory, while GPU runtimes are separate. The Hakua Windows CUDA component contains the native engine and separate PrismML and TurboQuant runtimes. You do not need to install system Node, Python, pip or a compiler. Full inference model weights are another separate download and can be tens or hundreds of GB. Downloads, installation and loading take longer than the 30-second sequence of setup actions.

For native memory chat, open **Hakua memory** in the sidebar after loading a supported native model. Copy the profile key shown in its dialog. Select a memory checkbox on the local page, then paste the key into **About → Settings**. Choose read and/or save consent for each message. The app creates the local profile automatically and keeps ordinary chat credentials separate. See [the memory guide](../serve/MEMORY_HARNESS.md).

For local PQ2_0 GGUF files, choose **PrismML** in the model's advanced llama-server backend settings. For TurboQuant, choose **TurboQuant**, K=`FP16` and V=`TURBO2`, `TURBO3` or `TURBO4`, then reload. Open **Hakua memory** in the same sidebar. For these additional runtimes, the app supplies the local profile key automatically; select read and/or save consent separately for each message. Opening memory chat first restarts the owned server with authentication and shared prompt caches disabled, so finish active requests first. Native and additional runtimes share the local memory profile. [Backend details and limits](LOCAL_LLAMA_BACKENDS.md).

The separate native engine supports text chat. Native image input and the separate DeepSeek native engine are not included in this preview. Full model weights remain separate downloads.

This preview uses the fork's installer for updates. Source setup wrappers and upstream Terminal installation commands describe different distribution paths. The upstream Niko1221 installer does not contain Hakua's fork changes. [Build from source](SOURCE_INSTALL.md) is for developers.

## When C: has little free space

The app and temporary extraction need several GB, before any full inference model weights. Choosing another installation drive does not automatically move Windows temporary files.

If needed, open PowerShell in the folder containing the downloaded EXE and use a temporary folder on a drive with room. Replace H: below with an existing drive on your PC. These environment settings apply to this PowerShell process and the installer it starts. Choose an installation directory with enough space in the installer.

```powershell
$installTemp = 'H:\Hakua-install-temp'
New-Item -ItemType Directory -Path $installTemp -Force | Out-Null
$env:TEMP = $installTemp
$env:TMP = $installTemp
Start-Process -FilePath (Join-Path $PWD 'Strata_0.4.0-preview.20261103.7_x64-setup.exe') -Wait
```

## 日本語の導入手順

上のEXEを取得して実行してください。7zを選んだ場合は、先に展開してから同梱EXEを実行します。両方を取得する必要はありません。未署名のプレビューですので、SHA256SUMS.txtとの照合をお願いします。

更新前にモデルをアンロードし、アプリを終了してデータをバックアップします。アプリと一時展開には数GBの空き容量が必要で、モデル重みの容量は別途必要です。C:の空き容量が少ない場合は、保存先・インストール先に加えて一時ファイルの置き場所にも余裕が必要です。上のPowerShell例では、H:上の一時フォルダーを使ってEXEを起動します。H:は実際に存在し、空き容量のあるドライブへ置き換えてください。設定はそのPowerShellと、そこから起動するインストーラーに適用されます。

トレイ収納が有効な場合、×は画面を隠します。更新前はトレイのStrataアイコンを右クリックして、Strata を終了を選んでください。

起動後は対応モデルを選んで読み込み、サイドバーのHakua memoryを開きます。表示された専用キーをコピーし、記憶ページのチェック欄を選択してからAbout → Settingsへ貼り付けます。記憶の参照・保存への同意は、送信ごとに選び直してください。

初回は、モデルを選ぶ前に準備画面から対応エンジンのインストールを選んでください。公式アプリと同じく専用Node・Pythonはアプリに同梱し、GPUエンジンは別配布にしています。アプリは署名付きHakuaエンジンコンポーネントを取得し、署名と全ファイルのハッシュを確認してから有効化します。取得済みのコンポーネントファイルから導入することもできます。このコンポーネントにネイティブCUDA・PrismML・TurboQuantの実行環境が入ります。モデル重みは別途必要です。システム側のNode・Python、pip、コンパイラーのインストールは不要です。

PQ2_0はPrismML、TurboQuantはKをFP16・VをTURBO2／TURBO3／TURBO4にして使用します。モデルを読み込んでサイドバーのHakua memoryを開くと、追加経路では本人用キーをアプリが自動で使います。参照・保存は送信ごとに別々のチェック欄で選び、ネイティブと同じローカル記憶を利用できます。初回は認証付き・共有キャッシュ無効で起動し直すため、処理中のリクエストを終えてから開いてください。別配布のネイティブエンジンはテキスト用で、ネイティブ画像入力とDeepSeek専用エンジンは含みません。検証条件と未確認事項は[リリース検証記録](HAKUA_RELEASE.md)に記載します。
