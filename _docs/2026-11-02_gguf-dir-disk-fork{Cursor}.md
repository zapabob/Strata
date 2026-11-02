# 公式の空き容量修正を zapabob/Strata の作業ツリーへ移した

- **日付**: 2026-11-02 18:12 JST
- **実装**: Cursor
- **対象**: `C:\Users\downl\Documents\ChatGPT\Strata` の `main`（未コミット）
- **元**: `fix/gguf-dir-disk-on-data-dir` の `9cf18021`（PR https://github.com/Niko1221/Strata/pull/4989）

## 内容

`--gguf-dir` は手持ちのファイル置き場である。空き容量は、これから書き込む先のドライブだけを見る。

- Qwen3.6: ピン留めファイルが無いときは、空き容量を見る前に missing と言う。そのフォルダへは落とさない。
- Flash-Next: pack と draft は data フォルダへ書くので、空き容量もそこを見る。
- DeepSeek: `--gguf-dir` に無いシャードは、そのドライブの必要量に入れない。共有ファイルは受け取るドライブに計上する。同じドライブのバイトは一つの枠のまま。

以前の作業ツリーにあった「無いファイルは黙って `--data-dir` へ落とす」動きは、公式側の契約と違うので捨てた。

## 検証

`py -3 -m unittest tools.test_setup_qwen36 tools.test_setup_unsloth.DiskRoom` と DeepSeek の空き容量 3 本。26 件 OK。

## ワークツリー

`H:\Strata\worktrees\gguf-dir-disk-check` は `git worktree remove` で消した。ブランチ `fix/gguf-dir-disk-on-data-dir` は fork に残してある。PR がそれを指している。
