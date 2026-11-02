# notices/ を Git 追跡から外す

- **日時**: 2026-11-02 19:08 JST
- **実装AI**: Cursor (Composer)

## 変更

- `apps/desktop/src-tauri/resources/notices/.gitignore`（`*` / `!.gitignore`）
- ルート `.gitignore` に Control/Harness と同型の `resources/notices/*` 除外を追加

## 結果

ステージ済み notice ツリーは `git status` に出ない。追跡されるのは ignore ファイルのみ。
