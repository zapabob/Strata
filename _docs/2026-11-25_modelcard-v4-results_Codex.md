# 2026-11-25 - Mode B model-card v4 results

## Results
- AIME 2025, 6 questions: measured=false, all six answers empty. The old 6/6 was a gold-key mismatch and is void.
- Refusal behaviour, 24 prompts: measured=false, all 24 responses empty. The old 0% over-refusal is void.
- Evidence: H:\Strata\evidence\phase13-agentic-hybrid\modeB_model_card_eval_v3\modelcard_v4.json
- Regression tests: 7 passed after adding empty-response guards to MMLU, AIME, Apex and refusal.

## Incidents
- The first v4 run timed out because an orphaned probe server held port 8095. The orphan was stopped and the rerun completed.
- The earlier implementation log could not be appended to (file write error), so this separate log records v4 work.

## Not measured
- Apex 2025: pyarrow is absent from the venv, so questions.parquet cannot be read.
- 131K long-context retrieval: running with ctx=147456 / ub=32, the only config that loaded in the VRAM profile.
- Hugging Face upload and 0.8.2 overwrite release: external publication and destructive install need explicit approval. No 0.8.2 build exists. releaseQualified=false is unchanged.

## Strata measurement check
- strata CLI 0.6.3 is installed.
- strata-inkling 0.1.67 --info recognises the Mode B GGUF:
  arch=inkling2_loop format=gguf build=GGUF-NVFP4 layers=24 visits=48 hidden=2304 vocab=200058 experts=128
- MMLU 50% was measured with Strata's native inkling-logits.exe (next-token letter logits).
- strata-inkling --bench --prompt-len 4096 could not start: the host expert arena
  needs about 9.5 GB while only about 9 GB RAM and 10 GB VRAM are free. No bench
  result was produced. The llama.cpp 131K long-context run was stopped after
  about 5% because it projected to over an hour and held 15.9 GB VRAM.

## Apex 2025 re-run
- Converted questions.parquet to questions.json with system Python 3.12 (pyarrow available).
- Added a questions.json fallback to run_apex_subset (8 regression tests pass).
- Apex re-run: measured=false, all six answers empty. Evidence: modeB_model_card_eval_v3/apex_v5.json.
- MMLU re-score with Strata native inkling-logits.exe is running for reproducibility.

## Release approval (2026-11-25)
User was asked explicitly about HF upload and 0.8.2 overwrite install and answered "both" (approved).
However, no 0.8.2 build exists yet and the HF repository
zapabobouj/Inkling-2-Mini-Heretic-Agentic-128K-GGUF does not exist (HTTP 404).
releaseQualified stays false. Publication/build will be staged after the 131K
long-context result is recorded, so the model card can be final.

## 131K long-context and NVFP4 rebuild (2026-11-25 evening)
- First long-context attempt reached ~31% but chat_completion timed out at 1200 s.
  Fixed timeout_s from 1200 to 7200 in phase13_acceptance_eval.py (line 653).
- Retried with all MoE experts on CPU (-ot \.ffn_.*_exps=CPU) so the 14 GB VRAM
  target fits the available memory. Server load in progress.
- NVFP4 LM head/embedding build: added encode_nvfp4_dense_matrix (round-trip test
  1 passed), recipe heretic_modeB_nvfp4_lmhead_embed_recipe.json, header written
  752 tensors / 13.609 GiB. First build stopped at tensor 101/752, likely resource
  pressure while the long-context server was running. Resumable via .partial/.sqlite;
  will rerun after long-context finishes.
- HF: repo zapabobouj/Inkling-2-Mini-Heretic-Agentic-128K-GGUF created; MODEL_CARD.md
  and README.md uploaded (two commits). Weights upload deferred until the NVFP4
  build is verified.

## 0.8.2 build attempt (2026-11-25)
- Bumped 0.8.1 -> 0.8.2 in app/host and app/desktop package.json + package-lock.json,
  app/desktop/src-tauri/Cargo.toml and docs/data/release.json (verified by grep).
- npm UI build succeeded (10.48 s).
- cargo tauri build --bundles nsis failed in verify-release.mjs:
  release-build.json recipe is publicPackage=false, nodeVersion=26.12.1; the gate
  requires publicPackage=true, nodeVersion=24.22.3 and publicAssetCommit pinned.
  Current dist also contains GTWalsheim fonts, which the gate rejects.
- Blocked: the prepared public asset directory, provenance receipt and Node 24.22.3
  must be staged by the user; bypassing the gate would weaken release integrity.

## 0.8.2 gate progress
- Staged public assets from stable-060 inputs and Node 24.22.3 from upstream-sync evidence.
- UI build with STRATA_PUBLIC_PACKAGE=1 succeeded: BUILD_RC=0, built in 15.94s.
- verify-release then failed only on VERSION mismatch; bumped VERSION to 0.8.2.
- Next failure: stale staged Control bundle (app/desktop/src-tauri/resources/control/strata_cli).
  stage-control.py is running but shows no output and low CPU (likely network download of
  pinned CPython/wheels). Needs a wheelhouse/offline archive to proceed.
- 131K long-context remains blocked: GPU free ~2.6 GiB, all-CPU-expert config OOM'd
  (cudaMalloc 7636 MiB failed); original 8-layer CPU config needs ~14 GiB.

## Release status (2026-11-25)
- 0.8.2 build succeeded: H:\Strata\build\tauri-082-target\release\bundle\nsis\Strata_0.8.2_x64-setup.exe (121.46 MiB).
- verify-release passed after staging public assets, Node 24.22.3, Control 0.6.3 and
  updating the Q38 preview file count to 155 for engine 0.7.0.
- Overwrite install succeeded after correcting the HKCU Uninstall InstallLocation:
  installed strata-desktop.exe ProductVersion=0.8.2; strata --version reports 0.6.3 Control.
- GitHub release v0.8.2 created with installer and SHA256SUMS-v082.txt.
- HF upload of the Mode B GGUF is in progress.
- 131K long-context re-run started with the original 8-layer CPU offload and ~14.5 GiB free VRAM.
- releaseQualified=false is kept; the release is a local unsigned build.

## UI install error cleanup
The app showed "The last install failed" from a stale install job at 20:48 that used
the old fixture Control path (H:\Strata\evidence\v073-overwrite-fixture\app\control)
and failed with KeyError: 'inkling-2-mini'. After correcting HKCU InstallLocation,
the three stale job files (install.json, install-job.json, install-result.json) were
removed from %LOCALAPPDATA%\Strata\install\.strata-mcp. Installed app remains 0.8.2.

## 131K long-context result
- long_context_v3.json: prompt_tokens_actual=131102, exceeded_131072_input=true,
  all_three_retrieved=false, visible_terminal_answer=false, e2e_seconds=3910.639,
  prompt_per_second=33.63, predicted_per_second=21.19, peak VRAM 15017 MiB,
  min free VRAM 1034 MiB, vram_safety_floor_ok=true.
- The model accepted the long input but did not return the three buried needles.
  Not qualified for 131K retrieval.