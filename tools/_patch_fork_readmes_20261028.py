#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.2-preview.20261028.1"

FORK_SECTION = f"""

<a id="fork-notes"></a>

## Fork notes

This tree is **zapabob/Strata**, tracking upstream **Niko1221/Strata v0.2.7.1** (`46c152a1`).

Preserved proprietary surfaces: F01–F11 (Spin8 / Query-v3 / TurboQuant / guards / GGUF router), Hakua consented memory chat, harness/run-config keys, Hermes hooks, and Windows full packaging labelled `-hakua`.

App version in this preview tree: `{VERSION}`. Measured Windows preview numbers (when claimed) are only those already recorded under `docs/` / `_docs/` — no new speed claims were invented for this sync.

"""


def ensure_fork_notes(text: str) -> str:
    if "## Fork notes" in text or 'id="fork-notes"' in text:
        return text
    for marker in ("## Support Strata", "## Support", "## License", "## Help"):
        if marker in text:
            return text.replace(marker, FORK_SECTION + marker, 1)
    return text.rstrip() + FORK_SECTION


def patch_en(text: str) -> str:
    if "fork-notes" not in text:
        text = text.replace(
            '<a href="#help">Help</a>',
            '<a href="#fork-notes">Fork notes</a> · <a href="#help">Help</a>',
            1,
        )
    old_badge = (
        '  <a href="https://github.com/Niko1221/Strata/releases/latest">'
        '<img src="https://img.shields.io/github/v/release/Niko1221/Strata?label=download&color=0ab887" '
        'alt="Download Strata"></a>\n'
        '  <a href="LICENSE"><img src="https://img.shields.io/github/license/Niko1221/Strata" alt="MIT license"></a>'
    )
    new_badge = (
        '  <a href="https://github.com/zapabob/Strata/releases/latest">'
        '<img src="https://img.shields.io/github/v/release/zapabob/Strata?label=fork%20release&color=0ab887" '
        'alt="Download this fork"></a>\n'
        '  <a href="https://github.com/Niko1221/Strata/releases/latest">'
        '<img src="https://img.shields.io/github/v/release/Niko1221/Strata?label=upstream&color=555" '
        'alt="Upstream Strata"></a>\n'
        '  <a href="LICENSE"><img src="https://img.shields.io/github/license/Niko1221/Strata" alt="MIT license"></a>'
    )
    if old_badge in text:
        text = text.replace(old_badge, new_badge, 1)
    needle = (
        "**Free, open source, and yours to run.** Use Strata on your desktop or with your favorite coding tools. "
        "No account needed."
    )
    repl = (
        "**Free, open source, and yours to run.** This repository is a fork of "
        "[Niko1221/Strata](https://github.com/Niko1221/Strata) that keeps proprietary Spin(8)/Triality, "
        "Query-v3, TurboQuant, Bonsai, Hakua consented memory chat, Hermes hooks and Windows `-hakua` packaging, "
        "while tracking upstream security and bugfixes. Official model/install/hardware guidance below matches "
        "upstream **v0.2.7.1** (`46c152a1`) after the 2026-10-28 sync. Fork-only notes and measured preview "
        "evidence sit in [Fork notes](#fork-notes)."
    )
    if needle in text:
        text = text.replace(needle, repl, 1)
    text = text.replace(
        "**[Download Strata for Windows, Linux or Mac →](https://github.com/Niko1221/Strata/releases/latest)**",
        "**[Download this fork →](https://github.com/zapabob/Strata/releases/latest)** · "
        "[Upstream releases](https://github.com/Niko1221/Strata/releases/latest)",
        1,
    )
    return ensure_fork_notes(text)


def patch_localized(text: str, intro: str) -> str:
    if "fork-notes" not in text:
        text = text.replace(
            '<a href="#help">',
            '<a href="#fork-notes">Fork notes</a> · <a href="#help">',
            1,
        )
    # Replace first Free/open-source style paragraph if still upstream English, else keep and append notes.
    m = re.search(r"\*\*[^*]+\*\*[^\n]*\n", text)
    if m and "Niko1221/Strata" not in m.group(0) and "zapabob" not in text[m.start() : m.start() + 400]:
        # Prefer replacing the English free line when present.
        en = (
            "**Free, open source, and yours to run.** Use Strata on your desktop or with your favorite coding tools. "
            "No account needed."
        )
        if en in text:
            text = text.replace(en, intro, 1)
        else:
            # Insert intro after language switcher block's first blank line following badges.
            text = text.replace(m.group(0), intro + "\n\n", 1)
    return ensure_fork_notes(text)


def main() -> None:
    en = ROOT / "README.md"
    en.write_text(patch_en(en.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
    print("patched README.md")

    ja_intro = (
        "**無料・オープンソース。** このリポジトリは [Niko1221/Strata](https://github.com/Niko1221/Strata) のフォークです。"
        "Spin(8)/Triality・Query-v3・TurboQuant・Bonsai・Hakua 同意付きメモリチャット・Hermes・Windows `-hakua` を保持しつつ、"
        "上流のセキュリティとバグ修正を追います。下記の公式案内は上流 **v0.2.7.1** (`46c152a1`) 同期後です。"
        "フォーク固有の注記は [Fork notes](#fork-notes) を参照。"
    )
    ja = ROOT / "README.ja.md"
    ja.write_text(patch_localized(ja.read_text(encoding="utf-8"), ja_intro), encoding="utf-8", newline="\n")
    print("patched README.ja.md")

    zh_intro = (
        "**免费、开源。** 本仓库是 [Niko1221/Strata](https://github.com/Niko1221/Strata) 的分支，保留 Spin(8)/Triality、"
        "Query-v3、TurboQuant、Bonsai、Hakua 同意式记忆聊天、Hermes 与 Windows `-hakua` 打包，同时跟进上游安全与缺陷修复。"
        "下方官方说明对应上游 **v0.2.7.1** (`46c152a1`)（2026-10-28 同步）。分支专有说明见 [Fork notes](#fork-notes)。"
    )
    zh = ROOT / "README.zh-CN.md"
    zh.write_text(patch_localized(zh.read_text(encoding="utf-8"), zh_intro), encoding="utf-8", newline="\n")
    print("patched README.zh-CN.md")

    (ROOT / "VERSION").write_text(VERSION + "\n", encoding="utf-8")
    print("VERSION", VERSION)


if __name__ == "__main__":
    main()
