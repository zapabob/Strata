<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="apps/host/public/brand/strata-lockup-dark.svg">
    <img src="apps/host/public/brand/strata-lockup-light.svg" alt="Strata" width="340">
  </picture>
</p>

<h3 align="center">あなた自身のパソコンで、高性能な AI を。</h3>
<p align="center">チャット、コーディング、画像の処理を、すべてローカルで。</p>

<p align="center">
  <a href="#モデル">モデル</a> · <a href="#インストール"><b>インストール</b></a> ·
  <a href="#ハードウェア">ハードウェア</a> · <a href="#ツール">ツール</a> ·
  <a href="#フォークについて">フォークについて</a> ·
  <a href="#ヘルプ">ヘルプ</a> · <a href="#strata-を支援する">支援</a>
</p>

<p align="center">
  <a href="https://github.com/zapabob/Strata/releases/latest"><img src="https://img.shields.io/github/v/release/zapabob/Strata?label=fork%20release&color=0ab887" alt="このフォークをダウンロード"></a>
  <a href="https://github.com/Niko1221/Strata/releases/latest"><img src="https://img.shields.io/github/v/release/Niko1221/Strata?label=upstream&color=555" alt="上流の Strata"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/Niko1221/Strata" alt="MIT ライセンス"></a>
</p>

<p align="center"><sub><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.pt-BR.md">Português</a></sub></p>

