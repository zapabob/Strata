# Qwen3.6 mapped-pack の stop 再起動は結果前に中断した

## 概要

`terminals/421121.txt` のシェルは終了コード 4294967295 で切れた。結果行 `READY`、`STOP`、`T`、`DONE`、`EXIT` は出ていない。この確認ではモデルを起動していない。

## 観測した端末

- ファイル: `C:\Users\downl\.cursor\projects\c-Users-downl-Documents-ChatGPT-Strata\terminals\421121.txt`
- コマンド: `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\downl\AppData\Local\Temp\q36-stop-restart\run.ps1"`
- `status: failed`
- `started_at: 2026-11-02T17:43:04.763Z`
- `running_for_ms: 994773`
- `exit_code: 4294967295`
- `elapsed_ms: 994773`
- `ended_at: 2026-11-02T17:59:39.536Z`
- 別の stderr ブロックはない

先頭の行:

```
utc=2026-11-02T17:43:07.5107447Z
strata_count=0
port8080_count=0
pack_size=20127612928
pack_mtime_local=2026-11-03T01:43:42.6586644+09:00
partial=0
lock=0
gpu_free_used_mib=14899, 1152
2026-11-02T17:43:07.9911986Z launch run1 stop
2026-11-02T17:43:08.1123291Z started mode=stop pid=18760
```

その後、`wait-ready` の行が `elapsed_s=15` から `elapsed_s=865` まで続く。各行の `poll size` は `20127612928`、`partial=0`、`partialSize=0`、`lock=0`。

最後の本文:

```
2026-11-02T17:57:33.7552546Z wait-ready elapsed_s=865 gpu=248, 15803 poll size=20127612928 mtimeUtc=2026-11-02T16:43:42.6586644Z partial=0 partialSize=0 lock=0
2026-11-02T17:57:37.0886859Z gen-sent mode=stop GEN 64 1,2,3
```

トークン: 大文字の `READY`、`STOP`、`DONE`、`EXIT` はない。独立した `T` 行もない。小文字の `stop` は `launch run1 stop`、`started mode=stop`、`gen-sent mode=stop` にある。`wait-ready` はある。

## 中断後の確認

2026-11-03 のこの確認で見たもの:

- pid 20176（このシェル）はいない
- pid 18760（`started mode=stop` の記録）はいない
- `strata.exe` は 0 件
- コマンド行に `qwen36-UD-Q4_K_XL` または `q36-expert-store` を含むプロセスは 0 件
- プロセスは止めていない
- `H:\Strata\models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf.q36epk` は存在する
- length は 20127612928
- mtime は `2026-11-03T01:43:42.6586644+09:00`
- 同じディレクトリに `*partial*` は出てこなかった

## 残留リスク

`GEN 64 1,2,3` を送った記録のあと、シェルが終了コード 4294967295 で終わっている。`STOP` も再起動の結果行も、この端末にはない。
