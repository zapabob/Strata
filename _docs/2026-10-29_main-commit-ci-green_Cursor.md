# 2026-10-29 main commit/push + CI green attempt {Cursor}

## Verdict

**Push to `origin/main`: YES.**  
**Cloud CI all-green on tip: NO** — fork kill-switch. `workflow_dispatch` returns HTTP 422 `Actions has been disabled for this repository` even while `GET …/actions/permissions` says `enabled:true` / `allowed_actions:all`. **Do not keep retrying API dispatch until the user flips Actions in the GitHub UI.**

## 概要

`main` へコミット＆プッシュ完了。pytest-randomly×thinc Seed フレークを `conftest.py` で修正。
クラウド製品 CI は fork 側で Actions が実質無効のため起動不可。ユーザーが UI で有効化するまでグリーン不可。

## 背景・要求

ユーザー明示: main に commit + push、CI オールグリーン、実装ログ、終了 WAV。

## 前提・判断

- `zapabob/Strata` は **fork**（`fork:true`）、`admin=true`。
- permissions API の `enabled=true` は kill-switch 解除を意味しない（dispatch は依然 422）。
- Billing API は token scope 不足（`gist,read:org,repo,workflow`）で 404 / 不可。
- 最終成功クラウド CI は約 **2026-10-25**。
- `Cargo.toml` の `lto=false` / `codegen-units=16` はローカル preview OOM 回避 → **未コミット**。
- `windows-schema.json` は line-ending ノイズ → **未コミット**。
- API 再試行は打ち切り。UI 有効化が唯一の道。

## 変更対象ファイル（コミット済）

| Path | 内容 |
|------|------|
| `conftest.py` | thinc `fix_random_seed` を `seed % 2**32` にクランプ |
| `_docs/2026-10-29_goal-audit_Cursor.md` | Goal 監査ログ |
| `_docs/2026-10-29_nsis-post-release_Cursor.md` | NSIS post-release ログ |
| `_docs/2026-10-29_main-commit-ci-green_Cursor.md` | 本ログ |

## 実装詳細（フレーク修正）

pytest-randomly は numpy には `seed % 2**32` を渡すが、entry-point seeder（thinc）には `randomly_seed + offset` をそのまま渡す。
値が 2**32 以上になると `numpy.random.seed` が ValueError。`conftest.pytest_configure` で thinc 側をクランプ。

## Git / push

| Item | Value |
|------|-------|
| Feature commit | `3db4e69c1d1fe086ebd0a822f8b84b9d6e312ace` — `[Other] clamp thinc seeds under pytest-randomly for reliable hermes tests` |
| Docs commit (tip) | `657bf11b05fc251bf33f67f89ddd275256884ff8` — `[Docs] record main push and Actions dispatch blocker evidence` |
| Push | `origin/main` FF only（force なし） |
| Feature URL | https://github.com/zapabob/Strata/commit/3db4e69c1d1fe086ebd0a822f8b84b9d6e312ace |
| Tip URL | https://github.com/zapabob/Strata/commit/657bf11b05fc251bf33f67f89ddd275256884ff8 |

## 意図的に dirty のまま

- `apps/desktop/src-tauri/Cargo.toml`（preview LTO=false）
- `apps/desktop/src-tauri/gen/schemas/windows-schema.json`（CRLF ノイズ）

## ローカル検証

```text
py -3 -m pytest tests/test_hakua_hermes_memory_stack.py -q
→ 修正前: 3 passed, 2 errors (Seed must be between 0 and 2**32 - 1)
→ 修正後: 4 passed（pytest-randomly 有効のまま）
```

## クラウド CI — ブロッカー

### 試行（打ち切り）

```text
gh workflow run 'Minimal serving runtime' --repo zapabob/Strata --ref main
gh workflow run 'Native preview CPU checks' --repo zapabob/Strata --ref main
gh workflow run 'Portable monitor client' --repo zapabob/Strata --ref main
gh workflow run 'Deploy GitHub Pages' --repo zapabob/Strata --ref main
→ 全て HTTP 422: Actions has been disabled for this repository
```

`PUT …/actions/permissions` と workflow enable は 200 を返すが、再 dispatch も 422。これ以上の API リトライは無効。

### ユーザーがやること（必須）

1. ブラウザで開く: https://github.com/zapabob/Strata/settings/actions  
2. **Actions permissions** で Actions を有効化  
   - 「Allow all actions and reusable workflows」を選ぶ（または少なくともこの fork で Actions を Enable）  
3. Save 後、次を再実行:

```powershell
gh workflow run "Minimal serving runtime" --repo zapabob/Strata --ref main
gh workflow run "Native preview CPU checks" --repo zapabob/Strata --ref main
gh workflow run "Portable monitor client" --repo zapabob/Strata --ref main
gh workflow run "Deploy GitHub Pages" --repo zapabob/Strata --ref main
gh run list --repo zapabob/Strata --branch main -L 8
```

### tip 上の製品 CI 状態

**起動ゼロ → オールグリーンではない（honest）。**

### 参考: 直近成功 run（別 tip・2026-10-25）

| Workflow | Run |
|----------|-----|
| Minimal serving runtime | https://github.com/zapabob/Strata/actions/runs/40246905899 |
| Native preview CPU checks | https://github.com/zapabob/Strata/actions/runs/40246904126 |
| Deploy GitHub Pages | https://github.com/zapabob/Strata/actions/runs/40246902009 |
| Portable monitor client | https://github.com/zapabob/Strata/actions/runs/40145203557 |

## 残留リスク

- fork Actions kill-switch が UI で直るまでクラウド緑は不可。
- Cargo.toml LTO=false が作業ツリーに残る（意図的）。

## 次の推奨アクション

1. Settings → Actions → General で Enable / Allow all  
2. 上記4本を `--repo zapabob/Strata` で dispatch  
3. 緑確認後、本ログへ run URL 追記
