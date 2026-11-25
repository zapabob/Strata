# TSI Benchmark Protocol

Status: **Evaluation protocol (`research/tsi-verified-evaluation`)** · **`releaseQualified=false`**

This protocol governs all reproducible NKAT–URT TSI and VRE evaluations on `zapabob/Strata`.

---

## 1. Dataset Split Discipline

Four strictly disjoint splits are maintained in `tools/tsi/tasks.py`:

| Split | CLI `--suite` | Count | Permitted Use |
|---|---|---:|---|
| Development | `dev` / `core-v1` | 12 | Feature development, prompt/parser debugging |
| Calibration | `calibration` | 4 | Restart cutoffs, threshold tuning, empirical committor calibration |
| Validation | `validation` | 4 | Policy/model selection across candidates |
| Frozen holdout | `frozen-holdout` / `holdout-v1` | 8 | Final untouched confirmation only — never used for tuning |

Post-hoc cherry-picking of budgets, seeds, models, or task subsets is prohibited. Multiple seeds on the same task are never counted as independent tasks in binomial or Hoeffding sample sizes $n$.

---

## 2. Independent Verification Hierarchy

Every trial records an explicit `verification_level`:

1. `UNVERIFIED` — failed, truncated, malformed, timed out, API error, or unverified prose.
2. `EXACT_ANSWER_VERIFIED` — exact parsed integer or `fractions.Fraction` match.
3. `DETERMINISTIC_TEST_VERIFIED` — deterministic test evaluation (e.g. exact polynomial root verification) with zero `eval()`/`exec()`.
4. `NUMERICAL_CERTIFICATE_VERIFIED` — exact predicate verification (counterexample compositeness, Diophantine witness).
5. `FORMAL_PROOF_VERIFIED` — granted **solely** by an exit-0 isolated Lean kernel check with fixed theorem signature and zero `sorry`, `admit`, `unsafe`, or unauthorised `axiom` declarations. Never granted by LLM self-grading.

Known benchmark problems (`known_benchmark_problem`) and independently novelty-checked scientific discoveries (`novel_discovery_candidate`) are aggregated separately.

---

## 3. Canonical Trial Record Schema (Version 1)

Each task trial writes one UTF-8 JSONL record containing all 17 mandatory fields:

```json
{
  "schema_version": 1,
  "task_id": "core-nt-01",
  "model_id": "example-model",
  "model_sha256": null,
  "engine_commit": "21473cc9b2fb33c27be1ffbd0bdc87c0e12fec02",
  "quantisation": "Q4_K_M",
  "seed": 42,
  "token_budget": 512,
  "tokens_used": null,
  "wall_time_ms": null,
  "attempts": [],
  "peak_vram_bytes": null,
  "peak_ram_bytes": null,
  "verifier": "exact_int",
  "verification_level": "UNVERIFIED",
  "verified": false,
  "termination_reason": "not_run"
}
```

Unmeasured values must be written as `null`, never `0`. Bearer tokens, API keys, and private user directory paths are redacted by `tools/tsi/metrics.py`.

---

## 4. Mandatory Reporting and Safety Floors

- **Paired comparison**: reference and candidate runs must evaluate identical tasks, prompts, seeds, and budget grids, reporting McNemar discordant counts (`ref_pass_cand_fail`, `ref_fail_cand_pass`) and both token-axis and wall-clock-axis RMST.
- **CPU vs GPU separation**: CPU-only unit tests and mock HTTP API tests must be reported separately from live RTX 5060 Ti inference measurements.
- **Hardware safety floors**: available RAM $\ge 3\text{ GiB}$, Windows commit $\ge 4\text{ GiB}$, GPU VRAM reserve $\ge 768\text{ MiB}$, free disk $\ge 5\text{ GiB}$ (`C:`) / $\ge 10\text{ GiB}$ (`H:`). Any context window (e.g. 128K) exceeding safe headroom must be recorded as **not run (out of safety budget)**.
