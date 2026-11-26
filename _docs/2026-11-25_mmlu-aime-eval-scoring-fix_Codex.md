# 2026-11-25 — MMLU 0/30 および AIME 虚偽満点の評価ハーネス修正

## 概要
Mode B（NVFP4 + Dense PQ2_0）のモデルカード評価で MMLU が 0/30 になった原因を調査し、採点ハーネス
`research/inkling-bonsai2/heretic_model_card_eval.py` を修正した。同じ評価スクリプトにあった AIME の
虚偽満点（6/6）も併せて修正し、TDD で 4 件の回帰テストを追加した。

## 背景・要求
- 別セッションの Phase XIII/XIV で `modeB_model_card_eval_v2/heretic_model_card_eval.json` に
  `mmlu.correct=0 / evaluated=30` が記録され、モデル品質の判断が不可能になっていた。
- 要求: 0/30 の原因を特定し、正しい MMLU 値を再計測できる状態にする。証跡のない数値は_MODEL_CARD.md_
  に載せない。

## 前提・判断
- PC 全体の `AGENTS.md` / `C:\Users\downl\_docs\prompts\CLAUDE-FABLE-5.md` / MILSPEC 自己標準 /
  `SOP-Implementation-Start-Gate.md` を適用。対象は既存 research スクリプトと回帰テストのみ。
- 選択した SOP: Common → Implementation Start Gate → Skill Selection → Application Development → Python。
- 選択した Skill: `milspec-codex-standard`, `deepresearch-defense-standard`（Web 情報不要と判断）,
  `systematic-debugging`, `test-driven-development`。
- 这次の作業はローカル証跡のみで完結し、Web 検索は行わない。

## 根本原因（3 点、いずれも証跡あり）
1. **MMLU 0/30（主因）**: `evaluation/mmlu-sm120/selection.json` の各 item は `row` / `tokens` /
   `answer` のみで、`question` / `choices` を持たない。旧 `run_mmlu_subset()` は
   `item.get("question")` と `item.get("choices")` を読むため `q=""`, `choices=[]` となり、
   **空プロンプト**を送信していた。サーバログ `heretic_eval_server.log` の MMLU 1 問目は
   `prompt eval time = ... / 13 tokens`、2 問目以降は `/ 3 tokens` で、空 user message のチャット
   テンプレート分しか無い。復号確認では `tokens` が
   `The following are multiple choice questions ... A basketball player scored 18 points ... A. ... Answer:`
   に正しくなり、選択肢 A/B/C/D と `Answer:` が 30/30 揃っている。
2. **AIME 6/6 は虚偽**: `aime2025/gold.json` のキーは `aime25-00` 形式、`test.jsonl` の `id` は
   `0` 形式。旧コードは `gold.get(qid, "")` なので `expected=""` となり、モデル出力が空
   （`content=""`, `finish_reason="length"`）のとき `predicted=""` と一致して全問「正解」に
   なっていた。拒否挙動も全 24 件 `response_chars=0, finished=false` で、推論トークンが
   `<|content_thinking|>` 側に留まり `content` が空のまま cap に達した可能性が高い（未修正・後述）。
3. **空予測の誤採点**: 上記の通り、`expected` と `predicted` が両方空でも正解扱いになる
   ガード欠如。

## 変更対象ファイル
- `research/inkling-bonsai2/heretic_model_card_eval.py`（修正）
- `research/inkling-bonsai2/test_heretic_model_card_eval.py`（新規、回帰テスト 4 件）
- `H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v2\mmlu_selection_decoded_v2.json`（新規・デコード証跡）
- 本ログ

## 実装詳細
- `load_mmlu_tokenizer(path)` を追加し、`tokenizers.Tokenizer.from_file` でローカル tokenizer を読み込む。
- `run_mmlu_subset(..., tokenizer_path: Path | None = None)` を変更:
  - `question`/`choices` がある従来形式はそのままテキスト生成評価。
  - `tokens` のみのピン留めセレクションはトークン ID を元のプロンプト文本に復号して評価。
  - 両方とも無い item は `ValueError` で即時失敗（空プロンプトを黙って採点しない）。
  - 復号後も空文字なら失敗。
  - `prompt_source`, `records`（row / gold / predicted / response_chars / finish_reason /
    prompt_chars / latency_s）を出力に追加し、監査可能にした。
  - `pred` が空のときは正解にしない。
- `gold_for(gold, qid)` を追加し、`aime25-00` / `apex25-00` のゼロ埋めキーと raw id の両方を解決。
- AIME / Apex で `expected` または `predicted` が空のとき正解扱いしないようにした。
- CLI に `--mmlu-tokenizer` を追加し、`main()` から `run_mmlu_subset` へ渡す。

## 実行コマンド
```
& 'H:\ComfyUI_Qwen\.venv\Scripts\python.exe' -m pytest \
  'C:\Users\downl\Documents\ChatGPT\Strata\research\inkling-bonsai2\test_heretic_model_card_eval.py' \
  -v --tb=line -p no:cacheprovider
& 'H:\ComfyUI_Qwen\.venv\Scripts\python.exe' -c "...compile(...)..."
& 'H:\ComfyUI_Qwen\.venv\Scripts\python.exe' mmlu_decode_evidence.py
```

