# Local llama-server backends

This document describes the 0.3.3 Windows preview. Check [the release qualification record](HAKUA_RELEASE.md) for publication status, measured inference results and package limits.

## Choose a runtime

Import a local GGUF through the model page. In the model's advanced settings, find **llama-server backend** and select one of the following. Reload the model after changing it.

| Choice | Intended use |
| --- | --- |
| Automatic | The existing runtime selection. This remains the default. |
| PrismML | PrismML PQ2_0 GGUF files, including files ending in `-PQ2_0.gguf`. |
| TurboQuant | Compatible standard GGUF weights with TurboQuant K/V cache quantization. |

PrismML and TurboQuant are separate executables with separate libraries. Selecting TurboQuant does not add PrismML's GGUF types to that executable. This candidate does not offer PQ2_0 weights and TurboQuant cache quantization together in one process.

For this Windows sm_120 candidate, set K to `FP16` and V to `TURBO2`, `TURBO3` or `TURBO4`. Each combination passed two Qwen3-0.6B-Q8_0 startup/chat/stream/stop/restart rounds with exact arithmetic-response and named-greeting assertions. TurboQuant K modes produced corrupted responses; they are excluded from the packaged K capabilities and GUI choices. The initial symmetric TURBO4 probe accepted a numeral inside a rambling response and is not a valid quality qualification. Help output alone is not proof of working inference. Quantized V requires flash attention. The app reads the model's K/V head geometry during import; reimport an older local-model entry if it has no geometry. Head widths do not have to equal 128: this fork pads rotation groups internally. Model architecture support still depends on the selected llama-server.

The app explicitly sets K/V precision and disables TurboQuant's automatic asymmetric and layer-adaptive overrides. It rejects an unsupported cache choice before stopping an existing model. A changed backend takes effect on the next model load.

The Hakua memory sidebar follows the native Strata memory profile. The separate llama-server chat path must not be assumed to have the same memory read/save integration. Memory and backend inference have separate qualification checks.

## Bundled runtime identity

The Windows candidate targets CUDA sm_120. Other GPU architectures require separately built and tested packages. Models are downloaded or imported separately.

| Runtime | Pinned source |
| --- | --- |
| PrismML | [PrismML-Eng/llama.cpp, 73bfe6cc485554822f80c473a3c0c4f25e80f41b](https://github.com/PrismML-Eng/llama.cpp/commit/73bfe6cc485554822f80c473a3c0c4f25e80f41b) |
| TurboQuant | [TheTom/llama-cpp-turboquant, 643956891dfdf51aecdbd05ca508dd21e21e8195](https://github.com/TheTom/llama-cpp-turboquant/commit/643956891dfdf51aecdbd05ca508dd21e21e8195) |

The standard-sm_120 builds apply reviewed two-file patches: `prism-standard-sm120-v1` for PrismML and `turboquant-standard-sm120-v1` for TurboQuant. They preserve the requested architecture and disable architecture-specific FP4 MMA selection; they do not change the quantization formulas. Runtime manifests identify the complete source commit, approved patch, executable, DLLs and SHA-256 hashes. Unexpected files, changed payloads and unknown source revisions are rejected. A newer bundled runtime takes precedence over an older installed component.

Build with PowerShell 7 using `tools/spin8_backend.ps1`. Stage a successful build with `tools/stage_llama_runtime.py`, passing the matching CUDA DLL search directory explicitly. The installer verification gate requires both current runtime packages and probes each executable with only System32 on PATH. A build or header import alone does not establish successful inference.

## 日本語

ローカルGGUFをモデル画面から追加し、モデルの詳細設定にあるllama-serverのバックエンドを選びます。PQ2_0形式は `PrismML`、通常のGGUFでTurboQuantキャッシュを使う場合は `TurboQuant` を選択します。変更後はモデルを読み込み直してください。初期値の `Automatic` は従来の選択処理を使います。

このWindows sm_120版では、Kを `FP16`、Vを `TURBO2`・`TURBO3`・`TURBO4` のいずれかに設定します。それぞれ計算結果と指定名への挨拶を再起動を挟んで確認しました。K側のTurboQuantは返答の崩れが再現したため、同梱ランタイムのK対応一覧とGUIの選択肢から外しています。量子化したVにはFlash Attentionが必要です。古いモデル登録にヘッド情報がない場合は、GGUFを追加し直してください。128以外のヘッド幅も内部のパディングで扱いますが、モデルの構造自体が選択したランタイムに対応している必要があります。

PrismMLとTurboQuantは専用の実行ファイル・DLLを使います。この候補版は、PQ2_0の重みとTurboQuantのキャッシュを同じプロセスで併用する構成を提供していません。Hakua記憶サイドバーはネイティブStrataの記憶プロファイルを使います。別のllama-server経路にも同じ記憶機能が働くとは扱わず、推論と記憶をそれぞれ検証します。

この文書は開発中の配布候補について説明しています。[リリース検証記録](HAKUA_RELEASE.md)に実際の推論・起動試験の結果が揃うまでは、公開済み・検証済みの完成版として扱わないでください。
