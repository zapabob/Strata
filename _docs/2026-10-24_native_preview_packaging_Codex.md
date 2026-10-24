# Native preview packaging — 24 October 2026

## Requirement and scope

P1 provides an unfinished Windows x64 sm120 native engine preview with required DLLs,
licences, source evidence and honest limits. Distribution numbering is independent of
the embedded engine version. It does not complete the 0.3.0 programme or Task4c1b.
The controller owns review, main integration, push, tag, Release and download verification.
No engine/default/math, GUI/updater, model, driver, pagefile or unrelated document changed.

The PC-wide canonical prompt, home/Codex/project AGENTS, CONTRIBUTING and security/packaging
docs were read. Applicable SOPs: Common Engineering, Implementation Start Gate, Skill
Selection, Security, DeepResearch, Application Development, LLMOps and Python. Skills:
milspec-codex-standard, build-manager, evidence-changelog-closeout,
deepresearch-defense-standard and agent-self-review-evolution. Context applies only where
compatible with the actual Windows environment and higher-priority instructions.

## Implementation

`packaging/native_preview.py` reuses the existing binary_deps PE reader and dependency rules.
It requires pinned input hashes, explicit public metadata, new destinations and enough disk
for five payload copies plus margin and a 10 GiB reserve. It parses every bundled PE strictly,
checks recursive imports and cuBLASLt, rejects bundled OS/driver DLLs, writes a relative
manifest, creates a real USTAR tar then single-threaded 7z, tests the archive and retains failed
stages. It performs no downloads, executable discovery through PATH or cleanup.
Private source paths are omitted from the public manifest. Payload integrity is not signing.

The README starts with a 93-word British-English scope statement. Release notes separate
implemented, verified, failed and unrun surfaces. The original owner-authorised Linux CPU
synthetic PoC figure and small seed/aggregate files are preserved with hashes; a standard-library
reproduction checks the numerical table and exploratory interval without training or new plots.
Single-six-bit outperformed the triality arms; the trained-query paired interval includes zero.

The readonly-contents CPU workflow covers Windows and Linux Spin8/codec contracts, PoC
numerical reproduction and packaging boundary tests. On Linux, the workflow supplies a
temporary pre-included header that redirects glibc's obsolete global `gamma(double)` symbol
during `<cmath>` inclusion so `spin8/src/spin8.cpp` compiles without modifying frozen native
compiler inputs. It has no publishing credentials or automatic release action.
CPU CI is not CUDA inference qualification.

## Source and dependency evidence

Native source content is frozen at c121dc8aa004a1eb8313b64ff73eaa512f5f0712.
The archive-freeze commit is ca0d8c169ce29571b4a3a81d7a55f13f946529ee.
The reused executable is cb491ae5c0b6636cdb18eb3e1c1840fecda1cfc82d252fb95aae4e98181ee542;
strata_kq.dll is f3bba767420ee22cbf221b2bceea58f96b10e5713421ec0c58d8f1a730091713.
No engine rebuild was performed. All 2,061 original build inputs were rechecked. Checkout
with core.autocrlf=true caused 45 text serialisation differences; compiled mismatches match
the frozen Git blobs exactly after CRLF normalisation. One noncompiled PowerShell guard's
historical mixed-line-ending bytes were reconstructed and matched its original SHA-256.
Four reviewed P0 Python validation files differ substantively; native code does not.
This records raw/frozen identities separately, not bit-identical reproducible compilation.

CUDA Toolkit 13.3 local EULA Attachment A lists versioned cuBLAS and cuBLASLt as distributable.
The actual cuBLAS PE recursively imports cuBLASLt. Their version resources both report
6,14,11,1360; this literal value is kept separately from the SDK version.
MSVC runtime files report 14.44.35211.0, although their directory says 14.44.35112.
The compiler is 14.44.35207. Community 2022 installation was confirmed with vswhere.
The official Community licence's individual/open-source permissions and distributable-code
section, together with the 2022 REDIST list, supply the redistribution basis. Unmodified
vendor licence documents and installed third-party notices accompany the runtime files.
No legal certification is claimed. Sources consulted on 24 October 2026:
https://learn.microsoft.com/en-us/visualstudio/releases/2022/redistribution
https://visualstudio.microsoft.com/license-terms/vs2022-ga-community/
https://visualstudio.microsoft.com/license-terms/vs2022-ga-diagnosticbuildtools/
https://visualstudio.microsoft.com/license-terms/vs2022-cruntime/

