# Implementation log — upstream PR-1 Q36 refuse unsupported serve flags

- Date: 2026-11-04T22:12:46+09:00
- Authoring agent: Cursor
- Workspace: `C:\Users\downl\Documents\ChatGPT\Strata` (Hakua fork) + worktree `C:\Users\downl\Documents\ChatGPT\Strata-pr-q36-refuse`
- Goal complete: **false** (no UpdateGoal complete)

## Overview

Opened the first small upstream pull request against Niko1221/Strata for issue #5023: under `--serve`, refuse explicit `--cache-type-k`, `--cache-type-v`, and hand-written `--vram-reserve-mib` instead of ignore-and-continue.

## Background / requirements

- Operator confirmed: 「小さく切って本家に出す」— open PR-1, not plan-only.
- Plan: `_docs/2026-11-04_q36-upstream-pr-plan{Cursor}.md`
- CONTRIBUTING: area-prefix title, one problem per PR, no Hakua-only cargo.

## Assumptions / decisions

1. Cut a clean branch from current `upstream/main` (`ffa80d73`), not from Hakua `main`.
2. Patch only the serve-mode unknown-flag branch in `src/qwen35/q36_engine.cu`.
3. Named three flags only; other unknown `--serve` flags still ignore (narrower than “all unknown fatal”).
4. Do not ship mapped-pack, private-cache, digest allowlists, or host `q36-run-contract.mjs`.
5. PR-2 (docs) deferred as not trivially required for this step.

## Changed files

| Path | Action |
|---|---|
| `src/qwen35/q36_engine.cu` (worktree / PR branch only) | Fatal refuse for the three flags under `--serve` |
| `_docs/2026-11-04_q36-upstream-pr-plan{Cursor}.md` | Note PR URL |
| `_docs/2026-11-04_q36-upstream-pr1-refuse-flags{Cursor}.md` | This log |

## Implementation details

Inside `else if (serve_mode && a.rfind("--", 0) == 0)`, before the ignore fprintf:

- If argv is `--cache-type-k`, `--cache-type-v`, or `--vram-reserve-mib`, print `… is not an option of this engine. It was not applied.` and `return 2`.
- Otherwise keep the previous ignore-and-continue path.

Branch: `pr/q36-refuse-unsupported-serve-flags`  
Commit: `3b7241f4315ed75ecf3ca6e159246cd8e7b18338`  
Remote head: `zapabob:pr/q36-refuse-unsupported-serve-flags`  
PR: https://github.com/Niko1221/Strata/pull/5216

## Commands run

```text
git fetch upstream
git worktree add -b pr/q36-refuse-unsupported-serve-flags … upstream/main
# patch q36_engine.cu
cl /EHsc _docs_local_validate_q36_refuse.cpp   # local harness, not committed
git commit / git push -u origin pr/q36-refuse-unsupported-serve-flags
gh pr create --repo Niko1221/Strata --base main --head zapabob:pr/q36-refuse-unsupported-serve-flags …
```

## Test / verification results

- Passed: mirrored argv harness (MSVC cl). Serve + each named flag → exit 2 + refuse message; unrelated unknown serve flag still ignored; without `--serve` unknown flag → usage exit 2. Diff only `q36_engine.cu` (+6/−1).
- Failed: none for harness cases.
- Not run: full CUDA rebuild of `strata_qwen35`; HIP/SYCL (no hipcc/icpx); live `strata-q36` binary dry-run with GGUF.

## Residual risks

- Maintainers may prefer making every unknown `--serve` flag fatal; this PR does not.
- CUDA/HIP/SYCL full rebuild not performed on the extracted revision; argv logic is compile-independent but CI must still build the TU.
- Commit author on the branch is `Hermes Agent <hermes@localhost>` (local git identity); amend not performed (no force-push).

## Recommended next actions

1. Watch PR #5216 review / CI.
2. Optionally open PR-2 docs branch for UD-Q4_K_XL 32 GB wording.
3. Wait on #5021 placement and #5022 scope before further engine PRs.
