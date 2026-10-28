#!/usr/bin/env python3
"""Reinject Hakua memory consent into upstream serve/web/app.js after merge."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "serve" / "web" / "app.js"


def main() -> None:
    text = APP.read_text(encoding="utf-8")
    if "let memoryMode = false;" in text:
        print("already patched")
        return

    old = (
        'let settings = {...DEFAULTS, ...store.get("sampling", {})};\n'
        "if (samplingUntouched(settings)) settings.temperature = DEFAULTS.temperature;\n"
        'let messages = store.get("chat", []);   // the open chat\'s messages (chats-ui.js: with the saved-chats list on, also that chat\'s own)\n'
        "let attachments = [];                 // {name, url}\n"
        "let busy = null;                      // {controller, msg, cut, cutAfterTool}\n"
        "let pending = null;                   // a message parked while an answer is written: {text, images, files, mode}\n"
    )
    new = (
        'let settings = {...DEFAULTS, ...store.get("sampling", {})};\n'
        "if (samplingUntouched(settings)) settings.temperature = DEFAULTS.temperature;\n"
        "const transcripts = (globalThis.StrataMemoryChat\n"
        '  ? StrataMemoryChat.createMemoryTranscripts(store.get("chat", []))\n'
        '  : {active:()=>store.get("chat", []), select:()=>store.get("chat", []),'
        ' setKey:()=>store.get("chat", []), replaceActive:(m)=>m});\n'
        "let memoryMode = false;\n"
        "let memoryConsent = null;             // one-shot strata_memory payload for the next generateReply\n"
        "let messages = transcripts.active();\n"
        "let attachments = [];                 // {name, url}\n"
        "let composerVersion = 0;\n"
        "let busy = null;                      // {controller, msg, cut, cutAfterTool}\n"
        "let pending = null;                   // a message parked while an answer is written: {text, images, files, mode}\n"
        "function clearComposerDraft() {\n"
        "  composerVersion++;\n"
        '  $("input").value = "";\n'
        "  attachments = [];\n"
        "  renderAttachments();\n"
        "  autosize();\n"
        "}\n"
        "function switchMemoryMode() {\n"
        "  if (!globalThis.StrataMemoryChat) return;\n"
        '  const selected = $("memory-read").checked || $("memory-store").checked;\n'
        "  if (!selected || memoryMode) return;\n"
        '  if (busy) { toast("warn", "Wait for this answer", "Change memory consent after the turn ends."); return; }\n'
        "  memoryMode = true;\n"
        '  apiKey = "";\n'
        '  $("api-key").value = apiKey;\n'
        "  apiKeyEnteredThisSession = false;\n"
        "  messages = transcripts.select(true);\n"
        "  clearComposerDraft();\n"
        '  $("attach-btn").disabled = $("file").disabled = true;\n'
        '  $("memory-exit").hidden = false;\n'
        "  renderChat();\n"
        "}\n"
        'if ($("memory-read") && $("memory-store")) {\n'
        '  for (const id of ["memory-read", "memory-store"]) $(id).addEventListener("change", switchMemoryMode);\n'
        "}\n"
        'if ($("memory-exit")) $("memory-exit").onclick = () => {\n'
        "  if (busy) return;\n"
        '  $("memory-read").checked = $("memory-store").checked = false;\n'
        "  memoryMode = false;\n"
        '  transcripts.setKey("");\n'
        '  apiKey = store.get("apikey", "");\n'
        '  $("api-key").value = apiKey;\n'
        "  apiKeyEnteredThisSession = false;\n"
        "  messages = transcripts.select(false);\n"
        "  clearComposerDraft();\n"
        '  $("attach-btn").disabled = $("file").disabled = false;\n'
        '  $("memory-exit").hidden = true;\n'
        "  renderChat();\n"
        "};\n"
    )
    if old not in text:
        raise SystemExit("anchor1 missing")
    text = text.replace(old, new, 1)

    old2 = (
        "function setBusy(on) {\n"
        '  $("stop-btn").hidden = !on;\n'
        '  $("send-btn").disabled = (on && !parksWhileBusy()) || !!panel;\n'
        '  $("input").disabled = !!panel;\n'
    )
    new2 = (
        "function setBusy(on) {\n"
        '  $("stop-btn").hidden = !on;\n'
        '  $("send-btn").disabled = (on && !parksWhileBusy()) || !!panel;\n'
        '  if ($("memory-read")) $("memory-read").disabled = on;\n'
        '  if ($("memory-store")) $("memory-store").disabled = on;\n'
        '  if ($("memory-exit")) $("memory-exit").disabled = on;\n'
        '  $("input").disabled = !!panel;\n'
    )
    if old2 not in text:
        raise SystemExit("anchor2 missing")
    text = text.replace(old2, new2, 1)

    anchor = "  if (busy) { park(p, own); return; }\n  clearUndo();"
    inject = (
        "  if (busy) { park(p, own); return; }\n"
        "  memoryConsent = null;\n"
        "  if (memoryMode && globalThis.StrataMemoryChat) {\n"
        "    try {\n"
        "      memoryConsent = StrataMemoryChat.prepareMemoryRequest({}, {\n"
        "        key: apiKey, entered: apiKeyEnteredThisSession, text: p.text,"
        " attachments: [...p.images, ...p.files],\n"
        '        read: $("memory-read").checked, storeSummary: $("memory-store").checked,'
        " crypto: globalThis.crypto,\n"
        "      }).strata_memory;\n"
        '    } catch (error) { toast("warn", "Memory request unavailable", error.message); return; }\n'
        "  }\n"
        "  clearUndo();"
    )
    if anchor not in text:
        raise SystemExit("send busy anchor missing")
    text = text.replace(anchor, inject, 1)

    body_anchor = (
        "  if (settings.mcp !== false && mcpInfo.tools > 0) body.strata_mcp = true;"
        "   // this server may run MCP tools for it\n"
    )
    body_inject = (
        body_anchor
        + "  if (memoryMode && memoryConsent) body.strata_memory = memoryConsent;\n"
        + '  if (memoryMode) { $("memory-read").checked = false; $("memory-store").checked = false; }\n'
        + "  memoryConsent = null;\n"
    )
    if body_anchor not in text:
        raise SystemExit("body mcp anchor missing")
    text = text.replace(body_anchor, body_inject, 1)

    if "function saveChat(" in text and "if (memoryMode) return;" not in text:
        text = text.replace("function saveChat() {\n", "function saveChat() {\n  if (memoryMode) return;\n", 1)

    APP.write_text(text, encoding="utf-8", newline="\n")
    print("patched", APP)
    print("memoryMode count", text.count("memoryMode"))


if __name__ == "__main__":
    main()
