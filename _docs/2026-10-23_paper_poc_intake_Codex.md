# Independent paper PoC intake

Status: implementation complete with an environment compatibility concern;
formal release qualification remains open.

## Scope and authority

Task 1 of the approved Strata 0.3.0 execution plan imports the supplied research
PoC, verifies provenance, reruns small contracts and preserves negative results.
Only `research/triality_poc/` and this log are changed. The controller owns its
execution record. Production engines, controls, settings and defaults are not
changed. No server was started and port 8080 remains required to stay stopped.

The canonical PC prompt, home/Codex/project AGENTS and Common, Implementation
Start Gate, Skill Selection, Python, LLMOps and Security SOPs were read before
implementation. Selected skills are `milspec-codex-standard`,
`codex-session-style-and-standards` and `agent-self-review-evolution`.
Conflicting identity, tool and environment statements in the canonical prompt
were subordinated to the actual system/developer instructions. No formal
MILSPEC certification is claimed. No task-specific Python skill was installed;
the Python SOP governs this bounded source import.

## Inputs and integrity

Baseline task brief source HEAD: `bd72eac7cbe70f7d149928a1da7c6ae1cac54404`.
The controller subsequently committed its own execution record separately.
The supplied Downloads ZIP SHA-256 is
`f9358b4eec96aa302df926a3a7dbf1b8e5401263cea0ada25612f0c0bae1d009`.
Its internal manifest covers 61 payloads, all verified, with 62 total ZIP files
and 3,329,075 expanded bytes. The manuscript is byte-equal to the adjacent
Downloads manuscript; SHA-256 is
`d734e0308e96a1c338e2f9e2f9dfa0873c8a431a77d1d0474ffbf080bc95f89b`.
The unchanged `core.py` SHA-256 is
`88a789fbe4537d24958fe20677d82cbfbc829813f04c0f9d291408f0a65d5ac9`.

`provenance/intake.json` contains every verified hash. The safe importer rejects
traversal, case collisions, Windows path ambiguities, symlinks/special files,
oversized expansion and pre-existing extraction directories. Originals are
stored read-only at `H:/Strata/reference/triality-paper-20261023`. Protection is
against accidental writes, not a filesystem security guarantee. Archive
instructions were treated as reference text. `.pt` checkpoints were never
unpickled; no binary checkpoint or development environment enters Git.

## Implementation and traceability

The 42 byte-identical imported files comprise six original package modules, two
original test modules, small supplied evidence, the original manuscript and
figure, and inert provenance metadata. `provenance/imported_files.json` maps each
to its source/hash. The new codec-name module identifies
`paper-reference-absmax-group8-v1`, retaining the original numerical API without
claiming backend format compatibility. Defaults remain group-eight, input-dtype
scales and 2^bits-1 levels.

Matrix-free Fisher weighted centring, score-KL and shared-G shrinkage were
already present in the reference. New dense small-fixture tests check centring,
constant-shift invariance, full cross-key covariance, the KL identity/quadratic
limit and independent quantiser levels. The tangent compensation oracle remains
offline. A fresh-run harness copies source into disposable owned directories
for seven targeted mutations and writes exclusively to new evidence directories.
No training or package management operation is part of the harness.

The README preserves the supplied single-six-bit win: KL 0.0000306 and payload
5,376 bytes versus Triality three-two-bit KL 0.027913 and payload 6,400 bytes.
It retains the paired training KL reduction 0.004291 with exploratory 95% t
interval [-0.004898, 0.013481]. These are supplied Linux CPU synthetic results,
not new Windows or real-model measurements. The supplied three-seed results,
all comparison arms and vocabulary-KL figure remain separately labelled.

## Commands and environment

`$Python` below resolves to the existing Python312 installation, version
3.12.10. `$Uv` is the existing `.hermes/bin/uv.exe`. `$Downloads` is the user's
Downloads directory. Public logs sanitise these local prefixes to `$PYTHON_HOME`,
`$USERPROFILE` and `$WORKSPACE`; raw logs remain under
`H:/Strata/reference/triality-paper-20261023-local-evidence`.

