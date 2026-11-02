# この PC の UD-Q4_K_XL 物理 RAM ゲート

- **日時**: 2026-11-02T16:02:45Z
- **実装AI**: Cursor
- **対象**: インストール済み host `0.4.0-preview.20261103.2` と同じ `admitQ36LegacyPhysical`

## 結果

legacy 経路は起動していない。

| 項目 | 値 |
|------|----|
| 物理 RAM | 34224861184 bytes |
| 判定に使った空き | 17738047488 bytes（約 16.5 GiB） |
| expert | 19195 MiB |
| reserve | 6844972236 bytes（RAM の 20%、4 GiB より大きい） |
| 必要量 | 26972388556 bytes |
| decision | `rejected` / `physical_reserve` |

メッセージ: Qwen3.6 UD-Q4_K_XL places about 18.7 GiB of experts in RAM with the current engine. 16.5 GiB is free and 6.4 GiB stays aside for the rest of the PC. The model was not started.

これは空き物理 RAM の判定であり、起動時間でもトークン速度でもない。mapped-pack の実 GGUF 起動は未計測。T04 の warmup 比較、T06 の転送、T07 の kernel、GUI 上の chat / stop / restart は未実行。
