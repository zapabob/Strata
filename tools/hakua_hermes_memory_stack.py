#!/usr/bin/env python3
"""Hakua ↔ Hermes SOUL/MEMORY stack: RAG, semantic graph, Ebbinghaus, Obsidian, sleep.

Source of truth (default): a Hakua principal profile directory that the consented
``hakua_harness`` can also mount (SOUL.md / MEMORY.md / ebbinghaus.db). Hermes
``~/.hermes/SOUL.md`` and ``memories/MEMORY.md`` are adapters that sync into that
profile. Symlinks/hardlinks are never used (memory_harness rejects them).

Environment (no secrets):
  HERMES_HOME              Hermes home (default ~/.hermes)
  HAKUA_MEMORY_HOME        Hakua data root (default ~/.hakua-memory)
  HAKUA_HERMES_PRINCIPAL   Principal folder name (default hermes)
  HAKUA_HERMES_PROFILE     Absolute override for the profile root
  HAKUA_MEMORY_SOT         hakua|hermes  (default hakua) — which side wins on sync
  OBSIDIAN_VAULT_PATH      Obsidian vault root (else open vault / data-dir default)
  HAKUA_OBSIDIAN_VAULT     Alias for OBSIDIAN_VAULT_PATH
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("hakua_hermes_memory_stack")

HOME = Path.home()
REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONA_FILES = ("SOUL.md", "USER.md", "MEMORY.md")
SECTION_SPLIT = re.compile(r"(?m)^(?=§\s*)")


def forgetting_retention_probe(elapsed_days: float, stability_days: float) -> float:
    """Ebbinghaus retention in [0, 1]. Uses hakua_memory when installed."""
    try:
        from hakua_memory.ebbinghaus.store import forgetting_retention

        return float(forgetting_retention(elapsed_days, stability_days))
    except Exception:  # noqa: BLE001
        import math

        if elapsed_days <= 0:
            return 1.0
        return max(0.0, min(1.0, math.exp(-float(elapsed_days) / max(0.01, float(stability_days)))))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return _sha256_bytes(path.read_bytes())


def _plain_copy(src: Path, dst: Path) -> dict[str, Any]:
    """Byte-copy into a dedicated plain file (never a link)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and (dst.is_symlink() or dst.stat().st_nlink > 1):
        dst.unlink()
    shutil.copy2(src, dst)
    # On Windows copy2 may preserve nothing about nlink; re-stat.
    if dst.is_symlink() or (dst.exists() and dst.stat().st_nlink > 1):
        raw = src.read_bytes()
        dst.unlink(missing_ok=True)
        dst.write_bytes(raw)
    return {
        "src": str(src),
        "dst": str(dst),
        "sha256": _sha256_file(dst),
        "bytes": dst.stat().st_size,
    }


