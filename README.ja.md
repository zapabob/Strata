# Hakua / Strata

Strata 上の Hakua チャットボット。このリポジトリは **zapabob Hakua フォーク**です。Windows プレビューの導入経路は、上流 Niko1221 のインストーラー経路ではありません。

[zapabob/Strata](https://github.com/zapabob/Strata) · 上流 [Niko1221/Strata](https://github.com/Niko1221/Strata)

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

## 導入（Windows プレビュー）

現行の公開アプリタグ: **[v0.4.0-preview.20261103.7](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.7)**。このタグの公開物は setup EXE と `SHA256SUMS.txt` のみです（対応する 7z はありません）。

1. [`Strata_0.4.0-preview.20261103.7_x64-setup.exe`](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.7/Strata_0.4.0-preview.20261103.7_x64-setup.exe) を取得します。
2. 実行前に [`SHA256SUMS.txt`](https://github.com/zapabob/Strata/releases/download/v0.4.0-preview.20261103.7/SHA256SUMS.txt) と照合します。Windows のコード署名はありません。setup EXE の SHA-256 は `5e8b8fff82b6e63dea48bf5c1907950911700c9bf30673444e5d2489a87c0336`（113,064,953 bytes）です。
3. すでに入っている場合はトレイから「Strata を終了」で完全終了してから EXE を実行します。導入済みなら `/S /UPDATE` で更新できます。
4. インストーラーはアプリを更新します。CUDA エンジンは入りません。導入後は下表のとおり、準備画面またはファイル取り込みで GPU 実行環境を入れます。

クリック手順は短いです。ダウンロード・エンジン有効化・モデル読み込みには時間がかかり、空き容量と VRAM も必要です。詳細は [HAKUA_INSTALL.md](docs/HAKUA_INSTALL.md)。測定した範囲は [HAKUA_RELEASE.md](docs/HAKUA_RELEASE.md)。上流 Niko1221 のインストーラーで本フォークを置き換えないでください。

## エンジン（署名あり / なし）

次のふたつを混ぜないでください。未署名を署名済みと書いてはいけません。

| コンポーネント | 場所 | 署名 | 識別子 |
| --- | --- | --- | --- |
| `.7` のアプリインストーラー | このタグ | Windows コード署名なし。アプリの Ed25519 自動更新でもない | 上記 setup SHA-256 `5e8b8fff…` |
| 署名付き CUDA（ネイティブ + PrismML + TurboQuant） | 引き続き [v0.4.0-preview.20261101.1](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261101.1) | 同タグで公開された Ed25519 フィード／コンポーネント | ネイティブエンジン digest `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1` — `.7` アプリタグでは **未変更** |
| `.7` の Qwen3.6 並列パッケージ | 別配布の未署名コンポーネント（`0.4.0-q36-…`） | `signature` は null。画像リーダーなし | hotspot-profile `strata.exe` SHA-256 `907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150`（`native-build.json` `cd235fdf812d43c45e0a0881073bee97483c5aa50c65bbefb877bd1e8e8dbd8b`。古い許可 digest は下表） |

PrismML と TurboQuant は署名済み `.20261101.1` コンポーネントに残ります。`.7` リリースはそれらのファイルを差し替えません。

## インストーラーに入るもの

| アプリインストーラー | 別配布 |
| --- | --- |
| GUI / Host、専用 Node 24.22.2、Control / CPython 3.12.15、Hakua-memory 0.3.5、Harness | CUDA エンジン（上表）。モデル重み（数十〜数百 GB） |
| この EXE による手動アプリ更新 | 署名付き自動アプリ更新は未検証 |

公開アプリにシステム側の Node / Python / pip / コンパイラーは不要です。

## ローカルモデルの読み込み

- **ネイティブ Strata パック**（対応する Qwen 系テキスト）：アプリのネイティブ準備／読み込みを使います。
- **Hikari / PQ2_0 GGUF**：**Load with Strata**（PrismML）を使います。PQ2_0 にネイティブ準備は使いません。
- **通常 GGUF + TurboQuant キャッシュ**：バックエンド `TurboQuant`、K=`FP16`、V=`TURBO2` / `TURBO3` / `TURBO4` にして読み込み直します。K 側 TurboQuant は実モデルで返答崩れが再現したため無効です。

PrismML と TurboQuant は署名付きエンジン内の別実行ファイルです。[LOCAL_LLAMA_BACKENDS.md](docs/LOCAL_LLAMA_BACKENDS.md)。GPU に収まるパックを ISTA-DASLab → Unsloth → Gyro の順で選びます。

モデルが Strata / supervisor 経路で動いているとき、Agent はそのローカル実体経由で、モデルが対応するツール（例: web search）を使えます。ネイティブ専用セッションでは同じ経路にはなりません。

## Hakua memory

対応モデルを読み込んだあと、サイドバーの **Hakua memory** を開きます。参照と保存の同意は別々で、送信ごとにリセットされます。

- ネイティブ：ダイアログのキーを About → Settings に貼り、記憶ページでチェックします。
- PrismML / TurboQuant：アプリがローカルキーを使います。初回は処理中のリクエストを終えてから開いてください（認証付き・共有キャッシュ無効でサーバーを起動し直します）。

手順: [MEMORY_HARNESS.md](serve/MEMORY_HARNESS.md)。Hermes の SOUL/MEMORY 運用ツールはチャットとは別で、基本利用には必須ではありません。

## 版

| | |
| --- | --- |
| GUI / Product | `0.4.0-preview.20261103.7` |
| Engine / Control | `0.4.0`（CUDA sm_120） |
| Hakua-memory | `0.3.5` |
| 上流固定 | `ffa80d73` · 0.2.10 |

リリース: [v0.4.0-preview.20261103.7](https://github.com/zapabob/Strata/releases/tag/v0.4.0-preview.20261103.7)。このタグのインストーラーと Qwen3.6 エンジンパッケージに署名はありません。`v0.4.0-preview.20261101.1` の Ed25519 フィードと署名済みエンジンは差し替えていません。アプリ更新はこのインストーラーで行います。

## Qwen3.6（32 GB RAM / 16 GB VRAM）

本線は Qwen3.6-35B-A3B UD-Q4_K_XL、context 65536、FP32 KV、MTP 2、prefill auto のままです。新しい経路は opt-in です。エンジンが適用しない設定は起動前に拒否します。private-cache の要求も拒否し、起動させるために外しません。

mapped expert pack は、起動がそれを要求し、解決した `strata.exe` の SHA-256 が次のいずれかであるときだけです。

- `907341c74d5a9f26c784e4aaad3460e376d4cabd84635c5d032879c59b08d150`（未署名 Q36 hotspot-profile。T07 プロファイル取得 PASS）
- `64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`（未署名 Q36 help-honesty 再ビルド。mapped-live READY を記録）
- `6fe110650940d0c19f09909d769393769650045e6bc6eab29ccc49734dbcab29`
- `dd53df07789e0fefcb87e33acab54f5bfe1faf312ef6bad515924736b715c5b5`
- `512d7f8bba66b57fbe0f8b90807825d3b3172a86dd039452bc29e685ca27d046`（古い digest。引き続き許可）

モデル設定に書いた digest ではフラグは開きません。既定は従来の host arena です。T04 採用は **KEEP_DEFAULT** です（bounded policy NOT_RUN）。T06 スケジューラは **BLOCKED** のままです。T07 hotspot **プロファイル**取得は PASS、kernel opt-in は NOT_RUN です。T08 は refuse PASS / 測定 FP16 NOT_RUN です。このビルドの起動時間とトークン速度は、観測メモ以上の主張をしません。CUDA spill guard は登録済み baseline に対して不合格です。

32GB の PC では、空き物理 RAM が legacy の 18.75 GiB expert arena と reserve を満たさないとき、UD-Q4_K_XL を起動前に拒否できます。それは 16GB VRAM に収まった測定ではありません。

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

MIT Strata フォーク。Hakua-memory とモデル重みは各自のライセンス。クレジットは原著者と上流に帰属します。任意の約 480 KB control vector は既定オフ（[Qwen Community License 1.0](data/experimental-speed-projection/LICENSE)）。
