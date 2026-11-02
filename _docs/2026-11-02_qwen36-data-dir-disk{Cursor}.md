# Qwen3.6 の空き容量チェックを data-dir に合わせる

- **日時**: 2026-11-02 17:41 JST（ローカル時計。時刻MCPは接続失敗）
- **実装AI**: Cursor (Grok)
- **GPU**: RTX 5060 Ti 16GB

## 仮説

1. 失敗は `C:\Users\downl\Desktop\gguf_models` の空き不足（必要 ~23GB、空き ~21GB）。
2. 起動引数は既に `--data-dir H:\Strata\models`（H: 空き約169GB）を渡している。
3. `--gguf-dir` に公式 `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` が無いのに、setup がそのフォルダをダウンロード先として空きを見ていた。

## 検証

- `native-jobs.json` / `setup.log` の実コマンドは  
  `--family qwen36 --model UD-Q4_K_XL --data-dir H:\Strata\models --gguf-dir C:\Users\downl\Desktop\gguf_models`。
- Desktop 側にあるのは別名の `Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive-Q4_K_M.gguf`（約19.7GB）。公式ファイルは無い。
- `install_own_path` は `--gguf-dir` があるとそこへ 22.9GB の空きを要求し、ファイルが無い場合は後段で「missing」になる。先に C: で落ちていた。

## 実装

`setup.py`（リポジトリ、`apps/desktop/src-tauri/resources/control/setup.py`、インストール済み `Programs\Strata\control\setup.py`）:

- `--gguf-dir` にピン留めファイルが無いときは、そのフォルダをダウンロード先にしない。
- 取得先は `--data-dir` 由来の `models/qwen36-<size>`。空きチェックもそちら。
- ファイルが既にある `--gguf-dir` は従来どおりそのまま使う。

## 検証結果

```text
py -3 -m unittest tools.test_setup_qwen36
→ 22 tests OK
```

同じ引数で再実行し、ディスクチェックを通過。ダウンロード先:

`H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`

Step 5 開始時点で進捗 0.79 / 22.85 GB。`.part` は H: に作成済み。H: 空きは約166GB。

## 注意

UD-Q4_K_XL は RAM 約32GB を要求し、このPCも 32GB。ページングの余地は小さい。
