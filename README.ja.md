# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata は、[Niko1221/Strata](https://github.com/Niko1221/Strata) を基にした Windows 向けフォークです。チャット、コーディング、エージェント作業をローカルモデルで実行できます。対応する MoE モデルでは、ネイティブエンジンが Expert の重みを VRAM、システム RAM、SSD に配置できます。

## Windows へのインストール

[Hakua の最新リリース](https://github.com/zapabob/Strata/releases/latest)から、ユーザー単位の Windows インストーラーを取得します。CUDA エンジンとモデルの重みは別配布です。Inkling 2 Mini の SC117 パックを使う場合は、「モデル」で対応する SQ-10、SQ-15、SQ-20 を選び、空きメモリーに合うコンテキスト長を設定してください。[Windows の導入ガイド](docs/HAKUA_INSTALL.md)

## Inkling 2 Mini CHiPS

Hakua 0.8.8 は Strata 0.2.23 の差分を取り込み、Inkling SQv2 の 16 KiB `.strata` 形式に対応しました。[Inkling 用の CUDA エンジン](docs/HAKUA_INSTALL.md#inkling-2-mini-chips)を入れ、「モデル」から手元のファイルを指定します。カスタムモデルには専用の識別子が付き、重みは元の場所から読み込みます。最初は 4,096 トークン、1 スロットで、ドラフトと画像入力をオフにして起動できます。完全な CHiPS SQv2 パックを RTX 5060 Ti 16 GB で読み込み、チャット API で応答を確認しました。[CHiPS モデル配布ページ](https://huggingface.co/Kujira/Inkling-2-Mini-Strata-CHiPS-Abliterated) · [検証記録](_docs/2026-11-28_upstream-023-hakua_Codex.md)

## 作業手順をスキルとして再利用する

「設定」→「ツール」の「スキルを必要なときに検索」をオンにすると、エージェントは全件一覧を受け取らず、必要な手順だけ検索して読み込みます。「スキル」画面では、完了した作業からの学習と、保存した手順の自動適用を個別に切り替えられます。手順は編集可能な `SKILL.md` として保存されます。自動適用は名前、起動フレーズ、ワークスペースの条件を確認します。「スキル」「補助エージェント」「ファイル操作」「目標」はそれぞれ個別に設定できます。[ワークフローの使い方](docs/WORKFLOW_SKILLS.md)

実際の Harness と試験用の応答を使い、ストリーミング、承認、停止、再開など33件のテストが通りました。DS4 の起動経路も維持しています。DS4 の実重量による生成、最大コンテキストでの検索、GPU の同時使用には別途検証が必要です。互換性と署名は[リリース記録](docs/HAKUA_RELEASE.md)に記載しています。Hakua 本体は [MIT ライセンス](LICENSE)で配布します。モデルと同梱コンポーネントには個別の利用条件があります。
