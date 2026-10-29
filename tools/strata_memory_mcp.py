#!/usr/bin/env python3
"""tools/strata_memory_mcp.py - Hermes Agent + hakua_memory + SOUL.md / Memory.md bridge & MCP server.

Provides:
1. Unified access to SOUL.md and Memory.md (MEMORY.md) across the Strata workspace and ~/.hermes.
2. Composite long-term memory backed by both hakua_memory (~/.hakua-memory) and Hermes Agent's
   Ebbinghaus SQLite store (~/.hermes/ebbinghaus_memory.db).
3. Both a CLI JSON interface (`--cli <action>`) for the Strata Node Host and a standard MCP
   (JSON-RPC 2.0 over stdio) server for Strata's MCP client (`serve/mcp.py`) and Agent Harness.
4. Delegates stack operations (RAG / semantic graph / Obsidian / sleep) to
   ``tools/hakua_hermes_memory_stack.py`` when available.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import math
import os
import re
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("strata_memory")

PROTOCOL = "2025-06-18"
PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
VERSION = "0.3.1"

REPO_ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home()
HERMES_DIR = Path(os.environ.get("HERMES_HOME") or (HOME / ".hermes"))
HAKUA_MEM_DIR = Path(os.environ.get("HAKUA_MEMORY_HOME") or (HOME / ".hakua-memory"))
HAKUA_SRC_DIR = HOME / "Documents" / "New project" / "hakua-memory" / "src"

if HAKUA_SRC_DIR.exists() and str(HAKUA_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(HAKUA_SRC_DIR))
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

try:
    from hakua_hermes_memory_stack import HakuaHermesMemoryStack
except Exception:  # noqa: BLE001 - stack is optional at import time
    HakuaHermesMemoryStack = None  # type: ignore[misc, assignment]


def _configure_logging() -> None:
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)


class StrataUnifiedMemory:
    """Unified bridge orchestrating Hermes agent files, SQLite, and hakua-memory."""

    def __init__(self) -> None:
        _configure_logging()
        self.hermes_dir = HERMES_DIR
        self.hakua_mem_dir = HAKUA_MEM_DIR
        self.hakua_mem_dir.mkdir(parents=True, exist_ok=True)
        self.composite: Any = None
        self.stack: Any = None
        if HakuaHermesMemoryStack is not None:
            try:
                self.stack = HakuaHermesMemoryStack()
                # Prefer the consented Hakua principal profile as Composite root.
                self.composite = self.stack.composite
                logger.info("Bound HakuaHermesMemoryStack profile=%s", self.stack.paths.profile_root)
            except Exception as exc:  # noqa: BLE001
                logger.warning("HakuaHermesMemoryStack init failed: %s", exc)
                self.stack = None
        if self.composite is None:
            self._init_composite()

    def _init_composite(self) -> None:
        try:
            from hakua_memory.composite import CompositeMemory
            self.composite = CompositeMemory(self.hakua_mem_dir, enable_rag=True)
            logger.info("Initialized hakua_memory CompositeMemory at %s", self.hakua_mem_dir)
        except Exception as exc:
            logger.warning("Could not initialize hakua_memory CompositeMemory: %s", exc)
            self.composite = None

    def get_soul_path(self) -> Path:
        if self.stack is not None:
            profile = self.stack.paths.profile_soul
            if profile.exists():
                return profile
            hermes = self.stack.paths.hermes_soul
            if hermes.exists():
                return hermes
        primary = self.hermes_dir / "SOUL.md"
        if primary.exists():
            return primary
        workspace = REPO_ROOT / "SOUL.md"
        if workspace.exists():
            return workspace
        return primary

    def get_memory_md_path(self) -> Path:
        if self.stack is not None:
            profile = self.stack.paths.profile_memory
            if profile.exists():
                return profile
            hermes = self.stack.paths.hermes_memory
            if hermes.exists():
                return hermes
        primary = self.hermes_dir / "memories" / "MEMORY.md"
        if primary.exists():
            return primary
        secondary = self.hermes_dir / "MEMORY.md"
        if secondary.exists():
            return secondary
        workspace = REPO_ROOT / "Memory.md"
        if workspace.exists():
            return workspace
        return primary

    def get_hermes_db_path(self) -> Path:
        return self.hermes_dir / "ebbinghaus_memory.db"

    def status(self) -> dict[str, Any]:
        """Return full health and statistics of all memory subsystems."""
        stack_status = self.stack.status() if self.stack is not None else None
        soul_p = self.get_soul_path()
        soul_info = {
            "path": str(soul_p),
            "exists": soul_p.exists(),
            "size_bytes": soul_p.stat().st_size if soul_p.exists() else 0,
            "modified_at": datetime.fromtimestamp(soul_p.stat().st_mtime, tz=timezone.utc).isoformat() if soul_p.exists() else None,
        }

        mem_p = self.get_memory_md_path()
        mem_info = {
            "path": str(mem_p),
            "exists": mem_p.exists(),
            "size_bytes": mem_p.stat().st_size if mem_p.exists() else 0,
            "modified_at": datetime.fromtimestamp(mem_p.stat().st_mtime, tz=timezone.utc).isoformat() if mem_p.exists() else None,
            "section_count": 0,
        }
        if mem_p.exists():
            try:
                content = mem_p.read_text(encoding="utf-8")
                mem_info["section_count"] = len(re.findall(r"^§\s+", content, re.MULTILINE))
            except Exception as exc:
                logger.warning("Error reading %s: %s", mem_p, exc)

        hermes_db = self.get_hermes_db_path()
        hermes_info = {
            "path": str(hermes_db),
            "exists": hermes_db.exists(),
            "size_bytes": hermes_db.stat().st_size if hermes_db.exists() else 0,
            "active_memories": 0,
            "total_memories": 0,
            "avg_strength": 0.0,
        }
        if hermes_db.exists():
            try:
                conn = sqlite3.connect(str(hermes_db))
                cur = conn.cursor()
                row = cur.execute("SELECT COUNT(*), AVG(strength) FROM memories").fetchone()
                if row:
                    hermes_info["total_memories"] = row[0] or 0
                    hermes_info["avg_strength"] = round(float(row[1] or 0.0), 3)
                act_row = cur.execute("SELECT COUNT(*) FROM memories WHERE state = 'active'").fetchone()
                if act_row:
                    hermes_info["active_memories"] = act_row[0] or 0
                conn.close()
            except Exception as exc:
                logger.warning("Error inspecting Hermes DB %s: %s", hermes_db, exc)

        composite_info: dict[str, Any] = {
            "enabled": self.composite is not None,
            "root": str(self.hakua_mem_dir),
            "stats": {},
        }
        if self.composite:
            try:
                composite_info["stats"] = self.composite.stats()
            except Exception as exc:
                composite_info["stats"] = {"error": str(exc)}

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "soul": soul_info,
            "memory_md": mem_info,
            "hermes_ebbinghaus": hermes_info,
            "hakua_composite": composite_info,
            "hakua_hermes_stack": stack_status,
        }

    def read_soul(self) -> dict[str, Any]:
        """Read active SOUL.md content and metadata."""
        p = self.get_soul_path()
        if not p.exists():
            return {"exists": False, "path": str(p), "content": ""}
        content = p.read_text(encoding="utf-8")
        return {
            "exists": True,
            "path": str(p),
            "size_bytes": len(content.encode("utf-8")),
            "content": content,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }

    def update_soul(self, content: str) -> dict[str, Any]:
        """Safely update SOUL.md with automatic timestamped backup."""
        p = self.get_soul_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists():
            bak_path = p.with_suffix(f".bak.{int(time.time())}")
            shutil.copy2(p, bak_path)
            logger.info("Created SOUL.md backup at %s", bak_path)
        p.write_text(content, encoding="utf-8")
        logger.info("Updated SOUL.md at %s (%d bytes)", p, len(content.encode("utf-8")))
        return {
            "updated": True,
            "path": str(p),
            "size_bytes": len(content.encode("utf-8")),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }

    def read_memory_md(self, limit: int = 50, filter_keyword: str = "") -> dict[str, Any]:
        """Read structured sections from MEMORY.md."""
        p = self.get_memory_md_path()
        if not p.exists():
            return {"exists": False, "path": str(p), "sections": []}
        raw_text = p.read_text(encoding="utf-8")
        raw_sections = re.split(r"(?m)^(?=§\s*)", raw_text)
        parsed = []
        for sec in raw_sections:
            sec = sec.strip()
            if not sec or not sec.startswith("§"):
                continue
            first_line, _, body = sec.partition("\n")
            header = first_line.lstrip("§").strip()
            body_clean = body.strip()
            if not header and body_clean:
                first_body_line = body_clean.split("\n")[0].strip()
                header = first_body_line[:60] + ("..." if len(first_body_line) > 60 else "")
            if filter_keyword and (filter_keyword.lower() not in sec.lower()):
                continue
            parsed.append({
                "header": header,
                "body": body_clean,
                "raw": sec,
            })
            if len(parsed) >= limit:
                break
        return {
            "exists": True,
            "path": str(p),
            "count": len(parsed),
            "sections": parsed,
        }

    def append_memory_md(self, title: str, content: str, category: str = "core") -> dict[str, Any]:
        """Append a new structured § section to MEMORY.md."""
        p = self.get_memory_md_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        new_entry = f"\n\n§ [{category}] {date_str}: {title}\n{content.strip()}\n"
        if not p.exists():
            p.write_text(f"# Long-Term Working Memory\n{new_entry}", encoding="utf-8")
        else:
            with p.open("a", encoding="utf-8") as f:
                f.write(new_entry)
        logger.info("Appended section to %s: [%s] %s", p, category, title)
        return {
            "appended": True,
            "path": str(p),
            "category": category,
            "title": title,
            "date": date_str,
        }

    def recall(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Multi-stage recall across hakua_memory, Hermes Ebbinghaus DB, and MEMORY.md."""
        results: list[dict[str, Any]] = []

        # 1. Hakua composite memory
        if self.composite:
            try:
                c_hits = self.composite.recall(query, top_k=top_k)
                for h in c_hits:
                    results.append({
                        "source": "hakua_composite",
                        "content": h.get("content", str(h)),
                        "score": float(h.get("score", 0.8)),
                        "metadata": h,
                    })
            except Exception as exc:
                logger.warning("Composite recall error: %s", exc)

        # 2. Hermes SQLite direct search
        hermes_db = self.get_hermes_db_path()
        if hermes_db.exists():
            try:
                conn = sqlite3.connect(str(hermes_db))
                cur = conn.cursor()
                # Split by space, punctuation, or CJK boundary
                raw_words = re.findall(r"[\w\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]+", query)
                keywords = [w.strip() for w in raw_words if len(w.strip()) >= 2]
                if not keywords and raw_words:
                    keywords = raw_words  # fallback even for 1-char CJK
                if keywords:
                    clauses = " OR ".join(["content LIKE ? OR cues LIKE ? OR tags LIKE ?"] * len(keywords))
                    params: list[str] = []
                    for kw in keywords:
                        pat = f"%{kw}%"
                        params.extend([pat, pat, pat])
                    query_sql = f"""
                        SELECT memory_id, content, strength, salience, retrieval_count, created_at, tags
                        FROM memories
                        WHERE state = 'active' AND ({clauses})
                        ORDER BY created_at DESC, (strength * salience) DESC
                        LIMIT ?
                    """
                    params.append(str(max(50, top_k * 10)))
                    rows = cur.execute(query_sql, params).fetchall()
                    for r in rows:
                        mem_id, content, strength, salience, ret_cnt, cr_at, tags = r
                        base_score = float(strength * salience)
                        # Boost exact tag match or recent creation
                        if any(kw.lower() in (tags or "").lower() for kw in keywords):
                            base_score += 5.0
                        if any(kw.lower() in content.lower() for kw in keywords):
                            base_score += 2.0
                        results.append({
                            "source": "hermes_ebbinghaus",
                            "memory_id": mem_id,
                            "content": content,
                            "score": round(base_score, 3),
                            "metadata": {
                                "strength": strength,
                                "salience": salience,
                                "retrieval_count": ret_cnt,
                                "created_at": cr_at,
                                "tags": tags,
                            },
                        })
                conn.close()
            except Exception as exc:
                logger.warning("Hermes DB query error: %s", exc)

        # 3. MEMORY.md keyword search
        mem_res = self.read_memory_md(limit=50)
        q_lower = query.lower()
        for sec in mem_res.get("sections", []):
            text = f"{sec['header']}\n{sec['body']}".lower()
            overlap = sum(1 for w in query.lower().split() if w in text)
            if overlap > 0:
                score = min(0.95, 0.4 + (overlap * 0.15))
                results.append({
                    "source": "memory_md",
                    "content": f"[{sec['header']}]\n{sec['body']}",
                    "score": round(score, 3),
                    "metadata": {"header": sec["header"]},
                })

        # Deduplicate & rank
        seen_texts: set[str] = set()
        unique_results: list[dict[str, Any]] = []
        # Sort by score descending
        results.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        for r in results:
            content_norm = " ".join(r["content"].split())[:200]
            if content_norm in seen_texts:
                continue
            seen_texts.add(content_norm)
            unique_results.append(r)
            if len(unique_results) >= top_k:
                break

        return {
            "query": query,
            "top_k": top_k,
            "count": len(unique_results),
            "results": unique_results,
        }

    def remember(
        self,
        content: str,
        importance: float = 0.7,
        tags: list[str] | None = None,
        sync_hermes: bool = True,
    ) -> dict[str, Any]:
        """Store a new memory across CompositeMemory and Hermes SQLite."""
        tags = tags or ["strata", "agent"]
        record_id = None
        composite_res = None
        tag_str = ",".join(tags)
        stack_res = None

        if self.stack is not None:
            try:
                stack_res = self.stack.remember(content, importance=importance, tags=tags)
                composite_res = stack_res.get("ebbinghaus")
            except Exception as exc:
                logger.warning("Stack remember error: %s", exc)

        # Store in CompositeMemory
        if composite_res is None and self.composite:
            try:
                composite_res = self.composite.remember(content, tags=tags, salience=importance)
                logger.info("Recorded to hakua CompositeMemory: %s", composite_res)
            except Exception as exc:
                logger.warning("Composite remember error: %s", exc)

        # Store in Hermes Ebbinghaus DB
        hermes_db = self.get_hermes_db_path()
        if sync_hermes and hermes_db.exists():
            try:
                conn = sqlite3.connect(str(hermes_db))
                cur = conn.cursor()
                now = time.time()
                cur.execute(
                    """
                    INSERT OR REPLACE INTO memories (
                        content, encoded, cues, tags, salience, valence, strength,
                        rehearsal_count, retrieval_count, source, session_id,
                        created_at, updated_at, state
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        content.strip(),
                        content.strip(),
                        " ".join(tags),
                        tag_str,
                        float(importance),
                        0.0,
                        1.0,
                        0,
                        0,
                        "strata_memory_mcp",
                        f"strata-{int(now)}",
                        now,
                        now,
                        "active",
                    ),
                )
                record_id = cur.lastrowid
                conn.commit()
                conn.close()
                logger.info("Stored memory #%s in Hermes DB", record_id)
            except Exception as exc:
                logger.warning("Hermes DB remember error: %s", exc)

        return {
            "saved": True,
            "hermes_memory_id": record_id,
            "composite_result": composite_res,
            "stack_result": stack_res,
            "importance": importance,
            "tags": tags,
            "content": content,
        }

    def sleep_consolidation(self) -> dict[str, Any]:
        """Run consolidation & Ebbinghaus decay pass across subsystems."""
        results: dict[str, Any] = {"consolidated_at": datetime.now(timezone.utc).isoformat()}

        # Preferred path: full Hakua↔Hermes stack (RAG reindex + graph + Obsidian + sleep).
        if self.stack is not None:
            try:
                results["hakua_hermes_stack"] = self.stack.sleep()
                return results
            except Exception as exc:
                results["hakua_hermes_stack"] = {"error": str(exc)}

        # Fallback: Hakua composite sleep only
        if self.composite:
            try:
                c_sleep = self.composite.sleep()
                results["hakua_composite"] = c_sleep
            except Exception as exc:
                results["hakua_composite"] = {"error": str(exc)}

        # Hermes DB consolidation
        hermes_db = self.get_hermes_db_path()
        if hermes_db.exists():
            try:
                conn = sqlite3.connect(str(hermes_db))
                cur = conn.cursor()
                now = time.time()
                # Apply mild forgetting curve to un-rehearsed memories older than 1 day
                cur.execute(
                    """
                    UPDATE memories
                    SET strength = MAX(0.1, strength * 0.95),
                        updated_at = ?
                    WHERE state = 'active' AND (? - updated_at) > 86400
                    """,
                    (now, now),
                )
                affected = cur.rowcount
                conn.commit()
                conn.close()
                results["hermes_ebbinghaus"] = {"decay_applied_count": affected}
            except Exception as exc:
                results["hermes_ebbinghaus"] = {"error": str(exc)}

        return results


def _build_mcp_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "memory_status",
            "description": "Get current health, statistics, file paths, and counts for SOUL.md, MEMORY.md, Hermes Ebbinghaus DB, and hakua-memory.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "memory_recall",
            "description": "Recall long-term memories relevant to a query from hakua-memory, Hermes Ebbinghaus DB, and MEMORY.md.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search or context query to retrieve memories for."},
                    "top_k": {"type": "integer", "description": "Maximum number of memories to return (default 5).", "default": 5},
                },
                "required": ["query"],
            },
        },
        {
            "name": "memory_remember",
            "description": "Store a new observation, user preference, architectural fact, or decision into the long-term memory systems.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The text content of the memory to retain."},
                    "importance": {"type": "number", "description": "Salience/importance from 0.0 to 1.0 (default 0.7).", "default": 0.7},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Categorical tags for retrieval cues."},
                },
                "required": ["content"],
            },
        },
        {
            "name": "memory_sleep",
            "description": "Trigger Ebbinghaus decay, dream/association consolidation, and memory reorganization.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "soul_read",
            "description": "Read the active SOUL.md system persona and singular directive.",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "soul_update",
            "description": "Update SOUL.md with an automated timestamped backup copy.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "New complete markdown content for SOUL.md."},
                },
                "required": ["content"],
            },
        },
        {
            "name": "memory_md_read",
            "description": "Read structured § sections from MEMORY.md.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of sections (default 50).", "default": 50},
                    "filter_keyword": {"type": "string", "description": "Optional keyword filter for sections."},
                },
            },
        },
        {
            "name": "memory_md_append",
            "description": "Append a new structured § section to MEMORY.md.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title or summary of the memory entry."},
                    "content": {"type": "string", "description": "Markdown body text of the memory entry."},
                    "category": {"type": "string", "description": "Category tag, e.g. 'core', 'user_preference', 'architecture' (default 'core').", "default": "core"},
                },
                "required": ["title", "content"],
            },
        },
    ]


def _handle_tool_call(mem: StrataUnifiedMemory, name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "memory_status":
        return mem.status()
    elif name == "memory_recall":
        return mem.recall(query=args.get("query", ""), top_k=int(args.get("top_k", 5)))
    elif name == "memory_remember":
        return mem.remember(
            content=args.get("content", ""),
            importance=float(args.get("importance", 0.7)),
            tags=args.get("tags") or [],
        )
    elif name == "memory_sleep":
        return mem.sleep_consolidation()
    elif name == "soul_read":
        return mem.read_soul()
    elif name == "soul_update":
        return mem.update_soul(content=args.get("content", ""))
    elif name == "memory_md_read":
        return mem.read_memory_md(
            limit=int(args.get("limit", 50)),
            filter_keyword=args.get("filter_keyword", ""),
        )
    elif name == "memory_md_append":
        return mem.append_memory_md(
            title=args.get("title", ""),
            content=args.get("content", ""),
            category=args.get("category", "core"),
        )
    else:
        raise ValueError(f"Unknown tool name: {name}")


def run_mcp_server() -> None:
    """Run standard MCP stdio JSON-RPC loop."""
    mem = StrataUnifiedMemory()
    logger.info("Starting Strata Memory MCP server on stdio (PID=%s)", os.getpid())

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as err:
            logger.error("Invalid JSON received: %s", err)
            continue

        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        try:
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": PROTOCOL,
                        "capabilities": {
                            "tools": {"listChanged": False},
                        },
                        "serverInfo": {
                            "name": "strata-memory-mcp",
                            "version": VERSION,
                        },
                    },
                }
            elif method == "notifications/initialized":
                continue
            elif method == "ping":
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": _build_mcp_tools()},
                }
            elif method == "tools/call":
                t_name = params.get("name")
                t_args = params.get("arguments") or {}
                call_res = _handle_tool_call(mem, t_name, t_args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                        ]
                    },
                }
            else:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
        except Exception as exc:
            logger.exception("Error processing MCP method %s", method)
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(exc)},
            }

        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def run_cli(args: argparse.Namespace) -> int:
    """Run CLI subcommands printing clean JSON to stdout."""
    mem = StrataUnifiedMemory()
    action = args.cli
    result: dict[str, Any]

    if action == "status":
        result = mem.status()
    elif action == "soul":
        result = mem.read_soul()
    elif action == "memory_md":
        result = mem.read_memory_md(limit=args.limit, filter_keyword=args.query or "")
    elif action == "recall":
        result = mem.recall(query=args.query or "", top_k=args.limit)
    elif action == "remember":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else ["cli"]
        result = mem.remember(content=args.content or "", importance=args.importance, tags=tags)
    elif action == "append_memory":
        result = mem.append_memory_md(title=args.title or "CLI Note", content=args.content or "", category=args.category)
    elif action == "sleep":
        result = mem.sleep_consolidation()
    else:
        logger.error("Unknown CLI action: %s", action)
        print(json.dumps({"error": f"Unknown CLI action: {action}"}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Strata Unified Memory Service & MCP Server")
    parser.add_argument("--cli", choices=["status", "soul", "memory_md", "recall", "remember", "append_memory", "sleep"], help="Run single CLI action returning JSON")
    parser.add_argument("--query", type=str, default="", help="Query string for recall / filter")
    parser.add_argument("--content", type=str, default="", help="Content string for remember / append_memory")
    parser.add_argument("--title", type=str, default="", help="Title for append_memory")
    parser.add_argument("--category", type=str, default="core", help="Category for append_memory")
    parser.add_argument("--tags", type=str, default="", help="Comma-separated tags for remember")
    parser.add_argument("--importance", type=float, default=0.7, help="Salience/importance score (0.0 - 1.0)")
    parser.add_argument("--limit", type=int, default=5, help="Result limit")

    parsed = parser.parse_args()

    if parsed.cli:
        sys.exit(run_cli(parsed))
    else:
        run_mcp_server()


if __name__ == "__main__":
    main()
