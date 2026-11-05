# Install Hakua / Strata on Windows

Product `0.4.1-beta.1` uses native engine/Control `0.4.1` and Hakua-memory `0.3.5`.
PrismML and TurboQuant retain their independently verified `0.4.0` runtime packages.
This is a Windows x64 CUDA sm_120 beta, tested on an RTX 5060 Ti with 16 GB VRAM and
32 GB system RAM. See the [release record](HAKUA_RELEASE.md) for publication status,
exact tests and limits. A successful short request does not qualify a full context window.

## Install or update

Download the [Windows setup EXE](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/Strata_0.4.1-beta.1_x64-setup.exe)
and compare it with [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.1-beta.1/SHA256SUMS.txt).
The desktop installer has no Windows code signature. Component signatures and checksums
are separate checks; they are not Windows executable signing.

Unload models, finish active requests and quit Strata, including its tray icon, before
updating. Back up the app data first. Run one installer at a time. Do not remove the
installation directory while setup is running. The installer replaces its managed
application files and preserves unrelated files in the installation root.

The usual per-user location is `%LOCALAPPDATA%\Programs\Strata` on C:. A previous
installation can retain another drive. Choose the intended folder in the installer.
Models, chats and memory have their own data locations; changing the application
folder does not move them. Leave existing model files where they are and select
that model folder in Strata. System Node, Python, pip and compilers are not required.

GPU runtimes are separate from the app. For this beta, download the matching
`strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz` from the
[beta release](https://github.com/zapabob/Strata/releases/tag/v0.4.1-beta.1) and import
it from the preparation screen. The app checks the component signature and all file
hashes before activating it. The normal latest feed still serves its earlier signed
release; installing the app alone does not upgrade that native engine. Keep the older
component available for rollback. The signed `0.4.0` release files are not replaced.

## Existing models and caches

Use **Use a local GGUF** for a file already on the PC. One shard is enough to select
a split set; all required shards are checked. Catalog setup also searches the chosen
model directory's subfolders for one matching valid set. If more than one matches,
choose the intended file. It does not silently select a different fine-tune.

A native model can need a one-time expert-pack conversion. The app displays completed
layers when the packer reports them. Resume reuses the matching checkpoint and counts
space already allocated to its temporary file. Existing GGUFs and expert packs stay
on disk; normal unload and restart do not delete them.

Qwen3.6 private conversation reuse is negotiated with the running engine. Within
one authenticated conversation, a completed prefix can be reused. Another conversation,
missing identity, cancellation, invalid requests and five minutes of idle time clear
that private state. This does not delete the model or its expert pack. The first
implementation accepts one active request; parallel private Qwen3.6 requests are refused.
The Host no longer rejects Qwen3.6 before startup because its private-cache digest
is absent from a list. The server checks the engine's actual capability before it
accepts requests. An engine without that capability needs the matching update.

The Qwen3.6 mapped expert pack is opt-in and requires an allowlisted executable.
It avoids the legacy full host expert arena, but the operating system may still page
mapped data. The experimental `STRATA_Q36_PIN_PIPELINE=1` and
`STRATA_Q36_STREAM_RESIDENT=1` environment switches retain the model's numeric formats.
They are off by default. The release record describes their bounded comparison; it is
not a guarantee of speed on another model, context length or PC.

## Chat, tools and memory

For a supported PQ2_0 GGUF, select **PrismML**. For TurboQuant, choose **TurboQuant**,
K=`FP16` and V=`TURBO2`, `TURBO3` or `TURBO4`, then reload. The release keeps the
quality-related refusals for unsupported K-cache choices. See [backend limits](LOCAL_LLAMA_BACKENDS.md).

Choose the loaded local model in the chat. Web search needs network access and a model
that emits a supported tool call. A tool request, its returned result and the assistant's
final answer are separate parts of the same turn. Stop cancels the active turn.
The app's request adapter keeps Qwen3.6 cache ownership separate for each chat.

Hakua memory is optional and remains off until enabled. Open it from the sidebar after
loading the model. Reference/save consent is selected separately for each message.
Additional local runtimes use the app's local profile key automatically. First enabling
memory can restart the owned server with authentication and shared caches disabled;
finish active requests first. See the [memory guide](../serve/MEMORY_HARNESS.md).

Native image input and the separate DeepSeek native engine are not included in this
Windows beta. Other GPUs, HIP, SYCL, Linux and Metal need their own builds and tests.

## 日本語の導入手順

`0.4.1-beta.1`のsetup EXEとチェックサムを取得します。更新前にモデルをアンロードし、
トレイのStrataも終了してから、一度だけインストーラーを実行してください。
Cドライブに入れる場合は、導入先を`%LOCALAPPDATA%\Programs\Strata`に指定します。
以前Hドライブを選んだ環境では、その場所が引き継がれることがあります。
モデル・会話・記憶の保存先は別なので、モデルを移したり消したりする必要はありません。

専用Node・Pythonは同梱されています。GPUエンジンは別配布です。このベータでは、同じ
リリースページの`strata-engine-0.4.1-windows-x86_64-cuda-cuda13.tar.gz`を準備画面から
読み込んでください。署名と全ファイルのハッシュを確認してから有効化します。
通常のlatest配信先は以前の署名付き版を維持しているため、アプリの更新だけでは新しい
Qwen3.6エンジンに切り替わりません。旧コンポーネントはロールバック用に残します。

取得済みGGUFは「ローカルGGUFを使用」で選択します。分割GGUFは一つを選ぶと一式を確認します。
モデルと変換済みパックは保持します。Qwen3.6の会話キャッシュは、認証された同じ会話で再利用し、
別の会話、キャンセル、エラー、識別情報のない要求、5分間の待機では消去します。
この消去でモデルファイルやパックが消えることはありません。

インストーラーと一時展開には数GBの空き容量が必要です。モデルの容量は別に確保してください。
公開状況、実測条件、未確認事項は[リリース記録](HAKUA_RELEASE.md)を参照してください。
