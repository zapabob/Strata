# Learn and apply workflow skills

In version 0.5.7, open **Skills** to enable either of two independent
options. **Automatically apply skills to agent workflows** sends the complete
instructions of matching enabled skills to the selected task model. Matching
uses the skill's trigger phrases and workspace scope. It covers ordinary agent
tasks, research, and goal/plan steps, including resume. Applied names appear in
the task. At most five complete documents are included; oversized documents are
omitted with a notice. Your tool permissions and approval choices still apply.

**Learn from completed work** reviews an eligible completed agent task with at
least three successful tools. The same selected model receives one additional,
tool-free request. It may return no reusable procedure. Cancelled, failed,
truncated and Plan-mode work does not create a skill. A new task interrupts the
review. The limit is twenty reviews per UTC day and one hundred learned skills.
Both options are off by default in a new profile.

The review receives a bounded task objective and redacted tool metadata. It does
not receive raw file contents, tool outputs, full conversation history, memories
or saved provider keys. Paths and command arguments become placeholders; common
credential forms are removed. The objective was already part of the task sent
to that model. Avoid including secrets in task descriptions or skill documents.
Automatically applied documents are sent to the chosen model in full, so keep
their instructions appropriate for that connection.

Each learned step must cite a tool the host observed completing successfully.
The result is a private, editable `SKILL.md` under this profile's `data/skills`
directory. No model weights change. The feature does not modify Codex, Hermes,
bundled instructions or global policy files. A document is a reusable procedure,
not evidence that a future task succeeded.

The Skills page shows review status, the last learned change and revision. Use
the existing editor to inspect instructions and triggers, disable a skill, or
narrow its workspace. Automatic improvement applies only to unchanged skills
created by this feature. Imported skills, manual edits and disabled choices are
preserved. **Undo last learned change** restores the previous revision; undoing
a newly created skill disables it while retaining its document. Older revisions
remain in `data/skill-learning-history`. If storage fails or the model returns an
invalid procedure, the task remains completed and the review reports its limit.

This procedural-document approach is inspired by
[Hermes Agent](https://github.com/NousResearch/hermes-agent) and its
[official skills guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/).
We appreciate their work on reusable agent skills. No Hermes code is copied and
no upstream endorsement is implied.

# Side questions with a subagent

Type `/btw` followed by a question. The host starts a real Harness child agent
under a dedicated side-question parent. The parent makes no model request. The
child uses the selected model, a bounded snapshot of completed user/assistant
messages, and a preset with no tools. It does not receive workspace instruction
files, memories, auto-applied skills or an unfinished main reply.

The answer appears separately and does not enter the main agent's context or
queue. Its Stop button cancels and disposes only that child. Up to two side
questions can run across the app, with one per chat. A model with one request
slot may queue inference behind the main request. The app stores up to five
side answers per chat. Helper assistants must be enabled in Settings → Tools;
there is no silent fallback to direct inference if delegation is unavailable.

The 0.5.6 preview used a direct tool-free request. The real child delegation and
workflow learning described here are changes in 0.5.7. Automated checks use the
real Harness/tool executor and a scripted model; these checks establish the
integration path, not arbitrary model quality or GPU concurrency performance.
