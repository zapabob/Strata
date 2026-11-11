# Workflow skill learning — 2026-11-11

The user requested Hermes-style skill learning from completed workflows while
the 0.5.6 distribution task was finishing. That preview is now published and
fully read back; do not move its immutable tag or replace any of its 17 assets.
The new app candidate will be 0.5.7-local.1. Native 0.5.5, Control 0.5.6 and
RustXNG 0.31.1 Full remain separately pinned and unchanged.

## Requirements and design

Learn reusable procedures from actual agent tool completions. On explicit
opt-in, examine eligible completed tasks with at least three successful tools;
cancelled, failed and truncated turns must not produce a learned skill. The
same selected model makes one bounded, tool-free review request. A new user
request takes priority and interrupts this review. No model training, extra
provider connection or permission bypass is introduced.

Use private, editable SKILL.md files in this Strata profile and the existing
skill catalog/reload pipeline. Require nonempty specific trigger phrases and
tie each procedural step to an actually completed tool. Existing imported or
manually edited instructions must not be overwritten automatically. Improve
only owned learned skills using optimistic hash checks and retained revisions.
The Skills page must expose opt-in, status, last learned change and undo;
ordinary skill editing and enable/disable remain available.

Send bounded, redacted goal/tool metadata to the task's selected model, not raw
file contents, tool outputs, chat transcripts, private memories or credentials.
Validate candidate schema and dangerous instruction patterns before saving.
Keep default behavior off for other installations. Enable this PC explicitly
after verifying the new installed app, under the user's request. Preserve all
other tool/search/approval choices, including RustXNG Full.

## Sources and standards

Hermes official documentation:
https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/
and local owning implementation in
`C:/Users/downl/Documents/New project/hermes-agent/agent/background_review.py`,
`agent/prompt_builder.py` and `tools/skill_manager_tool.py`.
The design follows the procedural-document loop; no Hermes source code is copied.
Skills read: hermes-agent, hermes-agent-skill-authoring, skill-creator, alongside
the already applied PC/project AGENTS, canonical prompt, SOPs and engineering
skills recorded in the 0.5.6 implementation log. No subagents are authorized
or spawned. This work changes Strata; it does not edit Codex/Hermes global skills,
the user's global AGENTS, policy or unrelated memory settings.

## Validation and delivery plan

Exercise eligibility and cancellation, redaction, actual evidence binding,
malformed or hostile model output, duplicate/update/manual-edit conflicts,
revision undo and restart persistence. Verify host API local-origin controls,
same-model tool-free review, next-task skill discovery/reuse and existing
btw/deepresearch behavior. Run TypeScript and relevant existing skills/agent
tests. Build with five compiler jobs and unchanged resource floors. Verify
packaged payload/self-tests and isolated installed WebView2 flows. Take a fresh
private backup before the authorized normal stop/unload and standard NSIS
overwrite. Publish a new prerelease and tar.7z only after concrete checks,
retaining stable/latest and historical assets. Record actual results below.

The user then explicitly clarified automatic application inside execution
workflows. Add a separate opt-in for host-selected skill context: match enabled
trigger phrases and workspace scope before execution, send whole bounded skill
documents to the chosen model, display the actually applied skill names, and
preserve approval modes. Include normal agent tasks, research and goal/plan
steps. Refresh matched context on goal resume and keep implementation framing
out of displayed human goal titles. Both learning and application will be
enabled on this PC; other installations retain opt-in defaults.

The next explicit request requires `/btw` to use a real subagent. It now starts
a Harness spawn activation with caller-only delivery under a dedicated parent
session. No parent model request is made, and the main chat's context and queue
are untouched. The side preset omits workspace instruction files, skills and
memory. A scoped empty inherited-tool mask and denial guard enforce no tools;
the completed-message snapshot and selected model are used. Exact child disposal
precedes parent reuse. Helpers disabled in Settings is respected, and unavailable
delegation does not silently fall back to direct inference.

## Results before packaging

TypeScript and focused host checks passed: 65 passed, zero failed, five optional
Harness cases skipped in that smaller run (`focused-skills-final`). The separate
real Harness run covers these optional integration paths along with learning,
automatic application, scopes, goals/plans/research and child lifecycle.

The initial child test caught a globally inherited working-directory tool. The
first preset-level restriction failed to activate, so it was replaced by a
restriction installed on the exact created Agent scope, following the SDK's
own lifecycle. The subsequent isolated run passed both child/lifecycle and
disabled-helper cases. Failed attempts and all resource receipts remain on H:.
Existing goal/plan/resume/research and actual learning/reuse tests passed while
this issue was being fixed. No failing attempt was relabelled as successful.

Installed UI and public delivery are still pending; their actual results will
be appended after the candidate build and verification.

The final combined Harness workflow suite passed 14/14. After narrowing bridge
commands to the dedicated side Agent scope, the isolated child suite passed
2/2 again. This leaves the main Agent's command/tool presentation unchanged.
Six real NSIS cleanup scenarios passed. The expanded profile/context/guard suite
was 38 passed and four failed. All four failing titles and behaviors reproduced
on the preserved pre-feature d9207991 checkout: dense text compaction, pre-send
summary, explicit compact timing, and the search-heavy Plan refusal guard. These
remain existing limitations, separately recorded from new feature checks. No
full-suite success or broad quality certification is claimed.
