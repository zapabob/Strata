# Qwen3.6 mapped-pack で 1 回止め、1 回再起動した

## 概要

既存の `.q36epk` を開いたまま `--serve` を 2 回した。1 回目は `GEN 64 1,2,3` の途中で `STOP` を送った。終了理由は `cancel`。`STOP` だけではプロセスは終わらず、その 10 秒後に標準入力を閉じて終了コード 0 になった。2 回目が再起動で、`GEN 4 1,2,3` は `length` で終わり、標準入力を閉じると終了コード 0 だった。pack は書き直していない。

これは 1 回の stop と 1 回の restart である。5 組の paired run ではない。2048 token の速度結果ではない。GUI の操作ではない。速度改善とは書かない。計画は終わっていない。既定は legacy のまま。

## 背景・要求

T09 の生成中停止と、その後の再起動を、インストール済みの `strata.exe` で 1 回ずつ見る。本線は UD-Q4_K_XL、context 65536、`--prefill auto`、MTP 2、cache 型なし。`--no-warmup` は付けていない。

## 前提・判断

- 実行ファイルは `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe`
- 引数は `--native`、`--max-context 65536`、`--prefill auto`、`--mtp 2`、`--q36-expert-store mapped-pack`、`--serve`
- 作業ディレクトリはエンジンのディレクトリ
- 開始前（`terminals/421123.txt`）: strata 0、ポート 8080 の接続 0、pack 20127612928 bytes、mtime `2026-11-03T01:43:42.6586644+09:00`、partial 0、lock 0、VRAM 空き 14922 MiB、使用 1129 MiB
- 他のサーバは止めていない。この起動は TCP の 8080 ではなく、エンジンの標準入出力
- モデル JSON は書いていない

同じセッションで、その前に 2 回起動している。どちらも全ファイル検証までは進み、`GEN` はエンジンに拒否された。stop と restart の結果には数えない。

1. 開始 `2026-11-02T17:43:08.1042326Z`。`expert_host_alloc` end `elapsed_ms=822738`。ログの warmup は 9.1 s。`READY 65536 stop` のあと stdout は `ERR expected: GEN <max_new> [key=value ...] <id,id,...>`。`T` も `DONE` も `STOP` もない。pack の partial は 0 のまま。このプロセス（pid 18760）は標準入力が閉じても残ったので、計測側が `Stop-Process` した。きれいな終了コードは取っていない。
2. 開始 `2026-11-02T18:01:23.0549510Z`。`expert_host_alloc` end `elapsed_ms=730669`。ログの warmup は 8.7 s。同じ `ERR`。`stop_sent=0`、`done_line` は空。標準入力を閉じた時刻 `2026-11-02T18:14:13.0794490Z`。終了コード 0、終了 `2026-11-02T18:14:22.6907908Z`。再起動は始めていない。端末側の要約は `_docs/2026-11-03_qwen36-mapped-pack-stop-restart-retry{Cursor}.md` にある。上の `elapsed_ms` はそのエンジンログにある。

## 実行

端末は `terminals/421123.txt`。終了コード 0。`started_at` `2026-11-02T18:18:30.841Z`、`ended_at` `2026-11-02T18:43:41.931Z`、`elapsed_ms=1511090`。

### stop（1 回目）

開始 `2026-11-02T18:18:33.9618013Z`。終了 `2026-11-02T18:31:02.0185573Z`。終了コード 0。pid 28500。殺していない。

観測した行:

- dense load end `elapsed_ms=33631`
- context 65536、prompt chunk 2048、MTP block loaded、experts 前の VRAM 空き 4.91 GiB
- `expert_host_alloc` end `elapsed_ms=665521`
- hybrid: 41/256 slots、VRAM 3.00 GiB、host は mapped file-backed の 18.75 GiB、CPU threads 6、staging 1.10 GiB、667.1 s
- warmup: prefill 8414 ms、decode 37 ms、spec 74 ms。ログの合計は 8.7 s
- `READY 65536 stop` を観測した時刻 `2026-11-02T18:30:41.1261549Z`
- `GEN 64 1,2,3` を書いた時刻 `2026-11-02T18:30:41.1306723Z`
- `PP 3 3 73 40.9`
- `T 4`、`T 5`。2 本目の `T` のあと `STOP` を書いた時刻 `2026-11-02T18:30:41.4591201Z`
- そのあと `T 6`、`T 24218`
- `DONE 4 3 275.1 100.2 cancel 1 4 0 0 0 0 0 0.0 3 0` を観測した時刻 `2026-11-02T18:30:41.5070786Z`
- stderr: prompt 3 tokens、reused 0、read 3、275 ms（10.9 tok/s）、generated 4、100 ms（39.9 tok/s）、drafts accepted 1 of 4、finish は cancel

