# Qwen3.6 mapped expert pack（opt-in、既定は legacy）

- **日時**: 2026-11-02 23:53:54 +09:00（`Get-Date -Format "yyyy-MM-dd HH:mm:ss K"`）
- **実装AI**: Cursor
- **ブランチ**: `feat/q36-32gb16gb`
- **GPU**: RTX 5060 Ti 16GB。この変更の GPU 起動・速度は未計測。

## 概要

Qwen3.6 の expert を、`expert_blob` と同じバイト列でファイルに書いてマップする経路を足した。既定は今まで通りの host arena。新経路は `--q36-expert-store mapped-pack` のときだけ動く。失敗しても 18.75 GiB の匿名 arena には落とさない。ホストは、ビルドしたエンジンの SHA-256 が allowlist に入るまで、このフラグを起動 argv に載せない。

## 背景・要求

計画 T05。UD-Q4_K_XL は GGUF を mmap したあと、さらに private host arena（計測 19195 MiB）を確保して expert を詰め直す。32GB 機ではここで落ちる。詰め直したバイト列そのものは維持し、全量 malloc / cudaHostAlloc を mapped 経路ではしない。

## 前提・判断

- 既定は `legacy`。T04 の bounded warmup、T06 の転送スケジュール、T07 のカーネル変更は既定にしない。計測が無い。
- `expert_blob` の並びは gate が 0、up が `up_off`、down が `down_off`。隙間と stride の端と `kMmqTail`（4096）は 0。
- パックの作業バッファは 1 expert の stride だけ。レイヤ全体は確保しない。
- 公開名は `<model>.q36epk`。書き込みは `.partial`、検証後に名前を替える。壊れた公開ファイルは `.rejected` にどける。
- モデルファイルの SHA-256、レイヤ形状、payload の SHA-256、レイヤ CRC が一致するときだけ再利用する。
- 別プロセスが lock を持っているときはビルドしない。
- ホストの `Q36_MAPPED_PACK_DIGESTS` は空。未登録のバイナリへ mapped-pack を送ると、古い `strata-q36` がフラグを無視して全量 arena を取る。だから起動前に拒否する。
- 速度の前後比較はしていない。未計測のまま。

## 変更対象ファイル

- `include/strata/qwen35/expert_store.hpp`
- `src/qwen35/expert_store.cpp`
- `src/qwen35/q36_engine.cu`
- `tests/qwen35/q36_expert_store_test.cpp`
- `CMakeLists.txt`
- `apps/host/server/q36-run-contract.mjs`
- `apps/host/tests/q36-run-contract.test.mjs`
- `apps/host/tests/q36-capabilities.test.mjs`

## 実装詳細

- パック形式 version 1、little-endian、magic `Q36EPK1`。payload は 4096 境界。
- `pack_expert_blob` は重なるコピーや stride を超えるコピーを拒否する。
- エンジンは hybrid の mapped 経路で `hblobs` をファイルビューにする。mtp-only と、CPU expert pool の無いビルドは拒否する。
- capability revision は `q36-argv-expert-store-1`。ソース基準の `170e0d33` は歴史上の印として残した。
- `warmupMode: bounded` は起動前に拒否する。既定の warmup は変えていない。

## 実行コマンド

```powershell
Get-Date -Format "yyyy-MM-dd HH:mm:ss K"
# 2026-11-02 23:53:54 +09:00

cmd /c "`"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat`" >nul && cl /nologo /std:c++17 /EHsc /W3 /I include /Fe:%TEMP%\q36_expert_store_test.exe tests\qwen35\q36_expert_store_test.cpp src\qwen35\expert_store.cpp && %TEMP%\q36_expert_store_test.exe"

node --test tests/q36-run-contract.test.mjs tests/q36-capabilities.test.mjs tests/q36-progress.test.mjs tests/resource-ram.test.mjs tests/native-control.test.mjs
```

## テスト・検証結果

| 項目 | 結果 |
|------|------|
| `q36_expert_store_test.exe` | 通過。SHA-256("") と SHA-256("abc") は .NET `Get-FileHash` と一致。バイト列、隙間と tail の 0、scratch が stride だけ、再利用、payload 改ざんの拒否と再生成、未知 version、lock、`.partial`、重なり拒否 |
| host `node --test`（上記 5 ファイル） | 28 pass / 0 fail |
| CUDA での `strata-q36` ビルド | 未実施 |
| 実 GGUF の mapped-pack 起動 | 未実施（NOT_RUN） |
| 速度の前後比較 | 未実施（NOT_RUN） |

## 残留リスク

- `q36_engine.cu` の mapped 分岐は、この CUDA バイナリにはまだ入っていない。インストール済み `strata-q36` は従来の arena のまま。
- allowlist が空なので、ホストは mapped-pack を起動に使わない。
- ファイル全体の SHA-256 は mapped-pack のたびに読む。20GB 級の GGUF ではその時間が出る。計測していない。
- mtp-only の hybrid は mapped-pack 未対応で起動失敗になる。16GB で主層が全部 VRAM に乗らない経路が対象。
- ディスク不足のときはパックを作らず、全量 arena にも落とさない。

## 次の推奨アクション

1. sm_120 の `strata-q36` をビルドし、その SHA-256 を `Q36_MAPPED_PACK_DIGESTS` に入れる。
2. そのバイナリで UD-Q4_K_XL、context 65536、FP32 KV、MTP 2 の起動を測る。未計測のまま速度を書かない。
3. 測った成果物だけをインストーラと GitHub リリースに載せ、README をその中身に合わせる。
