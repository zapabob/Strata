# 0.3.0-preview.20261024.1 — unfinished native CLI preview

**TL;DR:** This fork provides an unfinished native CLI preview for AI engineers investigating quantisation and attention optimisation. The Windows x64 artefact contains the engine executable and required DLLs, tested on a Ryzen 5 4500 with an RTX 5060 Ti. It consumes pretokenised IDs and an existing native model pack; it is not a free-text chat application or HTTP server. Default/off Q2 generation produced READY and EOS in a bounded diagnostic. Experimental three-view generation, Bonsai, quality, long-context performance and GUI integration remain unqualified. Download the complete archive, read its limits, and keep experimental modes off.

## Download and start

Use the [fork release](https://github.com/zapabob/Strata/releases/tag/v0.3.0-preview.20261024.1),
asset `Strata-0.3.0-preview.20261024.1-windows-x64-sm120-engine.tar.7z`.
Extract the 7z to obtain a real tar, then extract that tar. Keep all DLLs beside `strata.exe`.
No installation, administrator rights, Node, Python or CUDA Toolkit is required to run the executable.
An NVIDIA driver and Windows system libraries are required. Driver **616.92** was tested;
an older minimum driver has not been qualified. This is not an automatic app update.

From the extracted folder in PowerShell:

```powershell
.\strata.exe --help
```

This help check only establishes startup. Actual inference additionally requires a compatible native
pack, its original GGUF shards and tokens produced with that pack's tokenizer. None is included.
Do not substitute Bonsai weights or a different tokenizer into this Qwen example.
The following relative layout reproduces the bounded off diagnostic after you provide the existing
Qwen3.8-Flash-Next GSQ-RCO Q2_0 pack and two matching shards under `models\q2_0`:

```powershell
.\strata.exe --pack .\models\q2_0\native-pack `
  --native .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf `
  --ple-gguf .\models\q2_0\Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf `
  --tokens-file .\examples\ready-tokens.txt --max-new 32 --max-context 256 `
  --mmap-experts --expert-cache auto --expert-profile .\data\expert-profile.bin `
  --prefill 32 --eos-ids 248044,248046 --spin8-mode off --check-logits --gpu 0 `
  --spec 2 --suffix-draft 0 --lookup-chain 0 --vram-reserve-mib 10240
```

`ready-tokens.txt` encodes the 30-token diagnostic asking for READY. This is a pretokenised engine
interface, not an interactive text prompt. Pack preparation/tokenisation still use the separate source
tools. The validation ran under the repository's RAM, commit, output and process guards; the command
above alone does not install those guards. On the tested 32 GiB PC, headroom was checked before
execution and no other model or compiler job ran concurrently. Reserve settings are not universal
recommendations for other machines.

## Evidence and limits

| Surface | Implemented | Verified | Failed or not run |
| --- | --- | --- | --- |
| Native Windows CUDA engine | Existing final build, native cache features opt-in | Off-mode Q2 short generation decoded READY, then EOS; exit 0, owned children reaped | Full quality, 4K/32K, peak-memory and performance qualification not run |
| Spin8 / codec libraries | CPU and CUDA contracts, versioned dialects | Earlier focused native bridge/session/config/owner/manifest tests: 5/5; source CPU CI is separate | CPU CI cannot establish CUDA inference correctness |
| Native F32 three-view path | Admission and prefill | 12-layer admission; 29-token actual prefill completed | Generation failed after auto-sizing selected zero expert slots with 9216 MiB reserve |
| Compressed native three-view path | Opt-in implementation and capsule checks | Lower-level tests and admission only | Actual compressed model generation not run; failed prerequisite stopped the sequence |
| Hikari/Bonsai, Prism/TheTom integration | Research/integration source exists | No end-to-end claim in this preview | These are not separately qualified executables or model variants |
| GUI, HTTP, persistence, GPU monitor | Upstream/source components exist | Not qualified by this archive | No GUI installer, HTTP server, reconnect/persistence or monitor acceptance included |

The extracted final archive (`dcb40730897432c4a68925be9b9ee0b8c6bda7108143e884ff43df00d493a9d8`,
408,044,259 bytes) passed `--help` and actual off-mode Q2 generation (`off-clean-reserve10240`) from a
space-containing path with `PATH` restricted to `C:\Windows\System32` (verified from the child PEB),
all six bundled CUDA/MSVC DLLs loaded from the extracted directory, `--expert-cache auto` and
`--vram-reserve-mib 10240` (1,030 expert-cache slots, 1.33 GiB VRAM), decoding `READY` and terminating
on EOS with exit code 0 and zero remaining owned processes. Earlier runs on the extracted bundle with
6144 MiB reserve passed when launched through `uv` (`off-final`, which injected Python PATH entries)
and stopped on the unchanged 2 GiB commit-memory guard (`off-clean-final`) when host commit headroom
tightened. Prior 4096 MiB-reserve and 9216 MiB-reserve runs are also preserved. A successful two-token
answer does not establish model quality or a speed improvement. Experimental opt-in modes require a
manually validated capsule and the source tooling. Machine-specific capsules are not distributed.

Tested platform: Windows 11 Pro 10.0.26300, AMD Ryzen 5 4500, 32 GiB physical RAM,
NVIDIA RTX 5060 Ti 16 GiB, driver 616.92. Build: CUDA 13.3, MSVC 14.44.35207,
CMake 4.4.0; `STRATA_PORTABLE=OFF`, dynamic MSVC runtime, sm120. This does not qualify
all Windows CPUs, a portable AVX2/static-runtime build, HIP, SYCL, Linux or macOS.
The embedded engine version remains 0.1.47; the preview number is distribution metadata.

## Integrity, source and licences

`preview-manifest.json` gives the frozen source (`c121dc8aa004a1eb8313b64ff73eaa512f5f0712`) and
archive-freeze (`ca0d8c169ce29571b4a3a81d7a55f13f946529ee`) commits, binary/DLL hashes, exact
file sizes, build-input digest and recursively inspected PE imports. It excludes itself.
The release's outer SHA-256 covers the final archive. SHA-256 detects corruption; it is not an
identity signature. The executable is unsigned. The archive is immutable after final verification.
An external `qualification.json` (`bf6c6de583f4e23aa1bedc343b07614647530a51e15ef7afe38de44cba480a1d`)
records the checks performed on the extracted final bytes.

Native source corresponds to commit `c121dc8aa004a1eb8313b64ff73eaa512f5f0712`.
The reused executable SHA-256 is `cb491ae5c0b6636cdb18eb3e1c1840fecda1cfc82d252fb95aae4e98181ee542`;
`strata_kq.dll` is `f3bba767420ee22cbf221b2bceea58f96b10e5713421ec0c58d8f1a730091713`.
The 2,061-entry private build-input record was rechecked. Checkout line-ending conversions are
recorded separately from four reviewed Python validation changes; native content matches the frozen
source. This is source-to-build evidence, not a claim of bit-identical reproducible compilation.

Strata and the embedded ggml code retain their MIT licences; the SHA-256 implementation retains
its source notice. CUDA/cuBLAS and Microsoft runtimes retain their own terms and are not relicensed
under Strata's MIT licence. The bundle carries unmodified vendor licence documents and notices.
Use/distribution of those components is subject to those terms; do not remove their notices,
modify the vendor binaries or redistribute them as a standalone offering.

The CUDA Toolkit EULA's Attachment A includes versioned cuBLAS/cuBLASLt redistributables.
Microsoft's [2022 distributable list](https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution)
and [Community licence](https://visualstudio.microsoft.com/license-terms/vs2022-ga-community/)
cover unmodified VC/Redist runtime files under the stated terms. The build PC has Community 2022
and Build Tools installed; this fork is publicly released under MIT. Actual runtime file version is
14.44.35211.0, despite the redist directory's older version label. No driver or System32 DLL is bundled.

## What remains before a full release

Native F32 and compressed generation must both pass before three-view model support is claimed.
Real-model numerical quality, repeated speed comparisons, long-context/resource measurements,
default/off equality against a same-day baseline, cross-backend builds, GUI/HTTP acceptance,
model routing, persistence/recovery, signing and portable CPU qualification remain open.
The [synthetic Linux CPU PoC](../research/triality-poc/README.md) supplies research context only.
