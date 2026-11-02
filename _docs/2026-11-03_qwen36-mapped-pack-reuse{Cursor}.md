# Qwen3.6 mapped-pack の再利用を 1 回測った

## 概要

同じ `strata.exe` と同じ引数で、既存の `.q36epk` を開いて 1 回起動した。終了コードは 0。pack は書き直していない。`expert_host_alloc` は 763500 ms で、初回の 2799582 ms より短い。残りはモデル全体の SHA-256 と pack 全体の CRC である。速度改善の採用にはしない。

## 背景・要求

初回は pack 生成を含み、壁時計が約 49.4 分だった。再利用で生成と検証が分かれるかを見る。既定は legacy のまま。context 65536、`--prefill auto`、MTP 2、cache 型なし。

## 前提・判断

- 実行ファイルは初回と同じ `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe`
- 引数は初回と同じ。`--bench-pp 32 --bench-tg 8`
- 開始前の pack は 20127612928 bytes、最終書き込みは 2026-11-03 01:43:42。`.partial` と `.lock` はなかった
- 開始前の VRAM 空きは 14921 MiB。空き物理 RAM は約 21.2 GiB
- 他の `strata` プロセスはなかった

## 実行

開始 `2026-11-02T16:59:04.4059729Z`。終了 `2026-11-02T17:13:31.5009004Z`。終了コード 0。壁時計は約 14.5 分。

観測した行:

- dense load: 753 tensors、GPU 4.40 GiB、50.7 s。`elapsed_ms=50749`
- context 65536、prompt chunk 2048、MTP block loaded、experts 前の VRAM 空き 4.91 GiB
- `expert_host_alloc` end `elapsed_ms=763500`
- hybrid: 41/256 slots、VRAM 3.00 GiB、host は mapped file-backed の 18.75 GiB、CPU threads 6、staging 1.10 GiB、766.1 s
- warmup: prefill 12426 ms、decode 57 ms、spec 86 ms。ログの合計は 12.8 s
- bench 0: pp32 32.9 tok/s、tg8 29.1 tok/s
- bench 1: pp32 109.4 tok/s、tg8 32.1 tok/s
- bench 2: pp32 113.0 tok/s、tg8 31.6 tok/s
- hybrid 集計: GPU 25610/39168（65.4%）、CPU pool 13558 件で 1039 ms、slot replacement 1604

終了後も pack のサイズは 20127612928 bytes のまま。`.partial` はできていない。検証中の作業セットは約 18.1 GiB まで上がり、その時点の空き物理 RAM は約 2.5 GiB だった。これは file-backed の読み込みであり、新しい匿名 arena の確保ログはない。

## テスト・検証結果

再利用は終了コード 0。本線の context、chunk 2048、MTP 2 はログに残っている。

初回との差は 1 組だけ:

| 項目 | 初回 | 再利用 |
|---|---:|---:|
| `expert_host_alloc` | 2799582 ms | 763500 ms |
| hybrid ログの秒 | 2821.5 s | 766.1 s |
| warmup 合計 | 82.0 s | 12.8 s |
| 壁時計 | 約 49.4 分 | 約 14.5 分 |

`expert_host_alloc` の短縮は、pack を再生成しなかったことと一致する。コードは再利用のたびに GGUF 全体を hash し、pack 全体の CRC を見る。763500 ms はその費用を含む。

warmup の 82.0 s と 12.8 s は、直前のプロセス終了から約 90 秒後の 1 組である。CUDA の残留を分けていないので、mapped-pack が warmup を縮めた証拠にはしない。

合格にしていないもの:

- 5 組の paired run はない
- legacy との同日比較はない
- pp32 / tg8 は本線の 2048 token 速度ではない
- chat、stop、restart は未実行
- T04、T06、T07 は既定化していない

## 残留リスク

再利用でも起動前の全ファイル検証が約 12.7 分ある。検証中に空き物理 RAM が約 2.5 GiB まで減った。GUI はこの直接起動のログを表示していない。

## 次の推奨アクション

検証費用を隠す変更は、測定で分けてからにする。既定は legacy のまま。
