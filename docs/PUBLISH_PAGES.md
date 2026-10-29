# Publish GitHub Pages (zapabob/Strata)

Live URL: https://zapabob.github.io/Strata/

## Source of truth in this repo

Landing files live under `docs/` on `main`:

- `docs/index.html`
- `docs/assets/app.js`
- `docs/assets/style.css`
- `docs/UPSTREAM_SYNC.txt`

Product version for the current tip: **0.3.2-preview.20261029.2** (engine **0.1.53**).

## Why a manual script

`.github/workflows/pages.yml` may still fail with HTTP 422 when Actions are disabled for the fork. Until Actions work, publish by copying the `docs/` landing tree onto the legacy `gh-pages` branch.

## One-shot publish (parent / release PC)

From a clean checkout of `main` that already contains the updated `docs/` files:

```powershell
pwsh -File tools/publish_gh_pages.ps1
```

What it does:

1. Creates a temporary worktree on `origin/gh-pages`.
2. Copies `docs/index.html`, `docs/assets/*`, `docs/UPSTREAM_SYNC.txt`, and `docs/media` favicon/brand assets needed by the landing page.
3. Commits with message `[Docs] refresh Pages for <VERSION>`.
4. Pushes `gh-pages` with a normal fast-forward (no force).

Dry run (no push):

```powershell
pwsh -File tools/publish_gh_pages.ps1 -DryRun
```

## After NSIS lands

1. Fill SHA-256 into `docs/UPSTREAM_SYNC.txt` and the download card checksum in `docs/index.html`.
2. Re-run `tools/publish_gh_pages.ps1`.
3. Confirm https://zapabob.github.io/Strata/ shows product `0.3.2-preview.20261029.2`.
