"""Resolve the reviewed 0.2.13 merge through Git's index, with a dry default.

Only the pinned parent pair and explicit per-hunk choices are accepted. Git
objects preserve the conflicted inputs as well as both original parents. This
does not commit, publish, touch model data, or change frozen build evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OURS = "1f6661441bf7c09791abd6806a0e551477110b48"
THEIRS = "f33c8c30588ff00e24b6b63bad0bf6a14da19081"
CONFLICT = re.compile(r"^<<<<<<< HEAD\n(.*?)^=======\n(.*?)^>>>>>>> " + THEIRS + r"\n?", re.M | re.S)


def git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, input=data, check=True,
                          capture_output=True).stdout


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"Expected one anchor: {old[:120]!r}; got {text.count(old)}")
    return text.replace(old, new, 1)


def between(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Nonunique extraction: {start!r} / {end!r}")
    return text[text.index(start):text.index(end)]


def resolve(text: str, choices: list[str]) -> tuple[str, list[tuple[str, str]]]:
    matches = list(CONFLICT.finditer(text))
    if len(matches) != len(choices):
        raise ValueError(f"Expected {len(choices)} conflicts, found {len(matches)}")
    blocks = [(m[1], m[2]) for m in matches]
    iterator = iter(choices)
    def choose(match: re.Match[str]) -> str:
        choice = next(iterator)
        return match[1] if choice == "ours" else match[2] if choice == "theirs" else match[1] + match[2]
    return CONFLICT.sub(choose, text), blocks


def proposal() -> tuple[dict[str, str], dict[str, str]]:
    if git("rev-parse", "HEAD").decode().strip() != OURS:
        raise ValueError("Unexpected HEAD")
    if git("rev-parse", "MERGE_HEAD").decode().strip() != THEIRS:
        raise ValueError("Unexpected merge parent")
    names = git("diff", "--name-only", "--diff-filter=U", "-z").decode().strip("\0").split("\0")
    changes: dict[str, str] = {}
    reasons: dict[str, str] = {}
    simple = {
        ".gitattributes": ["both"],
        "apps/desktop/package.json": ["ours"],
        "apps/desktop/src-tauri/Cargo.lock": ["ours"],
        "apps/desktop/src-tauri/Cargo.toml": ["ours"],
        "apps/host/package.json": ["ours"],
        "apps/host/package-lock.json": ["ours", "ours"],
        "strata_cli/__init__.py": ["ours"],
        "strata_cli/bench_standard.py": ["ours"],
        "apps/host/tests/component-updates.test.mjs": ["ours"],
        "apps/host/tests/markdown-crlf.test.mjs": ["ours", "ours", "ours"],
        "apps/host/tests/qa1-storage.test.mjs": ["ours"],
        "tests/terminal/test_monitor_bundle.py": ["theirs"],
        "tests/terminal/test_private_files.py": ["ours"],
        "tests/terminal/test_tui2_023_old_launcher.py": ["ours"],
        "tests/terminal/test_tui2_023_versions.py": ["ours", "ours"],
        "tools/test_check_cuda_spills.py": ["both"],
        "tools/test_setup_unsloth.py": ["both"],
        "apps/host/server/native-settings.mjs": ["both"],
    }
    for name in names:
        text = (ROOT / name).read_text(encoding="utf-8")
        if name in simple:
            text, _ = resolve(text, simple[name])
            reason = "Retain fork versions/isolated fixtures; combine upstream imports and drafting hint where applicable."
        elif name.startswith("README") and name.endswith(".md"):
            # Fork README is a distribution guide, not the official engine's
            # hardware/performance page. Retain that distinction and supporters.
            text = git("show", f"{OURS}:{name}").decode()
            official = git("show", f"{THEIRS}:{name}").decode()
            marker = "<!-- supporters:start"
            if marker in text and marker in official:
                start = text.index(marker)
                finish = text.index("<!-- supporters:end", start)
                finish = text.index("-->", finish) + 3
                a = official.index(marker)
                b = official.index("<!-- supporters:end", a)
                b = official.index("-->", b) + 3
                text = text[:start] + official[a:b] + text[finish:]
            reason = "Preserve fork installer/qualification documentation and refresh upstream supporters."
        elif name == "AGENTS.md":
            text, _ = resolve(text, ["ours"])
            text = once(text, "upstream Niko1221 0.2.12 at 146df3c468739147f520ac3816de806f71232571 (upstream engine 0.1.58, taken as source;", "upstream Niko1221 0.2.13 at " + THEIRS + " (upstream engine 0.1.59, taken as source;")
            reason = "Retain local controls, independent versions and new official source identity."
        elif name == "docs/INSTALL.md":
            text, _ = resolve(text, ["ours"])
            text = text.replace("updating Strata (version 0.2.8)", "updating Strata (version 0.2.13)")
            reason = "Keep fork installation boundary and update official reference version."
        elif name == "packaging/README.md":
            text, _ = resolve(text, ["ours"])
            reason = "Keep published fork packaging facts; official recipe changes outside hunk survive."
        elif name == "CMakeLists.txt":
            text, blocks = resolve(text, ["theirs"] * 4)
            text = once(text, "project(strata VERSION 0.1.59 LANGUAGES CXX)", "project(strata VERSION 0.5.3 LANGUAGES CXX)")
            # Official extracted these blocks into backend macros. Reattach
            # fork additions there, not as duplicate targets in the root file.
            old = git("show", f"{OURS}:CMakeLists.txt").decode()
            engine_path = "cmake/strata_gpu_engine.cmake"
            engine = (ROOT / engine_path).read_text(encoding="utf-8")
            spin = between(old, '  option(STRATA_ENABLE_SPIN8 ', '  if(STRATA_BUILD_TESTS AND STRATA_ENABLE_CUDA AND NOT STRATA_HIP_GFX906)\n    add_executable(host_graph_launch_test')
            anchor = "  target_link_libraries(strata_engine PUBLIC strata_core strata_kernels strata_kernels_cpu ${_strata_gpu_runtime_target})\n"
            engine = once(engine, anchor, anchor + spin)
            engine = once(engine, "add_library(strata_qwen35 STATIC src/qwen35/q36_engine.cu)", "add_library(strata_qwen35 STATIC src/qwen35/q36_engine.cu src/qwen35/expert_store.cpp)")
            anchor = "  target_link_libraries(strata_qwen35 PRIVATE strata_prefill strata_kernels strata_warnings ${_strata_gpu_runtime_target})\n"
            engine = once(engine, anchor, anchor + "  if(WIN32)\n    target_link_libraries(strata_qwen35 PRIVATE bcrypt crypt32)\n  endif()\n")
            qtests = between(old, "  if(STRATA_BUILD_TESTS AND STRATA_ENABLE_CUDA AND NOT STRATA_HIP_GFX906)\n    add_test(NAME q36_version", "  strata_utf8_manifest(strata-q36)")
            engine = once(engine, "  strata_utf8_manifest(strata-q36)\n", qtests + "  strata_utf8_manifest(strata-q36)\n")
            anchor = '  set(STRATA_PLE_FIXTURE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/bench/micro" CACHE PATH\n'
            engine = once(engine, anchor, '  set(STRATA_PLE_PACK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/pack/full" CACHE PATH "Legacy PLE diagnostic dense pack")\n' + anchor)
            engine = once(engine, "add_test(NAME ple_parity COMMAND ple_parity --selftest\n", 'add_test(NAME ple_parity COMMAND ple_parity --selftest --pack "${STRATA_PLE_PACK_DIR}"\n')
            changes[engine_path] = engine
            reasons[engine_path] = "Port Spin8/native-cache, mapped Q36 sources/libraries/tests and PLE fixture settings to official GPU macro."
            cpu_path = "cmake/backends/cpu.cmake"
            cpu = (ROOT / cpu_path).read_text(encoding="utf-8")
            anchor = "    set_tests_properties(pool_tasks_test PROPERTIES TIMEOUT 180)\n"
            addition = between(old, "    add_executable(q36_bounded_cpu_parity_test", "    add_test(NAME router_dot_parity COMMAND router_dot_parity)")
            changes[cpu_path] = once(cpu, anchor, anchor + addition)
            reasons[cpu_path] = "Retain bounded CPU arithmetic parity test at official target registration point."
            cuda_path = "cmake/backends/cuda.cmake"
            cuda = (ROOT / cuda_path).read_text(encoding="utf-8")
            # Retain source/compiler binding and default guard (no new allowance).
            original_guard = between(old, "if(STRATA_ENABLE_CUDA AND STRATA_BUILD_TESTS AND NOT STRATA_ENABLE_HIP AND NOT STRATA_HIP_GFX906)\n  find_package(Python3", "\nif(STRATA_BUILD_TESTS)\n  enable_testing()")
            position = cuda.index("macro(strata_cuda_spill_guard)\n")
            changes[cuda_path] = cuda[:position] + "macro(strata_cuda_spill_guard)\n" + original_guard + "endmacro()\n"
            reasons[cuda_path] = "Preserve original spill policy and opt-in source/compiler-bound baseline in official macro."
            reason = "Use official modular CMake and model geometry; preserve independent native version and relocated fork targets."
        elif name == "metal/CMakeLists.txt":
            text, _ = resolve(text, ["theirs"])
            text = once(text, 'STRATA_VERSION="0.1.59-metal"', 'STRATA_VERSION="0.5.0-metal"')
            reason = "Use official resolved ggml root; keep independent Metal source version."
        elif name == "apps/host/server/index.mjs":
            text, _ = resolve(text, ["ours"])
            text = once(text, "json(res,200,{...settings,tuned});", "json(res,200,{...settings,tuned,hints:await native.settingsHints?.(nativeSettings[1])});")
            reason = "Combine official model-specific drafting hints with negotiated KV settings and checked save."
        elif name == "apps/host/server/native-control.mjs":
            text, blocks = resolve(text, ["ours", "ours", "ours"])
            hint = next(line for line in blocks[0][1].splitlines(keepends=True) if line.startswith(" async function settingsHints("))
            text = once(text, " function previousEngine()", hint + " function previousEngine()")
            auto = blocks[1][1][:blocks[1][1].index("  const {cfg,resources")]
            anchor = "  const {cfg,resources,visionPreferences,parallelChoice,parallelNote:chosenNote,dsNote,q36Note}=buildConfig"
            text = once(text, anchor, auto + anchor)
            text = once(text, "return {state:publicState,runObservations,", "return {state:publicState,settingsHints,runObservations,")
            reason = "Add official drafting hints/acquisition while keeping async tuning, authenticated memory, cancellation and Q36/projection admission."
        elif name == "apps/host/src/app/App.tsx":
            text, _ = resolve(text, ["ours"])
            text = once(text, "import { Component, useEffect, useRef, useState, type ReactNode } from 'react';", "import { Component, Suspense, useDeferredValue, useEffect, useRef, useState, type ReactNode } from 'react';")
            reason = "Keep observed model/hardware state and new official deferred/lazy routes."
        elif name == "apps/host/src/components/NativeSettings.tsx":
            text, blocks = resolve(text, ["both", "ours"])
            text = once(text, "<small>{tr(f.hint)}</small>", "<small>{tr(hints[f.id] ?? f.hint)}</small>")
            reason = "Keep owned asynchronous settings/drafts, observed storage and projection UI; display official per-model drafting hint."
        elif name == "apps/host/src/lib/native.ts":
            text, _ = resolve(text, ["ours"])
            text = once(text, "on_this_pc:string|null;installed:boolean;", "on_this_pc:string|null;/** Files excluding the lookup table, for the fit label. */fit_gb?:number|null;installed:boolean;")
            text = once(text, "images:boolean;sizes:NativeSize[]}", "images:boolean;sizes:NativeSize[];feed?:boolean;available?:boolean;unavailable_reason?:string}")
            reason = "Add signed-feed availability and actual fit size to fork cancellation/serving contracts."
        elif name == "apps/host/src/main.tsx":
            text, blocks = resolve(text, ["both", "theirs"])
            # Imports must remain top-level; mount only after translations load,
            # still through the fork's installed-build identity gate.
            text = once(text, "      <App />\n", "      <Startup />\n")
            reason = "Combine official translation/highlighter deferral with installed renderer/Host identity check."
        elif name == "setup.py":
            text, _ = resolve(text, ["ours"])
            text = once(text, '    if not mmproj.exists():\n        mmproj = find_in(roots, f"models/{fam[\'mmproj\']}") or mmproj\n    near =', '    if not mmproj.exists():\n        mmproj = find_in(roots, f"models/{fam.get(\'mmproj\', MMPROJ)}") or mmproj\n    near =')
            reason = "Preserve chosen adjacent picture reader and official no-picture-reader fallback before disk accounting."
        elif name == "src/prefill/prefill.cpp":
            text, _ = resolve(text, ["ours", "ours"])
            text = once(text, "rms_rope_rows(m.Qf, 24 * 512, 512, m.q, 6144, (const float*) wqn->data, T, 24, 256, EPS, p0, strata::kernels::rope_scaling(), m.cs);", "rms_rope_rows(m.Qf, kNHead * 2 * kHeadDim, 2 * kHeadDim, m.q, kQW, (const float*) wqn->data, T, kNHead, kHeadDim, EPS, p0, strata::kernels::rope_scaling(), m.cs);")
            text = once(text, "rms_rows(m.q, (const float*) wqn->data, T * 24, 256, 256, EPS, m.cs);", "rms_rows(m.q, (const float*) wqn->data, T * kNHead, kHeadDim, kHeadDim, EPS, m.cs);")
            text = once(text, "rope(m.q, T, 24, 256, 6144, p0, strata::kernels::rope_scaling(), m.cs);", "rope(m.q, T, kNHead, kHeadDim, kQW, p0, strata::kernels::rope_scaling(), m.cs);")
            text = once(text, "if (st.kv_rot || st.kv_hybrid) strata::kernels::fwht256_inplace_cuda(m.attn, T * 24, m.cs);", "if (st.kv_rot || st.kv_hybrid) strata::kernels::fwht256_inplace_cuda(m.attn, T * kNHead, m.cs);")
            reason = "Use official model geometry without dropping native-cache query and attention hooks."
        elif name == "apps/host/scripts/test.mjs":
            text, _ = resolve(text, ["ours"])
            text = once(text, "requestedTimeout===undefined?null:Number(requestedTimeout)", "requestedTimeout===undefined?600000:Number(requestedTimeout)")
            text = once(text, "...files],{cwd:root", "...process.argv.slice(2),...files],{cwd:root")
            reason = "Combine official bounded default and CLI arguments with fork isolated environment and filesystem guard."
        elif name == "apps/host/tests/packaged-control.test.mjs":
            text, _ = resolve(text, ["ours"])
            text = once(text, "readFileSync, appendFileSync }", "readFileSync, appendFileSync, realpathSync }")
            reason = "Retain fork mutation fixture and official canonical Mac temp root."
        elif name == "tests/terminal/test_split_parallel.py":
            text, _ = resolve(text, ["ours"])
            anchor = "        self.addCleanup(system.stop)\n"
            text = once(text, anchor, anchor + "        intel = mock.patch.object(Runner, 'intel_chosen', lambda self: False)\n        intel.start()\n        self.addCleanup(intel.stop)\n")
            reason = "Isolate synthetic Linux split selection and NVIDIA choice without globally changing pathlib platform."
        else:
            raise ValueError(f"Unreviewed conflict path: {name}")
        if re.search(r"^(<<<<<<<|=======|>>>>>>>)", text, re.M):
            raise ValueError(f"Unresolved markers: {name}")
        changes[name] = text
        reasons[name] = reason
    return changes, reasons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    changes, reasons = proposal()
    report = []
    # Compute every proposal successfully before modifying the index/worktree.
    for name, text in changes.items():
        content = text.encode("utf-8")
        row = {"path": name, "sha256": hashlib.sha256(content).hexdigest(), "reason": reasons[name]}
        if args.apply:
            before = (ROOT / name).read_bytes()
            row["conflictedInputObject"] = git("hash-object", "-w", "--stdin", data=before).decode().strip()
            obj = git("hash-object", "-w", "--stdin", data=content).decode().strip()
            mode = git("ls-files", "-s", "--", name).decode().split()[0]
            git("update-index", "--add", "--cacheinfo", mode, obj, name)
            git("checkout-index", "-f", "--", name)
        report.append(row)
    print(json.dumps({"applied": args.apply, "parents": [OURS, THEIRS], "resolutions": report}, indent=2))


if __name__ == "__main__":
    main()
