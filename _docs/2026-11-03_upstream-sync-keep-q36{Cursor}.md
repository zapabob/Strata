# 2026-11-03 upstream sync, Qwen3.6 契約は維持

## 概要

zapabob/Strata の `main`（`8bbdf043`）から `sync/upstream-q36-keep` を切り、Niko1221/Strata の `upstream/main` をマージした。独自の Qwen3.6 起動契約は残し、上流が変えた呼び出し側は公式 API に載せ替えた。新しい GitHub リリースは出していない。速度も署名も測っていない。

## 背景・要求

- 取り込み元: `upstream/main`
- 取り込み前の上流 SHA: `c62d5e3a15b40ea51c96aae9e8d36928965f53ab`（このフォークが既に含んでいた merge-base）
- 取り込み後の上流 SHA: `ffa80d73133ea5c548aefe57889a16e8085a938f`
- 範囲のコミット数: 708（`git log --oneline c62d5e3a..ffa80d73`）
- タグ `v0.2.10` が fetch で見えた。製品版の自称は Hakua `0.4.0-preview.20261103.2` / engine `0.4.0` のまま。上流の製品番号 0.2.10 / engine 0.1.56 には置き換えていない。

## セキュリティと依存の読み

編集前にコミットメッセージを見た。

- `CVE`、`path traversal`、`vulnerability` という件名は 0 件。
- `gh api repos/Niko1221/Strata/security-advisories` は空。
- 依存パッケージの CVE バンプという件名は 0 件。バージョン上げは製品 0.2.10 / engine 0.1.56（`aa471de5`、`be7d719e`、`72a0cc1d`、`f31abf7b`）。
- 認証・鍵の近く:
  - `6174eed4` / `1f7640a8`: split engine が拒否する GEN キー（`pen_from`）を送らない。`logprobs` / `logit_bias` は `--split-engine off` を名指しする 400。
  - `9efac55f`: Anthropic の `defer_loading` ツール（`#4663`）。
  - `243fdb21`: リクエストは出せる行だけを確定する（`#4677`）。
  - `e4a68ec6`: 起動テストが利用者設定を見ない（テスト分離）。
- `auth` 検索は author / matrix への誤爆が大半だった。

## 前提・判断

- 同じ行がバグ修正またはセキュリティ修正なら上流を採る。
- Qwen3.6 の起動契約、legacy RAM 入場、mapped-pack、起動ステージはフォークの振る舞いを残す。
- 上流が同じ機能を公式 API で足した場合、公式 API を呼び、フォーク側の平行実装は足さない。
- コンテキスト 65536、FP32 KV、MTP 2、prefill auto は Qwen3.6 本線では変えていない。DeepSeek の未測定警告だけ `DSV41_CONTEXT`（128K）に追従した。これは Qwen3.6 の本線ではない。
- 未署名は未署名、未測定の速度は未測定のまま。
- 作業ツリーに未コミットの独自実装はなかった。未追跡の `_docs/intake/`、`_docs/2026-11-02_qwen36-engine-died-host-experts{Cursor}.md`、`_docs/2026-11-03_upstream-qwen36-three-issues{Grok}.md` はコミットしていない。
- `v0.4.0-preview.20261103.3` は作っていない。既存リリースも触っていない。
- Niko1221 へは push していない。force push もしていない。

## 残したフォークの振る舞い

- `--cache-type-*` と手書き `--vram-reserve-mib` は起動前に拒否する。private-cache / prompt-cache を消して起動させない。
- UD-Q4_K_XL の legacy 物理 RAM 入場は spawn 前。legacy expert arena が既定。
- `--q36-expert-store legacy|mapped-pack` は opt-in。mapped-pack は匿名 arena へ落ちない。解決した `strata.exe` のファイルハッシュが allowlist にあるときだけ許す。モデル設定に書いた digest は信じない。
- Q36 起動ステージ。未知のステージは拒否のまま（`q36-startup-events.mjs` は衝突していない）。
- Hakua の版表記、未署名、未測定の記述。

## API の載せ替え

