#!/usr/bin/env python3
"""Three-way merge of official upstream v0.2.21 into the Hakua fork.

Uses BASE=v0.2.20, OURS=HEAD, THEIRS=upstream/main (v0.2.21).
- Preserves all fork-only and fork-retained files untouched.
- Adopts upstream additions and upstream-only modifications cleanly.
- Runs ``git merge-file --diff3`` on all files modified on both sides.
- Resolves every 3-way conflict with explicit, audited per-file resolvers so
  upstream v0.2.21 features, security fixes, and bug fixes are adopted while
  retaining Hakua's custom features and aligning custom code to the official API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, TypeVar

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover
    T = TypeVar("T")

    def tqdm(iterable: Iterable[T], **_: object) -> Iterable[T]:
        return iterable


LOGGER = logging.getLogger("strata.merge_0221")
LOG_FMT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"

CONFLICT_RE = re.compile(
    r"<<<<<<< fork\(HEAD\)\n(.*?)\|\|\|\|\|\|\| base\(v0\.2\.20\)\n(.*?)=======\n(.*?)>>>>>>> upstream\(v0\.2\.21\)\n",
    re.DOTALL,
)

# Files that are 0-byte stubs in HEAD (from an earlier intake) -> adopt upstream
ADOPT_UPSTREAM_PATHS: frozenset[str] = frozenset(
    {
        "terminal/tests/terminal/test_arc_feed_models.py",
        "terminal/tests/terminal/test_docker_files.py",
        "terminal/tests/terminal/test_feed_aarch64.py",
        "terminal/tests/terminal/test_launch_install.py",
        "terminal/tests/terminal/test_private_files.py",
        "terminal/tests/terminal/test_sycl_build_script.py",
        # Regenerated upstream registers / benchmark index
        "docs/SETTINGS.md",
        "docs/bench-results/README.md",
        "terminal/data/settings-register.json",
        # Engine files where upstream v0.2.21 supersedes stale pre-0.2.20 copies
        # (verified: all 7 fork compatibility symbols in hy4_gpu_model.hip.h exist in v0.2.21)
        "engine/src/hy4flash/run/hy4_gpu_model.hip.h",
        "engine/src/inkling2/cuda/ink_cuda.cuh",
        "engine/src/inkling2/cuda/ink_runner.cuh",
        "engine/tests/platform/host_limits_test.cpp",
    }
)

# Version-bearing files where fork keeps its own Hakua SemVer (0.8.0) on version-only conflicts
KEEP_FORK_ON_VERSION_CONFLICT: frozenset[str] = frozenset(
    {
        "app/desktop/package.json",
        "app/desktop/src-tauri/Cargo.toml",
        "app/desktop/src-tauri/Cargo.lock",
        "app/host/package.json",
        "app/host/package-lock.json",
        "app/host/tests/qa1-storage.test.mjs",
        "terminal/strata_cli/__init__.py",
    }
)


@dataclass
class FileAction:
    path: str
    category: str
    strategy: str
    hunks_resolved: int = 0
    sha256: str = ""


def git_ls_tree(repo: Path, rev: str) -> dict[str, tuple[str, str]]:
    """Return {path: (mode, blob_sha)} for all tracked files in rev."""
    out = subprocess.check_output(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", rev],
        stderr=subprocess.PIPE,
    )
    entries: dict[str, tuple[str, str]] = {}
    for raw in out.split(b"\x00"):
        if not raw:
            continue
        meta, path_b = raw.split(b"\t", 1)
        parts = meta.decode("utf-8").split()
        entries[path_b.decode("utf-8", errors="surrogateescape")] = (parts[0], parts[2])
    return entries


class BlobReader:
    """Persistent git cat-file --batch reader."""

    def __init__(self, repo: Path) -> None:
        self._proc = subprocess.Popen(
            ["git", "-C", str(repo), "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

    def read(self, rev: str, path: str) -> bytes:
        assert self._proc.stdin is not None and self._proc.stdout is not None
        self._proc.stdin.write(f"{rev}:{path}\n".encode("utf-8"))
        self._proc.stdin.flush()
        header = self._proc.stdout.readline().decode("utf-8", "replace").strip()
        parts = header.split()
        if len(parts) < 3 or parts[1] != "blob":
            raise RuntimeError(f"missing blob {rev}:{path} ({header})")
        data = self._proc.stdout.read(int(parts[2]))
        self._proc.stdout.read(1)
        return data

    def close(self) -> None:
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
            self._proc.wait(timeout=30)
        except Exception:
            self._proc.terminate()


def run_merge_file(repo: Path, ours: bytes, base: bytes, theirs: bytes, tmp: Path) -> tuple[bytes, int]:
    """Run git merge-file --diff3 and return (merged_bytes, conflict_count)."""
    p_o, p_b, p_t = tmp / "ours", tmp / "base", tmp / "theirs"
    p_o.write_bytes(ours.replace(b"\r\n", b"\n"))
    p_b.write_bytes(base.replace(b"\r\n", b"\n"))
    p_t.write_bytes(theirs.replace(b"\r\n", b"\n"))
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "merge-file",
            "-p",
            "--diff3",
            "-L",
            "fork(HEAD)",
            "-L",
            "base(v0.2.20)",
            "-L",
            "upstream(v0.2.21)",
            str(p_o),
            str(p_b),
            str(p_t),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if not 0 <= proc.returncode <= 127:
        raise RuntimeError(f"git merge-file failed ({proc.returncode})")
    return proc.stdout, proc.returncode


def resolve_hunks(text: str, handler: Callable[[int, str, str, str], str]) -> tuple[str, int]:
    """Replace every diff3 conflict hunk using handler(idx_1based, fork, base, upstream)."""
    counter = 0

    def _sub(match: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        return handler(counter, match.group(1), match.group(2), match.group(3))

    out = CONFLICT_RE.sub(_sub, text)
    if "<<<<<<<" in out or ">>>>>>>" in out:
        raise RuntimeError("Unresolved conflict markers remain after handler")
    return out, counter


# ---------------------------------------------------------------------------
# Explicit per-file conflict resolvers
# ---------------------------------------------------------------------------

def resolve_readme(_merged: str, ours: str, _theirs: str) -> tuple[str, int]:
    """Keep fork README (v0.8.0 + Gen-H) and update upstream reference to v0.2.21 / 0.1.67."""
    updated = ours.replace("v0.2.20", "v0.2.21").replace("0.2.20", "0.2.21").replace("0.1.66", "0.1.67")
    return updated, 13


def resolve_release_json(_merged: str, ours: str, theirs: str) -> tuple[str, int]:
    """Keep fork release.json top-level + historical_releases; sync upstream block to v0.2.21."""
    fork_doc = json.loads(ours)
    up_doc = json.loads(theirs)
    fork_doc["upstream"] = up_doc
    return json.dumps(fork_doc, indent=2, ensure_ascii=False) + "\n", 1


def resolve_metal_cmake(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(_idx: int, fork: str, _base: str, _up: str) -> str:
        # Keep fork's extra ggml include paths and Hakua engine version
        return fork

    return resolve_hunks(merged, h)


def resolve_native_expert(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    """Keep fork's Gen-I/J q8_0_quant_avx2 (cleanly merged outside conflict hunks) + adopt upstream #6552 dot_x4_enabled."""
    out, hunks = resolve_prefer_upstream(merged, _ours, _theirs)
    if "q8_0_quant_avx2" not in out:
        raise RuntimeError("native_expert.cpp: fork q8_0_quant_avx2 missing after 3-way merge")
    return out, hunks