**無料でオープンソース。自分の環境で動かせます。** このリポジトリは [Niko1221/Strata](https://github.com/Niko1221/Strata) のフォークです。Spin(8) / Triality、Query-v3、TurboQuant、Bonsai、Hakua メモリチャット、Windows の `-hakua` パッケージを残しつつ、上流のセキュリティ修正とバグ修正を取り込みます。モデル・インストール・ハードウェアの案内は、2026-10-27 同期後の上流 **v0.2.6**（`4b9e05a2`）に合わせています。フォーク固有の説明と測定済みプレビューは [フォークについて](#フォークについて) にあります。

## モデル

まず **ISTA-DASLab** をおすすめします。次に **Unsloth** などの提供元です。メモリに収まる互換モデルがある場合に選べます。

<details>
<summary><img src="docs/media/models/qwen.svg" width="22" alt="" align="middle"> &nbsp;<b>Qwen3.8-Flash-Next</b></summary>

| 提供元 | 選択肢 |
| --- | --- |
| **ISTA-DASLab · おすすめ** | Q2\_0, IQ2\_XS, IQ3\_XXS, IQ3\_S。[Coder: IQ1\_M](docs/MODELS.md#coder)（コーディング向け）。 |
| **Unsloth** | UD-IQ4\_XS, UD-Q4\_K\_XL, UD-Q5\_K\_XL, UD-Q6\_K\_XL, Q8\_0 |
| **Gyro · agentionai** | [Gyro-S, Gyro-M](https://huggingface.co/agentionai/Qwen3.8-Flash-Next-Gyro-GGUF)。メモリ使用量は少ないですが、動作は遅くなります。 |
| **その他の選択肢** | [Swift 1.5](docs/MODELS.md#swift-15), [NVFP4](docs/NVFP4.md), [OrcaRouter](docs/ORCA.md) |

[サイズ、必要なメモリ、互換性を比べる](docs/MODELS.md)。

</details>

<details>
<summary><img src="docs/media/models/qwen.svg" width="22" alt="" align="middle"> &nbsp;<b>Qwen3.6-35B-A3B</b></summary>

**Unsloth:** UD-Q4_K_XL, UD-Q6_K_XL, Q8_0。現在、このモデルで文書化されているパックです。

[モデルガイドと互換性](docs/QWEN36.md)。

</details>

<details>
<summary><img src="docs/media/models/deepseek.svg" width="22" alt="" align="middle"> &nbsp;<b>DeepSeekV4.1-Flash-1017</b></summary>

**デスクトップアプリ**と**ターミナル**で使えます。メモリに収まらない分は SSD から読み込むため、空きディスク容量がたくさん必要です。

| セット（IST-DAS） | ダウンロード | 必要な空き容量 |
| --- | ---: | ---: |
| 1.75 bpw | 239 GB | 約245 GB |
| 2.00 bpw | 257 GB | 約265 GB |
| 2.25 bpw | 274 GB | 約280 GB |

NVIDIA RTX 30・40・50 シリーズ（Windows と Linux）と、AMD Radeon AI PRO R9700（Linux）で動きます。セットアップがファイルと DeepSeek エンジンをダウンロードし、モデルを起動します。

```sh
strata launch --family deepseek41 --model ist-das-2.00bpw --plan
```

Strata 0.2.5 で 2.00 bpw のセットを使って測定しました。「出力」は回答の速さ、「プロンプト」は Strata が入力を読み込む速さです。

| ハードウェア | 出力 | プロンプト |
| --- | ---: | ---: |
| RTX 5070 12 GB, 64 GB RAM | 4〜6 トークン/秒 | 約 110 トークン/秒 (4K) |
| RTX 3060 12 GB, 46 GB RAM | 9〜11 トークン/秒 | 約 155 トークン/秒 (4K) |
| 1x Radeon AI PRO R9700, 251 GB RAM | 21〜25 トークン/秒 | 320〜360 トークン/秒 (8K) |
| 4x Radeon AI PRO R9700 | 74〜77 トークン/秒 | 400〜450 トークン/秒 (8K) |

[メモリ、ディスク、詳細](docs/DEEPSEEK41.md) · [上流のリリースノート](https://github.com/Niko1221/Strata/releases)

</details>

<a id="the-other-sizes"></a>

どれが動くかわからない場合は、[お使いのパソコンに合うモデルを選ぶ](docs/MODELS.md#pick-by-memory)。

## インストール

<a id="option-a-the-strata-app"></a>

### デスクトップアプリ

**上流のインストーラー:** [Niko1221/Strata のリリース](https://github.com/Niko1221/Strata/releases/latest)  
**このフォークのリリース:** [zapabob/Strata のリリース](https://github.com/zapabob/Strata/releases/latest)

アプリをインストールし、モデルを選んで、チャットを始めましょう。初回起動時に、アプリがお使いのグラフィックスカード用のエンジンをダウンロードします。[インストーラーのヘルプ](docs/INSTALL.md#the-app)。

<sub>上流 0.2.6 のファイル: `Strata-0.2.6-windows-x64-setup.exe` · `Strata-0.2.6-linux-x86_64.AppImage` · `Strata-0.2.6-macos-arm64.dmg`。フォークのパッケージには `-hakua` ラベルが付くことがあります。タグのリリースノートを見てください。</sub>

<p align="center">
  <img src="docs/media/app-chat.png" width="900" alt="チャットとライブのコードプレビューを並べて表示した Strata デスクトップアプリ">
  <br><sub>チャット、ファイル、ライブプレビューを1つのウィンドウで。</sub>
</p>

<a id="option-b-the-terminal-one-line"></a>

### ターミナルアプリ

ターミナルのほうが好みですか？ Strata をインストールして、**`strata launch`** を実行します。

<details open>
<summary><b>インストールコマンド</b></summary>

**Linux / Mac**

```sh
curl -fsSL https://github.com/Niko1221/Strata/releases/latest/download/install.sh -o install.sh && sh install.sh
```

**Windows PowerShell**

```powershell
irm https://github.com/Niko1221/Strata/releases/latest/download/install.ps1 | iex
```

Windows では、インストール後に新しいターミナルを開きます。そのあと:

```sh
strata launch
```

画面の案内に従って、モデルをダウンロードして起動します。[ターミナルガイド](docs/TERMINAL_LAUNCH.md)。

</details>

<p align="center">
  <img src="docs/media/terminal-monitor.png" width="900" alt="モデルの動作、速度、メモリ、最近のリクエストを表示する Strata ターミナルアプリ">
  <br><sub>動作中のモデルとハードウェアの状態を確認できます。</sub>
</p>

<a id="build-from-source"></a>

[ソースからビルド](docs/SOURCE_INSTALL.md) · [Docker](docs/DOCKER.md) · [インストールガイド（全文）](docs/INSTALL.md)

<a id="what-you-need"></a>

## ハードウェア

| 対応ハードウェア | ガイド |
| --- | --- |
| **NVIDIA GeForce RTX 20 / 30 / 40 / 50 シリーズ** | [NVIDIA のセットアップ](docs/INSTALL.md#what-you-need) |
| **AMD Radeon RX 7700 / 7800 / 7900、RX 9060 / 9070、AI PRO R9700** | [AMD のセットアップ](docs/AMD_HIP.md) |
| **AMD Radeon RX 6800 / 6900 · 試験的** | [RX 6000 のセットアップ](docs/AMD_HIP.md#rdna2-gfx1030) |
| **Intel Arc · Linux** | [Intel のセットアップ](docs/INTEL_ARC.md) |
| **Apple Silicon · M1 以降** | [Mac のセットアップ](docs/MAC.md) |
| **AMD Ryzen AI Max · Strix Halo** | [Strix Halo のセットアップ](docs/STRIX_HALO.md) |

<a id="using-it"></a>

## ツール

**Claude Code · Codex CLI · OpenCode · oh-my-pi · pi.dev · Hermes Agent · OpenClaw**。OpenAI 互換と Anthropic 互換の API を通じて、ほかのツールも使えます。

**`strata connect`** を実行すると、お使いのツールの設定方法が表示されます。[接続ガイド](docs/TERMINAL_LAUNCH.md#connect-your-apps-strata-connect)。

<a id="フォークについて"></a>

## フォークについて

このフォーク（`zapabob/Strata`）は、上流の新しい Host / Control API に合わせつつ、次の面を残しています。

| 領域 | 残しているもの |
| --- | --- |
| エンジン研究 | Spin(8) / Triality KV、Query-v3、TurboQuant 方言、Bonsai / Prism 経路 |
| Host | Hakua 同意付きメモリチャット、run-config の既知キー、ネイティブ読み込みキャンセルの所有権 |
| パッケージ | Windows フルパッケージ（任意の `-hakua` ラベル） |
| 取り込み | `_docs/upstream-intake/` の契約と `tools/merge_upstream_fork.py` |

上流同期の到達点: **公式 v0.2.6 / `upstream/main@4b9e05a2`**（Windows アンインストーラ修正と 0.2.6 の docs/feed）。マージ後のツリー上のアプリ版: **`0.3.2-preview.20261027.2`**。

### Windows 推論プレビュー（このフォークで測定）

以前のタグ `0.3.2-preview.20261027.1` は、Windows・RTX 5060 Ti 16 GiB・システム RAM 32 GiB で試したエンジンを同梱します。CUDA 13 / SM120 のプレビュー重ね合わせであり、上流インストーラの全経路をここで再測定したという意味ではありません。

試した設定は Qwen3.8 Q2_0、容量 **131072**、**spec4 + MTP**、**k8v4**、出力予約 256 トークンです。

| 実入力 | 初回と再生成 | 想起チェック | 後始末 |
| --- | --- | --- | --- |
| 4096 トークン | 両方完了、各 52 出力トークン | 両方合格 | 残 Job プロセスなし |
| 32768 トークン | 両方完了、各 52 出力トークン | 両方合格 | 残 Job プロセスなし |

これらの実行では source / controller 診断は OFF でした。32K の初回プロンプトは 494.76 秒、再プロンプトは接頭辞再利用で 0.646 秒でした。デコードはそれぞれ 13.759 秒と 3.255 秒でした。1 つの合成タスクの観察であり、統計的な速度や広い品質の主張ではありません。

使う前に [測定記録](docs/PERF131K.md) と [機械可読ステータス](docs/perf131k-status.json) を読んでください。その記録では、126000 トークンの全日長認定、画像推論、HIP/SYCL は未認定です。

任意のメモリハーネスは **既定では無効** です。[MEMORY_HARNESS](serve/MEMORY_HARNESS.md) を見てください。

<a id="guides"></a>

## ヘルプ

[すべてのガイド](docs) · [トラブルシューティング](docs/TROUBLESHOOTING.md) · [このフォークへ不具合を報告](https://github.com/zapabob/Strata/issues/new/choose) ·
[上流の issue](https://github.com/Niko1221/Strata/issues/new/choose) ·
[ベンチマーク](docs/COMMUNITY_BENCHMARKS.md) · [仕組み](docs/HOW_IT_WORKS.md) · [貢献する](CONTRIBUTING.md)

## Strata を支援する

**ローカル AI をみんなに開かれたものに。** 上流が公開プロジェクトを維持しています。コーヒー 1 杯が、その開発と試験の支えになります。

<a href="https://buymeacoffee.com/strataengine"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee: Strata を支援する" height="48"></a>

[MIT ライセンス](LICENSE) · [クレジットとモデルのライセンス](docs/HOW_IT_WORKS.md#credits) · [プライバシー](docs/SAFETY.md)

<sub>AI ツールと自動リーダー向け: <a href="AGENTS.md">技術リファレンス</a> · <a href="docs/AI_SETUP.md">セットアップ手順</a> · <a href="_docs/upstream-intake/fork-contracts.json">フォーク契約</a>。</sub>
