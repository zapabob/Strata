# Hermes Agent + Sakura-Inkling-2-Mini 98K on Windows — setup log

## Objective
User asked to run Sakura-Inkling-2-Mini at 98,304-token context through the
Windows Hermes Agent provider `inkling2`.

## Setup verified
- Hermes config `C:/Users/downl/.hermes/config.yaml`: provider `inkling2`,
  base_url http://127.0.0.1:8092/v1, key_env STRATA_API_KEY, models
  sakura-inkling-2-mini-131k / sakura-inkling-2-mini, discover_models true.
- Repo config `configs/strata-sakura-inkling2-98k.json`: exe
  H:/Strata/build/engine-cuda135/strata-inkling2.exe, model
  Sakura-Inkling-2-Mini-Uncensored-Q4_K_M.gguf, args `--max-context 98304
  --kv-q8 --expert-vram 7.8`, host 127.0.0.1 port 8092.
- Launch script `scripts/start-sakura-inkling2-hermes.ps1 -Context 98k`.
- STRATA_API_KEY set in environment.

## Bug fixed
First launch failed with `NameError: name 'hy4_kind' is not defined` at
terminal/serve/server.py:11196 — the v0.2.19 three-way intake dropped the local
`from serve import hy4_kind, inkling_kind` in the RAM-budget block. Added the
imports (commit f8cf23502); syntax check OK; restart succeeded.

## Verification (exact outputs)
- Server log: `model aliases: Sakura-Inkling-2-Mini-Uncensored-Q4_K_M,
  sakura-inkling-2-mini-98k` then `ready: http://127.0.0.1:8092/v1 ... context
  98304 tokens, API key required`.
- `GET /v1/models` (Bearer STRATA_API_KEY): 3 models (id sakura-inkling-2-mini
  + 2 aliases), all `status=loaded`, `context_length=98304`, `max_model_len=98304`.
- `GET /health`: `status=ok, max_context=98304, model=sakura-inkling-2-mini,
  loaded=true, api_key=true, service=strata`.
- `POST /v1/chat/completions` (model sakura-inkling-2-mini, 32 tokens):
  finish_reason=length, completion_tokens=32, predicted_per_second=24.4.
  With the Hermes-configured name sakura-inkling-2-mini-131k: resolves to
  sakura-inkling-2-mini, predicted_per_second=29.4.
- `POST /v1/messages` (Anthropic-compatible, x-api-key): stop_reason=max_tokens,
  output_tokens=16 — Hermes can use either API dialect.
- Server process: python PID 30668 listening on 127.0.0.1:8092 (the 600s shell
  timeout killed only the wrapper PowerShell, not the child server).

## Residual / caveat
- `message.content` is empty (null / 0 content blocks) even though tokens are
  generated: the Sakura Inkling-2 GGUF emits control-token-heavy output that the
  current tokenizer/chat-template path does not decode into visible text.
  Transport, provider auth, model resolution, 98K context and generation all
  work; visible answer quality is unqualified (`releaseQualified=false`).
- Server is a foreground-launched process; it stops when PID 30668 exits.
