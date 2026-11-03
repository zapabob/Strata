# unsigned q36 help rebuild 2026-11-04 05:15–05:22 JST

- Purpose: Hermes still held VRAM → mapped-live blocked; rebuild unsigned q36 with source help honesty instead of inventing speeds or killing Hermes.
- GPU: RTX 5060 Ti — used ~15178 MiB / free ~873 MiB / util mid-run ~33–99%. Hermes PIDs 22836 / 22944 not killed (DESIGN #6).
- Disk: H FreeGB ~77.31 (package/build); C FreeGB recovered to ~15.47 after earlier pressure (still prefer H: for TMP/npm-cache).
- Build: differential `cmake --build H:\Strata\releases\hakua040-native-sync-20261103 --config Release --target strata --target strata-q36 --parallel 2` → exit 0.
- Package: `H:\Strata\releases\hakua040-q36-engine-20261104-help\0.4.0-q36-windows-x86_64-cuda-cuda13` (manifest sha256 `687c44031b404fdaec82dbee7606a7899ca27fedbdae7e27e319154a08c0003a`); `signature` null; no picture reader.
- Installed **only** `%LOCALAPPDATA%\Strata\components\engine\0.4.0-q36-windows-x86_64-cuda-cuda13` (previous `6fe11065…` kept as `.bak-6fe11065`).
- Signed `0.4.0-windows-x86_64-cuda-cuda13\strata.exe` still `b5e4d5255a48882334b27ab643c22c9c1b54e4580f82b402176a9ca5661bf6f1` SIZE=108945408.
- New unsigned `strata.exe` SHA-256 **`64226fde7905821148c78b7de85ede4d291c4df8184d80866dccba014d7c02b7`** SIZE=114187776.
- Installed `--help` now prints `--q36-expert-store MODE …`.
- Staged `apps/desktop/.../engine-bundle/0.4.0-windows-…` refreshed for local native-build identity (gitignored binaries; not a new NSIS/GitHub release).
- Host allowlist + tests updated; older digests kept. Product `.5` installer **not** rebuilt this turn.
- mapped-live / T03 restart / T04–T08: still **BLOCKED / NOT_RUN**. No invented speeds. Goal complete = false.

## Planned live command (still wait for Hermes)

Same as NOTES-05-10, but digest is now `64226fde…` on the q36 component path.
