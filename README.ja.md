# Hakua / Strata

Strata 上の Hakua チャットボット。Windows プレビューとして、Hakua memory と別配布の GPU 実行環境を同梱構成にしています。[zapabob/Strata](https://github.com/zapabob/Strata) · 上流 [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## 導入（Windows プレビュー）

1. [setup EXE](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.3/Strata_0.4.0-preview.20261103.3_x64-setup.exe) を取得します。
2. 実行前に [SHA256SUMS.txt](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.3/SHA256SUMS.txt) と照合します。Windows のコード署名はありません。setup EXE の SHA-256 は `a6e8eb762d32f685f3a47d68e3c593f2b5df361bd42bb7c79d8d3a1f65d70f13`（113,054,600 bytes）です。
3. すでに入っている場合はトレイから「Strata を終了」で完全終了してから EXE を実行します。
4. 初回は準備画面で署名付きエンジンの導入を選ぶか、同じリリースの `.tar.gz` を取り込みます。その後モデルフォルダーを選んで読み込みます。

クリック手順は短いです。ダウンロード・エンジン有効化・モデル読み込みには時間がかかり、空き容量と VRAM も必要です。詳細は [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md)。測定した範囲は [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md)。

## インストーラーに入るもの

| アプリインストーラー | 別配布 |
| --- | --- |
| GUI / Host、専用 Node 24.22.2、Control / CPython 3.12.15、Hakua-memory 0.3.5、Harness | 署名付き CUDA エンジン（約 1.4 GB）：ネイティブ Strata + PrismML + TurboQuant |
| この EXE による手動アプリ更新 | モデル重み（数十〜数百 GB） |

公開アプリにシステム側の Node / Python / pip / コンパイラーは不要です。上流 Niko1221 のインストーラーには本フォークの変更は入りません。

## ローカルモデルの読み込み

- **ネイティブ Strata パック**（対応する Qwen 系テキスト）：アプリのネイティブ準備／読み込みを使います。
- **Hikari / PQ2_0 GGUF**：**Load with Strata**（PrismML）を使います。PQ2_0 にネイティブ準備は使いません。
- **通常 GGUF + TurboQuant キャッシュ**：バックエンド `TurboQuant`、K=`FP16`、V=`TURBO2` / `TURBO3` / `TURBO4` にして読み込み直します。K 側 TurboQuant は実モデルで返答崩れが再現したため無効です。

PrismML と TurboQuant はエンジン内の別実行ファイルです。[LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md)。GPU に収まるパックを ISTA-DASLab → Unsloth → Gyro の順で選びます。

モデルが Strata / supervisor 経路で動いているとき、Agent はそのローカル実体経由で、モデルが対応するツール（例: web search）を使えます。ネイティブ専用セッションでは同じ経路にはなりません。

## Hakua memory

対応モデルを読み込んだあと、サイドバーの **Hakua memory** を開きます。参照と保存の同意は別々で、送信ごとにリセットされます。

- ネイティブ：ダイアログのキーを About → Settings に貼り、記憶ページでチェックします。
- PrismML / TurboQuant：アプリがローカルキーを使います。初回は処理中のリクエストを終えてから開いてください（認証付き・共有キャッシュ無効でサーバーを起動し直します）。

手順: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md)。Hermes の SOUL/MEMORY 運用ツールはチャットとは別で、基本利用には必須ではありません。

## 版

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261103.3` |
| Engine / Control | `0.4.0`（CUDA sm_120） |
| Hakua-memory | `0.3.5` |
| 上流固定 | `ffa80d73` · 0.2.10 |

App version in this preview tree: `0.4.0-preview.20261103.3`

リリース: [v0.4.0-preview.20261103.3](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.3)。このタグのインストーラーと Qwen3.6 エンジンパッケージに署名はありません。`v0.4.0-preview.20261101.1` の Ed25519 フィードと署名済みエンジンは差し替えていません。アプリ本体の署名付き自動更新は未検証で、更新はこのインストーラーで行います。

インストーラーはアプリだけを更新します。CUDA エンジンは入りません。このタグの Qwen3.6 パッケージは別配布で、画像リーダーは無く、`signature` は null です。PrismML と TurboQuant は `v0.4.0-preview.20261101.1` の署名済みコンポーネントに残しています。

本線は Qwen3.6-35B-A3B UD-Q4_K_XL、context 65536、FP32 KV、MTP 2、prefill auto のままです。新しい経路は opt-in です。エンジンが適用しない設定は起動前に拒否します。private-cache の要求も拒否し、起動させるために外しません。mapped expert pack は、起動がそれを要求し、エンジン SHA-256 が `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5` または `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046` のときだけです。古いダイジェストも許可したままです。既定は従来の host arena です。このビルドの起動時間とトークン速度は未計測です。CUDA spill guard は登録済み baseline に対して不合格です。32GB の PC では、空き物理 RAM が legacy の 18.75 GiB expert arena と reserve を満たさないとき、UD-Q4_K_XL を起動前に拒否できます。それは 16GB VRAM に収まった測定ではありません。

## 制限（測定したプレビュー）

Windows x64、NVIDIA RTX 50 系 / CUDA sm_120。RTX 5060 Ti で確認。ネイティブはテキスト。ネイティブ画像入力と DeepSeek 専用ネイティブエンジンは含みません。他 GPU・OS は別パッケージが必要です。モデルと個人の記憶はアプリフォルダー外へ。個人の記憶・キー・重み本体は配布しません。

Spin(8) / Triality / Query-v3 / Bonsai は明示選択の実験機能です。全体の速度や品質向上は主張しません。

## 開発

```sh
python -m pytest tests/terminal tests/test_hakua_hermes_memory_stack.py
python -m unittest discover -s serve -p 'test_*.py'
npm --prefix apps/host test
npm --prefix apps/host run typecheck
```

[Models](docs/MODELS.md) · [Build](packaging/README.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Issues](https://github.com/zapabob/Strata/issues)

MIT の Strata フォークです。Hakua-memory とモデル重みは個別ライセンスで、原作者と上流のクレジットを残します。約 480 KB の制御ベクトルは既定 OFF、[Qwen Community License 1.0](data/experimental-speed-projection/LICENSE) です。
