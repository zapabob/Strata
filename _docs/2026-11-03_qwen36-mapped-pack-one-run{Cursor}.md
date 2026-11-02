# Qwen3.6 mapped-pack を 1 回だけ起動した

## 概要

インストール済みの `strata.exe` で、UD-Q4_K_XL を `--q36-expert-store mapped-pack` にして 1 回起動した。終了コードは 0。legacy の巨大な匿名 arena は取っていない。ログは「18.75 GiB in mapped file-backed host memory」と出た。

これは初回の pack 生成を含む 1 回の計測である。既定は legacy のまま。速度改善とは書かない。

## 背景・要求

legacy は空き物理 RAM が足りず、起動前に拒否される。mapped-pack は opt-in で、pack はモデルの隣に作る。H: の空きは計測前 83 GiB だった。VRAM の空きは計測前 14944 MiB だった。ポート 8080 は空だった。

## 前提・判断

- 実行ファイル: `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe`
- 引数: `--native` に GGUF、`--max-context 65536`、`--prefill auto`、`--mtp 2`、`--q36-expert-store mapped-pack`、`--bench-pp 32`、`--bench-tg 8`
- cache 型は渡していない。エンジン既定の FP32 KV のまま
- `--no-warmup` は付けていない。warmup は legacy のまま
- 保存設定 JSON の `q8_0` / `turbo3` は使っていない。そのファイルは書き換えていない
- 他のサーバは止めていない

## 実行

開始 `2026-11-02T16:08:09.7272413Z`。終了 `2026-11-02T16:57:31.6565753Z`。プロセスの終了コードは 0。壁時計は約 49.4 分。

観測した行:

- dense load: 753 tensors、GPU 4.40 GiB、27.1 s。`dense_load` end `elapsed_ms=27125`
- context 65536、prompt chunk 2048、MTP block loaded、experts 前の VRAM 空き 4.91 GiB
- `expert_host_alloc` end `elapsed_ms=2799582`（約 46.7 分。初回の hash、pack 書き込み、検証を含む）
- hybrid: 41/256 slots、VRAM 3.00 GiB、host は mapped file-backed の 18.75 GiB、CPU threads 6、staging 1.10 GiB、2821.5 s
- warmup: prefill 81527 ms、decode 69 ms、spec 109 ms。ログの合計は 82.0 s
- bench 0: pp32 29.8 tok/s、tg8 23.8 tok/s
- bench 1: pp32 74.4 tok/s、tg8 29.1 tok/s
- bench 2: pp32 120.7 tok/s、tg8 41.7 tok/s
- hybrid 集計: GPU 25610/39168（65.4%）、CPU pool 13558 件で 1269 ms、slot replacement 1604

pack ファイルは `H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf.q36epk`。サイズは 20127612928 bytes。公開時刻は 2026-11-03 01:43:42（ローカル）。

書き込み中、作業セットは 18.75 GiB の匿名 arena にはなっていない。途中の空き物理 RAM は 1.71 GiB まで減った。終了後の再利用起動は未実行。

## テスト・検証結果

この 1 回は終了コード 0。本線の context、chunk 2048、MTP 2 はログに残っている。

合格にしていないもの:

- 同日の legacy との paired run はない。legacy はこの PC の空き RAM では起動前拒否
- warmup 82.0 s を、過去ログの 306.6 s より速いとは書かない。経路も本数も違う
- 2821.5 s は初回 pack 生成を含む。過去の配置 266.0 s との優劣は未判定
- pp32 / tg8 は短い bench であり、2048 token の本線速度ではない
- 5 組の paired run、chat、stop、restart は未実行
- T04 の bounded warmup、T06 の転送方針、T07 の kernel は既定化していない

## 残留リスク

pack の再利用がどれだけ短いかは未計測。書き込み中に空き RAM が 1.71 GiB まで落ちた。GUI の起動段階表示は、この直接起動のログであり、インストール済みアプリの画面ではない。

## 次の推奨アクション

pack が既にある状態でもう 1 回同じ引数を走らせ、初回生成と再利用を分ける。既定は legacy のままにする。
