# Upstream pull-request plan for Qwen3.6 softness remedies

- Date: 2026-11-04T22:05:00+09:00
- Authoring agent: Cursor
- Workspace: zapabob/Strata (Hakua fork)
- Upstream: Niko1221/Strata (`upstream` remote present; integration baseline `ffa80d73`)
- Related audit: `_docs/2026-11-04_strata-official-q36-softness-audit{Cursor}.md`
- Related issues filed earlier: [#5021](https://github.com/Niko1221/Strata/issues/5021), [#5022](https://github.com/Niko1221/Strata/issues/5022), [#5023](https://github.com/Niko1221/Strata/issues/5023) (all OPEN as of 2026-11-04)
- Goal complete: **false** (no UpdateGoal complete)
- Upstream `gh pr create`: **not performed**

## Recommendation

Yes: offer small, reviewable pull requests against Niko1221/Strata rather than a single megadiff from the Hakua fork.

Reasons consistent with [CONTRIBUTING.md](../CONTRIBUTING.md):

1. One problem per pull request; area-prefixed titles (`[Engine]`, `[Docs]`, …).
2. Issues #5021–#5023 already state the problems; a focused patch that answers an open issue is easier to review than an unsolicited fork dump.
3. Much of the fork’s hardening is Hakua-specific (private-cache chatbot policy, unsigned digest allowlists, product packaging) and must not travel upstream.
4. Mapped expert-pack work is explicitly out of scope until maintainers agree range on #5022.

Do **not** open a pull request until a clean branch is cut from current `upstream/main`, the patch is free of Hakua-only paths, and the validation section contains only commands that were actually run.

## Inventory: upstream-appropriate versus Hakua-only

### Suitable for upstream (after extraction onto `upstream/main`)

| Candidate | Nature | Upstream anchor | Separability |
|---|---|---|---|
| Fatal refusal of explicit unsupported Q36 flags in `--serve` (at least `--cache-type-k`, `--cache-type-v`, hand-written `--vram-reserve-mib`) | Engine behaviour | #5023 | High — local change in `src/qwen35/q36_engine.cu` argument parsing; do not ship mapped-pack or Hakua digests with it |
| Optional host-side refusal of the same flags before launch | App / host | #5023 | Medium — requires a **minimal** slice of `prepareQ36Launch` (or equivalent) without private-cache, without digest allowlists, without mapped-pack gating |
| Documentation honesty for Qwen3.6 UD-Q4_K_XL “RAM setup plans for 32 GB” | Docs | Softness audit §A.4; no dedicated issue yet (may open a short `[Docs]` issue first) | High — `docs/MODELS.md` only |
| Before-start refusal when free physical RAM cannot hold the legacy host expert arena | Engine or host (placement undecided) | #5021 | Medium — **requires maintainer agreement on where the check lives** before coding a PR |

### Not suitable for upstream (Hakua-only or premature)

| Item | Why it must stay in the fork |
|---|---|
| Hakua private-cache / chatbot (`privacyRequired`, `--prompt-cache`, `--conversation-cache-mib` strip-and-continue refusal) | Product policy for the Hakua memory stack; upstream Strata does not ship that inject path |
| `Q36_MAPPED_PACK_DIGESTS` and unsigned local EXE allowlists (`64226fde…`, installer digests) | Packaging and signing are Hakua / zapabob release artefacts |
| Hakua product version strings, Windows preview packaging, Control/Hakua-memory pins | Fork branding and release recipe |
| Full `--q36-expert-store mapped-pack` engine + pin-pool + transfer path | #5022: agree scope before any patch; fork still lacks paired speed evidence |
| STOP → process-lifetime product contract | Fork still records `FAIL_STOP1_STILL_ALIVE`; no honest upstream claim yet |
| Mutated-retry suppression that shortens context / adjusts `--vram-reserve-mib` as “recovery” | Host policy intertwined with Hakua Q36 contract; extract only after a separate, agreed issue |
| Invented or unpaired token-speed claims | Forbidden by CONTRIBUTING and by the softness audit |

## Proposed pull requests (small set)

Open at most one at a time. Preferred order: **PR-1**, then **PR-2**, then wait on #5021 / #5022 before any third engine PR.

---

### PR-1 — Engine: refuse unsupported flags under `--serve`

**Proposed title**

`[Engine] Refuse unsupported Qwen3.6 flags under --serve instead of ignoring them`

**Problem**

When `strata-q36` runs with `--serve`, an option the engine does not implement is logged as `ignoring … (not an option of this engine)` and skipped. The process continues. An explicit `--cache-type-k`, `--cache-type-v`, or a hand-written `--vram-reserve-mib` therefore appears to have been accepted while having no effect. Outside `--serve`, the same unknown option already prints usage and returns 2.

**Approach**

In `src/qwen35/q36_engine.cu` (`strata::qwen35::run` argument loop), treat at least the following as fatal under `--serve` when present on the command line:

- `--cache-type-k`
- `--cache-type-v`
- `--vram-reserve-mib`

Print a clear refusal and return a non-zero status (prefer the same class of exit used for other invalid options, e.g. 2). Do not fall through to the “ignore and continue” branch for these flags.

Optional tightening, only if maintainers prefer it in the same change: make **any** unknown `--…` flag fatal in `--serve` as well. That is a slightly broader behavioural change; if chosen, state it explicitly in the PR body and keep the three named flags as the motivating cases for #5023.

**Related discussion**

https://github.com/Niko1221/Strata/issues/5023

**Exact file list (intended)**

- `src/qwen35/q36_engine.cu` — argument parsing only
- Optionally a small unit-style or scripted check under `tests/` **only if** an existing Q36 argv harness already lives upstream; otherwise document a manual `--serve` dry invocation. Do not invent a large new test tree.

**What this pull request must NOT include**

- Mapped expert pack (`--q36-expert-store`, pin pool, pack file format)
- `apps/host/server/q36-run-contract.mjs` wholesale
- Private-cache / Hakua memory refusal
- Digest allowlists
- Documentation rewrites beyond a one-line note if the engine message itself is sufficient
- Default performance or placement changes

**Validation (template — replace with measured results before opening)**

```text
Problem and result: Under --serve, an explicit --cache-type-* or --vram-reserve-mib no longer continues after “ignoring”; the process refuses and exits non-zero.
Related discussion: https://github.com/Niko1221/Strata/issues/5023
Approach: Fatal check before the serve-mode ignore branch for the named flags (and, if agreed, for all unknown -- flags).
Validation:
  Passed: <exact command, revision, OS/GPU, observed stderr and exit code>
  Failed: <none, or exact failure>
  Not run: CUDA/HIP/SYCL full matrix if a backend was unavailable — list which; hardware serve of a full GGUF if not required for argv-only refusal
Limits: Does not add before-start RAM admission (#5021). Does not change STOP lifetime. Does not ship mapped-pack.
```

**Draft pull-request body (paste-ready, King’s English)**

```text
## Summary

- Problem: with `--serve`, `strata-q36` logs `ignoring <flag> (not an option of this engine)` for options it does not implement and continues. An explicit `--cache-type-k` / `--cache-type-v` or a hand-written `--vram-reserve-mib` therefore looks applied when it is not.
- Result: those flags are refused before the ignore-and-continue path; the process exits non-zero with a clear message.
- Related: https://github.com/Niko1221/Strata/issues/5023

## Approach

In `src/qwen35/q36_engine.cu`, refuse the named flags under `--serve` instead of skipping them. No change to the legacy expert arena, defaults, or placement. Mapped expert-pack work is intentionally absent (see #5022).

## Validation

  Passed: <fill before opening>
  Failed: <fill>
  Not run: <fill>

## Limits

This change does not admit or refuse the host expert arena by free RAM (#5021). It does not redefine `STOP`. It does not alter packaging digests or host private-cache policy.
```

**Branch preparation (local only; do not force-push)**

```text
git fetch upstream
git switch -c pr/q36-refuse-unsupported-serve-flags upstream/main
# apply ONLY the argv fatal checks to q36_engine.cu as upstream currently has it
# build backends touched; run listed validation; then ask before gh pr create
```

---

### PR-2 — Docs: qualify the 32 GB RAM setup plan for UD-Q4_K_XL

**Proposed title**

`[Docs] Qualify the 32 GB RAM setup plan for Qwen3.6 UD-Q4_K_XL`

**Problem**

`docs/MODELS.md` lists UD-Q4_K_XL under “RAM setup plans for” **32 GB**. The measured decode table nearby cites a Radeon AI PRO R9700 (**32 GB VRAM**) and an RTX 3060 (**12 GB**, most experts on the CPU). On a machine with **16 GB VRAM and 32 GB system RAM**, the legacy hybrid path still asks for a large host expert arena (on the order of ~18–19 GiB of host experts in observed failure text). Free physical RAM after OS and other services may be insufficient; allocation can fail only after the process has started (`no host memory for the experts (…)`, issue #5021). The present wording can be read as an assurance of comfortable operation on any 32 GB RAM PC.

**Approach**

Amend the Qwen3.6 size table (and, if needed, one short clarifying sentence beneath it) so that “32 GB” remains a planning figure but states the conditions: hybrid placement when the card cannot hold the experts; host arena demand; coexistence with other large processes not assumed. Do not invent new token/s figures. Do not claim mapped-pack as the product default.

Prefer a brief `[Docs]` issue first if maintainers wish discussion; otherwise a documentation-only PR with honest limits is acceptable under CONTRIBUTING for focused fixes.

**Exact file list (intended)**

- `docs/MODELS.md` — Qwen3.6-35B-A3B section only (table row and at most one clarifying paragraph)

**What this pull request must NOT include**

- Engine or host code
- Hakua release notes, `_docs/` evidence dumps, installer hashes
- Speed claims without same-day paired measurements on the stated hardware

**Draft pull-request body (paste-ready, King’s English)**

```text
## Summary

- Problem: the Qwen3.6 UD-Q4_K_XL row “RAM setup plans for 32 GB” can be read as a general assurance for 32 GB system RAM, including small-VRAM hybrid machines where the host expert arena is large and may fail after start.
- Result: the documentation states the planning figure together with hybrid / host-arena conditions and points at measured decode rows without adding unverified speeds.
- Related observations: https://github.com/Niko1221/Strata/issues/5021 (post-start host allocation failure). This PR does not implement the refusal in #5021.

## Approach

Edit only the Qwen3.6 section of `docs/MODELS.md`. Keep the existing measured decode table. No default or engine change.

## Validation

  Passed: documentation consistency / link check for the edited section; <command or manual review note>
  Failed: none expected for docs-only
  Not run: GPU builds (not required for documentation-only changes per CONTRIBUTING)

## Limits

Does not change launch behaviour. Does not document mapped-pack as a default. Does not generalise one PC’s thrash observations as a qualification for all 16 GB / 32 GB machines.
```

---

### PR-3 — Deferred: before-start host arena refusal (#5021)

**Proposed title (only after placement is agreed)**

`[Engine] Refuse the Qwen3.6 full host expert arena before start when physical RAM cannot hold it`

*(If maintainers place the check in the host or in `strata launch` instead, retitle to `[GUI]` or `[TUI]` accordingly.)*

**Status:** **Do not open yet.**

Issue #5021 leaves open **where** the refusal belongs (engine versus host versus Terminal). CONTRIBUTING requires maintainer agreement on scope before that class of change. The fork’s `admitLegacyExperts` / `physical_reserve` logic in `q36-run-contract.mjs` is evidence of one approach, not a ready upstream patch: that module does not exist on `upstream/main` and is entangled with Hakua allowlists and private-cache policy.

**What would be required before a PR**

1. Maintainer answer on #5021 as to placement.
2. A minimal patch on that placement only, cut from `upstream/main`.
3. Validation on a machine that would otherwise hit `no host memory for the experts`, with passed / failed / not run kept separate.
4. Explicit exclusion of mapped-pack (#5022).

**Draft body skeleton (do not paste until agreed)**

```text
## Summary

- Problem: the legacy hybrid path allocates the full host expert arena after the process has started; failure surfaces as `no host memory for the experts (<MiB>)`.
- Result: when free physical RAM cannot hold the arena plus an agreed reserve, the start is refused before that allocation.
- Related: https://github.com/Niko1221/Strata/issues/5021 — placement: <agreed location>

## Approach

<agreed mechanism only>

## Validation

  Passed: <…>
  Failed: <…>
  Not run: <…>

## Limits

Mapped expert pack is out of scope (#5022). STOP lifetime unchanged. No Hakua packaging digests.
```

---

### Explicitly not proposed as pull requests now

| Topic | Reason |
|---|---|
| Mapped expert pack + pin pool | #5022 scope agreement outstanding; fork evidence incomplete for speed |
| STOP ends the process | Fork gate still `FAIL_STOP1_STILL_ALIVE`; no honest fix ready |
| Private-cache fail-closed | Hakua-only |
| Unsigned digest allowlist | Hakua-only |
| Wholesale `q36-run-contract.mjs` | New host module on the fork; would need redesign without Hakua coupling |

## Remotes and permissions

| Remote | URL | Role |
|---|---|---|
| `origin` | https://github.com/zapabob/Strata.git | Hakua fork (push) |
| `upstream` | https://github.com/Niko1221/Strata.git | Official Strata (fetch confirmed; push of topic branches for a PR normally goes to a fork under the contributor’s account) |

Authenticated GitHub user observed on this machine: `zapabob`. Opening a PR against Niko1221/Strata typically means: push a branch to `zapabob/Strata` (or another personal fork of upstream), then `gh pr create --repo Niko1221/Strata` from that head. **No pull request was opened in this session.**

Do not force-push. Do not push Hakua `main` as the PR head.

## Blockers to opening an upstream pull request immediately

1. No clean topic branch yet exists that contains **only** the PR-1 or PR-2 file set against current `upstream/main`.
2. Fork `q36_engine.cu` currently mixes mapped-pack work with other changes; a blind diff of Hakua `main`…upstream would be a megadiff and would violate #5022.
3. #5021 placement is unanswered; #5022 forbids mapped-pack PRs until scope is agreed.
4. CONTRIBUTING requires building every backend a touched engine file affects (CUDA, HIP, SYCL) before requesting review — not yet run for an extracted PR-1 patch.
5. Parent / operator approval is required before `gh pr create` to Niko1221.

## Suggested sequence for the operator

1. Wait for, or politely ping, maintainer guidance on #5023 (fatal named flags versus all unknown flags) and #5021 (placement).
2. Cut `pr/q36-refuse-unsupported-serve-flags` from `upstream/main`; implement PR-1 only; validate; ask before create.
3. Cut a separate docs branch for PR-2, or open a short `[Docs]` issue first.
4. Leave mapped-pack and STOP for later evidence and agreement.
5. Keep Hakua private-cache and digest allowlists on the fork exclusively.

## Parent-agent note (Japanese, informal — not for upstream)

なんJ向け一言: 上流には小さなPR差分で出せ、キングスイングリッシュで書け、Hakua専用とmapped-packはまだ出すな。`gh pr create`はまだやってない。

## Change set for this document

| File | Action |
|---|---|
| `_docs/2026-11-04_q36-upstream-pr-plan{Cursor}.md` | Created — plan and paste-ready draft bodies |

## Verification performed for this plan

- Passed: read softness audit; CONTRIBUTING area-prefix and one-problem rules; `gh issue view` #5021–#5023 OPEN; `git remote -v` shows `upstream` → Niko1221/Strata; confirmed `q36-run-contract.mjs` absent on `upstream/main`; confirmed serve-mode ignore branch still present in fork `q36_engine.cu`.
- Failed: none for documentation planning.
- Not run: extraction branch, CUDA/HIP/SYCL builds, `gh pr create`.
