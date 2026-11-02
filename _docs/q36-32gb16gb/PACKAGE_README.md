# Strata Qwen36 / RAM 32GB・VRAM 16GB 実装計画パッケージ

作成日: 2026-11-02 JST

## 読む順序

1. `DESIGN.md` — 目的、観測事実、未確定事項、方式比較、不変条件。
2. `Strata_Qwen36_Implementation_Plan_2026-11-02.md` — T00–T09、変更箇所、提案interface、TDD、mutation、回帰、Windows GPU / API / GUI試験、ロールバック、実装者向け指示。
3. `evidence-summary.json` — ユーザー提供の同一ログ2件を重複除外した集計。

`SHA256SUMS.txt` はこのパッケージの内容確認用です。

## 実装者へ

最初に公開mainとローカルworktree、インストール済みcomponentの実identityを再確認してください。公開mainの読取基準は `170e0d330edd9c03b5dcddfc64b77e498387ff86` です。このSHAと実行中EXEが同一sourceから作られたとは、このパッケージでは認定していません。

主baselineは同一Qwen3.6-35B-A3B UD-Q4_K_XL、context65536、同じtokenizer・FP32 KV・MTP2・実効prefill2048です。低context、低精度、別モデルへの置換を主改善へ混ぜないでください。

## 今回実施した確認

- ユーザー添付ログを全85行読み、2ファイルのbyte同一性とSHA-256を確認。
- 起動22、host allocation失敗14、VRAM不足2、expert配置完了2、warmup完了1を再集計。
- 公開mainとQwen36のload・expert layout・placement・warmup・引数処理・dispatch、Host resource設定を読取確認。
- 計画書のメモリ算術、task構成、Markdown fence、同梱ファイル、ZIP整合性を確認。

## 実施していないもの

Strata本体へのpatch適用、Windows PCの操作、モデル起動、CUDA build、CPU/GPUの実装テスト、速度・品質ベンチマーク、GitHubへのcommit/push/PR/merge/release。

本パッケージは計画資料であり、実装済みpatchや実行バイナリではありません。新しいflag/API/test targetは実装案です。過去の会話で作成済みとされたpatchやテスト成績は再利用していません。

原本ログには個人pathが含まれるため、原本はZIPへ複製していません。元ファイルのSHAと原本行番号からユーザー手元で照合できます。
