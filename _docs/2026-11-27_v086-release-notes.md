# Hakua 0.8.6

This Windows update adds on-demand skill discovery to the agent. In **Settings → Tools**, turn on **Find skills on demand** to keep the automatic catalogue out of new and resumed agent requests. The agent can search for skills and load the complete instructions by name. In **Skills**, learning from completed work and automatic application still have separate switches. In on-demand mode, automatic application requires a name or trigger match within the applicable workspace. File operations and `/goal` have independent controls.

Workspace skills can bring their scripts, templates and references into the agent's skill directory. The copy is bounded and skips links. Hakua retains its transactional skill import and its separate approval settings. The desktop dependency lock updates the Windows runtime's `cookie` and `url` crates. The application continues to enforce upstream same-origin API access and sandboxed HTML preview. See the [Strata 0.2.22 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.22) for the upstream changes already integrated into the fork.

## SC117 rendering check

For an installed SC117 SQ-10, SQ-15 or SQ-20 profile, choose **Conversation context** on the Models screen before loading. The choice applies to the next load in the current desktop session. Strata keeps the model's prepared configuration, cache format and Expert placement. Changing the context of a running model requires unloading and loading it again.

On a Windows PC with an RTX 5060 Ti 16 GB, SC117 SQ-10 generated a single-file scene from the published Pagoda Bench prompt in a Strata `/goal` session. The model repaired JavaScript errors and adjusted the camera after receiving diagnostics. Chrome opened the saved file with the specified Three.js imports and drew the scene in WebGL 2. The scene reported 7,079 voxels and five floors. All five roofs were visible after zooming out. The opening view still cropped the top. This check used no hand edits to the generated HTML and produced no official benchmark score.

The Windows installer is distributed separately from CUDA model engines. See the [workflow guide](../docs/WORKFLOW_SKILLS.md) and the [previous hardware measurements](2026-11-27_v085-release-notes.md).

## Native Expert placement

The Windows build uses the Expert promotion interval and swap budget before it creates the per-size-class cache policies. This leaves the default values in place. The adaptive VRAM/RAM path and the SSD Expert scratch path are separate in this engine.

With the SSD scratch path active, a 256-token native benchmark at 16,384 context capacity decoded 32 tokens at 13.3 tokens/s on the installed build and 13.1 tokens/s on the rebuilt default. Neither run exercised adaptive promotion, so these observations provide no estimate of its effect. The tuning harness requires the engine to confirm that adaptive promotion is active before recording a result for that mode.
