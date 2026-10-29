# 2026-10-29 hakua-memory pip 追加 {Cursor}

## 概要
ユーザー指示「pipでHakuaMemory足すよ」に従い、`hakua-memory==0.3.5` を開発用 Python と Strata Control Python に入れ、`requirements.txt` にピンした。

## 実施
| 対象 | 内容 |
| --- | --- |
| システム `py -3` | `hakua-memory[obsidian,rag]==0.3.5`（RAG/Obsidian extras）。vendor wheel で force-reinstall 後 extras 再適用 |
| インストール済み Control | `Programs\Strata\control\python` に vendor wheel（base、レビュー済み SHA） |
| リポジトリ resources Control | `apps/desktop/src-tauri/resources/control/python` に同 wheel |
| `requirements.txt` | `hakua-memory==0.3.5` 追加（base pin。extras はコメントで案内） |

## 検証
- Control: `EbbinghausMemoryStore` / `CompositeMemory` import OK
- システム: version 0.3.5 / CompositeMemory OK

## 残留
- インストーラ同梱には `packaging/lock_wheels.py` で runtime lock 再生成＋レビューが別途必要（MEMORY_HARNESS.md 手順）。
- embedding extra（llama-cpp）は未導入（重い／別契約）。
- 配線ワーカーの feat ブランチコミットとは別差分；まとめて main に載せる想定。
