# Acceptance v2: model evidence gate

The evaluator now checks `strata-spin8-acceptance-v2`. A pass qualifies only the recorded model evidence gate. It does not authorise publication. Required CI, Windows distributions, install and GUI tests, the remaining approved comparison arms, independent reviews and release closeout still apply. Output always identifies `qualification_scope=model_evidence_gate_only` and `release_authorized=false`.

## Scope and authority

Task 2 follows the approved execution record `_docs/2026-10-23_strata_030_execution_Codex.md` and its task brief. The verified starting commit was `cfeb3daf49dd2a5d46c304a4f29f744e335a2b01`, with a clean working tree. Only the evaluator, its test file and this implementation record are source changes. Task 1 research is untouched.

The canonical prompt was read from `C:/Users/downl/_docs/prompts/CLAUDE-FABLE-5.md`; higher-priority identity, tool and environment instructions govern conflicts. The home, Codex-local and project AGENTS were read. Applicable SOPs are Common, Implementation Start Gate, Skill Selection, Security, LLMOps and Python. Applied skills are milspec-codex-standard and incremental-implementation. The codebase-inspection skill was inspected but its LOC workflow is not applicable. Self-review uses agent-self-review-evolution in review-only mode.

No package, environment, server, engine binary, model file or runtime policy was changed. Python commands use the existing uv executable and Python 3.12.10. There is no repository pyproject.toml, uv.lock or .python-version at the root. Explicit standard-library validation preserves the existing standalone evaluator without adding pydantic or other dependencies.

## Version and result meanings

`evaluate(report, evidence_root=Path(...))` returns `passed`, `formal_eligible`, `failures`, `results`, `qualification_scope` and `release_authorized`. Here `formal_eligible` refers only to eligibility of this model evidence record. It is not a release decision.

Legacy v1 inputs retain the old diagnostic calculation under `diagnostic_passed` and retain their measured result rows. They always return `passed=false`, `formal_eligible=false` and `legacy_schema_not_formal_eligible`. A boolean-only v1 record cannot qualify a v0.3.0 model gate. Unknown schemas and malformed roots or nested values fail closed.

For v2, speed results are retained once the measurement rows validate, even when a later functional, quality or monitoring gate fails. A reported inconclusive quality result stays visible as `quality_status=reported_inconclusive`; it cannot qualify. This status describes the report and does not authenticate its contents.

## V2 record contract

The root has `schema`, `evidence_kind=measured`, an ISO `measured_date`, `builds`, `runtime` and exactly two `models`. `builds.baseline` and `builds.candidate` each identify a lowercase 40-character `source_commit` and a 64-character `binary_sha256`, with a content-matching evidence receipt. Obvious repeated-character identity placeholders fail validation.

Mandatory models are `bonsai27b` and `strata-q2_0`, exactly once each. Their ordered `model_sha256` lists must match these frozen inputs:

| Model | Required SHA-256 |
| --- | --- |
| bonsai27b | `0ab2a1f237b73e5002ecd8c9b764249b90ee59eca749a6226c44bb43b1036a13` |
| strata-q2_0 shard 1 | `69820c02ec7d0b45ef2ebb19d6620299db749fe2aded7f39f93c6b88b199b720` |
| strata-q2_0 shard 2 | `316b46f3a2dbd68c900f43136ab9449f9dcc3725dfd8c794847c204bc161e113` |

Every model has `performance_mode=single-view|three-view` and exactly two contexts, `input_tokens=4096` and `32768`. Quality, physical-three-K functionality and monitoring measurements are required separately for all four model/context combinations. A model-level quality or overhead scalar does not substitute for these records.

Each context contains `conditions`, `warmups`, `pairs`, `quality`, `functional` and `monitor`. Conditions identify `cuda_architecture=sm_120`, device, sampling, positive integer concurrency, `baseline_profile=optimised`, candidate mode, candidate physical K count, codec and adapter SHA-256. The physical count of the performance candidate must be one for single-view or three for three-view. The chosen performance mode is independent of the physical-three-K functional gate.

`warmups` contains exactly three paired runs, so each arm receives three warm-ups. `pairs` contains exactly ten measured pairs. Within each group, the order alternates baseline/candidate, candidate/baseline. Every row has an explicit `run_index`: warm-up indices 0 through 5 and measured indices 6 through 25. Repeated measured pair ordering, duplicate indices and insufficient repetitions fail.

Every measurement row has `arm`, `model_id`, ordered `model_sha256`, `input_tokens`, `measured_date`, `source_commit`, `binary_sha256`, `conditions_sha256`, `prompt_sha256`, positive integer `completion_tokens`, positive finite `decode_seconds` and `ttft_seconds`, plus evidence. Each arm matches its own build; both arms match the same model, day, context and conditions. Prompt hashes and completion lengths match within each pair. Completion lengths are fixed within each group. Decode speeds and their median ratio must also remain finite; finite inputs whose derived speed overflows do not pass.

The `quality`, `functional` and `monitor` receipts share the model/day/context binding and the candidate source, binary and conditions identity. They are not accepted as unbound scalar claims.

Quality has `outcome=conclusive`, positive integer `evaluated_tokens`, nonnegative finite baseline and candidate mean NLL, and `datasets`. Each dataset role, evaluation/training/calibration/selection, identifies an id, SHA-256, source, revision and split. Their ids and dataset hashes must be distinct. Distinct hashes do not prove that datasets contain no overlapping examples; dataset curation remains a producer/reviewer responsibility. `fixed_cases` records pass/fail results for both arms by required case id; the evaluator derives the count of new failures rather than trusting a supplied zero.