def discover_obsidian_vault() -> Path:
    """Resolve vault: env → Obsidian open vault → Hakua data-dir default."""
    for key in ("OBSIDIAN_VAULT_PATH", "HAKUA_OBSIDIAN_VAULT"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser().resolve()
    obsidian_json = Path(os.environ.get("APPDATA", "")) / "obsidian" / "obsidian.json"
    if obsidian_json.is_file():
        try:
            data = json.loads(obsidian_json.read_text(encoding="utf-8"))
            vaults = data.get("vaults") or {}
            open_path = None
            newest = None
            newest_ts = -1
            for meta in vaults.values():
                if not isinstance(meta, dict):
                    continue
                path = meta.get("path")
                if not path:
                    continue
                if meta.get("open"):
                    open_path = path
                ts = int(meta.get("ts") or 0)
                if ts >= newest_ts:
                    newest_ts = ts
                    newest = path
            chosen = open_path or newest
            if chosen:
                return Path(chosen).expanduser().resolve()
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.warning("Could not parse Obsidian vaults: %s", exc)
    for candidate in (
        HOME / "Documents" / "ObsidianVault",
        HOME / "Documents" / "Obsidian Vault",
        HOME / "Documents" / "Obsidian",
    ):
        if candidate.is_dir():
            return candidate.resolve()
    root = Path(os.environ.get("HAKUA_MEMORY_HOME") or (HOME / ".hakua-memory"))
    return (root / "obsidian-vault").resolve()


@dataclass(frozen=True)
class StackPaths:
    hermes_home: Path
    hakua_home: Path
    profile_root: Path
    principal: str
    sot: str
    hermes_soul: Path
    hermes_memory: Path
    profile_soul: Path
    profile_memory: Path
    profile_user: Path
    obsidian_vault: Path
    obsidian_hakua: Path

    @classmethod
    def resolve(cls) -> "StackPaths":
        hermes_home = Path(os.environ.get("HERMES_HOME") or (HOME / ".hermes")).expanduser().resolve()
        hakua_home = Path(os.environ.get("HAKUA_MEMORY_HOME") or (HOME / ".hakua-memory")).expanduser().resolve()
        principal = os.environ.get("HAKUA_HERMES_PRINCIPAL", "hermes").strip() or "hermes"
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", principal):
            raise ValueError("HAKUA_HERMES_PRINCIPAL must match [A-Za-z0-9_-]{1,64}")
        override = os.environ.get("HAKUA_HERMES_PROFILE", "").strip()
        profile_root = (
            Path(override).expanduser().resolve()
            if override
            else (hakua_home / "profiles" / principal).resolve()
        )
        sot = (os.environ.get("HAKUA_MEMORY_SOT") or "hakua").strip().lower()
        if sot not in {"hakua", "hermes"}:
            raise ValueError("HAKUA_MEMORY_SOT must be 'hakua' or 'hermes'")
        hermes_soul = hermes_home / "SOUL.md"
        hermes_memory = hermes_home / "memories" / "MEMORY.md"
        if not hermes_memory.exists() and (hermes_home / "MEMORY.md").exists():
            hermes_memory = hermes_home / "MEMORY.md"
        vault = discover_obsidian_vault()
        return cls(
            hermes_home=hermes_home,
            hakua_home=hakua_home,
            profile_root=profile_root,
            principal=principal,
            sot=sot,
            hermes_soul=hermes_soul,
            hermes_memory=hermes_memory,
            profile_soul=profile_root / "SOUL.md",
            profile_memory=profile_root / "MEMORY.md",
            profile_user=profile_root / "USER.md",
            obsidian_vault=vault,
            obsidian_hakua=vault / "Hakua",
        )


class HakuaHermesMemoryStack:
    """Vertical slice: Hermes persona files + Hakua composite + Obsidian + sleep."""

    def __init__(self, paths: StackPaths | None = None) -> None:
        self.paths = paths or StackPaths.resolve()
        self.paths.profile_root.mkdir(parents=True, exist_ok=True)
        self.composite: Any = None
        self._init_composite()

    def _init_composite(self) -> None:
        try:
            from hakua_memory.composite import CompositeMemory

            self.composite = CompositeMemory(self.paths.profile_root, enable_rag=True)
            logger.info("CompositeMemory at %s", self.paths.profile_root)
        except Exception as exc:  # noqa: BLE001 - optional local package
            logger.warning("CompositeMemory unavailable: %s", exc)
            self.composite = None

    # ── Persona sync (Hermes ↔ Hakua profile) ─────────────────────────

    def sync_persona(self, *, direction: str | None = None) -> dict[str, Any]:
        """Sync SOUL.md / MEMORY.md between Hermes and the Hakua profile.

        direction: 'to_hakua' | 'to_hermes' | None (use SOT policy).
        """
        sot = self.paths.sot
        if direction is None:
            direction = "to_hakua" if sot == "hakua" else "to_hermes"
        if direction not in {"to_hakua", "to_hermes"}:
            raise ValueError("direction must be to_hakua or to_hermes")

        pairs = [
            ("SOUL.md", self.paths.hermes_soul, self.paths.profile_soul),
            ("MEMORY.md", self.paths.hermes_memory, self.paths.profile_memory),
        ]
        copied: list[dict[str, Any]] = []
        skipped: list[dict[str, Any]] = []
        for name, hermes_path, profile_path in pairs:
            src, dst = (hermes_path, profile_path) if direction == "to_hakua" else (profile_path, hermes_path)
            if not src.is_file():
                skipped.append({"file": name, "reason": "missing_src", "src": str(src)})
                continue
            if dst.is_file() and _sha256_file(src) == _sha256_file(dst):
                skipped.append({"file": name, "reason": "identical", "sha256": _sha256_file(src)})
                continue
            if direction == "to_hermes":
                dst.parent.mkdir(parents=True, exist_ok=True)
            copied.append({"file": name, **_plain_copy(src, dst)})
        return {
            "direction": direction,
            "sot": sot,
            "profile_root": str(self.paths.profile_root),
            "copied": copied,
            "skipped": skipped,
            "persona_sha256": self.persona_sha256(),
            "at": _utc_now(),
        }

    def persona_sha256(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for name in PERSONA_FILES:
            digest = _sha256_file(self.paths.profile_root / name)
            if digest:
                out[name] = digest
        return out

    def harness_user_snippet(self, *, key_env: str = "HAKUA_HERMES_KEY") -> dict[str, Any]:
        """Operator-owned hakua_harness user object (keys stay in env)."""
        approvals = self.persona_sha256()
        user: dict[str, Any] = {
            "principal": self.paths.principal,
            "key_env": key_env,
            "root": str(self.paths.profile_root),
        }
        if approvals:
            user["persona_sha256"] = approvals
        return user

    def read_soul(self) -> dict[str, Any]:
        # Prefer profile (SOT=hakua) else Hermes
        for path in (self.paths.profile_soul, self.paths.hermes_soul):
            if path.is_file():
                content = path.read_text(encoding="utf-8")
                return {
                    "exists": True,
                    "path": str(path),
                    "content": content,
                    "sha256": _sha256_bytes(content.encode("utf-8")),
                    "size_bytes": len(content.encode("utf-8")),
                }
        return {"exists": False, "path": str(self.paths.profile_soul), "content": ""}

    def read_memory_md(self, *, limit: int = 50, filter_keyword: str = "") -> dict[str, Any]:
        path = self.paths.profile_memory if self.paths.profile_memory.is_file() else self.paths.hermes_memory
        if not path.is_file():
            return {"exists": False, "path": str(path), "sections": [], "count": 0}
        raw = path.read_text(encoding="utf-8")
        sections: list[dict[str, str]] = []
        for sec in SECTION_SPLIT.split(raw):
            sec = sec.strip()
            if not sec or not sec.startswith("§"):
                continue
            first, _, body = sec.partition("\n")
            header = first.lstrip("§").strip()
            body_clean = body.strip()
            if filter_keyword and filter_keyword.lower() not in sec.lower():
                continue
            sections.append({"header": header, "body": body_clean, "raw": sec})
            if len(sections) >= limit:
                break
        return {"exists": True, "path": str(path), "sections": sections, "count": len(sections)}

    def append_memory_md(self, title: str, content: str, category: str = "core") -> dict[str, Any]:
        """Append to profile MEMORY.md (SOT) then optionally mirror to Hermes."""
        path = self.paths.profile_memory
        path.parent.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        entry = f"\n\n§ [{category}] {date_str}: {title}\n{content.strip()}\n"
        if not path.exists():
            path.write_text(f"# Long-Term Working Memory\n{entry}", encoding="utf-8")
        else:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(entry)
        mirror = None
        if self.paths.sot == "hakua":
            mirror = _plain_copy(path, self.paths.hermes_memory)
        return {
            "appended": True,
            "path": str(path),
            "category": category,
            "title": title,
            "date": date_str,
            "hermes_mirror": mirror,
            "persona_sha256": self.persona_sha256(),
        }

    # ── Graph / RAG / Ebbinghaus ──────────────────────────────────────

    def remember(
        self,
        content: str,
        *,
        importance: float = 0.7,
        tags: list[str] | None = None,
        link_graph: bool = True,
    ) -> dict[str, Any]:
        tags = tags or ["hakua", "hermes"]
        if self.composite is None:
            return {"saved": False, "error": "hakua_memory CompositeMemory not available"}
        result = self.composite.remember(
            content,
            tags=tags,
            salience=float(importance),
            source="hakua_hermes_memory_stack",
        )
        graph = None
        if link_graph:
            node_id = f"mem-{result.get('memory_id', hashlib.sha1(content.encode()).hexdigest()[:12])}"
            graph = self.composite.add_node(
                {
                    "node_id": node_id,
                    "node_type": "Memory",
                    "label": (content.strip().splitlines() or ["memory"])[0][:80],
                    "summary": content.strip()[:2000],
                    "status": "asserted",
                    "authority": "hermes",
                    "confidence": float(importance),
                    "salience": float(importance),
                    "evidence": [],
                }
            )
        return {"saved": True, "ebbinghaus": result, "graph": graph, "tags": tags}

    def recall(self, query: str, *, top_k: int = 5) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        if self.composite is not None:
            try:
                for hit in self.composite.recall(query, top_k=top_k):
                    results.append({"source": "ebbinghaus", "content": hit.get("content", str(hit)), "score": float(hit.get("score", hit.get("retention", 0.5))), "metadata": hit})
            except Exception as exc:  # noqa: BLE001
                logger.warning("Ebbinghaus recall failed: %s", exc)
            try:
                for hit in self.composite.search(query, top_k=top_k):
                    results.append({"source": "semantic_graph", "content": hit.get("summary") or hit.get("label") or str(hit), "score": float(hit.get("score", 0.5)), "metadata": hit})
            except Exception as exc:  # noqa: BLE001
                logger.warning("Graph search failed: %s", exc)
            try:
                for hit in self.composite.search_documents(query, top_k=top_k):
                    results.append({"source": "rag", "content": hit.get("text") or hit.get("content") or str(hit), "score": float(hit.get("score", 0.4)), "metadata": hit})
            except Exception as exc:  # noqa: BLE001
                logger.warning("RAG search failed: %s", exc)

        mem = self.read_memory_md(limit=40)
        q = query.lower()
        for sec in mem.get("sections", []):
            blob = f"{sec['header']}\n{sec['body']}".lower()
            overlap = sum(1 for w in q.split() if len(w) >= 2 and w in blob)
            if overlap:
                results.append({"source": "memory_md", "content": f"[{sec['header']}]\n{sec['body']}", "score": min(0.95, 0.35 + 0.12 * overlap), "metadata": {"header": sec["header"]}})

        results.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in results:
            key = " ".join(str(item.get("content", "")).split())[:180]
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= top_k:
                break
        return {"query": query, "top_k": top_k, "count": len(deduped), "results": deduped}

    def reindex_from_persona(self) -> dict[str, Any]:
        """Push SOUL/MEMORY into RAG + graph nodes (idempotent-ish by path title)."""
        if self.composite is None:
            return {"ok": False, "error": "CompositeMemory unavailable"}
        out: dict[str, Any] = {"rag": [], "graph": []}
        soul = self.read_soul()
        if soul.get("exists"):
            out["rag"].append(self.composite.ingest_markdown(soul["content"], title="SOUL.md", source_uri="persona://SOUL.md"))
            out["graph"].append(
                self.composite.add_node(
                    {
                        "node_id": "persona-soul",
                        "node_type": "Persona",
                        "label": "SOUL.md",
                        "summary": soul["content"][:4000],
                        "status": "asserted",
                        "authority": "operator",
                        "confidence": 1.0,
                        "salience": 1.0,
                        "evidence": [],
                    }
                )
            )
        mem_path = self.paths.profile_memory if self.paths.profile_memory.is_file() else self.paths.hermes_memory
        if mem_path.is_file():
            text = mem_path.read_text(encoding="utf-8")
            out["rag"].append(self.composite.ingest_markdown(text, title="MEMORY.md", source_uri="persona://MEMORY.md"))
            for idx, sec in enumerate(self.read_memory_md(limit=32).get("sections", [])):
                out["graph"].append(
                    self.composite.add_node(
                        {
                            "node_id": f"memory-md-{idx}",
                            "node_type": "Episode",
                            "label": (sec.get("header") or f"section-{idx}")[:80],
                            "summary": (sec.get("body") or "")[:2000],
                            "status": "asserted",
                            "authority": "hermes",
                            "confidence": 0.7,
                            "salience": 0.65,
                            "evidence": [],
                        }
                    )
                )
        return {"ok": True, **out, "at": _utc_now()}

    # ── Obsidian ──────────────────────────────────────────────────────

    def sync_obsidian(self, *, export: bool = True, import_memory: bool = True) -> dict[str, Any]:
        vault = self.paths.obsidian_vault
        hakua_dir = self.paths.obsidian_hakua
        hakua_dir.mkdir(parents=True, exist_ok=True)
        actions: list[dict[str, Any]] = []

        if export:
            soul = self.read_soul()
            if soul.get("exists"):
                target = hakua_dir / "SOUL.md"
                target.write_text(soul["content"], encoding="utf-8")
                actions.append({"action": "export", "path": str(target)})
            mem = self.paths.profile_memory if self.paths.profile_memory.is_file() else self.paths.hermes_memory
            if mem.is_file():
                target = hakua_dir / "MEMORY.md"
                shutil.copy2(mem, target)
                actions.append({"action": "export", "path": str(target), "sha256": _sha256_file(target)})
            if self.composite is not None:
                try:
                    from hakua_memory.obsidian import write_diary, write_dream

                    stats = self.composite.stats()
                    diary = write_diary(
                        hakua_dir,
                        f"sleep-status-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
                        "```json\n" + json.dumps(stats, ensure_ascii=False, indent=2) + "\n```\n",
                    )
                    actions.append({"action": "export_diary", "path": str(diary)})
                    dream = write_dream(hakua_dir, f"Hakua sleep snapshot at {_utc_now()}\n\nPrincipal: `{self.paths.principal}`\n")
                    actions.append({"action": "export_dream", "path": str(dream)})
                except Exception as exc:  # noqa: BLE001
                    actions.append({"action": "export_wiki_error", "error": str(exc)})

        if import_memory:
            vault_memory = hakua_dir / "MEMORY.md"
            # Prefer vault note only when operator edits Obsidian as upstream of Hermes SOT=hermes
            # or when profile MEMORY is missing.
            if vault_memory.is_file() and (
                self.paths.sot == "hermes" or not self.paths.profile_memory.is_file()
            ):
                actions.append({"action": "import", **_plain_copy(vault_memory, self.paths.profile_memory)})
                if self.paths.sot == "hakua":
                    actions.append({"action": "mirror_hermes", **_plain_copy(self.paths.profile_memory, self.paths.hermes_memory)})

        return {
            "vault": str(vault),
            "hakua_dir": str(hakua_dir),
            "actions": actions,
            "at": _utc_now(),
        }

    # ── Sleep / consolidate ───────────────────────────────────────────

    def sleep(self, *, prune: bool = True, reindex: bool = True, sync_obsidian: bool = True) -> dict[str, Any]:
        """Full consolidation cycle: persona sync → reindex → Ebbinghaus sleep → Obsidian flush."""
        report: dict[str, Any] = {
            "mode": "hakua_sleep",
            "started_at": _utc_now(),
            "profile_root": str(self.paths.profile_root),
            "principal": self.paths.principal,
        }
        # Align adapters before consolidation.
        if self.paths.sot == "hakua" and self.paths.hermes_soul.is_file() and not self.paths.profile_soul.is_file():
            report["bootstrap_sync"] = self.sync_persona(direction="to_hakua")
        elif self.paths.sot == "hermes":
            report["bootstrap_sync"] = self.sync_persona(direction="to_hakua")
        else:
            # Keep Hermes mirror fresh from profile SOT without clobbering newer Hermes-only edits
            # when hashes already match; still push profile → Hermes for MEMORY when profile exists.
            report["bootstrap_sync"] = self.sync_persona(direction="to_hermes") if self.paths.profile_soul.is_file() else self.sync_persona(direction="to_hakua")

        if reindex:
            report["reindex"] = self.reindex_from_persona()

        if self.composite is None:
            report["ebbinghaus_sleep"] = {"error": "CompositeMemory unavailable"}
        else:
            try:
                report["ebbinghaus_sleep"] = self.composite.sleep(prune=prune)
            except TypeError:
                report["ebbinghaus_sleep"] = self.composite.sleep()
            except Exception as exc:  # noqa: BLE001
                report["ebbinghaus_sleep"] = {"error": str(exc)}
            try:
                report["stats"] = self.composite.stats()
            except Exception as exc:  # noqa: BLE001
                report["stats"] = {"error": str(exc)}

        if sync_obsidian:
            report["obsidian"] = self.sync_obsidian(export=True, import_memory=False)

        report["persona_sha256"] = self.persona_sha256()
        report["harness_user"] = self.harness_user_snippet()
        report["finished_at"] = _utc_now()
        return report

    def status(self) -> dict[str, Any]:
        composite_stats: dict[str, Any] = {}
        if self.composite is not None:
            try:
                composite_stats = self.composite.stats()
            except Exception as exc:  # noqa: BLE001
                composite_stats = {"error": str(exc)}
        return {
            "status": "healthy",
            "timestamp": _utc_now(),
            "paths": {
                "hermes_home": str(self.paths.hermes_home),
                "hakua_home": str(self.paths.hakua_home),
                "profile_root": str(self.paths.profile_root),
                "principal": self.paths.principal,
                "sot": self.paths.sot,
                "hermes_soul": str(self.paths.hermes_soul),
                "hermes_memory": str(self.paths.hermes_memory),
                "obsidian_vault": str(self.paths.obsidian_vault),
            },
            "persona_sha256": self.persona_sha256(),
            "soul_exists": self.paths.profile_soul.is_file() or self.paths.hermes_soul.is_file(),
            "memory_exists": self.paths.profile_memory.is_file() or self.paths.hermes_memory.is_file(),
            "composite": {"enabled": self.composite is not None, "stats": composite_stats},
            "harness_user": self.harness_user_snippet(),
        }

    def close(self) -> None:
        if self.composite is not None:
            try:
                self.composite.close()
            except Exception:  # noqa: BLE001
                pass
            self.composite = None


def _configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    parser = argparse.ArgumentParser(description="Hakua↔Hermes memory stack (RAG/graph/Ebbinghaus/Obsidian/sleep)")
    parser.add_argument(
        "command",
        choices=["status", "sync", "sleep", "recall", "remember", "obsidian", "harness-snippet", "reindex"],
        help="Action to run",
    )
    parser.add_argument("--direction", choices=["to_hakua", "to_hermes"], default=None)
    parser.add_argument("--query", default="")
    parser.add_argument("--content", default="")
    parser.add_argument("--tags", default="hakua,hermes")
    parser.add_argument("--importance", type=float, default=0.7)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-prune", action="store_true")
    parser.add_argument("--no-reindex", action="store_true")
    parser.add_argument("--no-obsidian", action="store_true")
    args = parser.parse_args(argv)

    stack = HakuaHermesMemoryStack()
    try:
        if args.command == "status":
            result: Any = stack.status()
        elif args.command == "sync":
            result = stack.sync_persona(direction=args.direction)
        elif args.command == "sleep":
            result = stack.sleep(
                prune=not args.no_prune,
                reindex=not args.no_reindex,
                sync_obsidian=not args.no_obsidian,
            )
        elif args.command == "recall":
            result = stack.recall(args.query, top_k=args.top_k)
        elif args.command == "remember":
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]
            result = stack.remember(args.content, importance=args.importance, tags=tags)
        elif args.command == "obsidian":
            result = stack.sync_obsidian()
        elif args.command == "harness-snippet":
            result = {"hakua_harness": {"enabled": False, "users": [stack.harness_user_snippet()]}}
        elif args.command == "reindex":
            result = stack.reindex_from_persona()
        else:
            raise ValueError(args.command)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        stack.close()


if __name__ == "__main__":
    raise SystemExit(main())