def resolve_agent_bridge(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, fork: str, _base: str, up: str) -> str:
        if idx == 1:
            # Combine fork's selectSkillsForTurn/onTurnBegin/localStallMs with upstream's
            # 2h engineGraceMs, contextOptimizer, controlRpcMs, helperStopMs, boundedRpc
            return (
                "export function createAgentBridge({ dataDir, componentsDir = null, bundledDir = null, gate = true, "
                "localInstances, connections, tools = () => undefined, defaultLocalId = () => null, skillsDir = () => null, "
                "selectSkillsForTurn = () => [], onTurnBegin = () => null, onGoal = () => {}, onPlan = () => {}, "
                "onQueue = () => {}, onWake = () => {}, proxyBase = null, searchMock = null, expertSampling = () => null, "
                "engineProgress = () => null, engineGraceMs = 2 * 60 * 60_000, helperLimitMs = () => 0, "
                "contextOptimizer = () => null, stallMs = 4 * 60_000, localStallMs = 30 * 60_000, stallToolMs = 20 * 60_000, "
                "env = process.env, nodePath = process.execPath, log = () => {}, liveMs = 90_000, startRuntimeImpl = null, "
                "startTimeoutMs = 120_000, sessionReadyMs = 60_000, sessionRetryMs = 1_500, restartWaitMs = 120_000, "
                "controlRpcMs = 15_000, helperStopMs = 10_000 }) {\n"
                "  localStallMs = localSilenceLimit(env.STRATA_LOCAL_STALL_MS, localStallMs);\n"
                "  const boundedRpc = (runtime, method, args, signal = null) => {\n"
                "    const deadline = AbortSignal.timeout(controlRpcMs);\n"
                "    const bounded = signal ? AbortSignal.any([signal, deadline]) : deadline;\n"
                "    return beforeAbort(() => runtime.gw.rpc(method, args, { signal: bounded }), bounded);\n"
                "  };\n"
            )
        if idx == 2:
            # Keep fork's turn.research cleanup + adopt upstream's agent-question-end emit
            research_part = "\n".join(
                line for line in fork.splitlines() if "for (const [k, v] of questions)" not in line
            )
            return (
                research_part
                + "\n"
                + "      turn.snapshot?.resolve?.();\n"
                + "      for (const [k, v] of questions) if (v.sessionId === turn.sessionId || v.chatId === c.id) { "
                + "questions.delete(k); emit({ type: 'agent-question-end', callId: v.callId }); }\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_llm_shape(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, _fork: str, _base: str, up: str) -> str:
        if idx == 1:
            return up
        if idx == 2:
            return (
                "      const sampling = samplingForPolicy(samplingNow(), policyOf(base));\n"
                "      const nativeAgent = /^strata-local(?:-|~|$)/.test(key);\n"
                "      if (req.method === 'POST' && /\\/chat\\/completions\\/?$/.test(rest) && body.length && "
                "(budget || sampling || nativeAgent || /hy4-flash/i.test(body.toString('utf8', 0, Math.min(body.length, 512))))) {\n"
                "        try { body = Buffer.from(JSON.stringify(shapeBody(JSON.parse(body.toString('utf8')), "
                "{ sampling, budget, nativeAgent }))); } catch { /* not JSON: pass it on untouched */ }\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_profile_mjs(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, fork: str, _base: str, up: str) -> str:
        if idx == 4:
            # Adopt upstream Inkling thinking compat + keep fork's privateConversationCache header
            return (
                "      // Inkling-2-Mini thinks like the others (0.2.21): its thinking comes back as reasoning_content, and Off sends none.\n"
                "      compat: THINKING_COMPAT,\n"
                "      ...(inst.privateConversationCache ? { headers: { 'x-strata-conversation-cache': '1' } } : {}),\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_host_index(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, fork: str, _base: str, up: str) -> str:
        if idx == 1:
            return (
                "import { createChatStore, drainChatStore, storeFailure, validChatId } from './chat-store.mjs';\n"
            )
        if idx == 2:
            return (
                "import { selectSkills, skillInstructions, withSkills, historyWithSkills } from './skill-selection.mjs';\n"
                "import { previewSkillMarkdown } from './skill-import.mjs';\n"
                "import { createChatWebSearch, referenceHistory } from './chat-web-search.mjs';\n"
                "import { createRustxngRuntime } from './rustxng-runtime.mjs';\n"
                "import { createRustxngSearch } from './web-search-rustxng.mjs';\n"
                "import { btwRequest } from './chat-btw.mjs';\n"
            )
        if idx == 3:
            return (
                "const inFlightChatSaves = new Set();\n"
                "const trackChatSave = fn => {\n"
                "  const p = Promise.resolve().then(fn);\n"
                "  const done = p.then(() => {}, () => {});\n"
                "  inFlightChatSaves.add(done);\n"
                "  done.finally(() => inFlightChatSaves.delete(done));\n"
                "  return p;\n"
                "};\n"
            )
        if idx == 4:
            return (
                "    const result = await modelProviders.stream({ selection, "
                "message: withSkills(skillState, message, workspaceId), "
                "history: historyWithSkills(skillState, referenceHistory(history, webReferences), workspaceId), "
                "images, thinking, signal: requestSignal, "
                "systemPrompt: ['You are Strata, a helpful assistant. Answer clearly. Do not claim to have read files or performed actions unless their results are included in the conversation.', userRules.promptBlock()].filter(Boolean).join('\\n\\n'), onFrame: frame => {\n"
            )
        if idx == 5:
            # Combine fork's single-line proxyCompletion (servingPolicy, referenceHistory, strata_cache_session,
            # getEffectiveSystemPrompt) with upstream's hy4Local/inklingLocal effort mapping & withSkills
            return (
                "    try{serving.mark(entry.id,{state:'generating'});const applied=selectSkills(skillState,message,workspaceId);"
                "const hy4Local=instance.arch==='hy4flash'||/^hy4-flash/i.test(String(instance.model??instance.apiModelId??''));"
                "const inklingLocal=instance.arch==='inkling2_loop'||/^inkling-2-mini/i.test(String(instance.model??instance.apiModelId??''));"
                "const thinkKey=String(thinking).toLowerCase();"
                "const effortWord=hy4Local?(thinkKey==='xhigh'?'max':({off:'none',minimal:'high',low:'high',medium:'high',high:'high',max:'max'}[thinkKey]??'high')):"
                "inklingLocal?({off:'none',xhigh:'max',minimal:'minimal'}[thinkKey]??thinkKey):"
                "({off:'none',max:'high'}[thinkKey]??(thinkKey==='xhigh'?'high':thinkKey));"
                "const result=await proxyCompletion({baseUrl:`http://127.0.0.1:${instance.port}/v1`,modelId:instance.apiModelId,"
                "servingPolicy:instance.servingPolicy,authorization:instance.key,"
                "message:withSkills(skillState,message,workspaceId),"
                "history:historyWithSkills(skillState,referenceHistory(history,webReferences),workspaceId),images,"
                "extra:{...(sessionId?{strata_cache_session:createHash('sha256').update(String(sessionId)).digest('hex')}:{}),"
                "strata_mcp:!webReferences&&useTools===true,"
                "...(thinkingBudget>0&&thinkKey!=='off'?{reasoning_budget_tokens:thinkingBudget}:{}),"
                "reasoning_effort:effortWord},systemPrompt:getEffectiveSystemPrompt([]),"
                "signal:signal?AbortSignal.any([signal,cancel.signal]):cancel.signal,"
                "onFrame:frame=>onFrame({...frame,requestId:entry.id,model:instance.label,"
                "contextMax:instance.metrics?.engine?.max_context??instance.context,skills:applied.map(s=>s.name)})});"
                "serving.mark(entry.id,{...result,usageSource:result.usageSource});"
                "serving.finish(entry.id,{tokensOut:result.tokensOut,durationMs:Date.now()-started});return result;}"
                "catch(e){serving.finish(entry.id,{durationMs:Date.now()-started,error:e.message});"
                "onFrame({type:'error',message:e.message,requestId:entry.id});return {error:e.message};}\n"
            )
        if idx == 6:
            return "      const systemPrompt = getEffectiveSystemPrompt([]);\n"
        if idx == 7:
            return (
                "          message: withSkills(skillState, message, workspaceId),\n"
                "          history: historyWithSkills(skillState, referenceHistory(history, webReferences), workspaceId),\n"
                "          disableTools: plainOnly || !!webReferences,\n"
            )
        if idx == 8:
            return "        const removed = await trackChatSave(() => chatStore.remove(id));\n"
        if idx == 9:
            return (
                "      if(instructions.length>40000)throw new Error('Skill instructions must contain 1–40000 characters.');\n"
                "      const onlyIn = body.onlyIn || null;\n"
                "      if (onlyIn !== null && !workspaces.some(w => w.id === onlyIn)) throw new Error('Choose an available workspace.');\n"
                "      // Keep the creation options with the skill, including its workspace scope.\n"
            )
        if idx == 10:
            # Keep fork's durable beforePublish/rollback using validated onlyIn
            return fork.replace("body.onlyIn??null", "onlyIn")
        if idx == 11:
            return up
        if idx == 12:
            # Combine fork's hub.close(), supervisor.stop(), rustxng.close() with upstream's #6661 drainChatStore
            return (
                "  server.close();\n"
                "  // #6661: drain any in-flight or queued chat saves to disk before tearing down sockets and exiting.\n"
                "  await drainChatStore(chatStore, { inFlight: inFlightChatSaves, timeoutMs: typeof CHAT_DRAIN_MS === 'number' ? CHAT_DRAIN_MS : 3000 });\n"
                "  // SSE responses need their terminating HTTP chunk before remaining sockets are forced closed.\n"
                "  await hub.close();\n"
                "  server.closeAllConnections?.();\n"
                "  await Promise.allSettled([localShare.stop(),cloudflare.stop(),native.close(),agent.close(),supervisor.stop(),rustxng.close()]);\n"
                "  await drainChatStore(chatStore, { timeoutMs: 1000 });\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_native_control(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, fork: str, _base: str, up: str) -> str:
        if idx == 1:
            # Import mergeEnvChanges + fork's flagValue
            return (
                "import { draftingHint, NATIVE_FIELDS, APP_OWNED_FIELDS, withoutDraftLayer, withPromptCacheSpread, "
                "withoutPromptCacheSpread, resolveDrafter, validateNativeSettings, validateMcpServers, publicMcpServers, "
                "publicNativeEnv, restoreNativeEnv, mergeEnvChanges, speedSwitchRows } from './native-settings.mjs';\n"
                "import { validModelPort } from './ports.mjs';\n"
                "import { resourceSettings, saferStart, reserveChoice, validRamReserve, withRamReserve, launchBudgetArgs } from './native-resources.mjs';\n"
                "import { USER_KEY, capture as captureUserArgs, flagValue, merge as mergeUserArgs, setFlag as setUserFlag, stamped as stampedUserArgs } from './native-user-args.mjs';\n"
            )
        if idx == 2:
            # Keep fork's rich native-control functions (projection, q36, saveChecked, preflightInstall),
            # AND add upstream's #6772 `base` diff-save + mergeEnvChanges into `save(...)` + Hy4/Inkling hints
            patched = fork.replace(
                "function save(model,{values,mcp},capability=null,memoryCapability=null){",
                "function save(model,{values,mcp,base},capability=null,memoryCapability=null){",
                1,
            ).replace(
                "if('env' in patch)next.env=restoreNativeEnv(patch.env,config.env??{});",
                "let baseValues=null;try{if(base&&typeof base==='object'&&!Array.isArray(base))baseValues=validateNativeSettings(base);}catch{baseValues=null;}\n"
                "  if('env' in patch)next.env=restoreNativeEnv(baseValues?mergeEnvChanges(patch.env,baseValues.env??{},config.env??{}):patch.env,config.env??{});",
                1,
            ).replace(
                "async function settingsHints(model){try{if(!packaged||typeof control.draftingPlan!=='function')return {};",
                "async function settingsHints(model){try{const {path:p0,config:c0}=record(model);"
                "if(String(c0.arch??'').toLowerCase()==='hy4flash'||/^hy4-flash/i.test(String(c0.model_name??model)))"
                "return {drafting:'DFly2 is Hy4-Flash’s built-in speculative drafter (on by default). Off disables speculative drafting.'};"
                "if(String(c0.arch??'').toLowerCase()==='inkling2_loop'||/^inkling-2-mini/i.test(String(c0.model_name??model)))"
                "return {drafting:'DSpark Block-8 is Inkling-2-Mini’s built-in speculative drafter (on by default). Off disables speculative drafting.'};"
                "if(!packaged||typeof control.draftingPlan!=='function')return {};",
                1,
            )
            return patched
        if idx == 3:
            # Add upstream's `arch` field onto fork's `instance` while keeping desktopMemoryAccess, servingPolicy, refusalProjection, beginObservation
            return fork.replace(
                "aliases:cfg.aliases??[],",
                "aliases:cfg.aliases??[],arch:(String(cfg.arch??'').toLowerCase()==='hy4flash'?'hy4flash':String(cfg.arch??'').toLowerCase()==='inkling2_loop'?'inkling2_loop':(cfg.arch??null)),",
                1,
            )
        return up

    return resolve_hunks(merged, h)


def resolve_native_gateway(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(_idx: int, fork: str, _base: str, up: str) -> str:
        return fork + up

    return resolve_hunks(merged, h)


def resolve_run_config_check(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, _fork: str, _base: str, up: str) -> str:
        if idx == 1:
            return up.replace(
                "'tool_call_recovery', 'codex_compaction_cache',",
                "'tool_call_recovery', 'undeclared_tool_calls', 'codex_compaction_cache',",
            )
        return up

    return resolve_hunks(merged, h)


def resolve_skill_files(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, _fork: str, _base: str, up: str) -> str:
        if idx == 1:
            return (
                "import { copyFileSync, cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, "
                "renameSync, rmSync, statSync, writeFileSync } from 'node:fs';\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_native_settings_tsx(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(_idx: int, fork: str, _base: str, _up: str) -> str:
        return fork.replace(
            "`/api/native/models/${model}/settings`, { values: parsed, mcp: tools }",
            '`/api/native/models/${model}/settings`, { values: parsed, mcp: tools, base: JSON.parse(original ?? "{}").values }',
            1,
        )

    return resolve_hunks(merged, h)


def resolve_native_ts(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(_idx: int, fork: str, _base: str, _up: str) -> str:
        # Add upstream's format, hy4, inkling on NativeSize and arch on NativeInstance while keeping all fork fields
        out = fork.replace(
            "context_fit?:import('./native-fit').ContextFit|null;",
            "format?:string;context_fit?:import('./native-fit').ContextFit|null;"
            "hy4?:{placement:{vram_gb:number;ram_gb:number;ssd_gb:number};mode:'ram_vram_zero_ssd'|'near_resident_ssd'|'cross_tier_ssd';recommended:boolean;unified:boolean;engram_gb:number}|null;"
            "inkling?:{placement:{vram_gb:number;ram_gb:number;ssd_gb:number;full_vram?:boolean};mode:'full_vram'|'ram_vram_zero_ssd'|'near_resident_ssd'|'cross_tier_ssd';recommended:boolean;unified:boolean;context:number;kv_gb:number;parallel_choices?:number[]}|null;",
            1,
        ).replace(
            "export interface NativeInstance {id:string;apiModelId:string;model:string;label:string;aliases?:string[];",
            "export interface NativeInstance {id:string;apiModelId:string;model:string;label:string;arch?:string|null;aliases?:string[];",
            1,
        )
        return out

    return resolve_hunks(merged, h)


def resolve_store_ts(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, fork: str, _base: str, up: str) -> str:
        if idx == 1:
            # Check if stopSession is defined in the merged file; if so use it, else keep fork's stopStreaming
            if "function stopSession(" in merged or "export function stopSession(" in merged:
                return up
            return fork
        if idx == 2:
            # Keep turnPrefs while adopting Inkling-2-Mini default 'Low' thinking fallback
            return (
                "        ...(turnPrefs.agent === false ? { agent: false } : {}),\n"
                "        thinking: turnPrefs.thinking ?? ((() => { const n = nativeState(); const i: any = n?.instances.find((x: any) => x.id === n.defaultId) ?? n?.instances[0]; return !state.remoteModel && !!i && (i.arch === 'inkling2_loop' || /^inkling-2-mini/i.test(String(i.model ?? i.apiModelId ?? ''))); })() ? 'Low' : 'Medium'),\n"
                "        thinkingBudget: turnPrefs.thinkingBudget,\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_chat_tsx(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, fork: str, _base: str, up: str) -> str:
        if idx == 1:
            # Adopt #6668 QuestionCard focus + /pause-for-update while keeping `let text = draft.trim();`
            return up.replace("const text = draft.trim();", "let text = draft.trim();")
        if idx == 2:
            # Keep fork's remote/supervised/useSlashCommands AND add upstream's awaitingQuestion
            return (
                "    const awaitingQuestion = useStore(s => !!(session && s.agentAsks[session.id]?.length));\n"
                + fork
            )
        return up

    return resolve_hunks(merged, h)


def resolve_frontend_py(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, _fork: str, _base: str, up: str) -> str:
        if idx == 1:
            return up.replace(
                "        self._dialect = inkling_dialect.InklingDialect()\n",
                "        self._dialect = inkling_dialect.InklingDialect()\n        self._inkling_thinking = thinking\n",
                1,
            )
        return up

    return resolve_hunks(merged, h)


def resolve_inkling_kind_py(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, _fork: str, _base: str, up: str) -> str:
        if idx == 1:
            return up
        if idx == 2:
            # Fork advantage: only emit `--draft off` when the engine advertises spec_opts=1
            # (newer official binary); older/fork Sakura 98K binaries reject `--draft off`.
            # Also adopt upstream's --draft-beam and --draft-adapt for v0.2.21!
            return (
                "        return [\"--draft\", \"off\"] if (info or {}).get(\"spec_opts\") == \"1\" else []\n"
                "    if (info or {}).get(\"drafter\") != \"dspark\":\n"
                "        return []\n"
                "    out = [\"--draft\", \"dspark\"]\n"
                "    # an engine that lists spec_opts=1 takes the window shape: one linear chain (the block drafter) unless the run config says otherwise\n"
                "    if (info or {}).get(\"spec_opts\") == \"1\":\n"
                "        beam = cfg.get(\"draft_beam\", inkling_family.DRAFT_BEAM)\n"
                "        if isinstance(beam, int) and not isinstance(beam, bool) and 1 <= beam <= 8:\n"
                "            out += [\"--draft-beam\", str(beam)]\n"
                "        if cfg.get(\"draft_adapt\", inkling_family.DRAFT_ADAPT) is True:\n"
                "            out += [\"--draft-adapt\"]\n"
                "    return out\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_launch_cmd_py(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    def h(idx: int, fork: str, _base: str, up: str) -> str:
        if idx == 1:
            # Keep fork's --output-language and DeepSeek/dense help notes + upstream's Inkling KV note
            return (
                "    g.add_argument(\"--context\", type=_context, metavar=\"SIZE\", "
                "help=\"how much text it remembers at once: 32k, 64k, 128k, 256k or a number of tokens (DeepSeek-V4.1-Flash: up to 512k and 1m)\")\n"
                "    g.add_argument(\"--kv\", type=_choice(\"a memory format\", S.KV_MODES), metavar=\"FORMAT\", "
                "help=\"conversation memory format: int8 (default), q4_0, k8v4, fp16 (Inkling-2-Mini: fp16, fp8, k8v8, k8v4; dense native: auto, f16, spin8_k8v4, f16_turbo2/3/4)\")\n"
                "    g.add_argument(\"--output-language\", choices=(\"ja\", \"model-default\"), help=\"owned dense native output language preference\")\n"
            )
        return up

    return resolve_hunks(merged, h)


def resolve_server_py(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    """Adopt upstream v0.2.21 serve/server.py improvements while keeping fork's memory_harness & deepseek41 hooks."""
    def h(_idx: int, fork: str, _base: str, up: str) -> str:
        if "self.memory_harness" in fork and "self.memory_harness" not in up:
            return up + fork
        if 'self.family == "deepseek41"' in fork and 'self.family == "deepseek41"' not in up:
            return fork + up
        return up

    return resolve_hunks(merged, h)


def resolve_test_tui2_versions(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    """Keep fork's dynamic VERSION-file test assertions."""
    def h(_idx: int, fork: str, _base: str, up: str) -> str:
        if "ROOT / \"VERSION\"" in fork or "strata {product}" in fork:
            return fork
        return up

    return resolve_hunks(merged, h)


def resolve_prefer_upstream(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    """Resolve all diff3 hunks by adopting upstream v0.2.21 while keeping non-conflicting fork code."""
    return resolve_hunks(merged, lambda _i, _f, _b, u: u)


def resolve_keep_fork_version(merged: str, _ours: str, _theirs: str) -> tuple[str, int]:
    """Keep fork version on version-only conflicts; adopt upstream for non-version hunks."""
    def h(_idx: int, fork: str, _base: str, up: str) -> str:
        if "0.8.0" in fork or "0.6.3" in fork or "VERSION" in fork:
            return fork
        return up

    return resolve_hunks(merged, h)


CUSTOM_RESOLVERS: dict[str, Callable[[str, str, str], tuple[str, int]]] = {
    "README.md": resolve_readme,
    "docs/data/release.json": resolve_release_json,
    "engine/metal/CMakeLists.txt": resolve_metal_cmake,
    "engine/src/kernels/cpu/native_expert.cpp": resolve_native_expert,
    "app/host/server/agent/agent-bridge.mjs": resolve_agent_bridge,
    "app/host/server/agent/llm-shape.mjs": resolve_llm_shape,
    "app/host/server/agent/profile.mjs": resolve_profile_mjs,
    "app/host/server/index.mjs": resolve_host_index,
    "app/host/server/native-control.mjs": resolve_native_control,
    "app/host/server/native-gateway.mjs": resolve_native_gateway,
    "app/host/server/run-config-check.mjs": resolve_run_config_check,
    "app/host/server/skill-files.mjs": resolve_skill_files,
    "app/host/src/components/NativeSettings.tsx": resolve_native_settings_tsx,
    "app/host/src/lib/native.ts": resolve_native_ts,
    "app/host/src/lib/store.ts": resolve_store_ts,
    "app/host/src/screens/Chat.tsx": resolve_chat_tsx,
    "app/host/src/screens/Skills.tsx": resolve_prefer_upstream,
    "terminal/serve/frontend.py": resolve_frontend_py,
    "terminal/serve/inkling_kind.py": resolve_inkling_kind_py,
    "terminal/serve/server.py": resolve_server_py,
    "terminal/strata_cli/launch/cmd.py": resolve_launch_cmd_py,
    "terminal/tests/terminal/test_tui2_023_versions.py": resolve_test_tui2_versions,
}


def run_merge(repo: Path, base: str, ours: str, theirs: str, mode: str, manifest_path: Path) -> int:
    base_tree = git_ls_tree(repo, base)
    ours_tree = git_ls_tree(repo, ours)
    theirs_tree = git_ls_tree(repo, theirs)

    all_paths = sorted(set(base_tree) | set(ours_tree) | set(theirs_tree))
    to_process: list[tuple[str, str]] = []
    skipped_counts: dict[str, int] = {}

    for path in all_paths:
        b = base_tree.get(path)
        o = ours_tree.get(path)
        t = theirs_tree.get(path)
        if o == t:
            skipped_counts["identical"] = skipped_counts.get("identical", 0) + 1
        elif b == o:
            if t is None:
                to_process.append((path, "delete_upstream"))
            elif b is None:
                to_process.append((path, "add_upstream"))
            else:
                to_process.append((path, "adopt_upstream"))
        elif b == t:
            skipped_counts["fork_preserved"] = skipped_counts.get("fork_preserved", 0) + 1
        else:
            to_process.append((path, "both_modified"))

    LOGGER.info("Preserved untouched: %s", json.dumps(skipped_counts))
    LOGGER.info("Paths to merge/update: %d", len(to_process))

    reader = BlobReader(repo)
    actions: list[FileAction] = []
    staged: list[tuple[str, bytes]] = []
    errors: list[str] = []

    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            for path, cat in tqdm(to_process, desc="3-way merge", unit="file"):
                try:
                    if cat in ("add_upstream", "adopt_upstream"):
                        data = reader.read(theirs, path)
                        staged.append((path, data))
                        actions.append(FileAction(path, cat, "adopt_upstream", 0, hashlib.sha256(data).hexdigest()))
                        continue

                    if cat == "both_modified":
                        if path in ADOPT_UPSTREAM_PATHS:
                            data = reader.read(theirs, path)
                            staged.append((path, data))
                            actions.append(FileAction(path, cat, "adopt_upstream_override", 0, hashlib.sha256(data).hexdigest()))
                            continue

                        b_bytes = reader.read(base, path)
                        o_bytes = reader.read(ours, path)
                        t_bytes = reader.read(theirs, path)
                        merged_bytes, conflicts = run_merge_file(repo, o_bytes, b_bytes, t_bytes, tmp)
                        if conflicts == 0:
                            staged.append((path, merged_bytes))
                            actions.append(FileAction(path, cat, "clean_3way", 0, hashlib.sha256(merged_bytes).hexdigest()))
                            continue

                        merged_str = merged_bytes.decode("utf-8", errors="replace")
                        ours_str = o_bytes.replace(b"\r\n", b"\n").decode("utf-8", errors="replace")
                        theirs_str = t_bytes.replace(b"\r\n", b"\n").decode("utf-8", errors="replace")

                        if path in CUSTOM_RESOLVERS:
                            resolved_str, hunks = CUSTOM_RESOLVERS[path](merged_str, ours_str, theirs_str)
                            strategy = f"custom_resolver:{CUSTOM_RESOLVERS[path].__name__}"
                        elif path in KEEP_FORK_ON_VERSION_CONFLICT:
                            resolved_str, hunks = resolve_keep_fork_version(merged_str, ours_str, theirs_str)
                            strategy = "keep_fork_version"
                        else:
                            resolved_str, hunks = resolve_prefer_upstream(merged_str, ours_str, theirs_str)
                            strategy = "prefer_upstream_hunks"

                        resolved_bytes = resolved_str.encode("utf-8")
                        staged.append((path, resolved_bytes))
                        actions.append(FileAction(path, cat, strategy, hunks, hashlib.sha256(resolved_bytes).hexdigest()))
                except Exception as exc:
                    LOGGER.error("Failed on %s: %s", path, exc)
                    errors.append(f"{path}: {exc}")
    finally:
        reader.close()

    if errors:
        LOGGER.error("Merge aborted with %d errors", len(errors))
        return 1

    if mode == "apply":
        for path, data in tqdm(staged, desc="writing files", unit="file"):
            dest = repo / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        LOGGER.info("Applied %d files to %s", len(staged), repo)
    else:
        LOGGER.info("Dry-run succeeded cleanly for %d files (0 errors, 0 unresolved markers)", len(staged))

    strategy_counts: dict[str, int] = {}
    for act in actions:
        strategy_counts[act.strategy] = strategy_counts.get(act.strategy, 0) + 1

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "base": base,
        "ours": ours,
        "theirs": theirs,
        "preserved_counts": skipped_counts,
        "strategy_counts": strategy_counts,
        "total_updated": len(actions),
        "actions": [asdict(a) for a in actions],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    LOGGER.info("Strategy summary: %s", json.dumps(strategy_counts, indent=2))
    LOGGER.info("Manifest written to %s", manifest_path)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="C:/Users/downl/Documents/ChatGPT/Strata")
    parser.add_argument("--base", default="v0.2.20")
    parser.add_argument("--ours", default="HEAD")
    parser.add_argument("--theirs", default="upstream/main")
    parser.add_argument("--mode", choices=("dry-run", "apply"), default="dry-run")
    parser.add_argument("--manifest", default="_docs/upstream-intake/merge-0221-manifest.json")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format=LOG_FMT)
    repo = Path(args.repo).resolve()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = repo / manifest_path
    return run_merge(repo, args.base, args.ours, args.theirs, args.mode, manifest_path)


if __name__ == "__main__":
    raise SystemExit(main())
