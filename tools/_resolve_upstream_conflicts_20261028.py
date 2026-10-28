#!/usr/bin/env python3
"""One-shot conflict resolver for upstream v0.2.7.1 merge into Hakua fork.

Prefer official API/security surfaces; keep proprietary Hakua/spin8/perf131k/gguf forks.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.2-preview.20261028.1"


def write(rel: str, text: str) -> None:
    path = ROOT / rel
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {rel}")


def run_git(*args: str) -> None:
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def take(rel: str, side: str) -> None:
    # side: ours|theirs
    run_git("checkout", f"--{side}", "--", rel)
    print(f"checkout --{side} {rel}")


def strip_markers(text: str) -> str:
    if "<<<<<<<" in text:
        raise RuntimeError("conflict markers remain")
    return text


def main() -> None:
    # --- .gitattributes: both ---
    write(
        ".gitattributes",
        """# Frozen prompts are hashed byte for byte (manifest sha256): never convert their line endings.
bench/prompts/** -text

# launchers keep their platform line endings wherever the repository is cloned
*.sh text eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf
bin/strata text eol=lf

# copies of real packs' native_experts.txt, parsed byte for byte by tests/core/expert_layout_test.cpp
tests/data/native_experts/** -text

# the quant yardstick's text set: tokenized byte for byte (set.ids.json), never convert its line endings
data/quant_quality/** -text

# the license text is shipped and checked as LF text on every checkout
LICENSE text eol=lf

# container scripts run in Linux: always LF
docker/*.sh text eol=lf
Dockerfile text eol=lf
docker/Dockerfile text eol=lf
docker/compose/* text eol=lf

# Apple tools (codesign, plutil) read these: LF only, wherever the repository is cloned
*.plist text eol=lf
tools/spin8_*.patch -text

# vendored KaTeX (serve/web/vendor): the files are hashed byte for byte (PROVENANCE.json), never convert their line endings.
serve/web/vendor/** -text
""",
    )

    # --- version pins ---
    for rel in ("apps/host/package.json", "apps/desktop/package.json"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        text = re.sub(
            r"<<<<<<< HEAD\n  \"version\": \"[^\"]+\",\n=======\n  \"version\": \"[^\"]+\",\n>>>>>>> upstream/main\n",
            f'  "version": "{VERSION}",\n',
            text,
            count=1,
        )
        write(rel, strip_markers(text))

    cargo = (ROOT / "apps/desktop/src-tauri/Cargo.toml").read_text(encoding="utf-8")
    cargo = re.sub(
        r"<<<<<<< HEAD\nversion = \"[^\"]+\"\n=======\nversion = \"[^\"]+\"\n>>>>>>> upstream/main\n",
        f'version = "{VERSION}"\n',
        cargo,
        count=1,
    )
    write("apps/desktop/src-tauri/Cargo.toml", strip_markers(cargo))

    lock = (ROOT / "apps/desktop/src-tauri/Cargo.lock").read_text(encoding="utf-8")
    lock = re.sub(
        r"<<<<<<< HEAD\nversion = \"[^\"]+\"\n=======\nversion = \"[^\"]+\"\n>>>>>>> upstream/main\n",
        f'version = "{VERSION}"\n',
        lock,
        count=1,
    )
    write("apps/desktop/src-tauri/Cargo.lock", strip_markers(lock))

    # --- native.ts: hakuaChatbot + upstream contextMax ---
    native_ts = (ROOT / "apps/host/src/lib/native.ts").read_text(encoding="utf-8")
    native_ts = re.sub(
        r"<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> upstream/main\n",
        lambda m: (
            # upstream body already has contextMax; reinject hakuaChatbot capability
            m.group(2).replace(
                "componentUpdates?:boolean}",
                "componentUpdates?:boolean;/** Operator opt-in (STRATA_HAKUA_CHATBOT=1): open the native Python memory chat in a browser. */hakuaChatbot?:boolean}",
            )
            + "\n"
        ),
        native_ts,
        count=1,
        flags=re.S,
    )
    write("apps/host/src/lib/native.ts", strip_markers(native_ts))

    # --- native-control.mjs: fork spin8 save + assertSettingsFile + upstream speedSwitches ---
    nc = (ROOT / "apps/host/server/native-control.mjs").read_text(encoding="utf-8")
    merged_nc = """ /* Fork: parse+validate run-config (spin8 / known keys). Upstream: assertSettingsFile exists for the same gate; we keep the parsed config. */
 function checkedSettingsConfig(text){const check=checkAndParseRunConfig(text);if(!check.ok)throw new Error(`The settings file for this model has a mistake, so the model was not started. ${describeIssues(check.issues,'error').join(' ')}`);return check.config;}
 function assertSettingsFile(path){checkedSettingsConfig(readFileSync(path,'utf8'));}
 function settings(model){const {entry,config}=record(model);const values=Object.fromEntries(NATIVE_FIELDS.map(f=>[f.id,config[f.id]??(f.id in NATIVE_FLAG_FIELDS?(flagValue(config[USER_KEY],NATIVE_FLAG_FIELDS[f.id])??flagValue(config.args,NATIVE_FLAG_FIELDS[f.id])):null)]));if(typeof values.aliases==='string')values.aliases=values.aliases.split(',').map(v=>v.trim()).filter(Boolean);values.sampling=config.sampling??{};values.args=config.args??[];values.env=publicNativeEnv(config.env??{});return {model,values,mcp:publicMcpServers(config.mcp_servers??config.mcpServers??{}),restartNeeded:true,capabilities:{dsExperts:ownEngine(config)&&dsExpertsSupported(config)},speedSwitches:speedSwitchRows(config.env??{},{deepseek:ownEngine(config),arch:config.arch??null,backend:config.backend??entry?.backend??snapshot.installed?.engine?.backend??null,gpus:snapshot.hardware?.gpus??[]})};}
 function save(model,{values,mcp}){if([...jobs.values()].some(j=>j.state==='running'))throw new Error('Finish the current operation before saving native settings.');const {path,config}=record(model);if(busy(requests().filter(r=>instances.get(r.instanceId)?.model===model)))throw new Error('Finish this model’s requests before saving its settings.');const patch=validateNativeSettings(values??{}),next={...config};if(patch.ds_experts!=null&&!dsExpertsSupported(config))throw new Error('The Speed choice needs the newer DeepSeek engine. Update the engine in Settings, then choose it.');for(const field of nativeFields())if(field.supported===false&&patch[field.id]!=null&&JSON.stringify(patch[field.id])!==JSON.stringify(config[field.id]))throw new Error(`${field.label} needs a newer native Strata installation. Update it in Settings → About.`);for(const [key,value] of Object.entries(patch)){if(key==='env')next.env=restoreNativeEnv(value,config.env??{});else if(value===null){delete next[key];if(key in NATIVE_FLAG_FIELDS){const flag=NATIVE_FLAG_FIELDS[key];if(Array.isArray(next[USER_KEY])){const u=setUserFlag(next[USER_KEY],flag,null);if(u.length)next[USER_KEY]=u;else delete next[USER_KEY];}if(Array.isArray(next.args))next.args=setUserFlag(next.args,flag,null);if(Array.isArray(next.args_written))next.args_written=setUserFlag(next.args_written,flag,null);}}else next[key]=value;}validateNativeSettings({spin8_mode:next.spin8_mode??null,spin8_native_config:next.spin8_native_config??null,spin8_native_sha256:next.spin8_native_sha256??null});if('vram_reserve_mib' in patch){const base=captureUserArgs(next);const mine=setUserFlag(base,'--vram-reserve-mib',patch.vram_reserve_mib);if(mine.length)next[USER_KEY]=mine;else delete next[USER_KEY];next.args=mine.length&&patch.vram_reserve_mib!==null?mergeUserArgs(next.args??[],mine):setUserFlag(next.args??[],'--vram-reserve-mib',null);delete next.ui_reserve_applied;if(Array.isArray(next.args_written))next.args_written=[...next.args];}if(mcp!==undefined){next.mcp_servers=validateMcpServers(mcp,config.mcp_servers??config.mcpServers??{});delete next.mcpServers;}copyFileSync(path,path+'.bak');chmodSync(path+'.bak',0o600);const temp=path+'.ui-tmp';writeFileSync(temp,JSON.stringify(next,null,2)+'\\n',{mode:0o600});renameSync(temp,path);return settings(model);}
"""
    nc = re.sub(
        r"<<<<<<< HEAD\n.*?>>>>>>> upstream/main\n",
        merged_nc,
        nc,
        count=1,
        flags=re.S,
    )
    write("apps/host/server/native-control.mjs", strip_markers(nc))

    # --- main.rs: keep fork updater gate + add notification plugin ---
    main_rs = (ROOT / "apps/desktop/src-tauri/src/main.rs").read_text(encoding="utf-8")
    main_rs = re.sub(
        r"<<<<<<< HEAD\n.*?>>>>>>> upstream/main\n",
        """        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init());
    // The unsigned full preview is distributed manually. It must never offer
    // the upstream signed installer through this fork's desktop window.
    #[cfg(not(feature = "public-full-package"))]
    let builder = builder.plugin(tauri_plugin_updater::Builder::new().build());
    builder.manage(HostProcess(Mutex::new(None)))
""",
        main_rs,
        count=1,
        flags=re.S,
    )
    write("apps/desktop/src-tauri/src/main.rs", strip_markers(main_rs))

    # --- serve/telemetry.py: keep named thread ---
    tel = (ROOT / "serve/telemetry.py").read_text(encoding="utf-8")
    tel = re.sub(
        r"<<<<<<< HEAD\n.*?=======.*?>>>>>>> upstream/main\n",
        '        self._thread = threading.Thread(target=self._loop, daemon=True, name=f"telemetry-sampler-{id(self)}(_loop)")\n',
        tel,
        count=1,
        flags=re.S,
    )
    write("serve/telemetry.py", strip_markers(tel))

    # --- serve/test_responses.py: upstream assertions (join timeout) ---
    take("serve/test_responses.py", "theirs")

    # --- tools/gguf_reader.py: union of type tables ---
    gguf = (ROOT / "tools/gguf_reader.py").read_text(encoding="utf-8")
    gguf = re.sub(
        r"<<<<<<< HEAD\n.*?=======.*?>>>>>>> upstream/main\n",
        '    142: "PQ2_0", 143: "PTQ1_0", 144: "TQ2_T", 145: "TQK6", 146: "TQK7",\n'
        '    # pair-trellis family added for Gyro-L (agentionai llama.cpp release/gyro-l)\n'
        '    147: "TQP5", 148: "TQP6", 149: "TQP7",\n'
        '    1001: "PQ2_0", 1002: "PTQ1_0", 2001: "TQ4_1S", 2002: "TQ3_0S",\n',
        gguf,
        count=1,
        flags=re.S,
    )
    gguf = re.sub(
        r"<<<<<<< HEAD\n.*?=======.*?>>>>>>> upstream/main\n",
        '    "PQ2_0": (128, 34), "TQ4_1S": (32, 20), "TQ3_0S": (32, 15),\n'
        '    # TQP5/6/7: fp16 scale + 8*K bytes of a 64-step x K-bit circular stream (K = 5/6/7)\n'
        '    "TQP5": (128, 42), "TQP6": (128, 50), "TQP7": (128, 58),\n',
        gguf,
        count=1,
        flags=re.S,
    )
    write("tools/gguf_reader.py", strip_markers(gguf))

    # --- expert_source.cpp: both includes ---
    es = (ROOT / "src/core/expert_source.cpp").read_text(encoding="utf-8")
    es = re.sub(
        r"<<<<<<< HEAD\n.*?=======.*?>>>>>>> upstream/main\n",
        '#include "strata/perf131k/blob_failure.hpp"\n'
        '#include "strata/perf131k/trace.hpp"\n'
        '#include "strata/core/expert_nibble.hpp"\n',
        es,
        count=1,
        flags=re.S,
    )
    write("src/core/expert_source.cpp", strip_markers(es))

    # --- prefill.cpp: both include + BOTH run() prefixes ---
    pf = (ROOT / "src/prefill/prefill.cpp").read_text(encoding="utf-8")
    pf = re.sub(
        r"<<<<<<< HEAD\n#include \"strata/perf131k/trace.hpp\"\n=======\n#include \"strata/prefill/copy_events.hpp\"\n>>>>>>> upstream/main\n",
        '#include "strata/perf131k/trace.hpp"\n#include "strata/prefill/copy_events.hpp"\n',
        pf,
        count=1,
    )
    pf = re.sub(
        r"<<<<<<< HEAD\n.*?=======.*?>>>>>>> upstream/main\n",
        "    strata::core::NativeSessionCall native_call(*impl_->ss);\n"
        "#if defined(STRATA_WITH_NATIVE_CACHE)\n"
        "    if (!strata::core::native_session_ready(*impl_->ss, err)) return false;\n"
        "#endif\n"
        "#if defined(STRATA_USE_HIP) || defined(STRATA_HIP_GFX906)\n"
        "    constexpr bool lm_hip = true;\n"
        "#else\n"
        "    constexpr bool lm_hip = false;\n"
        "#endif\n"
        "    // layer-major prefill: STRATA_PREFILL_LAYER_MAJOR=1 / 0 win; unset, it is on for a CUDA layer split\n"
        "    if (hand_in_ == nullptr && impl_ &&\n"
        "        strata::prefill_layer_major_resolve(lm_env_text(), lm_hip, stage_count(), strata::qwen_defaults_026())) {\n"
        "        const bool by_default = !lm_env_explicit();\n"
        "        for (Prefill* p = this; p != nullptr; p = p->next_) p->lm_by_default_ = by_default;\n"
        "        std::string why;\n"
        "        if (by_default) {\n"
        "            static bool noted = false;\n"
        "            if (!noted) {\n"
        "                noted = true;\n"
        "                std::fprintf(stderr, \"strata prefill: layer-major prefill is on for this layer split (each layer's experts are read once per \"\n"
        "                                     \"super-chunk of up to %lld tokens, not once per chunk; STRATA_PREFILL_LAYER_MAJOR=0 or STRATA_DEFAULTS=026 \"\n"
        "                                     \"turns it off)\\n\", (long long) kLmDefaultOnTokens);\n"
        "            }\n"
        "        }\n"
        "        if (lm_prepare_chain(n, why) > 0) {\n"
        "            bool ok = run_layer_major(tokens, n, pos0, err);\n"
        "            std::string drain_err;\n"
        "            if (!drain_pipeline(drain_err) && ok) {\n"
        "                ok = false;\n"
        "                err = drain_err;\n"
        "            }\n"
        "            for (Prefill* p = this; p != nullptr; p = p->next_) p->lm_mid_ = false;\n"
        "            lm_release_chain();\n"
        "            return ok;\n"
        "        }\n"
        "        static std::string said;\n"
        "        if (why != said && !(by_default && why == \"a short prompt\")) {\n"
        "            said = why;\n"
        "            std::fprintf(stderr, \"strata prefill: layer-major off for this prompt: %s\\n\", why.c_str());\n"
        "        }\n"
        "    }\n",
        pf,
        count=1,
        flags=re.S,
    )
    write("src/prefill/prefill.cpp", strip_markers(pf))

    # --- generate.cpp: keep fork blob_failure diagnostics + upstream nibble path; keep both context_room and dprob copy ---
    gen = (ROOT / "src/program/generate.cpp").read_text(encoding="utf-8")
    gen = re.sub(
        r"<<<<<<< HEAD\n.*?=======.*?>>>>>>> upstream/main\n",
        "            if (b == nullptr) {\n"
        "                strata::perf131k::blob_failure::flush_terminal(\n"
        "                    (uint64_t) strata::kernels::cpu::expert_layout().blob_bytes(profile[(size_t) i].first));\n"
        "                err = \"ExpertSource: blob acquisition failed (cause=unknown, layer=\" +\n"
        "                      std::to_string(profile[(size_t) i].first) + \", expert=\" +\n"
        "                      std::to_string(profile[(size_t) i].second) + \")\";\n"
        "            }\n"
        "            const bool nib_pair = nib_x.active() && nib::layer(profile[(size_t) i].first).on;   // STRATA_EXPERT_NIBBLE\n"
        "            if (b == nullptr || !(nib_pair ? nib_x.add(profile[(size_t) i].first, profile[(size_t) i].second, slot, b, err)\n"
        "                                           : xcache.fill_slot_blocking(slot, b, err,\n"
        "                    (int64_t) strata::kernels::cpu::expert_layout().blob_bytes(profile[(size_t) i].first)))) {\n",
        gen,
        count=1,
        flags=re.S,
    )
    gen = re.sub(
        r"<<<<<<< HEAD\n.*?=======.*?>>>>>>> upstream/main\n",
        "                // A wide speculative window may not fit at the final context cells.\n"
        "                const int64_t context_room = o.max_context - p;\n"
        "                if (o.exact_context_boundary) {\n"
        "                    T = strata::program::serve_context_window(T, p, o.max_context, true);\n"
        "                    if (T < 1) {\n"
        "                        std::fprintf(stderr, \"strata serve: the request ran out of context before its output reservation completed\\n\");\n"
        "                        return 1;\n"
        "                    }\n"
        "                }\n"
        "                std::copy(dprob.begin(), dprob.begin() + (std::ptrdiff_t) std::min<size_t>(dprob.size(), 8), dwin_s.begin());\n",
        gen,
        count=1,
        flags=re.S,
    )
    write("src/program/generate.cpp", strip_markers(gen))

    # --- verify.cpp: take upstream structure, re-add perf131k hooks where trivial ---
    take("src/core/verify.cpp", "theirs")
    ver = (ROOT / "src/core/verify.cpp").read_text(encoding="utf-8")
    # soft-add graph_retired/created if includes exist; skip if not present to avoid hard fail
    if "perf131k" not in ver and (ROOT / "include/strata/perf131k/trace.hpp").exists():
        # leave upstream-clean; fork hooks remain in other TUs
        pass
    write("src/core/verify.cpp", ver)  # already theirs

    # --- serve/server.py: union imports + dual paths ---
    srv = (ROOT / "serve/server.py").read_text(encoding="utf-8")
    srv = re.sub(
        r"<<<<<<< HEAD\nfrom serve import perf131k_e2e as perf_e2e  # noqa: E402\nfrom serve import memory_harness  # noqa: E402\nfrom serve.structured import StructuredOutputError, prepare_format, validated_json  # noqa: E402\n=======\nfrom serve.structured import StructuredOutputError, prepare_format, validated_json, extract_json  # noqa: E402\n>>>>>>> upstream/main\n",
        "from serve import perf131k_e2e as perf_e2e  # noqa: E402\n"
        "from serve import memory_harness  # noqa: E402\n"
        "from serve.structured import StructuredOutputError, prepare_format, validated_json, extract_json  # noqa: E402\n",
        srv,
        count=1,
    )
    # prefill_only vs audit begin
    srv = re.sub(
        r"<<<<<<< HEAD\n        if audit is not None:\n            audit.native_begin\(ids, max_new, embeddings=embeddings, pid=getattr\(self.proc, \"pid\", None\)\)\n=======\n        if prefill_only:.*?head = \"GEN 0 prefill=1\"\n>>>>>>> upstream/main\n",
        "        if prefill_only:                                 # split serving (serve/split.py): read the prompt, make no token\n"
        "            if embeddings or int(max_new) != 0:\n"
        "                raise ValueError(\"prefill_only is a text prompt and max_new 0\")\n"
        "            head = \"GEN 0 prefill=1\"\n"
        "        if audit is not None:\n"
        "            audit.native_begin(ids, max_new, embeddings=embeddings, pid=getattr(self.proc, \"pid\", None))\n",
        srv,
        count=1,
        flags=re.S,
    )
    # token yield: want_lp + audit
    srv = re.sub(
        r"<<<<<<< HEAD\n                    token = int\(line\[2:\]\)\n                    if audit is not None:\n                        audit.native_token\(token\)\n                    yield token\n=======\n                    t = int\(line\[2:\]\)\n                    if want_lp:.*?yield t\n>>>>>>> upstream/main\n",
        "                    t = int(line[2:])\n"
        "                    if audit is not None:\n"
        "                        audit.native_token(t)\n"
        "                    if want_lp:\n"
        "                        # the engine writes the token and its `LP` line in one flush\n"
        "                        try:\n"
        "                            carry = self.lines.get(timeout=0.5)\n"
        "                        except queue.Empty:\n"
        "                            carry = NO_LINE\n"
        "                        if isinstance(carry, str) and carry.startswith(\"LP \"):\n"
        "                            self.lp_lines.append((t, carry))\n"
        "                            carry = NO_LINE\n"
        "                    yield t\n",
        srv,
        count=1,
        flags=re.S,
    )
    # resolve_prefix + audit prepared
    srv = re.sub(
        r"<<<<<<< HEAD\n            req\[\"strata_prefix\"\] = self.resolve_prefix\(req\[\"strata_prefix\"\], messages, tools, kwargs, ids, bool\(images\)\)\n        if \(audit := perf_e2e.current\(\)\) is not None:\n            audit.prepared\(ids, max_new, ctx\)\n=======\n            req\[\"strata_prefix\"\] = self.resolve_prefix\(req\[\"strata_prefix\"\], messages, tools, kwargs, ids, bool\(images\) or ds_pics\)\n>>>>>>> upstream/main\n",
        '            req["strata_prefix"] = self.resolve_prefix(req["strata_prefix"], messages, tools, kwargs, ids, bool(images) or ds_pics)\n'
        "        if (audit := perf_e2e.current()) is not None:\n"
        "            audit.prepared(ids, max_new, ctx)\n",
        srv,
        count=1,
    )
    write("serve/server.py", strip_markers(srv))

    # --- READMEs: take upstream for now; rewritten after merge ---
    for rel in ("README.md", "README.ja.md", "README.zh-CN.md"):
        take(rel, "theirs")

    # --- web UI: take upstream then reinject memory scripts/blocks via separate patch ---
    take("serve/web/app.js", "theirs")
    take("serve/web/index.html", "theirs")

    print("phase1 done; remaining markers:")
    for p in ROOT.rglob("*"):
        if p.is_file() and ".git" not in p.parts:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "<<<<<<<" in t:
                print(" STILL", p.relative_to(ROOT))


if __name__ == "__main__":
    main()