`DONE` の 10 秒後もプロセスは生きていた。`exited_before_stdin_close=0`。標準入力を閉じた時刻 `2026-11-02T18:30:51.5076143Z`。終了コード 0。

終了後の pack は 20127612928 bytes。mtime は `2026-11-02T16:43:42.6586644Z`。partial 0、lock 0。

### restart（2 回目）

1 回目の終了後、strata は 0 件、VRAM 空き 14948 MiB、使用 1103 MiB、pack は 20127612928 bytes のまま。ここから同じ引数でもう 1 回起動した。

開始 `2026-11-02T18:31:07.2805161Z`。終了 `2026-11-02T18:43:41.3251836Z`。終了コード 0。pid 19396。`STOP` は送っていない。殺していない。

観測した行:

- dense load end `elapsed_ms=47697`
- context 65536、prompt chunk 2048、MTP block loaded、experts 前の VRAM 空き 4.91 GiB
- `expert_host_alloc` end `elapsed_ms=683336`
- hybrid: 41/256 slots、VRAM 3.00 GiB、host は mapped file-backed の 18.75 GiB、CPU threads 6、staging 1.10 GiB、684.9 s
- warmup: prefill 8316 ms、decode 34 ms、spec 83 ms。ログの合計は 8.6 s
- `READY 65536 stop` を観測した時刻 `2026-11-02T18:43:33.8749839Z`
- `GEN 4 1,2,3` を書いた時刻 `2026-11-02T18:43:33.8749839Z`
- `PP 3 3 71 42.3`
- `T` は 4、5、6、24218
- `DONE 4 3 274.0 110.5 length 3 4 0 0 0 0 0 0.0 3 0` を観測した時刻 `2026-11-02T18:43:34.2643560Z`
- stderr: prompt 3 tokens、reused 0、read 3、274 ms（10.9 tok/s）、generated 4、110 ms（36.2 tok/s）、drafts accepted 3 of 4、finish は length
- 標準入力を閉じた時刻 `2026-11-02T18:43:34.2643560Z`。終了コード 0

監視中、pack は 20127612928 bytes のまま、partial は 0、lock は 0。`.q36epk.partial` への再生成は始まっていない。終了後も同じサイズ、mtime は `2026-11-03T01:43:42.6586644+09:00`。strata は 0 件。ポート 8080 の接続は 0。

## テスト・検証結果

stop の終了コードは 0。`DONE` の理由は `cancel`。生成は 4 token で止まり、64 token までは出ていない。`STOP` はプロセスを終了させていない。終了は、その後に標準入力を閉じたことによる。

restart の終了コードは 0。`READY` の context は 65536。`DONE` の理由は `length`。生成は 4 token。

どちらの `expert_host_alloc` も、pack を書き直さない全ファイル検証の時間である。665521 ms と 683336 ms。

合格にしていないもの:

- 上の tok/s は、エンジンが 3 token の prefill と 4 token の生成に対して印字した値である。2048 token の本線速度ではない
- 5 組の paired run はない
- GUI の chat、停止ボタン、再起動は未実行
- T04、T06、T07 は既定化していない
- この 2 回の `expert_host_alloc` を、過去の起動より速いとは書かない

## 残留リスク

起動の大半は、再利用時の全ファイル検証である。GUI はこのログを表示していない。`STOP` のあと、観測上は `T` がさらに 2 本出てから `DONE cancel` になった。

## 次の推奨アクション

既定は legacy のまま。検証を短くする変更は、短縮分を別計測してからにする。
