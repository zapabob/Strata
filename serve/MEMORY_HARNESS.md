# Optional local memory harness

This feature is off unless the server configuration explicitly enables it.
It has only been tested with synthetic profiles and a scripted engine. The real
hakua writer and real-model summary quality have not been qualified here.

The operator supplies `hakua_harness` in the existing server configuration:

```json
{
  "enabled": true,
  "users": [
    {"principal": "alice", "key_env": "ALICE_EXISTING_KEY", "root": "H:/private-memory/alice"},
    {"principal": "bob", "key_env": "BOB_EXISTING_KEY", "root": "H:/private-memory/bob"}
  ]
}
```

Each environment variable must contain a unique ASCII key already accepted by
the server's existing `api_key` configuration. The ASCII restriction makes
HTTP header identity unambiguous across the server's legacy UTF-8 decoding.
No keys are generated or logged.
Principal names and paths come from this operator configuration, never the
request. Roots must be absolute, separate directories. Protect them with the
operating system's file permissions. Hostile concurrent filesystem replacement
is outside this prototype's guarantees. Symlinked or hardlinked profile files
are rejected or omitted.

Mapped keys can use the three inference APIs, token counting and model listing.
They cannot use shared status, telemetry, monitor, slot or management routes.
They also cannot invoke server MCP tools or read server-local image paths, even
when a request omits `strata_memory`. `STRATA_BATCH_TRACE` must be off because
its control-line output can expose generated token IDs.
Keep a separate unmapped operator key if those facilities are needed. Existing
unmapped keys retain their original privileges. This is not a general-purpose
tenant isolation system. Private inference and summary runs omit text tails,
tool names and API-monitor records; aggregate timing remains shared internally.
The server also disables its process-global Responses compaction-tool cache
while the harness is configured; client-supplied session IDs cannot partition
that cache. At startup the harness requires explicit `--prompt-cache 0` and
`--conversation-cache-mib 0` in the effective native engine arguments. It also
rejects slot save/restore. The engine cannot resume a previous request through
its conversation-prefix cache under those settings. This static and synthetic
check has not yet been verified with two real users switching on the native
engine. Therefore this prototype must remain disabled for multiuser production
traffic until cache switching and restored session data are tested.

Each request independently supplies:

```json
"strata_memory": {"read": true, "store_summary": true, "turn_id": "unique-turn-id"}
```

The two boolean consents are independent. Omitting this field performs no
memory read or summary write. `read` permits bounded reads of that principal's
`SOUL.md`, `USER.md` and `ebbinghaus.db`. Recall uses SQLite read-only immutable
mode and query-only enforcement, without constructing a hakua store. It omits
databases with WAL, shared-memory or rollback-journal sidecars. Recall is lexical
over at most 64 recent accessible, current, active records; at most four bounded
snippets enter the prompt. This is not full semantic retrieval or fresh WAL
visibility. Current text inputs and visible answers are limited to 16,384
characters for memory processing.

`store_summary` permits a second inference through the already-local engine.
Its input contains only this turn's current user text and completed visible
assistant text. It has no tools, history, recalled records or persona files.
Reasoning, incomplete generations and tool-call continuations are not saved.
The model is instructed to omit credentials; model-generated summaries still
need real-model quality and privacy qualification before production use.

The harness rejects prompt plus reserved output exceeding either the actual
engine context or 131,072 tokens. It never reduces an explicit output reservation
to accommodate memory. Automatic MCP rounds with memory consent are rejected.
Memory consent is also rejected while a `perf131k_e2e` audit is active: a second
summary inference must not overwrite the pilot request's receipt or token totals.

The optional `hakua_memory.ebbinghaus.store.EbbinghausMemoryStore` import occurs
only after a completed consented turn and successful local summary. A missing
dependency leaves the API answer intact and skips persistence. The writer was
inspected against hakua-memory commit `2908c6b9`; this work does not install or
change it. The library constructor may migrate the dedicated profile database.

The per-profile `strata-turns.db` ledger records an attempt before invoking the
writer. A normal retry with the same turn ID and content does not write again.
Reusing an ID for different content is refused. A crash after recording an
attempt can omit a memory: status is uncertain and the attempt is never replayed,
because hakua's duplicate-content handling can change reinforcement metadata.
This is at-most-once writer invocation, not exactly-once delivery. Persistence
errors and uncertain attempts are reported without private content in logs.
There is no HTTP persistence-status endpoint in this prototype.

Run synthetic checks with an existing Python environment containing Jinja2:

```powershell
py -3 -m unittest serve.test_memory_harness -v
```

Tests create temporary synthetic profiles, never real user memory or a model
process. No live launch, cloud request or dependency installation is needed.