## テスト・検証結果
- RED（修正前）: 4 件すべて失敗。理由は `run_mmlu_subset() got an unexpected keyword argument
  'tokenizer_path'`（2 件）、`assert 0 == 1`（AIME gold）、`assert 1 == 0`（空採点）。
- GREEN（修正後）: **4 passed in 4.00s**。
- `compile()` による構文チェック: `compile-ok`。
- デコード証跡: `count=30`, `all_nonempty=true`, `all_have_choices=true`,
  `all_end_with_answer=true`。
- **未実施**: 実機での MMLU 再計測。実行時に RTX 5060 Ti が 13,868 MiB / 16,311 MiB 使用
  （空き 2,183 MiB）で、別タスクの 131K–147K VRAM 試験が稼働中のため、新しい llama-server を
  起動できない。競合を避けるため実行しなかった。

## 残留リスク
- 既存の `heretic_model_card_eval.json` の `mmlu.accuracy_pct=0.0` と
  `aime2025.accuracy_pct=100.0` は**無効**。修正済みハーネスで再計測するまで MODEL_CARD / HF
  アップロード / 0.8.2 リリースに使用してはならない。
- 拒否挙動の `content=""`（24/24）は未修正。`<|content_thinking|>` の推論が cap 内で
  完了しないことが原因の可能性があるが、確認には libera な GPU が必要。現状の
  `benign_over_refusal_rate_pct=0.0` も「拒否していない」ことを意味しない。
- MMLU 再計測では `reasoning_effort="none"` でも `content` が空になる場合は、letter を
  `reasoning_content` から抽出する方針を検討する（現状は空を不正解として安全側に倒している）。

## 次の推奨アクション
1. 他タスクの VRAM 試験完了後、以下で再計測する:
   ```
   H:\ComfyUI_Qwen\.venv\Scripts\python.exe research\inkling-bonsai2\heretic_model_card_eval.py \
     --model H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\ablated-models\Inkling-2-Mini-Heretic-ModeB-NVFP4-DensePQ2.gguf \
     --server H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\llama-server.exe \
     --rust-preflight H:\Strata\builds\strata-inkling-native-pq2-sm120\strata-gguf-preflight.exe \
     --prism-scales H:\Strata\builds\strata-inkling-native-pq2-sm120\prism-loop-scales.exe \
     --mmlu-selection H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\mmlu-sm120\selection.json \
     --mmlu-tokenizer H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\source\tokenizer.json \
     --mmlu-limit 30 \
     --aime-dir H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\aime2025 --aime-limit 6 \
     --out-dir H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3
   ```
   実際の exe パスは v2 の実行記録で確認して微調整する。
2. 再計測値を `records` と突き合わせ、`prompt_source=tokens` かつ `response_chars>0` を確認する。
3. 拒否挙動の空 `content` は別チケットとして、`reasoning_content` の扱いを切り分けてから修正する。

---

## 実機再計測の結果（2026-11-25 追加）

### 生成方式（修正済みハーネス、v3）
`run_mmlu_v3.py` で Mode B GGUF をctx 4096・OT 8 層 CPU オフロードで起動し、
修正済み `run_mmlu_subset()` を 30 問に適用した。

- `load_seconds=152.04`, `eval_seconds=91.65`, `prompt_source=tokens`
- プロンプト長 158–545 文字（空プロンプトの問題は解消）
- **しかし全 30 件が `response_chars=0`, `finish_reason="length"` で 0/30。**
- サーバログには `chat template supports preserving reasoning, it is enabled by default`
  とあり、16 トークン枠を推論トークンが消費して `content` が空になったと考えられる。
- よって生成方式の MMLU 0/30 はモデル品質ではなく**ハーネスの制約**。
  `mmlu_v3.json` はそのまま残すが、MODEL_CARD には載せない。

### ネイティブ logits 方式（上流モデルカードと同一プロトコル、v3）
`run_mmlu_native_v3.py` で `inkling-logits.exe --last --gpu-layers 99` を実行し、
ピン留めセレクションの `label_token_ids` に対する next-token logits を argmax した。

- `tool_rc=0`, 30/30 完了, ログ `/native/inkling-logits.log`
- **15/30 = 50.0%**（予測分布 A:8 / B:2 / C:17 / D:3、正解分布 A:9 / B:9 / C:5 / D:7）
- トークン長 55–166、各 4 つの有限 logits を確認
- 上流の 77.0%（1,000 問・mixed subject）とは問題数と科目が異なるため直接比較しない。

### 成果物
- `H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3\mmlu_v3.json`
- `H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3\mmlu_native_v3.json`
- `H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\MODEL_CARD.md`（検証済み数値のみ記載、
  未計測項目は `Not measured` として明示。AIME 6/6 と拒否 0% は除外）

### 追加の未完了
- 推論トークンと `content` の分離を確認する `probe_reasoning_response.py` は、他タスクが
  GPU を再占有したためサーバが起動直後に終了し、結果が出なかった。orphan プロセスを停止済み。
  `reasoning_content` 対応は未実施のまま。
- 防御を追加: 全回答が空 `content` の場合、`measured=False` と理由を返し、0.0% と誤報告しない
  （回帰テスト 5 件すべて通過）。これは v3 の生成結果ファイルを作成した後に加えたため、
  `mmlu_v3.json` 自体は古い形式のままだが、README で無効と明記している。
- HF アップロードと 0.8.2 上書きリリースは行っていない。__`releaseQualified=false` は維持__。
