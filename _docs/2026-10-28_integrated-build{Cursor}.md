# 2026-10-28 integrated-build{Cursor}

実施：2026-10-27 23:53 → 2026-10-28 00:12 JST。作業先 `H:/Strata/worktrees/hakua-chatbot-20261027`（HEAD `80c0142f` 付近、branch `codex/strata-hakua-chatbot-20261027`）。
GPU: NVIDIA GeForce RTX 5060 Ti 16GB (driver 616.92)。CUDA toolkit: **13.3.73**。ggml pin: `H:/Strata/deps/ggml-3cf03257`（valid）。
実装AI: Cursor。なんJ風に言うと「単発ターゲットじゃなくて統合で殴れ」案件。署名キー無しでも unsigned まで通せ、という裁定で走った。

## CoT 仮説検証

| ID | 仮説 | 結果 |
|----|------|------|
| H1 | `packaging/README.md` の Windows 出荷物は NSIS（`cargo tauri build --bundles nsis`）。`full_windows.py` は別系統の pin 済み ZIP 組立器 | **採用** |
| H2 | 既存 `build-cuda-sm120-verify` は Release+CUDA+sm_120+ggml pin 済みで再利用可 | **採用**（CONFIG/BUILD ともに 0） |
| H3 | host は `npm run build` が本番バンドルの正典（full `npm test` は前回 hang 実績あり、今回は build+focused） | **採用** |
| H4 | 署名キー無しでも `createUpdaterArtifacts:false` で unsigned NSIS は通る | **採用** |
| H5 | 今夜のツリーに production `--spec` が無いので `full_windows.py build` は新規 ZIP 不可 → SKIP 文書化 | **採用** |
| H6 | 他エージェントの README 作業を踏まない | **採用**（README 未変更、stash 不要） |

## Canonical path（調査）

- `packaging/README.md` Desktop app: `fetch-node` → `npm --prefix ../host run build` → `cargo tauri build --bundles nsis`
- `docs/AI_SETUP.md` / `docs/SOURCE_INSTALL.md`: 利用者は installer / `strata launch`。ソース CUDA は `cmake … -DSTRATA_ENABLE_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=…`
- `packaging/full_windows.py`: `--spec` + `--stage` + `--archive` の ZIP 組立（WebView2 / Control / Harness / engine / generic-gguf の pin 必須）
- 既存 draft ZIP: `H:\Strata\releases\0.3.2-preview.20261027.1\full-package\`（今夜は再組立せず）

## Stage results

### 1) Inspect docs / scripts — PASS

Commands: read `packaging/README.md`, `docs/AI_SETUP.md`, `docs/SOURCE_INSTALL.md`, `packaging/full_windows.py`, `_docs/cmake-cuda-all.cmd`。exit n/a。

### 2) Engine CUDA sm_120 — PASS

```text
cmd /c _docs\cmake-cuda-all.cmd
# = cmake -G Ninja -B build-cuda-sm120-verify -DCMAKE_BUILD_TYPE=Release
#   -DSTRATA_ENABLE_CUDA=ON -DSTRATA_BUILD_TESTS=OFF -DSTRATA_PORTABLE=ON
#   -DCMAKE_CUDA_ARCHITECTURES=120 -DSTRATA_GGML_DIR=H:/Strata/deps/ggml-3cf03257
#   + cmake --build … --target strata -j 8
```

| Check | Result |
|-------|--------|
| CONFIG_EXIT | **0** |
| BUILD_EXIT / ENGINE_EXIT | **0** |
| duration | **280.8 s** |
| version | `strata 0.1.51` |
| artifact | `build-cuda-sm120-verify/strata.exe` (**79,448,064** bytes) |
| log | `_docs/integrated-build-engine-20261027.log` |
| notes | MSVC/CUDA C4819 warnings only; reused existing build dir (not `build-integrated-20261027`) |

### 3) apps/host production build — PASS

```powershell
Set-Location apps\host; npm run build
```

| Check | Result |
|-------|--------|
| HOST_BUILD_EXIT | **0** |
| duration | **9.7 s** |
| artifact | `apps/host/dist/index.html` + vite assets (`index-ag1gEBlv.js` etc.) |
| log | `_docs/integrated-build-host-20261027.log` |
| optional focused test | `node --test tests/no-acquire.test.mjs` → **5/5 PASS**, EXIT **0**, ~12 s |

（full `npm test` は前回 hang+1fail 実績あり → 今回は build 必須 + focused のみ）

### 4a) Engine component package — PASS (text-only)

```powershell
py -3 packaging\package_engine.py --src build-cuda-sm120-verify --backend cuda --version 0.1.51 `
  --out dist-integrated-20261027\components\engine --arch sm_120 --variant cuda13 --platform windows-x86_64
```