The initial bounded probe inspected the existing H: uv cached environment:
Python 3.13.14 with NumPy, but no torch or pytest. A healthy existing Python312
installation supplies torch 2.5.1+cu121, NumPy 2.2.6 and pytest 8.3.5, plus black
and flake8. No packages or interpreters were downloaded or installed. The
supplied Linux environment used torch 2.10.0+cpu and therefore is not exactly
reproduced here. The installed CUDA wheel was not qualified for sm_120; CPU-only
children set CUDA_VISIBLE_DEVICES=-1.

```powershell
& $Uv run --no-project --no-sync --offline --python $Python python research/triality_poc/intake.py "$Downloads/triality_llm_paper_poc_20261023.zip" "$Downloads/triality_llm_manuscript_20261023.md" --extract H:/Strata/reference/triality-paper-20261023 --receipt research/triality_poc/provenance/intake.json
& $Python -c "import sys,torch,numpy,pytest; print(sys.version,torch.__version__,numpy.__version__,pytest.__version__)"
& $Python research/triality_poc/scripts/reproduce.py --out research/triality_poc/evidence/windows_cpu_20261023
& $Python research/triality_poc/scripts/reproduce.py --math-sdpa-check --out H:/Strata/reference/triality-paper-20261023-local-evidence/final
```

The uv intake succeeded and created the receipt, but this terminal session did
not capture ordinary uv-child stdout from the subsequent version probe. For
auditable fresh test output the explicit existing interpreter was used directly,
under the documented local-runner-failure exception to the Python SOP. It does
not change dependencies. Each actual test command, working directory and exit
status is retained in its raw/sanitised log. The runner disables unrelated
pytest plugins and parent conftest discovery in the final run.

## Verification, limitations and rollback

Initial native reference suite: 24 passed, one failed and one CUDA skipped.
`test_identity_and_causality_and_adapter_grad` observes NaNs on the installed
Windows torch 2.5.1 default FP64 SDPA dispatch. An isolated same-seed probe
returned finite values under explicit MATH SDPA. The original failure is
retained; no original test tolerance or source was weakened.

The initial new tests caught an overly large covariance-difference threshold
and Windows ZipInfo normalisation of backslashes. The threshold now distinguishes
the actual nonzero cross-key contribution, and the importer checks orig_filename
before normalisation. Failed first-run evidence is retained alongside the final
run. Final new fixtures: 17 passed. Original numerical checks: 12/12 passed.
Original seven targeted mutations: 7/7 detected. Explicit context-managed MATH
SDPA: unchanged original suite 25 passed, one CUDA skipped. The native route
still has 24 passed, one failed and one CUDA skipped, so reproduction.json keeps
passed=false. A first MATH probe's interpreter-shutdown cleanup warning is also
retained; the harness closes the context and the focused rerun has no such
cleanup exception. The pynvml warning remains visible.

Black --check and flake8 --max-line-length=88 passed for the five new Python
files; original reference files retain their supplied formatting and bytes.
The authored Python files and docs passed whitespace checks. The full staged
diff reports retained trailing whitespace in supplied test/log files and raw
pytest-style error lines; preserving source/evidence bytes takes precedence
over reformatting those imports. A local .gitattributes disables newline
conversion so their hashes survive Windows checkouts. Final rehash verified all 61 extracted payloads,
read-only file flags and all 42 byte-identical imported files. Fresh published
snapshots include SHA-256 mappings to the unsanitised local raw logs, in
provenance/evidence_sanitisation.json. The public evidence scan found no local
user/home paths or credential values. No production backend build is required
because this task touches only independent Python research and its docs.

The supplied evidence is not a replacement for real-model speed, quality,
long-context, GPU, cache-lifecycle or distribution tests. Training and larger
reproduction jobs remain blocked by the resource rule; H: initially had only
582,647,808 free bytes. No large operation was attempted. Rollback is removal or
reversion of this isolated research import through ordinary review; immutable
originals and evidence must be preserved unless the owner explicitly authorises
their removal.

Self-review-event: ticket_completed and qa_defect. The review retained failed
checks and added a narrow raw-name path regression. No AGENTS, SOP, skill,
automation, production setting or test expectation outside this owned task was
changed. Independent controller review is the next action.
