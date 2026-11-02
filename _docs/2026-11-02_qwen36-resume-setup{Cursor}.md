# Qwen3.6 UD-Q4 の導入を続きから完了した

- **日付**: 2026-11-02 18:20 JST
- **実装**: Cursor

## 内容

本体 `H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf` はピン留めサイズと SHA-256 が既に一致していた。`--gguf-dir` を外し、導入済みの setup を `--yes --no-start` で再実行した。

## 結果

exit 0。約 7 秒。

- モデルファイルは already downloaded
- トークナイザ: `H:\Strata\models\packs\qwen36-ud-q4_k_xl\tokenizer`
- 起動設定: `C:\Users\downl\AppData\Local\Strata\install\strata-qwen36-ud-q4_k_xl.json`
- 起動スクリプト: `C:\Users\downl\AppData\Local\Strata\install\run-qwen36-ud-q4_k_xl.bat`

モデル自体は起動していない。UD-Q4_K_XL は RAM 約 32 GB を求め、この PC は 32 GB。