- `buildConfig(args, config, drafter, trusted)`。`chooseParallel` に上流の `drafter` を渡し、Qwen3.6 には `trusted.binarySha256`（実行ファイルの SHA-256）を渡す。
- load は上流の `ensurePictures`、`draftPlan`、`installMtpLayer` のあとで Qwen3.6 契約と RAM ゲートに入る。設定の保存はロード開始時のスナップショットでは上書きしない。`ui_context_chosen` と `picturesNote` は足した。
- `serve/server.py`: Anthropic はメモリハーネスの `self._prepare` を残し、`ContextOverflow.anthropic_text()` と `callable_tools` / `deferred` を上流どおり使う。`apply_vision_defaults(with_component_engine(cfg))` のあとで hakua harness の事前検査を行う。`refuse_for_split` を batched 生成の前に置く。prefill の GEN 行は `rid_key` を含む。`set_restore_points` と perf audit は両方残した。
- `generate.cpp`: `lookup_default.hpp` と HIP の `serve_stop_bound.hpp` を足し、native cache の include も残した。Windows HIP の `engine_main` / `#endif`（`#3431`）を採り、`host_trace` は共有の関数本体に置いた。`dfr_lookup` と `--exact-context-boundary` は両方。lookup chain は `S_look` と `context_room` の両方で頭を抑える。
- `prefill.cpp`: `qsa_fuse_nr()` は native cache セッションが無いときだけ。あるときは RMS と RoPE の間で `query` する古い順を守る。layer-major の既定コメントは上流（未設定ならオフ）に合わせた。実装の呼び出しは自動マージ済みの `prefill_layer_major_resolve`。
- agent bridge の戻り値に `messageHelper` と `answerQuestion` を足し、`startingPid` の debug は残した。
- capabilities に `dflash2Support` / `dflash2Selq4` / `dflash2Split` / `stoppedForUpdate` を足し、`hakuaChatbot` は残した。
- run config の既知キーは `ui_context_chosen` と `hakua_harness` の両方。
- Metal の定義は `STRATA_HAVE_DFLASH2=1` を足し、版文字列は `0.4.0-metal` のまま。
- `PRODUCT_VERSION` は VERSION ファイルの `0.4.0-preview.20261103.2` に合わせた。衝突前の定数は `0.4.0-preview.20261101.1` で、package.json / VERSION より古かった。
- README の上流固定行を `ffa80d73` · 0.2.10 にした。DeepSeek の容量表は Hakua の README 構成に挿すと別物の説明になるので入れていない。英語・日本語・中国語 README に、既存テストが要求する `App version in this preview tree` の1行を足した。衝突前の README にもその文は無かった。

## 変更対象ファイル

衝突は 44 ファイル。解消後に衝突マーカーは残っていない。自動マージされた Qwen3.6 契約ファイル（`q36-run-contract.mjs`、`q36-startup-events.mjs`）はマーカーなし。

## 実行コマンド

```text
git fetch upstream
git checkout -b sync/upstream-q36-keep
git merge upstream/main --no-edit
node --test tests/q36-run-contract.test.mjs tests/q36-capabilities.test.mjs tests/native-control.test.mjs
py -3 -m unittest discover -s tests/qwen36 -p test_*.py
py -3 -m unittest tests.terminal.test_tui2_023_versions.VersionBump.test_the_documents_that_state_the_current_version_agree tests.terminal.test_tui2_023_versions.VersionBump.test_every_place_the_app_version_lives_says_0_2_3 tests.terminal.test_tui2_023_versions.VersionBump.test_version_prints_the_product_and_the_build
```

`tests/q36-startup-events.test.mjs` はこのツリーに無い。

## テスト・検証結果

- host の指定テスト: 19 件成功、失敗 0。所要約 1.2 秒。モデルは起動していない。
- `tests/qwen36`: 7 件成功。
- 版の一致テスト 3 件: README の1行を足したあと成功。
- `node --check`（native-control、native-resources、run-config-check、agent-bridge、local-models、supervisor、q36-run-contract）と `py_compile`（server.py、setup.py、strata_cli）はエラーなし。
- `agent-bridge` の実行テストは Harness が無いため 15 件スキップ、失敗 0。`qa1-storage` は 6 件成功。

## 残留リスク

- C++/CUDA/HIP/SYCL はビルドしていない。`generate.cpp` と `prefill.cpp` の衝突解消は読んだ範囲の括弧と、native cache の呼び出し順に基づく。コンパイラは通していない。
- `apps/host` の全 `npm test` と typecheck は回していない。
- 22GB の Qwen3.6 は起動していない。速度は測っていない。署名は主張しない。
- DeepSeek の 128K 既定は上流に合わせた。Qwen3.6 本線の 65536 / FP32 KV / MTP 2 / prefill auto は契約テストが守っている。実機の起動では未確認。
- この作業は Qwen3.6 の目標完了を意味しない。

## 次の推奨アクション

- sync ブランチのテストが通ったので `main` へ fast-forward し、force なしで `origin` に push する。
- エンジンの実ビルドは別作業。リリース `20261103.3` は作らない。