## Checks before and after archive freeze

Python commands used uv run --no-project --offline with existing Python 3.12; no dependency
installation or global environment repair. Packaging unittest: 12 passed. Black formatting
and flake8 (100-column limit) passed; the intentional test-loader import is annotated.
PoC numerical reproduction passed. Windows CPU Spin8: 6/6 tests passed in 9.05 seconds;
CPU tqcodec with dialects and Spin8 composition: 10/10 passed in 8.39 seconds.
Both were fresh builds, --config Release --parallel 1, CUDA OFF, followed by ctest
--output-on-failure --no-tests=error. No changed native engine was compiled.

The frozen archive `Strata-0.3.0-preview.20261024.1-windows-x64-sm120-engine.tar.7z`
(`dcb40730897432c4a68925be9b9ee0b8c6bda7108143e884ff43df00d493a9d8`, 408,044,259 bytes)
passed `7z t`, two-step extraction into `H:/Strata/build/preview-package-20261024/extracted space/Strata-native-preview`,
22-file payload hash/size verification, recursive PE import verification and clean-PATH
(`C:\Windows\System32`) `--help` (exit 0, contained before resume, 0 active processes after cleanup).

Actual extracted-bundle off-mode Q2 inference ran in three preserved stages:
1. `off-final` (6144 MiB reserve, launched via `uv`): decoded `READY` and EOS (`44061, 248046`),
   exit 0, all six bundled CUDA/MSVC DLLs loaded from the extracted directory, but PEB inspection
   showed `uv` injected Python directories into `PATH`.
2. `off-clean-final` (6144 MiB reserve, launched directly with `PATH=C:\Windows\System32`):
   PEB confirmed `PATH=C:\Windows\System32` and all six DLLs from the extracted directory, but
   available commit fell to 2,129,047,552 bytes at 143.125 s (`commit_memory_pressure`), stopping
   before generation completed (outer Job exit 125, `active_processes_after_cleanup=0`).
3. `off-clean-reserve10240` (10240 MiB reserve, `--expert-cache auto` selecting 1,030 slots /
   1.33 GiB VRAM, launched directly with `PATH=C:\Windows\System32`): PEB confirmed
   `PATH=C:\Windows\System32` (PID 8684), all six bundled CUDA/MSVC DLLs loaded from the extracted
   directory, 30-token prompt, context 256, spec 2, decoded `READY` and EOS (`44061, 248046`),
   child exit 0, `owned_child_reaped=true`, `contained_before_resume=true`,
   `active_processes_after_cleanup=0`.
`verify_qa.py` verified all receipts and wrote `H:/Strata/releases/0.3.0-preview.20261024.1/qualification.json`
(`bf6c6de583f4e23aa1bedc343b07614647530a51e15ef7afe38de44cba480a1d`) and `SHA256SUMS.txt`.

## Risk, containment and self-review

Output roots are fresh and exclusive, with serial heavy I/O and no model copies. The unchanged
guard accepts only task5a-* roots; the controller authorised a fresh task5a-preview-package
root for QA while packaging uses its assigned preview-package root. RAM/commit floors,
timeouts and owned-process cleanup remain unchanged. No 8080 service is started.

Known limits: native F32 prefill only, compressed generation unrun, no quality/speed/long-context
or GUI claim, unsigned nonportable build tested on one machine. Rollback is to stop using this
separate extracted preview; no installed app/update feed is modified. Evidence is retained.
Self-review trigger: release preparation, source-byte QA rejection, `uv` PATH injection in the
first QA run, and glibc `gamma(double)` collision in Linux CPU CI. Corrective scope stays in
the task's source-binding report, strict-PATH reserve-adjusted QA run, and workflow CMake flags;
no governance/skill or frozen native source changes are needed.
