# GUI evidence notes 2026-11-04 JST

- DisplayVersion (Uninstall registry + FileVersion + /api/setup): 0.4.0-preview.20261103.5
- strata-desktop.exe pid 15168; host http://127.0.0.1:47831
- hakua-chatbot.enabled present; Hakua記憶 visible in sidebar
- Models page: Qwen3.6-35B-A3B / UD-Q4_K_XL selected
- UI refuse (red): Qwen3.6 has no tested prompt-cache isolation. Private cache flags were not removed to force a start.
- Same text as API job 538f2458-3f79-4a1c-9ab9-14d413d71ecb
- UI resource panel at capture: free VRAM ~0.6–0.7 GB, free RAM ~1.9–4 GB (Hermes llama-server holding VRAM; not killed)
- Chat/stop/restart NOT run (VRAM blocked; refuse path does not need full load)
- mapped-pack live NOT run (see ../evidence-2026-11-04-mapped-live/preflight-blocker.json)
- Remeasure 2026-11-04 04:09 JST: Hermes PIDs 22836/22944 still hold VRAM (729 MiB free); mapped-live still BLOCKED — see ../evidence-2026-11-04-mapped-live/NOTES-04-08.md
