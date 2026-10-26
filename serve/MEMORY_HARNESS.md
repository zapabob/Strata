# Optional local memory harness

This feature is off unless the server configuration explicitly enables it.
It has been tested with synthetic profiles, a scripted engine, and one
temporary-profile write/read through the installed hakua writer at `2908c6b9`.
Real-model summary quality and native multiuser traffic have not been qualified.

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
Each user may also supply `persona_sha256`, an operator-owned object mapping
`SOUL.md`, `USER.md` and/or `MEMORY.md` to their approved lowercase SHA256 values.
Missing approvals omit those files. `MEMORY.md` is approved prompt context;
it is not a destination for raw turn storage. Changed bytes and links are
omitted, even with read consent. Each file is capped at 8192 bytes by default;
an operator may set `persona_max_bytes` per user to an integer from 1 through
32768. Approval is checked against the same byte
buffer inserted into the prompt; content updates require explicit operator
reapproval and a configuration reload. No approval is inferred from a request
or from the file merely existing. The configuration example above enables no
persona files until those approvals are added.
The approval change was checked with Python 3.12: 27 tests ran, including the
temporary-profile real hakua writer; two symlink subcases were skipped for
missing Windows privilege. Astra xhigh found no actionable defect in static
review. The logs are under
`H:\Strata\evidence\p01-boundary-20261026\memory-persona-approval-python312.log`.
These checks do not qualify native model cache switching or summary quality.
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
approved `SOUL.md`, `USER.md`, `MEMORY.md` and `ebbinghaus.db`. Recall uses SQLite read-only immutable
mode and query-only enforcement, without constructing a hakua store. It omits
databases with WAL, shared-memory or rollback-journal sidecars. Recall is lexical
over at most 64 recent accessible, current, active records; at most four bounded
snippets enter the prompt. This is not full semantic retrieval or fresh WAL
visibility. Current text inputs and visible answers are limited to 16,384
characters for memory processing.

The Python server's Chat page offers separate read and save checkboxes. Both
start unchecked on every page load. After selecting one, enter the mapped
profile key under About > Settings. The page does not reuse its saved ordinary
API key or save the profile key. Memory chat has a separate, tab-only transcript
and does not replay a prior ordinary chat to another principal. Changing the
key clears that transcript, any unsent draft and any attachments. Leaving
memory chat clears them too. Each completed, failed or cancelled request
clears the checkboxes, so the next turn needs new consent. The page sends a
fresh turn ID through the same
`strata_memory` API path. Text attachments, pictures and MCP tool rounds are
unavailable in memory chat. The desktop app's Node Host chat is a separate
route; its unauthenticated local UI cannot provide a trustworthy per-user
identity for this harness. Its API gateway rejects `strata_memory` instead of
forwarding it with the Host's shared native engine key.

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
inspected and smoke-tested against hakua-memory commit `2908c6b9`; this work
does not install or change it. The library constructor may migrate the dedicated
profile database.

The released installer does not bundle hakua-memory by default. For an
operator-managed source installation, install a reviewed hakua-memory wheel
in the Python environment that runs `serve.server`; use the base package,
without embedding or RAG extras. The reviewed source revision was `2908c6b9`
(package version `0.3.5`); a new wheel needs its own source and writer-contract
review. To include it in a future installer, pin the reviewed version in
`requirements.txt`, regenerate and review all three
`packaging/locks/runtime-<target>-cp312.txt` files with
`packaging/lock_wheels.py`, then rebuild the Terminal and staged Control
components and verify `hakua_memory.ebbinghaus.store` imports under each
bundled interpreter. Keep the harness disabled in the shipped configuration.
Including the dependency alone does not enable memory in the Node Host chat.

The per-profile `strata-turns.db` ledger records an attempt before invoking the
writer. A normal retry with the same turn ID and content does not write again.
Reusing an ID for different content is refused. A crash after recording an
attempt can omit a memory: status is uncertain and the attempt is never replayed,
because hakua's duplicate-content handling can change reinforcement metadata.
This is at-most-once writer invocation, not exactly-once delivery. Persistence
errors and uncertain attempts are reported without private content in logs.
There is no HTTP persistence-status endpoint in this prototype.

Run synthetic checks with the installed Hakua base package and an existing
Python environment containing Jinja2. The Chrome tests require local Chrome
and Node; they create temporary profiles and do not launch a native model:

```powershell
py -3 -m unittest serve.test_memory_harness -v
node --test apps/host/tests/native-gateway.test.mjs
node --test serve/web/test_memory_chat.cjs
node --test serve/web/test_memory_python_server.cjs
```

On Windows Python 3.12, the 29 Python checks passed; two symlink subcases were
skipped because symlink creation lacks privilege. The Host gateway and browser
contract suites each passed two checks. The browser-to-Python suite passed one
check with the production Python HTTP handler, a scripted `MockEngine`, and the
installed Hakua writer: synthetic principal A stored one summary, while B's
read-only turn stored none. The browser mock uses thinking off to produce
visible text; it does not qualify a real model's summary quality. No real user
memory, native model, GPU, live server or public package was used. Real native
cache switching between principals, model summary privacy/quality and installer
inclusion remain unverified; keep the harness disabled for production traffic.
