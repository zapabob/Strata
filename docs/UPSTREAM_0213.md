# Official 0.2.13 source integration

The installed personal build (product0.5.4-local.1, Control0.5.5, native0.5.4) combines official main
[`f33c8c30`](https://github.com/Niko1221/Strata/commit/f33c8c30588ff00e24b6b63bad0bf6a14da19081)
and [v0.2.13](https://github.com/Niko1221/Strata/releases/tag/v0.2.13) with the
Hakua fork. Checked on 2026-11-10. It was built and installed locally, with
artifact-bound checks and remaining limits below. It is not a public release.

App/Control source is85a78234; native source is separately frozen at7bb24974.
The earlier personal0.5.3-local.1 artifacts from1f666144/ded724a4 remain preserved.
Their results are not used as new checks. Public downloads remain0.5.1.

## Combined APIs

The official changes include per-model drafter download sizes, tuned/stock Auto
preparation, generated launch-policy tables, signed-feed model families and
geometry-based engines, plus deferred screens, translations and syntax coloring.
The fork retains authenticated per-turn memory consent, existing local GGUF
reuse, workspace file CRUD and reversible trash, Qwen3.6 mapped/bounded experts,
private cache ownership and current-child evidence, refusal-direction opt-in,
Windows Job controls and signed fork components.

New CMake backend modules contain the fork's existing cache hooks and Qwen3.6
tests. No resource allowance was raised. Product, Control, CUDA and Metal source
versions remain independent of official version numbers.

## Verification and limits

Focused Host131 passed; TypeScript passed; vendored ggml127-file verification
passed. Python drafting/card/private-file/monitor/setup group204 passed,2 skipped;
new official feature group144 passed,5 skipped; affected server group187 passed,
2 skipped. Source browser workspace checks8 passed,0 page errors, on desktop
and Japanese mobile layouts. Full server discovery exceeded its600s deadline
and remains incomplete. These are source, CPU/mock, browser and local-HTTP
checks. Separate actual native and installed-model checks are recorded below;
no new speed benchmark is claimed.

The base-catalog check retains a known pre-merge missing-key failure in six
languages; there are no new missing keys. The actual outcome, failed attempts,
public-advisory version comparisons and build status are in the
[implementation log](../_docs/2026-11-10_upstream-0213-integration_OpenCode.md).

Five-job native/app builds passed with retained incremental objects and caches.
Fresh native CPU, GPU and sanitizer checks passed. Bounded/legacy paths each
passed7 short actual requests, restart passed2, and their comparison passed.
Model/pack/tokenizer snapshots matched before/after. These use4096 capacity,
not a full4096-token prompt or long-context quality test.

The installer qualified29544 exact payload files and13 startup self-tests.
Backed-up overwrite preserved4028 user files and the older native component.
Actual candidate and installed WebView2 Q36/Prism checks passed without mocked
inference. Installed workspace CRUD passed7 UI checks. Prism had one restart
warm-up timeout; the unchanged serial rerun passed both answers and restart.
That failure remains a residual risk. A supplemental source-memory browser
fixture failed before UI checks because browser launch rejected the debugging
profile/environment; it is not reported as a pass. Server-side memory tests passed.

Normal startup passed: no debugging, models unloaded, settings retained, app left
open. The fresh native resource guard independently measured12 violations;
releaseQualified=false remains. Older resource findings retain their own binaries.
Full-window generation, general quality, low-precision quality and positive
Qwen3.8 projection are unqualified.
