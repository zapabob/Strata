# T0 ベースライン固定（Hakua chatbot 実装）

- 記録時刻（UTC）: 2026-10-27T12:59:56Z
- 作業ディレクトリ: `H:\Strata\worktrees\hakua-chatbot-20261027`
- ブランチ: `codex/strata-hakua-chatbot-20261027`
- HEAD: `bc450f46a0e9a120048b0e3b126a686c06d9cc67`
- 計画書固定コミット: `782085b0b60cfa79aedfca5cf5036dfc677a0b5e`（本ブランチはそれより新しい Hakua GUI コミット群の上）

## Build identity（取得できたもの）

| 項目 | 値 |
|---|---|
| repoCommit | `bc450f46a0e9a120048b0e3b126a686c06d9cc67` |
| hostVersion (`apps/host/package.json`) | `0.3.1` |
| hostHash (`package.json` SHA256) | `DC8819A10C1CCF462F6DE1AE7E6EFB1100D676F46A9538135FE7C0EEFE0577A1` |
| controlHash | 未計測（今回は T1 GUI store から着手） |
| engineHash | 未計測（ネイティブエンジンバイナリの実機ハッシュは T7/T8 前に採取） |
| modelId / modelHash | 今回の T1/T2 修正対象外。性能比較前に再記録 |
| sanitizedConfigHash | 未計測 |

## git 状態（保護対象）

- staged: `apps/host/package.json`, `packaging/full_windows.py`
- untracked: 既存 `_docs/*.md`（Hakua / NSIS / auth など）。破壊操作なしで維持

## PC 実測（計画前提との差）

| 項目 | 計画前提 | 実測 |
|---|---|---|
| OS | Windows 11 Pro | Windows 11 Pro `10.0.26300` |
| CPU | Ryzen 5 4600 | **AMD Ryzen 5 4500** 6コア / 12スレッド |
| GPU | RTX 5060 Ti 16GB | NVIDIA GeForce RTX 5060 Ti、ドライバ `616.92`（nvidia-smi）／WDDM `32.0.16.1692` |
| VRAM | 16GB | total 16311 MiB、used 15373 MiB、free **678 MiB**（測定時点でほぼ満杯） |
| RAM | DDR4 32GB | TotalVisible ~31.9 GiB、FreePhysical ~0.47 GiB（測定時点で逼迫） |
| ストレージ | 空き不足の情報あり | C: free ~55.5 GiB、H: free ~200.5 GiB |

注: VRAM/RAM は Cursor・他プロセス併用時のスナップショット。T8 性能測定前に単独起動でも再測する。

## 実行環境

- Node: 開発機で `node` 利用可（apps/host engines `>=24.12.0`）
- Python: 3.12.x（別ログで確認済み）
- 対象修正ツリー: worktree 上の開発 Host（インストール済みアプリと混同しない）

## 既知問題の扱い（計画 F01–F09）

- T1 対象 F01/F02: 現行 `store.ts` に残存（送信ペイロードが await 後に global を再読、queued-release 再送が `sendMessage(next)` で activeSession 依存）→ RED で固定する
- T2 対象 F03: native-control 直列化は T1 の次
- F04–F09: 後続。今回は対象外として未着手

## 次アクション

1. `apps/host/tests/chat-turn-ownership.test.mjs` で F01/F02 を RED 確認
2. `store.ts` に送信スナップショットと session 宛再送を入れる
3. T2 RED（native-load-cancel）へ進む
