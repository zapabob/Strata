# Hikari return from Swift — 2026-11-02

The user supplied the Swift engine error and then explicitly chose to return to Hikari-Bonsai 27B, repeating the request to start Hikari in Strata.

The Swift log reported exit code 2 because cache-type-k turbo4 / cache-type-v q8_0 were supplied without spin8-native-config. generate.cpp:3826-3828 confirms this argument check. This is distinct from the earlier disk-space/import-routing defect. Swift's saved configuration still contains those native-cache settings; the user selected Hikari recovery, so this task did not alter or qualify Swift.

Initial inspection found Hikari stopped and a native Swift app-1 instance marked ready with engine phase unloaded. Loading the existing Hikari reference through POST /api/models/local-e7d83e78598be18b75bf0498/load automatically unloads native instances. Subsequent observed Swift load jobs at 05:38:08 and 05:38:38 interrupted the first recovery verification. The user was informed to wait during the switch. A further normal stop returned server_stop_failed; by the next process/port inspection, no matching Swift server or listener on 18500 remained. No direct process kill was issued in this follow-up. Retrying the supported Hikari load API cleared the stale native instance and succeeded.

Final verification used Node fetch against the same /api/chat/stream route used by the chat screen, with no model override, no session/history, no tools and a short arithmetic prompt. It returned HTTP 200, 5,397 bytes of NDJSON, status/queued/start/reasoning/delta/done frames, answer 42, no errors, and done usage 3,395 input / 46 output tokens. An earlier PowerShell attempt did not capture stream frames and was not treated as a passing end-to-end check.

Final observed engine state: running=true, error=null, PID 36944, actual process context 65,536. The executable is C:\Users\downl\AppData\Local\Strata\components\generic-gguf\prism-b10826-c9c34bc\llama-server.exe. The model is the existing Hikari-LoRA-fixed-scale-PQ2_0.gguf under the user's C: Hikari directory, ID local-e7d83e78598be18b75bf0498. Its existing UI label is Hf · PQ2_0. GET /v1/models advertises only that local ID; native instances count is zero.

No source, dependency, model-file or Swift configuration edit was made in this follow-up. No new code tests were needed for the runtime switch. The model screen defaults to the native catalogue when native support is available, so displaying Swift there does not identify the active local model. The verified direct chat URL is http://127.0.0.1:47831/#/chat. Interactive UI clicking remains unverified because of the previously recorded computer-use bridge failure.

This is a short text-chat recovery check, not a long-context, agent-tool or performance qualification. The earlier installed import-routing fix and backups remain as recorded in 2026-11-02_hikari-import-routing-fix_Codex.md.
