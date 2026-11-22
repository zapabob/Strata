# Sakura-Inkling-2-Mini tokenizer/output — Deep Research + fix evaluation

## Objective
User asked to deep-research the Sakura-Inkling-2-Mini tokenizer problem and
incorporate the fix. Hermes 98K returned empty `message.content` despite tokens
being generated.

## Deep Research (primary sources, read 2026-11-23)
- GGUF: `webmp3/Sakura-Inkling-2-Mini-GGUF` (independent quant of
  thinkingmachines/Inkling-2-Mini, Apache-2.0; needs llama.cpp b12600+,
  looped Inkling-2 architecture PR #32694). The local file
  Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf is 17.48 GB Q4_K_M.
- Official chat template: `thinkingmachines/Inkling-2-Mini/chat_template.jinja`
  (role_token `<|message_user|>` etc., `{%- generation -%}` markers,
  `<|content_text|>` / `<|content_thinking|>` / `<|content_invoke_tool_json|>`
  channels, `reasoning_effort` map). Fetched in full as reference.
- ggml-org/llama.cpp issue #32710 (open, 2026-11-21) "inkling2_loop:
  perplexity nan on CUDA" and #32778 (open, 2026-11-22) "prompts longer than
  ~96 tokens produce all-'?' output ... server stays broken afterwards":
  Root cause = scheduler op-offload of HOST-resident experts on the LOOPED
  layers (6-17, applied 3x/token). The three passes share one device copy;
  `sched_copy_experts` uploads only pass-1 experts, so passes 2-3 read
  unuploaded experts -> NaN/garbage from the first token. Fix commits
  `d652ead` (ggml-backend: copy offloaded weights again in each split that
  uses them) and `435f508` (ggml: copy host experts again for each split that
  reads them). Workarounds: `--no-op-offload`, `-ub < 32`, or keep looped-layer
  experts resident on GPU (non-looped blocks 0-5 / 18-23 may stay on host).

## Findings in this fork
- The Sakura GGUF DOES embed the official chat template: 6868 chars with
  role_token/generation/content_text all present (verified with the repo's
  GGUFFile parser). So the tokenizer/template is NOT the problem — an earlier
  suspicion based on a 200 KB header scan was wrong and was retracted.
- The fork's CUDA engine (`engine/src/inkling2/cuda/ink_runner.cuh`) uses its
  own expert placement (`place_experts`, `--expert-vram` cap), not ggml's
  scheduler. The exact llama.cpp bug does not directly apply, but the same
  structural risk (looped layers sharing host experts) is plausible.
- Hermes 98K with `--expert-vram 7.8`: tokens generated (~10-24 tok/s) but
  `content` empty / control-token-heavy (`1 11 196980 2 ...`).

## Fix attempts and measured effects
1. Added official `chat_template_inkling.jinja` to terminal/serve — then
   retracted and removed after confirming the GGUF already embeds the same
   template (no repo change remained).
2. `--expert-vram 11.5` (keep more looped experts in VRAM, Deep Research
   workaround): benchmark 98K --kv-q8 --chunk 512 --tokens 1..16:
   `pp 22.33 t/s, tg 30.83 t/s, hits=12290 misses=1822 cpu_ms=443.2`,
   2338/3072 experts in VRAM (11.37 GiB). Improvement vs 7.8 (tg 9.11-11.93,
   cpu_ms ~2000-2655) is ~3x on decode. Evidence:
   H:/Strata/evidence/antigravity-sakura98k-vramfix-r2.txt.
3. `--chunk 16` (op-offload batch < 32 workaround) with expert-vram 11.5:
   launched; evidence antigravity-sakura98k-chunk16.txt (result pending at
   time of writing). Embedded template SHA-256 53a9035f...6dc (6868 chars,
   138 lines) — the GGUF carries the official Inkling template verbatim.

## Tokenizer / parser verified healthy (2026-11-23)
- Decoded the benchmark's generated token IDs with the GGUF tokenizer
  (terminal/tools/strata_tokenizer.py, system Python 3.12): `1='"'`,
  `68014='\n\n'`, `2='#'`, `220=' '`, `16='1'`, `142702=<Korean char>` — i.e.
  the model emits valid multilingual Markdown text, NOT the all-'?' garbage
  of upstream #32778. Output corruption is avoided with expert-vram 11.5.
- `serve.inkling_dialect.InklingDialect.feed_channels()` correctly parses both
  raw text (`('content', '"\n\n# 1. hello\n\n')`) and wrapped
  `<|message_model|><|content_text|>...<|end_message|>`. Test evidence:
  H:/Strata/evidence/test-inkling-dialect.py. So the tokenizer, template and
  channel parser are all healthy.
- `--chunk 16` run: tg 26.76 t/s (slightly slower than chunk 512's 30.83),
  same token pattern — the small ubatch workaround adds no benefit; the
  expert-vram increase is the effective mitigation.
- RESOLVED: with the vramfix config (`--expert-vram 11.5`) the same Hermes-style
  chat completion that previously returned empty content now returns a correct
  answer: question "What is 17 times 23?" -> `content=[391]`, finish=length,
  predicted 38.9 tok/s (previously content empty at 24.4 tok/s with 7.8).
  So raising expert-vram fixes both the garbage channel output AND the empty
  `content`. Evidence: vramfix server on 127.0.0.1:8092, 2026-11-23.

## Conclusion so far
- The "tokenizer problem" is NOT a tokenizer/template/parser defect — all
  three verified healthy. It is a host-expert/looped-pass output corruption
  (upstream #32710/#32778 class) mitigated by raising `--expert-vram` 7.8 ->
  11.5 (~3x decode). Recommend updating the 98K config accordingly; keep
  `releaseQualified=false` because visible answer quality is still not fully
  qualified.

## GPU / RAM / CPU distribution (user request 2026-11-23)
The fork's `place_experts()` (inkling2_engine.cu:2919) already implements the
Deep-Research-recommended distribution; no engine source change was needed:
- **GPU VRAM**: Priority 1 = looped core layers blk.6-17 (executed 3x/token),
  Priority 2 = outer layers via Fate Zeta-Lagrangian allocation, capped by
  `--expert-vram` (11.5 GiB in vramfix config).
- **pinned RAM**: `pp_stage` buffers (2 x STRATA_PP_STAGE_MB, default 64 MB)
  for prompt staging over PCIe.
- **CPU**: remaining host-resident experts computed by worker threads
  (`--cpu-threads`, default 5 physical cores here).
- `STRATA_VRAM_RESERVE_MB=3328` keeps WDDM shared-memory migration off on the
  16 GB RTX 5060 Ti; `STRATA_TIER2_FLOOR=0` prioritizes tier1.
Added launcher params `-PpStageMb/-VramReserveMb/-Tier2Floor` and the
`98k-vramfix` ValidateSet case (commit 64d376540); the server log confirms
`expert distribution: GPU(<=--expert-vram) + pinned-RAM(64MB x2) + CPU workers;
VRAM reserve 3328MB, tier2-floor 0`.
- VERIFIED end-to-end: the 98K server with this distribution answered
  "What is 17 times 23?" -> `content=[391]` (correct) at 37.4 tok/s,
  expert cache 89.4% hit, prompt 5402 ms. So GPU/VRAM (looped core + Fate-zeta
  outer, <=11.5 GiB), pinned RAM (2x64 MB staging) and CPU workers (host
  experts) cooperate correctly under Hermes.

## Residual
- No llama.cpp scheduler in this fork, so upstream fix commits cannot be
  cherry-picked directly; the fork's `place_experts` / looped-pass path would
  need an equivalent "copy host experts per pass" fix if the workaround is
  insufficient.
