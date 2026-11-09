"""Only adapter syntax/help/dry-plan and mocked small tests; never executes native phases."""
from __future__ import annotations

import ast
import datetime
import json
import os
import subprocess

from common import HERE, NODE, PYTHON, UV


def main() -> int:
    output = HERE / ("validation-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    output.mkdir()
    for name in ("temp", "uv-cache"):
        (output / name).mkdir()
    env = dict(os.environ)
    env.update(TMP=str(output / "temp"), TEMP=str(output / "temp"), UV_CACHE_DIR=str(output / "uv-cache"),
               UV_PYTHON_DOWNLOADS="never", UV_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONNOUSERSITE="1")
    python = [str(UV), "run", "--offline", "--no-config", "--no-project", "--no-managed-python",
              "--python", str(PYTHON), "python", "-B"]
    rows = []
    for path in HERE.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rows.append({"name": "python-ast", "passed": True})
    commands = [
        ("python-version", python + ["--version"]),
        ("node-version", [str(NODE), "--version"]),
        ("node-syntax", [str(NODE), "--check", str(HERE / "binding.mjs")]),
        ("binding-help", [str(NODE), str(HERE / "binding.mjs"), "--help"]),
        ("adapter-help", python + [str(HERE / "adapter.py"), "--help"]),
        ("retry-help", python + [str(HERE / "retry_prepare.py"), "--help"]),
        ("model-help", python + [str(HERE / "model.py"), "--help"]),
        ("dry-plan", python + [str(HERE / "adapter.py"), "plan", "--source-root", "H:/PARENT-SUPPLIES-FROZEN-SOURCE",
                                "--reviewed-commit", "0" * 40]),
        ("tokenizer-readonly", python + ["-c", "from pathlib import Path; from model import tokenizer, PROMPT; "
            "tk=tokenizer(Path(" + repr(str(HERE.parents[2])) + ")); ids=tk.encode(PROMPT); "
            "print({'roundTrip':tk.decode(ids)==PROMPT,'inputIds':ids,'scope':'tokenizer files and GGUF header only; no inference'})"]),
        ("pytest", python + ["-m", "pytest", str(HERE / "test_adapters.py"), "-q", "-p", "no:cacheprovider",
                              "--noconftest", "--confcutdir", str(HERE),
                              "--basetemp", str(output / "pytest-temp")]),
        ("flake8", python + ["-m", "flake8", str(HERE), "--select=E9,F", "--exclude=validation-*"]),
    ]
    for name, command in commands:
        with (output / (name + ".txt")).open("x", encoding="utf-8") as log:
            done = subprocess.run(command, cwd=HERE, env=env, stdout=log, stderr=subprocess.STDOUT,
                                  timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
        rows.append({"name": name, "command": command, "exitCode": done.returncode, "passed": done.returncode == 0})
    result = {"passed": all(row["passed"] for row in rows), "checks": rows,
              "scope": "No build, app, native executable, model, packaging or Job launch/termination",
              "output": str(output)}
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
