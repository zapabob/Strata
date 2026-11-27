# Hakua / Strata

[English](README.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Polski](README.pl.md)

Hakua / Strata は、[Niko1221/Strata](https://github.com/Niko1221/Strata) を基にした Windows 向けフォークです。チャット、コーディング、エージェント作業をローカルモデルで実行できます。対応する MoE モデルでは、ネイティブエンジンが Expert の重みを VRAM、システム RAM、SSD に配置できます。

## はじめる

[Hakua のリリース](https://github.com/zapabob/Strata/releases)からユーザー単位の Windows インストーラを取得します。CUDA エンジンは別配布です。アプリの「モデル」から、インストールしたモデルに合う版を選びます。Inkling 2 Mini の SC117 シリーズは SQ-10、SQ-15、SQ-20 を個別に選べます。コンテキスト長は空きメモリーに合わせて設定してください。[Windows の導入ガイド](docs/HAKUA_INSTALL.md)と[モデル一覧](docs/MODELS.md)に対応条件を記載しています。

## 作業手順をスキルとして再利用する

「設定」→「ツール」の「スキルを必要なときに検索」をオンにすると、エージェントは全件一覧を受け取らず、必要な手順だけ検索して読み込みます。「スキル」画面では、完了した作業からの学習と、保存した手順の自動適用を個別に切り替えられます。手順は編集可能な `SKILL.md` として保存されます。自動適用は名前、起動フレーズ、ワークスペースの条件を確認します。「スキル」「補助エージェント」「ファイル操作」「目標」はそれぞれ個別に設定できます。[ワークフローの使い方](docs/WORKFLOW_SKILLS.md)

## 実機結果と測定範囲

RTX 5060 Ti 16 GB で、SC117 SQ-10 が Strata の `/goal` から Pagoda Bench の単体 HTML を生成し、診断を受けて自分で描画器を修正しました。Chrome で縮小すると屋根が5枚見え、モデルの計測値は7,079ボクセルでした。初期表示では上端が切れ、公式スコアは未測定です。[0.8.5 のエンジン計測](_docs/2026-11-27_v085-release-notes.md)では、記載したコンテキスト容量で短い入力を測りました。最大長の検索能力については別の試験が必要です。

コンポーネントの互換性、署名、検証範囲は[リリース記録](docs/HAKUA_RELEASE.md)を参照してください。Hakua 本体は [MIT ライセンス](LICENSE)で配布します。モデルと同梱コンポーネントには個別の利用条件があります。
