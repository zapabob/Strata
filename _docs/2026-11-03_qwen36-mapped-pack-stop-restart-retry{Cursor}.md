# Qwen3.6 mapped-pack の stop 再起動リトライは GEN 拒否で run2 に入らなかった

## 概要

`terminals/421122.txt` は終了コード 0 で終わった。これは `918b8da0` に記録した `terminals/421121.txt`（終了コード 4294967295、`READY` / `STOP` / `T` / `DONE` なし）のやり直しであり、あの中断を成功に書き換えるものではない。

この端末に出たプロトコル結果は、ハーネス要約の `ready_line=READY 65536 stop` と、`ERR expected: GEN <max_new> [key=value ...] <id,id,...>` である。`T` 行、`STOP` 送信、`DONE` 行、run2 はない。`expert_host_alloc` という文字列はこのファイルにない。

## 背景・要求

mapped-pack の stop のあと restart する測定の再試行結果を、端末が実際に印字した範囲だけ残す。モデルはこの確認では起動していない。

## 前提・判断

`421121` の文書は「結果行は出ていない」と書いている。このリトライには `ready_line=READY 65536 stop` がある。同じファイルへ足すと前文と矛盾するため、別ファイルにした。

## 観測した端末

- ファイル: `C:\Users\downl\.cursor\projects\c-Users-downl-Documents-ChatGPT-Strata\terminals\421122.txt`
- コマンド: `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\downl\AppData\Local\Temp\q36-stop-restart\run.ps1"`
- `status: succeeded`
- `started_at: 2026-11-02T18:01:20.260Z`
- `running_for_ms: 782961`
- `exit_code: 0`
- `elapsed_ms: 782961`
- `ended_at: 2026-11-02T18:14:23.221Z`

先頭:

```
utc=2026-11-02T18:01:22.5010023Z
strata_count=0
port8080_count=0
pack_size=20127612928
pack_mtime_local=2026-11-03T01:43:42.6586644+09:00
partial=0
lock=0
gpu_free_used_mib=14917, 1134
2026-11-02T18:01:22.9406343Z launch run1 stop
2026-11-02T18:01:23.0631981Z started mode=stop pid=11920
```

`wait-ready` は `elapsed_s=15` から `elapsed_s=755` まで。各行の `poll size` は `20127612928`、`mtimeUtc=2026-11-02T16:43:42.6586644Z`、`partial=0`、`partialSize=0`、`lock=0`。

本文の末尾:

```
2026-11-02T18:14:13.0733412Z gen-sent mode=stop GEN 64 1,2,3
2026-11-02T18:14:13.0784498Z engine_rejected_line ERR expected: GEN <max_new> [key=value ...] <id,id,...>
2026-11-02T18:14:22.7822893Z finished mode=stop exit=0 killed=0
2026-11-02T18:14:22.7868247Z run1 returned 0
```

ハーネス要約（印字どおり）:

```
harness_result=engine_rejected_line
mode=stop
pid=11920
started=1
start_utc=2026-11-02T18:01:23.0549510Z
ready_seen=1
ready_line=READY 65536 stop
ready_observed_utc=2026-11-02T18:14:13.0733412Z
gen_sent=1
gen_sent_utc=2026-11-02T18:14:13.0733412Z
t_count=0
stop_sent=0
stop_sent_utc=
done_line=
err_line=ERR expected: GEN <max_new> [key=value ...] <id,id,...>
done_observed_utc=
exited_before_stdin_close=0
stdin_closed=1
stdin_close_utc=2026-11-02T18:14:13.0794490Z
killed_our_pid=0
engine_exited=1
engine_exit=0
exit_utc=2026-11-02T18:14:22.6907908Z
partial_seen=0
last_gpu=14922, 1129
last_pack=final size=20127612928 mtimeUtc=2026-11-02T16:43:42.6586644Z partial=0 partialSize=0 lock=0
2026-11-02T18:14:22.8241885Z run2 not started because run1 did not finish a DONE and exit on its own
```

時系列の本文に独立した `READY` 行、`T` 行、`STOP` 行、`DONE` 行は出ていない。`READY` の文字は要約フィールド `ready_line=READY 65536 stop` にある。トークン id の `T` 行はなく、`t_count=0`。`stop_sent=0`。`done_line` は空。run2 は始まっていない。

## 確認時のパックとプロセス

この記録を書く直前の確認:

- `strata.exe` は 0 件。止めていない
- `H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf.q36epk` は存在する
- length は 20127612928
- mtime は `2026-11-03T01:43:42.6586644+09:00`
- 同じディレクトリの `*partial*` は 0 件

## 実行コマンド

測定本体は端末 421122 の `run.ps1`。この確認ではモデルを起動していない。パック長と `*partial*` と `strata.exe` の有無だけを見た。

## テスト・検証結果

再測定はしていない。上記は `421122.txt` の印字と、その後のファイル長・プロセス列挙の結果である。

## 残留リスク

stop モードのプロセスは `engine_exit=0` で終了している。`STOP` は送られていない。再起動の `READY` と `DONE` はこの端末にない。`expert_host_alloc` のミリ秒もこの端末にない。

## 次の推奨アクション

`GEN` の形を直すかどうかは、この記録の範囲外である。
