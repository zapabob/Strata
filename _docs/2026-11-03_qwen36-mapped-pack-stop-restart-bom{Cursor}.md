# Qwen3.6 mapped-pack の stop cancel と restart DONE が端末 421123 に出た

## 概要

`terminals/421123.txt` はシェル終了コード 0 で終わった。run1 の要約は `stop_sent=1` と `done_line=DONE 4 3 275.1 100.2 cancel 1 4 0 0 0 0 0 0.0 3 0`。run2 は起動し、`done_line=DONE 4 3 274.0 110.5 length 3 4 0 0 0 0 0 0.0 3 0`。両 run の `engine_exit=0`。

これは `918b8da0`（`terminals/421121.txt`、終了コード 4294967295、`READY` / `STOP` / `T` / `DONE` なし）と `ea37b4cf`（`terminals/421122.txt`、シェル終了コード 0、`ERR expected: GEN <max_new> [key=value ...] <id,id,...>`、`stop_sent=0`、run2 未開始）の上書きではない。

この確認ではモデルを起動していない。

## 背景・要求

BOM 修正後の mapped-pack stop と restart について、端末が印字した行だけを別ファイルに残す。

## 前提・判断

前2回の文書は残す。この端末に stop の `cancel` と restart の `DONE` が出ているため、新規ファイルにした。

## 観測した端末

- ファイル: `C:\Users\downl\.cursor\projects\c-Users-downl-Documents-ChatGPT-Strata\terminals\421123.txt`
- タイトル: `Start stop and restart after BOM fix`
- コマンド: `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\downl\AppData\Local\Temp\q36-stop-restart\run.ps1"`
- `status: succeeded`
- `started_at: 2026-11-02T18:18:30.841Z`
- `running_for_ms: 1511090`
- `exit_code: 0`
- `elapsed_ms: 1511090`
- `ended_at: 2026-11-02T18:43:41.931Z`

先頭:

```
utc=2026-11-02T18:18:33.5005499Z
strata_count=0
port8080_count=0
pack_size=20127612928
pack_mtime_local=2026-11-03T01:43:42.6586644+09:00
partial=0
lock=0
gpu_free_used_mib=14922, 1129
2026-11-02T18:18:33.8563983Z launch run1 stop
2026-11-02T18:18:33.9679628Z started mode=stop pid=28500
```

run1 の `wait-ready` は `elapsed_s=15` から `elapsed_s=724` まで印字されている。読んだ各行の `poll size` は `20127612928`、`mtimeUtc=2026-11-02T16:43:42.6586644Z`、`partial=0`、`partialSize=0`、`lock=0`。最後の `wait-ready` と、その後の結果行:

```
2026-11-02T18:30:38.8785378Z wait-ready elapsed_s=724 gpu=202, 15849 poll size=20127612928 mtimeUtc=2026-11-02T16:43:42.6586644Z partial=0 partialSize=0 lock=0
2026-11-02T18:30:41.1306723Z gen-sent mode=stop GEN 64 1,2,3
2026-11-02T18:30:41.5070786Z done mode=stop DONE 4 3 275.1 100.2 cancel 1 4 0 0 0 0 0 0.0 3 0
2026-11-02T18:31:02.0881606Z finished mode=stop exit=0 killed=0
2026-11-02T18:31:02.0898560Z run1 returned 0
```

run1 ハーネス要約（印字どおり）:

```
harness_result=ok
mode=stop
pid=28500
started=1
start_utc=2026-11-02T18:18:33.9618013Z
ready_seen=1
ready_line=READY 65536 stop
ready_observed_utc=2026-11-02T18:30:41.1261549Z
gen_sent=1
gen_sent_utc=2026-11-02T18:30:41.1261549Z
t_count=4
t_line_0=T 4
t_line_1=T 5
t_line_2=T 6
t_line_3=T 24218
stop_sent=1
stop_sent_utc=2026-11-02T18:30:41.4591201Z
done_line=DONE 4 3 275.1 100.2 cancel 1 4 0 0 0 0 0 0.0 3 0
err_line=
done_observed_utc=2026-11-02T18:30:41.5070786Z
exited_before_stdin_close=0
stdin_closed=1
stdin_close_utc=2026-11-02T18:30:51.5076143Z
killed_our_pid=0
engine_exited=1
engine_exit=0
exit_utc=2026-11-02T18:31:02.0185573Z
partial_seen=0
last_gpu=14956, 1095
last_pack=final size=20127612928 mtimeUtc=2026-11-02T16:43:42.6586644Z partial=0 partialSize=0 lock=0
run2_gpu_free_used_mib=14948, 1103
run2_pack_size=20127612928
```

