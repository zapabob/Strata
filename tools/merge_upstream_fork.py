#!/usr/bin/env python3
"""tools/merge_upstream_fork.py - Plan/status (and optional execute) merge of official upstream into this fork.

Default mode is non-destructive: inspect remotes, compute divergence, inventory proprietary
paths, optionally create a backup branch, and emit a JSON/Markdown plan. Destructive merge
requires --execute after --plan review. Uncommitted work is never discarded.

MILSPEC notes: typed helpers, logging to stderr, JSON report to stdout when --json.
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_UPSTREAM_URL = "https://github.com/Niko1221/Strata.git"
DEFAULT_UPSTREAM_REMOTE = "upstream"
DEFAULT_UPSTREAM_REF = "upstream/main"
DEFAULT_ORIGIN_REMOTE = "origin"

# Fork contracts F01–F11 plus Hakua / Hermes / packaging surfaces that must survive merge.
PROPRIETARY_PATHS: Sequence[str] = (
    "_docs/upstream-intake/fork-contracts.json",
    "adapters/upstream",
    "apps/host/server/memory.mjs",
    "apps/host/server/native-control.mjs",
    "apps/host/server/run-config-check.mjs",
    "apps/host/src/lib/store.ts",
    "packaging/full_windows.py",
    "serve/memory_harness.py",
    "spin8",
    "tests/contracts/test_fork_feature_matrix.py",
    "tests/contracts/test_upstream_compatibility.py",
    "tools/check_upstream_cut.py",
    "tools/generate_t00_intake.py",
    "tools/merge_upstream_fork.py",
    "tqcodec",
)

PROPRIETARY_FEATURES: Sequence[Dict[str, str]] = (
    {"id": "F01", "name": "Clifford/Spin(8)/Triality KV Cache", "anchor": "spin8"},
    {"id": "F02", "name": "Query-v3 & Identity Initialization", "anchor": "tqcodec / adapters"},
    {"id": "F03", "name": "TurboQuant Dialects", "anchor": "tqcodec"},
    {"id": "F04", "name": "Dynamic Shared Audit Fix & Guard", "anchor": "src + host guards"},
    {"id": "F05", "name": "Model/Pack/Position/Hash Snapshot Integrity", "anchor": "native-control / run-config"},
    {"id": "F06", "name": "GUI/CLI Fork-Specific Settings & Clean OFF", "anchor": "apps/host"},
    {"id": "F07", "name": "Windows Ownership, Job Guard & Fail-Closed", "anchor": "packaging / control"},
    {"id": "F08", "name": "Hikari 27B PQ2_0 & Nimble Weights", "anchor": "prism / model bundles"},
    {"id": "F09", "name": "Research PoC, Negative Results & Ledger", "anchor": "_docs"},
    {"id": "F10", "name": "Refusal-Direction / Control Vector Steering", "anchor": "research opt-in"},
    {"id": "F11", "name": "Arbitrary GGUF & DeepSeek Derivative Integration", "anchor": "ModelBundle router"},
    {"id": "HAKUA", "name": "Hakua consented authenticated memory chat", "anchor": "apps/host + serve/memory_harness.py"},
    {"id": "KEYS", "name": "Fork / Hakua harness API keys + run-config known keys", "anchor": "run-config-check / native keys"},
    {"id": "HERMES", "name": "Hermes agent + long-term memory integration", "anchor": "serve / docs"},
    {"id": "PKG", "name": "Hakua-labelled Windows full packaging (-hakua)", "anchor": "packaging/full_windows.py"},
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [strata.merge_upstream] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("strata.merge_upstream")


@dataclass
class RemoteInfo:
    name: str
    fetch_url: str
    push_url: str


@dataclass
class MergePlan:
    generated_at: str
    mode: str
    branch: str
    head_sha: str
    upstream_remote: str
    upstream_ref: str
    upstream_sha: str
    merge_base: str
    ahead: int
    behind: int
    dirty: bool
    dirty_paths: List[str] = field(default_factory=list)
    remotes: List[RemoteInfo] = field(default_factory=list)
    proprietary_features: List[Dict[str, str]] = field(default_factory=list)
    proprietary_path_status: Dict[str, bool] = field(default_factory=dict)
    backup_branch: Optional[str] = None
    blockers: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    merge_tree_conflicts: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    executed: bool = False
    execute_result: Optional[str] = None


def run_git(args: Sequence[str], *, check: bool = False, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result


def list_remotes() -> List[RemoteInfo]:
    proc = run_git(["remote", "-v"])
    rows: Dict[str, Dict[str, str]] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name, url, kind = parts[0], parts[1], parts[2].strip("()")
        rows.setdefault(name, {})[kind] = url
    return [
        RemoteInfo(name=name, fetch_url=urls.get("fetch", ""), push_url=urls.get("push", ""))
        for name, urls in sorted(rows.items())
    ]


def ensure_upstream_remote(remote: str, url: str, *, fetch: bool) -> None:
    remotes = {r.name: r for r in list_remotes()}
    if remote not in remotes:
        logger.info("Adding remote %s -> %s", remote, url)
        run_git(["remote", "add", remote, url], check=True)
    elif remotes[remote].fetch_url.rstrip("/") != url.rstrip("/"):
        logger.warning(
            "Remote %s fetch URL is %s (expected %s); leaving as-is",
            remote,
            remotes[remote].fetch_url,
            url,
        )
    if fetch:
        logger.info("Fetching %s (tags, prune)", remote)
        run_git(["fetch", remote, "--tags", "--prune"], check=True, timeout=300)


def rev_parse(ref: str) -> str:
    proc = run_git(["rev-parse", ref])
    if proc.returncode != 0:
        raise RuntimeError(f"Cannot resolve ref {ref}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def porcelain_paths() -> List[str]:
    proc = run_git(["status", "--porcelain"])
    paths: List[str] = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:].strip()
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        paths.append(entry)
    return paths


def left_right_count(left: str, right: str) -> tuple[int, int]:
    proc = run_git(["rev-list", "--left-right", "--count", f"{left}...{right}"], check=True)
    parts = proc.stdout.strip().split()
    if len(parts) != 2:
        raise RuntimeError(f"Unexpected rev-list output: {proc.stdout!r}")
    return int(parts[0]), int(parts[1])


def merge_tree_conflicts(ours: str, base: str, theirs: str) -> List[str]:
    """Best-effort conflict preview via git merge-tree (no working-tree change)."""
    proc = run_git(["merge-tree", base, ours, theirs], timeout=300)
    conflicts: List[str] = []
    if proc.returncode != 0 and not proc.stdout and not proc.stderr:
        return [f"merge-tree failed ({proc.returncode})"]
    text = proc.stdout + "\n" + proc.stderr
    current: Optional[str] = None
    for line in text.splitlines():
        if line.startswith("changed in both"):
            # older merge-tree style
            current = line
        if line.startswith("+<<<<<<<") or line.startswith("<<<<<<<"):
            if current and current not in conflicts:
                conflicts.append(current)
        if line.startswith("CONFLICT"):
            conflicts.append(line.strip())
        # modern merge-tree --write-tree style markers are different; also parse "merged"
        if "Auto-merging" in line and "CONFLICT" in text:
            pass
    # Fallback: parse paths after "changed in both\n  base\n  our\n  their"
    if not conflicts:
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            if line.strip() == "changed in both" and idx + 1 < len(lines):
                # next non-empty indented path-ish lines often include filenames
                for j in range(idx + 1, min(idx + 8, len(lines))):
                    candidate = lines[j].strip()
                    if candidate and not candidate.startswith(("+", "-", "@", "merged")):
                        if "/" in candidate or candidate.endswith((".py", ".mjs", ".ts", ".md", ".cpp", ".h")):
                            conflicts.append(candidate)
                            break
    # Deduplicate while preserving order
    seen = set()
    ordered: List[str] = []
    for item in conflicts:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered[:200]


def path_exists(rel: str) -> bool:
    return (REPO_ROOT / rel).exists()


def create_backup_branch(prefix: str = "backup/pre-upstream-merge") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"{prefix}-{stamp}"
    run_git(["branch", name, "HEAD"], check=True)
    logger.info("Created backup branch %s at HEAD", name)
    return name


def stash_if_dirty(*, message: str) -> Optional[str]:
    paths = porcelain_paths()
    if not paths:
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = f"{message}-{stamp}"
    run_git(["stash", "push", "-u", "-m", label], check=True)
    logger.info("Stashed dirty work as %s", label)
    return label


def build_plan(
    *,
    mode: str,
    upstream_remote: str,
    upstream_ref: str,
    create_backup: bool,
) -> MergePlan:
    branch_proc = run_git(["branch", "--show-current"], check=True)
    branch = branch_proc.stdout.strip() or "DETACHED"
    head = rev_parse("HEAD")
    remotes = list_remotes()
    remote_names = {r.name for r in remotes}
    blockers: List[str] = []
    notes: List[str] = []

    if upstream_remote not in remote_names:
        blockers.append(f"Missing remote '{upstream_remote}'. Re-run with --ensure-remote --fetch.")
    try:
        upstream_sha = rev_parse(upstream_ref)
    except RuntimeError as exc:
        upstream_sha = ""
        blockers.append(str(exc))

    merge_base = ""
    ahead = behind = 0
    conflicts: List[str] = []
    if upstream_sha:
        mb = run_git(["merge-base", "HEAD", upstream_ref])
        if mb.returncode != 0:
            blockers.append(f"No merge-base between HEAD and {upstream_ref}")
        else:
            merge_base = mb.stdout.strip()
            ahead, behind = left_right_count("HEAD", upstream_ref)
            if behind == 0:
                notes.append(f"Already up to date with {upstream_ref} (behind=0).")
            else:
                notes.append(f"Fork is ahead={ahead}, behind={behind} vs {upstream_ref}.")
            conflicts = merge_tree_conflicts(head, merge_base, upstream_sha)
            if conflicts:
                notes.append(f"merge-tree heuristic flagged {len(conflicts)} conflict hint(s).")

    dirty_paths = porcelain_paths()
    dirty = bool(dirty_paths)
    if dirty:
        blockers.append(
            "Working tree is dirty. Stash or commit before --execute "
            "(Hakua cancel-path edits must be preserved)."
        )

    proprietary_status = {p: path_exists(p) for p in PROPRIETARY_PATHS}
    missing = [p for p, ok in proprietary_status.items() if not ok]
    if missing:
        notes.append(
            "Some proprietary paths are absent from the worktree "
            f"(sparse-checkout or not yet landed): {', '.join(missing[:12])}"
            + ("…" if len(missing) > 12 else "")
        )

    backup_branch = None
    if create_backup and mode in {"plan", "execute"}:
        backup_branch = create_backup_branch()

    next_steps = [
        "Review this plan JSON/Markdown; keep proprietary features listed below.",
        "Ensure dirty Hakua edits are committed or stashed (script can --stash-dirty).",
        f"Re-run: py -3 tools/merge_upstream_fork.py --plan --upstream-ref {upstream_ref}",
        "When ready (explicit): py -3 tools/merge_upstream_fork.py --execute "
        f"--upstream-ref {upstream_ref} --stash-dirty --backup",
        "Resolve conflicts preferring fork proprietary anchors + upstream security/bugfixes.",
        "Run host tests + check_upstream_cut; then build, tag/release (no auto-push), rewrite README.",
    ]

    return MergePlan(
        generated_at=datetime.now(timezone.utc).isoformat(),
        mode=mode,
        branch=branch,
        head_sha=head,
        upstream_remote=upstream_remote,
        upstream_ref=upstream_ref,
        upstream_sha=upstream_sha,
        merge_base=merge_base,
        ahead=ahead,
        behind=behind,
        dirty=dirty,
        dirty_paths=dirty_paths,
        remotes=remotes,
        proprietary_features=list(PROPRIETARY_FEATURES),
        proprietary_path_status=proprietary_status,
        backup_branch=backup_branch,
        blockers=blockers,
        next_steps=next_steps,
        merge_tree_conflicts=conflicts,
        notes=notes,
    )


def execute_merge(plan: MergePlan, *, stash_dirty: bool, no_commit: bool) -> MergePlan:
    if plan.blockers and not (stash_dirty and all(b.startswith("Working tree is dirty") for b in plan.blockers)):
        # Allow only the dirty-tree blocker to be cleared via stash.
        remaining = [b for b in plan.blockers if not b.startswith("Working tree is dirty")]
        if remaining:
            plan.execute_result = "refused: blockers remain"
            plan.notes.append("Execute refused due to blockers: " + "; ".join(remaining))
            return plan

    stash_label = None
    if stash_dirty and plan.dirty:
        stash_label = stash_if_dirty(message="pre-upstream-merge-hakua")
        plan.notes.append(f"Stashed dirty work: {stash_label}")
        plan.dirty = False
        plan.dirty_paths = []
        plan.blockers = [b for b in plan.blockers if not b.startswith("Working tree is dirty")]

    if plan.blockers:
        plan.execute_result = "refused: blockers remain after stash"
        return plan

    args = ["merge", "--no-ff", plan.upstream_ref, "-m", f"Merge {plan.upstream_ref} into fork (preserve proprietary)"]
    if no_commit:
        args = ["merge", "--no-ff", "--no-commit", plan.upstream_ref]
    proc = run_git(args, timeout=600)
    if proc.returncode != 0:
        plan.executed = False
        plan.execute_result = f"merge failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        plan.notes.append("Merge stopped with conflicts or error; working tree may be mid-merge. Resolve manually.")
        plan.notes.append("To abort: git merge --abort")
        if stash_label:
            plan.notes.append(f"Restore stash later with: git stash list  # look for {stash_label}")
        return plan

    plan.executed = True
    plan.execute_result = "merge completed"
    plan.head_sha = rev_parse("HEAD")
    if stash_label:
        pop = run_git(["stash", "pop"])
        if pop.returncode != 0:
            plan.notes.append(
                f"Merge OK but stash pop failed; restore manually: git stash apply (label {stash_label})"
            )
        else:
            plan.notes.append("Restored stashed Hakua/local edits via stash pop.")
    return plan


def plan_to_markdown(plan: MergePlan) -> str:
    lines = [
        f"# Upstream merge plan ({plan.mode})",
        "",
        f"- Generated: `{plan.generated_at}`",
        f"- Branch: `{plan.branch}` @ `{plan.head_sha}`",
        f"- Upstream: `{plan.upstream_ref}` @ `{plan.upstream_sha}`",
        f"- Merge-base: `{plan.merge_base}`",
        f"- Ahead / behind: **{plan.ahead}** / **{plan.behind}**",
        f"- Dirty: `{plan.dirty}`",
        f"- Backup branch: `{plan.backup_branch or '(none)'}`",
        f"- Executed: `{plan.executed}` ({plan.execute_result or 'n/a'})",
        "",
        "## Remotes",
    ]
    for remote in plan.remotes:
        lines.append(f"- `{remote.name}` fetch=`{remote.fetch_url}` push=`{remote.push_url}`")
    lines.extend(["", "## Proprietary features (must preserve)"])
    for feat in plan.proprietary_features:
        lines.append(f"- **{feat['id']}** {feat['name']} — `{feat['anchor']}`")
    lines.extend(["", "## Proprietary path presence"])
    for path, ok in plan.proprietary_path_status.items():
        lines.append(f"- `{'OK' if ok else 'MISSING'}` `{path}`")
    if plan.dirty_paths:
        lines.extend(["", "## Dirty paths (preserve)"])
        for path in plan.dirty_paths:
            lines.append(f"- `{path}`")
    if plan.merge_tree_conflicts:
        lines.extend(["", "## merge-tree conflict hints"])
        for item in plan.merge_tree_conflicts:
            lines.append(f"- {item}")
    if plan.blockers:
        lines.extend(["", "## Blockers"])
        for item in plan.blockers:
            lines.append(f"- {item}")
    if plan.notes:
        lines.extend(["", "## Notes"])
        for item in plan.notes:
            lines.append(f"- {item}")
    lines.extend(["", "## Next steps"])
    for item in plan.next_steps:
        lines.append(f"1. {item}")
    lines.append("")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Plan or execute upstream merge into Strata fork")
    parser.add_argument("--plan", action="store_true", help="Build a dry plan (default if no --execute)")
    parser.add_argument("--status", action="store_true", help="Alias for --plan without backup")
    parser.add_argument("--execute", action="store_true", help="Perform git merge (requires clean tree or --stash-dirty)")
    parser.add_argument("--ensure-remote", action="store_true", help="Add upstream remote if missing")
    parser.add_argument("--fetch", action="store_true", help="Fetch upstream before planning")
    parser.add_argument("--upstream-remote", default=DEFAULT_UPSTREAM_REMOTE)
    parser.add_argument("--upstream-url", default=DEFAULT_UPSTREAM_URL)
    parser.add_argument("--upstream-ref", default=DEFAULT_UPSTREAM_REF, help="e.g. upstream/main or upstream/v0.2.6")
    parser.add_argument("--backup", action="store_true", help="Create backup branch at HEAD")
    parser.add_argument("--stash-dirty", action="store_true", help="On execute, stash -u dirty work first")
    parser.add_argument("--no-commit", action="store_true", help="With --execute, stop before merge commit")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    parser.add_argument("--output", type=str, default="", help="Write plan JSON to this path")
    parser.add_argument("--markdown-output", type=str, default="", help="Write plan Markdown to this path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    mode = "execute" if args.execute else "plan"
    if args.status and not args.execute:
        mode = "status"

    if args.ensure_remote or args.fetch:
        ensure_upstream_remote(args.upstream_remote, args.upstream_url, fetch=args.fetch)

    create_backup = bool(args.backup) and mode != "status"
    plan = build_plan(
        mode=mode,
        upstream_remote=args.upstream_remote,
        upstream_ref=args.upstream_ref,
        create_backup=create_backup,
    )

    if args.execute:
        plan = execute_merge(plan, stash_dirty=args.stash_dirty, no_commit=args.no_commit)

    payload: Dict[str, Any] = asdict(plan)
    text_json = json.dumps(payload, indent=2, ensure_ascii=False)
    text_md = plan_to_markdown(plan)

    if args.output:
        out = Path(args.output)
        if not out.is_absolute():
            out = REPO_ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text_json, encoding="utf-8")
        logger.info("Wrote JSON plan to %s", out)
    if args.markdown_output:
        md = Path(args.markdown_output)
        if not md.is_absolute():
            md = REPO_ROOT / md
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(text_md, encoding="utf-8")
        logger.info("Wrote Markdown plan to %s", md)

    if args.json:
        sys.stdout.write(text_json + "\n")
    else:
        sys.stdout.write(text_md + "\n")

    if args.execute and not plan.executed:
        return 2
    if plan.blockers and mode != "execute":
        return 0  # plan/status succeed even with blockers; they are reported
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
