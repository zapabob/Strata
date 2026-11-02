# Qwen3.6 mapped-pack で 1 件応答して終了した

## 概要

既存の `.q36epk` を開いたまま `--serve` し、制御線へ `GEN 8 1,2,3` を 1 件送った。`READY 65536 stop` のあと `DONE` が出て、標準入力が閉じるとプロセスは終了コード 0 で終わった。pack は書き直していない。速度の採用にはしない。

## 背景・要求

T09 の起動、応答、停止を、インストール済みの `strata.exe` で 1 回見る。本線は UD-Q4_K_XL、context 65536、`--prefill auto`、MTP 2、cache 型なし。既定は legacy のまま。GUI の画面操作ではない。

## 前提・判断

- 実行ファイルは `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13\strata.exe`
- 引数は `--native`、`--max-context 65536`、`--prefill auto`、`--mtp 2`、`--q36-expert-store mapped-pack`、`--serve`
- 送った行は `GEN 8 1,2,3` だけ。生成が終わったあと標準入力を閉じた
- 開始前の pack は 20127612928 bytes、最終書き込みは 2026-11-03 01:43:42
- 他のサーバは止めていない。この起動は TCP の 8080 ではなく、エンジンの標準入出力プロトコル

## 実行

開始 `2026-11-02T17:15:32.3539737Z`。終了 `2026-11-02T17:29:55.4212605Z`。終了コード 0。壁時計は約 14.4 分。

観測した行:

- dense load: 753 tensors、GPU 4.40 GiB、30.6 s。`elapsed_ms=30570`
- context 65536、prompt chunk 2048、MTP block loaded、experts 前の VRAM 空き 4.91 GiB
- `expert_host_alloc` end `elapsed_ms=783673`
- hybrid: 41/256 slots、VRAM 3.00 GiB、host は mapped file-backed の 18.75 GiB、CPU threads 6、staging 1.10 GiB、786.6 s
- warmup 合計 12.6 s。prefill 12146 ms、decode 45 ms、spec 108 ms
- `READY 65536 stop`
- `PP 3 3 82 36.7`
- `T` は 4、5、6、24218、10、4838、1665、15
- `DONE 8 3 296.1 173.4 length 5 6 0 0 0 0 0 0.0 3 0`
- stderr: prompt 3 tokens、reused 0、read 3、296 ms（10.1 tok/s）、generated 8、173 ms（46.1 tok/s）、drafts accepted 5 of 6、finish は length
- 集計: GPU 1755/3936（44.6%）、CPU pool 2181 件で 137 ms、slot replacement 647

終了後の pack は 20127612928 bytes、最終書き込みは 2026-11-03 01:43:42 のまま。`.partial` と `.lock` はない。

## テスト・検証結果

この 1 件は終了コード 0。`READY` の context は 65536。応答は 8 token で `length` により終わった。

合格にしていないもの:

- 3 token の prefill 10.1 tok/s と 8 token の 46.1 tok/s は、本線の 2048 token 速度ではない
- 生成中の `STOP` と、その後の再起動は未実行。止めたのは、応答後に標準入力を閉じたこと
- GUI の chat、停止ボタン、再起動は未実行
- 5 組の paired run はない
- T04、T06、T07 は既定化していない

## 残留リスク

起動の大半は、再利用時と同じ全ファイル検証（`expert_host_alloc` 783673 ms）である。GUI はこのログを表示していない。

## 次の推奨アクション

既定は legacy のまま。検証を短くする変更は、短縮分を別計測してからにする。