時系列の本文に `STOP` で始まる行はない。`STOP` 送信の印字は要約フィールド `stop_sent=1` と `stop_sent_utc=2026-11-02T18:30:41.4591201Z` である。finish reason として印字された語は `cancel`。`T` 行は `T 4`、`T 5`、`T 6`、`T 24218`。`expert_host_alloc` という文字列はこのファイルにない。

run2:

```
2026-11-02T18:31:07.2055923Z launch run2 restart
2026-11-02T18:31:07.2844249Z started mode=finish pid=19396
```

run2 の `wait-ready` は `elapsed_s=15` から `elapsed_s=739` まで印字されている。読んだ各行の `poll size` は `20127612928`、`mtimeUtc=2026-11-02T16:43:42.6586644Z`、`partial=0`、`partialSize=0`、`lock=0`。最後の `wait-ready` と、その後の結果行:

```
2026-11-02T18:43:26.3869024Z wait-ready elapsed_s=739 gpu=105, 15946 poll size=20127612928 mtimeUtc=2026-11-02T16:43:42.6586644Z partial=0 partialSize=0 lock=0
2026-11-02T18:43:33.8749839Z gen-sent mode=finish GEN 4 1,2,3
2026-11-02T18:43:34.2643560Z done mode=finish DONE 4 3 274.0 110.5 length 3 4 0 0 0 0 0 0.0 3 0
2026-11-02T18:43:41.3743775Z finished mode=finish exit=0 killed=0
2026-11-02T18:43:41.3847998Z run2 returned 0
```

run2 ハーネス要約（印字どおり）:

```
harness_result=ok
mode=finish
pid=19396
started=1
start_utc=2026-11-02T18:31:07.2805161Z
ready_seen=1
ready_line=READY 65536 stop
ready_observed_utc=2026-11-02T18:43:33.8749839Z
gen_sent=1
gen_sent_utc=2026-11-02T18:43:33.8749839Z
t_count=4
t_line_0=T 4
t_line_1=T 5
t_line_2=T 6
t_line_3=T 24218
stop_sent=0
stop_sent_utc=
done_line=DONE 4 3 274.0 110.5 length 3 4 0 0 0 0 0 0.0 3 0
err_line=
done_observed_utc=2026-11-02T18:43:34.2643560Z
exited_before_stdin_close=0
stdin_closed=1
stdin_close_utc=2026-11-02T18:43:34.2643560Z
killed_our_pid=0
engine_exited=1
engine_exit=0
exit_utc=2026-11-02T18:43:41.3251836Z
partial_seen=0
last_gpu=14858, 1193
last_pack=final size=20127612928 mtimeUtc=2026-11-02T16:43:42.6586644Z partial=0 partialSize=0 lock=0
```

run2 の時系列本文にも `STOP` で始まる行はない。要約は `stop_sent=0`。`READY` の文字は要約フィールド `ready_line=READY 65536 stop` にある。`T` 行は `T 4`、`T 5`、`T 6`、`T 24218`。finish reason として印字された語は `length`。`expert_host_alloc` はこの run の印字にもない。

## 確認時のパックとプロセス

この記録を書く直前、`2026-11-03T03:45:15+09:00` の列挙:

- `strata.exe` は 0 件。止めていない
- `H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf.q36epk` は存在する
- その length は 20127612928
- その LastWriteTime は `2026/11/03 1:43:42`
- 同じディレクトリの `*.partial` 列挙は 0 件
- 同じディレクトリに見えた他ファイルは `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`（length 22853663008、LastWriteTime `2026/11/02 18:15:20`）と `Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf.done`（length 71、LastWriteTime `2026/11/02 18:18:07`）

## 実行コマンド

測定本体は端末 421123 の `run.ps1`。この確認ではモデルを起動していない。パック長と `*.partial` と `strata.exe` の有無だけを見た。

## テスト・検証結果

再測定はしていない。上記は `421123.txt` の印字と、その後のファイル長・プロセス列挙の結果である。

## 残留リスク

`expert_host_alloc` のミリ秒はこの端末にない。本文に `STOP` で始まる生行はなく、送信の根拠は run1 要約の `stop_sent=1` だけである。計画完了とは書いていない。

## 次の推奨アクション

このファイルは観測の記録である。次の測定要否はこの記録の範囲外である。
