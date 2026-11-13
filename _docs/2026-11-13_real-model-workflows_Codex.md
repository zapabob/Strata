# Strata 0.5.8 real-model workflow verification

Status: COMPLETE for bounded real-model workflow checks, with the initial resource failure and model accuracy limitations recorded below. No production code, dependencies, release assets or CI changed. This is not new release qualification.

## Scope and environment

The request was to start installed Strata and exercise /btw, /deepresearch, workflow skill learning and automatic application using an actual local model. No scripted language-model responses or manually authored learned skill substituted for these observations.

Primary checkout: C:/Users/downl/Documents/ChatGPT/Strata, main at a9c84cb82199dfa66978712ffc10feb376231766.
Private evidence root: H:/Strata/validation/real-workflows-058-20261113-codex.

The installed application started normally. Its host and shell both reported 0.5.8. The native shell was PID 37480, the host PID 9360 and its listener 127.0.0.1:47831. UI checks used the same installed host and profile.

Apply the PC-wide MILSPEC baseline and relevant Implementation Start Gate, Security, Application Development, LLMOps, Python and TypeScript SOPs. Applied skills were milspec-codex-standard, browser-testing-with-devtools, computer-use and deepresearch-defense-standard. Existing user conversations, credentials and unrelated files were not exported.

## Authorised Hermes preparation

The initial GPU owner was Hermes llama-server PID 12308 under .hermes/llama/prism-b10826-c9c34bc/bin, listening on loopback 8080. It held approximately 11 GiB GPU memory. The user approved normal stop and unload. The UI displayed Operation interrupted; a normal console interrupt was then sent after executable, creation time and exclusive console membership were verified. The listener closed but the process remained after 45 seconds. hermes-normal-stop.json retains this incomplete normal-stop attempt.

The user subsequently explicitly approved force termination of this exact PID. At execution the process was already absent. hermes-approved-stop-final.json records alreadyAbsent=true and forceKillUsed=false. No process was force killed, and Hermes was not restarted.

## Actual local model

The existing Qwen3.5 9B Q4_K_M GGUF was loaded through installed PrismML 0.4.1, build 1965755c, bundled with the signed engine 0.5.8. The display label is DeepSeek V4 Pro Qwen3.5 9B UNCENSORED Heretic; the actual GGUF model family is Qwen3.5 9B.

The file is H:/Strata/models/新しいフォルダー/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic.i1-Q4_K_M.gguf, 5629111584 bytes, metadata SHA-256 8c2ba1af53823a0dc9403caa8398a75273113f5f7e8d1c00a9b2d4a8720b8392. Variant ID: local-cbca9a0eca0f30752f82f2ce.

The final test runtime was PID 38808, actual context 65536, all GPU layers, batch 256 and no mmap. Captured agent messages have demo=false and remoteModel=false. The saved 256K preference and larger route metadata do not establish actual 256K inference. This is bounded task evidence, not general model quality, full-window generation or GPU concurrency qualification.

## /btw

PASS. Conversation qa-real-workflows-058-20261113 returned 15+27=42 in aside aside_x5of9an4wqws from separate agent d2d9686e-8550-4154-a053-a238df626abb. The UI identified a tool-free subagent answer. The main conversation still had two messages at aside completion. An initial main question also returned 6 times 7 as 42.

## Workflow self-learning

PASS. In qa-real-learning-058-20261113, the model read three fixture CSVs, wrote audit.json and read it back: five successful actual tools. The output correctly identified beta at 0.5.7 versus expected 0.5.8, with zero duplicates, missing IDs or failed checks.

The model's subsequent review saved revision 1 of Inventory Discrepancy Verification with the five observed procedure steps, path placeholders and reuse limits. The app generated this document from the completed workflow; it was not manually written for the test.

## Automatic application and accuracy

PASS for matching, execution and UI persistence. A new conversation qa-real-auto-058-20261113 used different delta/epsilon/zeta fixtures and trigger phrases, without naming or manually selecting a skill. It executed six successful actual tools. The UI displayed one used skill and the badge persisted after a full reload once the answer finished loading.

The first output correctly identified epsilon at 0.5.6 versus 0.5.8 but also counted three passed checks as needing additional verification. This is a semantic accuracy failure. The original followup/audit.json is retained.

