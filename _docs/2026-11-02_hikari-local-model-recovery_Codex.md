# Hikari local-model recovery

## Request and acceptance

The user reported a disk-space error naming the local Hikari-Bonsai folder and confirmed that the intended model is the existing Hikari-Bonsai 27B. Acceptance: register that exact GGUF with PrismML, load it through the installed Strata app, and obtain a real response without downloading the unrelated native Qwen model.

## Diagnosis

Persisted native jobs and the setup log recorded family qwen, model Q2_0, and --gguf-dir pointing to the Hikari directory. The latest command already supplied --data-dir H:\Strata\models. Changing that setting alone would not correct the incompatible preparation path. The failed job requested approximately 35 GB at the C: GGUF source folder.

Disk inspection found approximately 30.14 GiB free on C: and 157.15 GiB on H:. The existing file C:\Users\downl\Desktop\SO8T\gguf_models\zapabobouj\Hikari-Bonsai-27B-Nimble-LoRA-GGUF\Hikari-LoRA-fixed-scale-PQ2_0.gguf is 7,206,168,928 bytes. Installed-host inspection reported architecture qwen35, quantization PQ2_0, 26.9B parameters, one shard, and a chat template. This was metadata inspection, not a fresh full-file hash verification.

## Changes and rollback

The installed host at http://127.0.0.1:47831 registered the existing file through POST /api/local-models as Hikari-Bonsai 27B Nimble LoRA, ID local-e7d83e78598be18b75bf0498. No weights were copied, moved, deleted, or downloaded by this recovery. The host settings were changed through PATCH /api/engine to PrismML and 32K context; inherited INT8 KV was retained. 32K is an operational starting configuration, not a context-capacity qualification.

Persistent changes: C:\Users\downl\.strata\data\local-models.json and state.json. Before editing, state.json was backed up as state.json.bak-hikari-20261102-050610. To reverse the settings, use the app to restore Automatic/recommended context, or restore the backup with the app stopped. Removing the local-model reference does not delete its weights.

Hermes already ran the same GGUF in its own PrismML server on port 8080, PID 41236, with 98,304 context tokens. Approximately 4.5 GiB of VRAM and 5.2 GiB of system RAM were free. The user explicitly approved stopping that inference server and switching to Strata. Its exact executable and GGUF command argument were rechecked before Stop-Process. Hermes itself was left running. Strata started its own PrismML process, PID 32584. Returning inference ownership to Hermes would require unloading Strata first and starting Hermes' local model again.

## Commands and verification

Inspection used Get-PSDrive, the local native-jobs.json/setup.log, Get-CimInstance Win32_Process, Get-NetTCPConnection, nvidia-smi, repository and installed source reads, and the installed host APIs. No private chat or credential contents were needed.

POST /api/local-models/inspect recognized the intended GGUF. POST /api/engine/validate returned ok=true with no issues. POST /api/local-models registered the existing path. PATCH /api/engine stored PrismML and 32K. No native preparation job was active immediately before POST /api/models/local-e7d83e78598be18b75bf0498/load.

Actual load passed: GET /api/engine/status reported running=true, status=running, error=null and PID 32584. GET /v1/models advertised the intended local model in real mode with context 32768. The library reported the intended model as loaded/current.

Actual inference passed: POST /v1/chat/completions through the Strata host, temperature 0, max_tokens 256, user prompt What is 17 + 25? Reply with only the result. Response content was exactly 42, finish_reason=stop. Reported usage was 3,395 prompt tokens and 39 completion tokens. Measured wall time was 4.99 seconds for this single smoke request; this is not a throughput benchmark or general quality result.

## Scope and controls

Applied PC-wide and project AGENTS, canonical pre-implementation prompt, common engineering/start-gate/skill-selection/application/LLMOps/security SOPs, debugging-and-error-recovery, milspec-codex-standard, codex-session-style-and-standards, and agent-self-review-evolution. Imported prompt identity/tool/environment claims do not override the actual runtime. No formal MILSPEC compliance is claimed.

Pre-existing GDN/CUDA experiments, desktop Cargo edits, and their evidence were preserved. No source code, dependency, release, or governance change was made. Code regression tests are not applicable to this runtime configuration change. Verification used the installed application and real model execution. The first apply_patch attempt to add this log failed without creating the file; the log was then created with a native PowerShell literal here-string.

## Limits and self-review

The UI action that allowed a Hikari folder to reach native Qwen preparation was not reproduced interactively; the mismatch is established by real job logs. Historical failed jobs remain as diagnostic history. Full-file integrity, long-context recall, general quality, throughput, and Hakua memory were not retested. Existing H: download remnants were not deleted. Other application files and processes were not stopped.

Self-review-event: type=ticket_completed scope=local-model-import category=correctness evidence=_docs/2026-11-02_hikari-local-model-recovery_Codex.md

Decision: review-only. Before interpreting preparation disk-space errors, verify that GGUF architecture and quantization match the selected execution path. No AGENTS, skill, or SOP edit is warranted for this individual recovery. The local model is registered, configured, loaded, and responds through Strata.
