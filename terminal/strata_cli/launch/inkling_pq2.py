"""Serve a local PQ2_0 GGUF with the source-built native Strata Inkling engine."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from strata_cli.launch.settings import DEFAULT_PORT
from strata_control.inkling_pq2 import inspect_model


def launch(a) -> int:
    supported = {"command", "raw_argv", "inkling_engine", "family", "model_path", "context", "port", "kv", "vision",
                 "data_dir", "parallel", "api_key", "api_key_env", "access", "gpu", "plan", "output", "yes", "drafting"}
    unsupported = sorted(k for k, value in vars(a).items() if k not in supported and value)
    if unsupported:
        flags = ", ".join("--" + key.replace("_", "-") for key in unsupported)
        raise ValueError(f"The foreground native launch does not implement {flags}.")
    if a.access not in (None, "local") or a.family not in (None, "inkling-2-mini"):
        raise ValueError("Use --family inkling-2-mini and --access local with this native engine.")
    if not a.model_path:
        raise ValueError("Supply the text GGUF with --model-path.")
    if a.drafting not in (None, "off"):
        raise ValueError("This PQ2_0 native profile has drafting off.")
    model = Path(a.model_path).expanduser().resolve()
    engine = Path(a.inkling_engine).expanduser().resolve()
    if not model.is_file() or not engine.is_file() or engine.stem.lower() != "strata-inkling":
        raise ValueError("Select a text GGUF and the native Strata binary named strata-inkling.")
    maximum = inspect_model(model)
    context, slots = a.context or 4096, a.parallel or 1
    if context > maximum:
        raise ValueError(f"The GGUF supports at most {maximum:,} tokens per request.")
    kv = a.kv or "k8v4"
    if kv not in ("k8v4", "k8v8", "fp16", "fp8"):
        raise ValueError("Available Inkling KV formats are k8v4, k8v8, fp8 and fp16.")
    args = ["--native", str(model), "--max-context", str(context), "--parallel", str(slots),
            "--kv", kv, "--draft", "off"]
    if a.gpu is not None:
        if not a.gpu.isdecimal():
            raise ValueError("Select a single GPU with --gpu NUMBER for this local profile.")
        args += ["--gpu", a.gpu]
    if a.vision and a.vision != "off":
        from strata_control.inkling_family import VISION_FILE
        vision = model.parent / VISION_FILE
        if not vision.is_file():
            raise ValueError(f"The native vision reader requires {VISION_FILE} beside the text model.")
        args += ["--vision", str(vision)]
    if a.api_key and a.api_key_env:
        raise ValueError("Choose one API key source.")
    key = os.environ.get(a.api_key_env) if a.api_key_env else a.api_key
    if a.api_key_env and not key:
        raise ValueError(f"The API key environment variable {a.api_key_env} is empty.")
    port = a.port or DEFAULT_PORT
    url = f"http://127.0.0.1:{port}/v1"
    plan = dict(schema_version=1, ok=True, backend="strata-inkling", mode="foreground", url=url,
                model=model.stem, context_per_slot=context, slots=slots, authenticated=bool(key),
                native_command=[str(engine), "--serve", *args])
    if a.plan:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    if a.output == "json":
        raise ValueError("Use --plan --output json for a machine-readable plan. Serving streams native logs.")
    from tools.strata_tokenizer import extract
    terminal = Path(__file__).resolve().parents[2]
    data_dir = Path(a.data_dir).expanduser() if a.data_dir else None
    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="inkling-pq2-", dir=data_dir) as tmp:
        folder = Path(tmp).resolve()
        extract(model, folder)
        cfg = dict(exe=str(engine), args=args, cwd=str(engine.parent), tokenizer=str(folder / "tokenizer"),
                   model_name=model.stem, arch="inkling2_loop", backend="nvidia", log=str(folder / "engine.log"),
                   lib_dirs=[str(engine.parent)], port=port, parallel=slots, drafting="off", api_key=key or "none")
        from strata_cli.launch.runner import write_private
        configuration = folder / "run.json"
        write_private(configuration, cfg)
        print(f"Serving {model.stem} at {url} with {engine.name}. Press Ctrl+C to stop.", flush=True)
        command = [sys.executable, str(terminal / "strata.py"), "serve", "--config", str(configuration),
                   "--host", "127.0.0.1", "--port", str(port)]
        try:
            with subprocess.Popen(command) as child:
                try:
                    if os.name == "nt":
                        from serve import winjob
                        winjob.contain(child)
                    return child.wait()
                finally:
                    if child.poll() is None:
                        child.terminate()
        except OSError as exc:
            raise ValueError(f"Could not start the native server: {exc}") from exc
