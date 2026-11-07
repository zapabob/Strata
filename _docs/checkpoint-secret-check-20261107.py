"""Narrow, redacted credential/payload check of the intended Git checkpoint."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github-token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b"),
    "vendor-secret": re.compile(r"\b(?:sk-(?:proj-|ant-api\d+-)?[A-Za-z0-9_-]{32,}|hf_[A-Za-z0-9]{30,})\b"),
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main() -> int:
    names = git("diff", "--cached", "--name-only", "--diff-filter=ACM", "-z").decode().split("\0")
    names = [name for name in names if name]
    issues = []
    for name in names:
        if name.startswith(("Microsoft/", "private-backups/")) or Path(name).suffix.lower() in {".exe", ".dll", ".db", ".sqlite", ".gguf"}:
            issues.append((name, 0, "unexpected-runtime-or-private-payload"))
            continue
        text = git("show", ":" + name).decode("utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            for rule, expression in RULES.items():
                if expression.search(line):
                    issues.append((name, number, rule))
    for name, number, rule in issues:
        print(f"{name}:{number}: {rule} (value redacted)")
    print(f"Checked {len(names)} staged files; credential/payload findings: {len(issues)}")
    return int(bool(issues))


if __name__ == "__main__":
    sys.exit(main())