A clarification explicitly defined passed as success and required no further execution evidence. The original output was preserved. Five further successful actual tools created and reread followup/audit-clarified.json. Its counts and the final answer agree: one version mismatch, epsilon; zero duplicates, missing IDs and failed checks. The UI displayed two automatically used skills for this turn. This verifies reuse with explicit criteria without erasing the first model error.

The learned count increased from three to six. Three new revision-1 documents were produced: my-learned-inventory-audit-verification, my-learned-inventory-discrepancy-audit and my-learned-inventory-discrepancy-audit-clarified. The last document includes the clarified passed-status criterion. Bodies and hashes are retained privately. All three are restricted by onlyIn to verification workspace ws_1bzvhz. The original seven skill objects, including bodies and preferences, compare unchanged. Learning and automatic application remain enabled as before testing.

## /deepresearch

PASS for actual retrieval and final sourced chat response, with manual intervention and coverage limits. RustXNG 0.31.1 Full performed three distinct queries in one actual web_search call. Four web_fetch calls completed with HTTP 200 for official Rust pages:

https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html
https://doc.rust-lang.org/std/marker/trait.Copy.html
https://doc.rust-lang.org/std/clone/trait.Clone.html
https://doc.rust-lang.org/book/ch15-04-rc.html

The final UI response displayed Summary, Key findings and Sources with four URLs. The model proposed an unnecessary local summary file twice despite the research-only instruction. Both writes were denied through the manual approval UI; both results record Denied. Nothing ran. The proposed file is absent. A subsequent save-file question was answered No, just show me the result.

The final response concentrated on Copy, Clone and Rc rather than fully covering ownership and borrowing. This is not an unattended research-quality pass. Its optional learning review was skipped as review-incomplete. Successful learning is established by the three CSV workflows instead. No cloud model was used; the public search queries and page retrievals were actual network operations.

## Resource findings and verification defects

The first mmap runtime used context 32768 and completed the initial main/aside questions and first learning task. Available RAM then fell to approximately 2.33 GiB, below the unchanged 3 GiB hard floor. The model was normally unloaded immediately upon observation. The load-only guard had not covered the entire subsequent UI workflow. This initial attempt is a resource failure; zero violations across all attempts is not claimed.

The second run used no mmap, batch 256 and actual context 65536. A continuous watcher covered the remaining workflows with a 4 GiB soft normal-stop threshold ahead of the unchanged 3 GiB hard floor. Its 5344 samples had minimum RAM 9100398592 bytes. The outer guard independently recorded minimum available RAM 9098055680 bytes, about 8.47 GiB; minimum commit headroom was 20031275008 bytes and H free 97212821504 bytes. It exited successfully with no remaining owned job process. The soft stop did not trigger. RAM, commit and disk floors were not lowered.

A separate QA setup defect was corrected: importing a session's workspace property did not bind the actual chat folder. A preliminary trial had three failed CSV reads in the default folder and is not counted as successful. Correct conversations used the production /api/chat/folder endpoint before execution. Unrelated default-folder filenames or contents were not exported in the verification receipt.

These are verification workflow defects. No global SOP, policy, Codex skill or production test was rewritten to hide them.

## Cleanup and evidence

All verification turns and learning reviews are idle. The verification model was normally unloaded. Strata remains open without a loaded engine. Original beginner settings, 256K context preference, unlimited output-token preference, automatic GPU layers, mmap enabled and batch 2048 were restored and read back. The tools-view SHA-256 matches the pre-test value, preserving search/provider/tool settings and approval choices. The watcher was explicitly ended and its containment receipt passed.

REAL_MODEL_VERIFICATION.json records message, request and tool identities; actual-model flags; aside identity; learned skill hashes; retrieval results; output counts and limitations. CLEANUP_VERIFICATION.json records readback, idle state and unchanged original skills/tools. resource-watch-r2-final.json, resource-watch-r2.jsonl and receipts/resource-watch-r2.json retain resource evidence. Original and clarified outputs remain in workspace; generated skill documents are also copied under proofs.

The installed release was not changed. No release tag, upload or hosted-CI claim was added by this verification. General model quality, autonomous instruction following, full-window generation, GPU concurrency and releaseQualified remain outside these results. The initial resource breach and first audit's inaccurate count remain explicit.
