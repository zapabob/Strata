# 上流へ Qwen3.6 の issue を3本出した

- 日時: 2026-11-03T03:41:20+09:00
- 実装AI: Grok
- 対象: Niko1221/Strata の issue。コード変更なし。pull request なし。

## 概要

CONTRIBUTING.md の通り、既存の issue と pull request を検索したあと、問題ごとに1本、上流へ issue を開いた。権限不足は起きていない。zapabob/Strata への代替 issue は作っていない。

## 背景・要求

Qwen3.6-35B-A3B UD-Q4_K_XL の legacy expert arena、未適用フラグ、opt-in mapped pack を、上流の議論に載せる。mapped-pack の pull request は開かない。fork の main は push しない。force-push もしない。

## 前提・判断

- 上流の基準コミットは `c62d5e3a15b40ea51c96aae9e8d36928965f53ab`。
- `qwen36`、`qwen3.6`、`q36`、expert arena、host memory、`cache-type`、`vram-reserve`、`mapped-pack`、`q36epk`、`no host memory`、`physical_reserve` を `gh` で検索した。
- 近いスレは別問題だった。#4116 は IQ3_S の error 1453。#4051 は一般 arena が拒否せずホストを詰まらせる件。#3508 は Pascal の expert cache 配置。#3303 は `--kv` 未解析。#4882 は Maya。#4134 は `strata launch` の未知引数。#4044 は Q2_0 の `experts.bin` サイズ不一致。#640 は既存の Linux mapped arena。コメント追加はしていない。
- タイミングはすべてこの PC の1回。資格試験や他機への一般化としては書いていない。mapped-pack を速いとは書いていない。
- インストーラのハッシュ、エンジン digest の allowlist、フォークの版文字列は本文に入れていない。

## 変更対象ファイル

ワークスペースのソースは変更していない。追加したのはこの実装ログだけ。

## 実装詳細

開いた issue:

1. https://github.com/Niko1221/Strata/issues/5021
   `[Engine] Qwen3.6 UD-Q4_K_XL: refuse the full host expert arena before the process starts`
   起動前拒否をどの経路に置くかは未決、と書いた。`native-control.mjs` へのパッチは要求していない。
2. https://github.com/Niko1221/Strata/issues/5023
   `[Engine] Qwen3.6: refuse --cache-type-* and a hand-written --vram-reserve-mib before start`
3. https://github.com/Niko1221/Strata/issues/5022
   `[Engine] Qwen3.6: agree the scope of an opt-in mapped expert pack before any patch`
   範囲合意の前に PR は出さない。pin pool（2×32 MiB）と transfer scheduler は未計測のため範囲外。startup stage は後続候補。

引用した fork のコミット: `fa894d95`、`d83f93f9`、`a91353fe`、`0928d45c`、`bc9de663`。

## 実行コマンド

- `gh search issues` / `gh search prs`（Niko1221/Strata）
- `gh issue view` で近傍スレを確認
- `git grep` / `git show` で `c62d5e3a` の `src/qwen35/q36_engine.cu` を確認
- `gh issue create --repo Niko1221/Strata` を3回。いずれも exit 0

## テスト・検証結果

- Passed: 3 issue とも state OPEN。タイトルは上記と一致。
- Failed: なし。
- Not run: エンジンの再起動、CUDA ビルド、ベンチマーク。この作業は投稿のみ。

## 残留リスク

- メンテナが近傍スレと重複と判断して閉じる可能性はある。検索時点では同一問題のスレはなかった。
- 起動前拒否の置き場所は issue 上の質問のまま。合意はまだない。
- mapped-pack の2つのミリ秒は各1回。再測定も既定変更の根拠にもしていない。
- 広い検索の途中で Search API が一時的に 403 になった。その後、残りの語は制限回復後に検索した。

## 次の推奨アクション

- 上流の返信を待つ。範囲の合意前に mapped-pack の pull request は開かない。
- Qwen3.6 の計画目標は、この投稿だけでは完了ではない。
