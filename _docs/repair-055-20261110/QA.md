# Repair acceptance notes

These are local acceptance notes, not changes to PC/project governance.
The original pass/fail receipts stay immutable; a corrected fixture gets a new
attempt label. No test is skipped or treated as passing because a rerun succeeds.

- Source-browser setup preserves the OS browser environment; only the Host gets
  the isolated app/profile locations. Browser data itself remains explicitly private.
- Match the actual route contract: workspace registration returns200, whereas
  real-file creation returns201. Check source instead of assuming REST status.
- Scope chat selectors to workspace groups. The task board deliberately shares
  the generic session-row class and must not count as a newly created chat.
- Wait for visible async operation completion before reading its disk result.
  A click alone is not proof that restoration or saving finished.
- Compare metadata persistence and the agent's working-folder scope after moving
  a chat. Removing a workspace must preserve files and make chats reappear when
  the same folder is registered again.
- Numerical parsing ignores comment headers describing possible failure words,
  but retains strict process exits, actual verdicts, route coverage and byte equality.
- Keep old/current raw timing rows, slower cases and coverage gaps. One old/new
  pair is not a general speedup claim. Pointer-table MMQ is absent in this build.
- Source diagnostics, current-driver repetitions, final source-bound binaries and
  actual installed acceptance are distinct. Never transfer one layer's pass to another.
- Packaged supervisor-agent acceptance must observe `start` with `agent=true`,
  a completed real response and no unavailable/skipped fallback. Plain chat alone
  missed the reported undefined.map branch. Preserve plain-chat checks too.
- Check generated recipe syntax and all read-only plans before runtime execution;
  imports must refer to the actual helper exports. Keep failed preparation receipts.
- Final numerical checks must bind the completed frozen-source build and compare
  tested library/executable hashes before and after; diagnostic success is insufficient.
- Read the browser MCP's actual tool schema (`target` in the staged0.0.80 build).
  Request a current explicit snapshot; action responses may link a saved snapshot.
  A page title or search-box echo is not search-result evidence: require actual
  result links/content. Record a provider challenge without bypassing it.
- Capture an actually observed QA runtime config while its child is alive. Normal
  teardown removes ephemeral JSON; activation must require the hash-bound capture
  and full test-start, not synthesize a previously tested configuration.

Self-review trigger: five local browser-fixture corrections/failed verification
gates. Evidence: sidebar red/green receipts and gpu-numerical-r1. Decision: narrow
QA notes and corrected fixtures; no weaker production/resource/security gate and
no automatic AGENTS/Skill/SOP change.