Functional evidence records three physical K views, one shared V view, positive integer real-model loads and strict-graph executions, and executed/failure counts for every required case. Required names are `japanese`, `english`, `code`, `long_context`, `tool_call`, `oom`, `cancel`, `cache_save`, `cache_restore`, `cache_copy`, `cache_position` and `cache_invalidation`. Each must execute at least once with zero failures. Fixed quality cases use the same case ids.

Monitoring records baseline and monitored elapsed seconds and derives overhead. `audits` has explicit CPU-audit and GPU-probe counts for `load`, `coefficient_change`, `tokens_1024` and `seconds_60`. `faults` covers `cpu_coefficients` and `gpu_probe`; each records positive injections, matching stopped and invalidated counts, and `error=transform_invariant_violation`. Boolean counts are rejected.

Runtime policy is `keep-8080-stopped`. Evidence receipts are required for `before`, `after_success`, `after_failure` and `after_cancel`, each recording integer port 8080 and integer listener count zero. Restoration of the previous service is not a v2 requirement. Evaluation itself does not start, stop or probe a service.

## Numerical gates

For each required model/context, the median candidate decode speed divided by median baseline speed must be at least 1.05. Median candidate TTFT divided by baseline TTFT must be at most 1.05. Candidate mean NLL must be at most baseline mean NLL plus `ln(1.01)`. Comparing NLL values in this form avoids cancellation at the inclusive boundary; this is the PPL ratio threshold without exponentiating large values. Newly failed fixed cases must be zero. Measured monitoring overhead `(monitored_seconds-baseline_seconds)/baseline_seconds` must be at most 0.01.

## Evidence files and trust boundary

Every receipt-bearing record has `evidence={path, sha256}`. The receipt file is a JSON object exactly matching that record with its `evidence` key removed. This binds the raw recorded values to the evaluated claims, including bool/int distinctions. Receipts do not execute commands or contain instructions the evaluator follows.

The caller supplies `--evidence-root`; v2 cannot qualify without it. Paths use safe relative forward-slash components. Absolute paths, traversal, backslashes, colons, empty/dot components, paths longer than 240 characters and resolved paths outside the root are rejected. Resolved symlinks escaping the root are rejected. Each file read is bounded to 1 MiB plus a detection byte. Total distinct receipt bytes are bounded to 16 MiB. The report read is separately bounded to 16 MiB plus a detection byte. Reads are cached within one evaluation.

Hashes, schema checks and provenance records establish recorded consistency. They cannot establish that a measurement happened, that the machine or model truly matched its declaration, that a baseline was optimised, or that a producer did not fabricate an entire consistent record. This tool does not claim fabricated-data detection beyond structural, obvious-placeholder, hash and provenance validation. It does not rehash large model or engine files; independent acquisition/build and real-run evidence remain necessary. A hostile process concurrently replacing files is outside this local offline verification guarantee.

Synthetic positive fixtures exist only in unit-test temporary directories and are removed by test cleanup. They are evaluator test inputs, never saved benchmark proof. No real-model qualification input was produced during this task.

## Validation and implementation history

The initial pytest attempt encountered a test-fixture syntax error; that collection error is not counted as meaningful RED evidence. After correcting it, the new tests were replayed against the frozen base evaluator through an in-memory module loaded with `git show cfeb3daf49dd2a5d46c304a4f29f744e335a2b01:tools/spin8_acceptance.py`. This produced one assertion failure because legacy v1 wrongly returned `passed=true`, and one expected API error because the old evaluator lacked the v2 evidence-root contract. This is the recorded contract RED, not a fabricated benchmark failure.

An intermediate complete focused pytest run passed 21 tests in 20.20 seconds. A later run passed 23 tests in 31.74 seconds, including three-view candidates and inclusive NLL/overhead limits. Final verification passed all 26 tests in 28.06 seconds, including CLI success/failure, exact frozen identities, repetition counts, dataset provenance and boolean monitor counts. Black check left both files unchanged, flake8 reported no findings with the documented line-length/style options, and `git diff --check` passed.

Commands use this prefix, with no installation or dependency sync: `C:/Users/downl/.hermes/bin/uv.exe run --no-project --python C:/Users/downl/AppData/Local/Programs/Python/Python312/python.exe`. The interpreter reported Python 3.12.10. The existing environment emits warnings about two dangling distribution metadata directories; these were not repaired. Pytest plugin autoload is disabled for focused runs to avoid unrelated global plugin work. The repository conftest still protects the real user config.

Validation commands are `python -m pytest tools/test_spin8_acceptance.py -q`, `python -m black --check tools/spin8_acceptance.py tools/test_spin8_acceptance.py`, `python -m flake8 tools/spin8_acceptance.py tools/test_spin8_acceptance.py --max-line-length=100 --extend-ignore=E203,W503`, and `git diff --check`. CLI success and malformed JSON exit codes are tested in temporary directories. CLI JSON uses stdout as its existing machine-readable interface.

## Self-review and remaining work

Self-review-event: type=qa_defect scope=tools/spin8_acceptance.py category=release-gate evidence=_docs/2026-10-23_acceptance_v2_Codex.md

Trigger evidence was the boolean-only legacy fixture granting a pass and the missing versioned provenance contract. Decision is review-only for governance: the authorised task changes evaluator checks and tests, with no AGENTS, SOP, skill or automation edits. During implementation, review also caught overflow in derived speeds, a test-fixture reset error and loss of visible speed results when quality was inconclusive. Focused regression tests cover these findings. Final code review checks scope, default behavior, failure closure and evidence bounds.

Runtime, GPU, real-model quality/speed, CI, package/install/GUI and release qualification were not run by this task. They remain separate execution tasks. Rollback is an ordinary revert of this task's source commit, with no model or runtime restoration needed. No formal MILSPEC compliance or v0.3.0 release-readiness claim is made.