| Check | Result |
|-------|--------|
| PACKAGE_ENGINE_EXIT | **0** |
| duration | **8.9 s** |
| artifact | `dist-integrated-20261027/components/engine/0.1.51-windows-x86_64-cuda-cuda13/` (**~569 MiB**, 5 files) |
| contents | `strata.exe`, `strata_kq.dll`, `cublas64_13.dll`, `cublasLt64_13.dll`, `engine-component.json` |
| note | no `strata-vision` → text-only（app は picture reader 無しと表示）。cublas は CUDA **v13.2** bin から同梱（toolkit 13.3 環境でも import 解決で 13.2 パス） |
| log | `_docs/integrated-build-package-engine-20261027.log` |

### 4b) Desktop NSIS installer — PASS (unsigned)

Blockers hit then cleared:

1. `cargo` not on PATH → prepend `$env:USERPROFILE\.cargo\bin`
2. `RUSTC_WRAPPER=sccache` but sccache missing → clear wrapper（repo `.cargo/config.toml` は空 wrapper 指定）

```powershell
$env:Path = "$env:USERPROFILE\.cargo\bin;" + $env:Path
Remove-Item Env:RUSTC_WRAPPER -ErrorAction SilentlyContinue; $env:RUSTC_WRAPPER = ''
Set-Location apps\desktop
npx --yes tauri build --bundles nsis
```

| Check | Result |
|-------|--------|
| NSIS_EXIT | **0** |
| duration | **626.4 s** (~10.4 min) |
| app version | `0.3.2-preview.20261027.2` |
| desktop exe | `apps/desktop/src-tauri/target/release/strata-desktop.exe` (**9,566,208** bytes) |
| installer | `apps/desktop/src-tauri/target/release/bundle/nsis/Strata_0.3.2-preview.20261027.2_x64-setup.exe` (**176,610,345** bytes / ~168.4 MiB) |
| SHA-256 | `839029112EF655466BDC04E92E5A97325B3BA03E05B5F92F4DCB96D015E4A0DF` |
| signing | **unsigned**（`createUpdaterArtifacts: false` — 仕様どおり build box OK） |
| sidecar | `fetch-node.ps1 --check` EXIT 0 → Node v24.12.0 |
| log | `_docs/integrated-build-nsis-20261027.log` |

### 5) packaging/full_windows.py fresh ZIP — SKIP

| Check | Result |
|-------|--------|
| status | **SKIP** |
| reason | ツリー内に production `--spec` pin JSON 無し。`full_windows.py` は WebView2 offline payload + Control + Harness + engine + generic-gguf の source pin が必要。今夜の shippable は README 正典の **NSIS** |
| prior draft (not rebuilt) | `H:\Strata\releases\0.3.2-preview.20261027.1\full-package\Strata-full-windows-draft.zip` |
| probe log | `_docs/integrated-build-full-windows-20261027.log` |

Signing keys / feed: 未配置 → signed release は本タスク範囲外（build-focused）。UpdateGoal complete にはしない。

## Hardware / disk notes

| Item | Value |
|------|-------|
| GPU VRAM during wrap-up | used ~1327 MiB / total 16311 MiB（engine link 時も余裕） |
| H: free | ~187.8 GB（開始時計測） |
| C: free | ~55.6 GB |
| force-push | **not done** |
| README stash | **not needed**（README 未 dirty） |

## Overall

**INTEGRATED BUILD: SUCCESS**（engine + host prod bundle + engine component + unsigned NSIS）。

Not done / out of scope: signed feed、Tauri updater `.sig`、`full_windows.py` 新規 ZIP、フル `npm test`、install→実推論までの release+install Goal。

## Artifact index

1. `build-cuda-sm120-verify/strata.exe` — engine 0.1.51 sm_120
2. `apps/host/dist/` — host production UI
3. `dist-integrated-20261027/components/engine/0.1.51-windows-x86_64-cuda-cuda13/` — local engine component
4. `apps/desktop/src-tauri/target/release/bundle/nsis/Strata_0.3.2-preview.20261027.2_x64-setup.exe` — installable NSIS
