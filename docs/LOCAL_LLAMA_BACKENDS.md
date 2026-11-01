# Local llama-server backends

This document describes the 0.4.0 source candidate. Packaging and publication are pending. The published 0.3.3 inference measurements below remain separately identified. Check [the release qualification record](HAKUA_RELEASE.md) for publication status, measured inference results and package limits.

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

In the 0.4.0 candidate, load the verified PrismML or TurboQuant model and open **Hakua memory** in the sidebar. The app finishes the switch to a private, authenticated owned server before opening the text chat dialog. Finish active requests first. Read and save consent are independent and reset after each turn. The dialog's key and full conversation remain in RAM; only a consented factual summary is written to the shared local Hakua-memory profile. Closing or stopping cancels an unfinished turn. A summary already completed just before cancellation may have been saved. If a model returns an acknowledgment instead of a useful summary, nothing is saved. This path supports plain text without tools or attachments. Ordinary chat remains a separate path and grants no memory consent. Memory and backend inference have separate qualification checks; these source changes do not establish a completed 0.4.0 package test.

Actual adapter checks on 2026-11-01 saved synthetic facts, restarted the owned server and recalled exact identifiers with Hikari PQ2_0 on PrismML, and with [Unsloth Qwen3-1.7B-Q8_0](https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/tree/d7f544eead698dbd1f15126ef60b45a1e1933222) on TurboQuant using FP16 K/Turbo3 V. A controlled comparison also passed with FP16 V for Qwen3-0.6B and Qwen3-1.7B. Qwen3-0.6B with Turbo3 V failed to produce a useful summary and was rejected; its ordinary inference checks do not establish memory-summary quality. This is a model/cache-specific limitation, not a successful memory test. Use a model/cache combination that passes your own save/restart/recall check. The UI reports when no useful summary was saved. The model files used in these tests are not included in the installer. Final packaged Host/UI/engine qualification remains pending.

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

PrismMLとTurboQuantは専用の実行ファイル・DLLを使います。この候補版は、PQ2_0の重みとTurboQuantのキャッシュを同じプロセスで併用する構成を提供していません。0.4.0候補では、対応モデルの読み込み後にHakua memoryを開くと、管理下のサーバーを認証付き・共有キャッシュ無効で起動し直し、同じローカル記憶を使うダイアログを表示します。参照・保存は毎回別々に同意します。通常のチャットには同意を引き継ぎません。追加経路はテキストのみで、ツールや添付ファイルは使いません。会話全文とキーはダイアログのメモリー内に保持し、同意した有用な要約だけを保存します。中止直前に保存が完了した要約は残る場合があります。モデルが有用な要約を返さなければ保存しません。推論・記憶・最終配布物をそれぞれ検証します。

この文書は開発中の配布候補について説明しています。[リリース検証記録](HAKUA_RELEASE.md)に実際の推論・起動試験の結果が揃うまでは、公開済み・検証済みの完成版として扱わないでください。

2026-11-01のアダプター試験では、PrismMLのHikari PQ2_0と、TurboQuantのQwen3-1.7B-Q8_0（K=FP16、V=Turbo3）で、要約の保存とサーバー再起動後の識別子の読み出しを確認しました。一方、Qwen3-0.6BのV=Turbo3では有用な要約を返せず、保存を拒否しています。同じ0.6BのV=FP16では保存・再起動後の読み出しが通りました。通常の返答ができても、記憶要約の品質まで確認したことにはなりません。モデルとキャッシュ設定ごとに確認してください。有用な要約が得られなかった場合は、画面に保存されなかった理由を表示します。最終配布物での確認は別に必要です。
