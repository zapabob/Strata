"""Run the published Pagoda Bench user prompt against both native Strata models."""

import argparse
import hashlib
from html import unescape
import json
from pathlib import Path
import re
import sys
import time

from filelock import Timeout
import psutil
import requests
from tokenizers import Tokenizer

from benchmark_apex import visible_and_reasoning
from benchmark_generation import competing_inference, digest, read, save
from benchmark_modeb_nvfp4 import stamp
from benchmark_modeb_strata import engine_options, native
from phase7_controls import immutable
from sm120_native import Nvml


SOURCE = "https://artificialanalysis.ai/microevals/pagoda-bench-1788018029907"
PROMPT_DIGEST = "0221b0589379ba83a6c0b9d5ed9f1de2e129c78ba26b6d289414d6bcb4324dc1"
SEED = 47
FENCE = re.compile(r"(?:^|\n)[ \t]*\x60{3}html[ \t]*\r?\n(.*?)\r?\n[ \t]*\x60{3}(?=\r?\n|$)", re.I | re.S)
DOCUMENT = re.compile(r"(?:<!doctype\s+html\s*>\s*)?<html(?=\s|>).*?</html\s*>", re.I | re.S)
ENGINES = ("strata-inkling.exe", "strata-inkling2.exe", "llama-server.exe", "ollama.exe")
ADMISSION_ERRORS = {"shared_gpu_pressure", "insufficient_gpu_admission_headroom"}


def published_prompt():
    response = requests.get(SOURCE, timeout=(10, 25))
    response.raise_for_status()
    prompts = re.findall(r"<p>(# ROLE\n.*?)</p>", response.text, re.S)
    if len(prompts) != 1:
        raise ValueError("Could not identify the published user prompt")
    text = unescape(prompts[0])
    if hashlib.sha256(text.encode()).hexdigest() != PROMPT_DIGEST:
        raise ValueError("The published prompt differs from the verified text")
    return text


def freeze(args, tokenizer):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "terminal"))
    from serve.frontend import ChatTemplate

    record = args.out / "protocol.json"
    if record.is_file():
        ids = read(record)["input_ids"]
    else:
        template = ChatTemplate(args.template)
        rendered = template.render([dict(role="user", content=published_prompt())],
                                   tools=None, reasoning_effort="none")
        ids = tokenizer.encode(rendered, add_special_tokens=False).ids
    if not ids or len(ids) + args.budget >= args.context:
        raise ValueError("The published prompt and budget exceed the requested context")
    model_paths = dict(sq10=args.sq10, nvfp4=args.nvfp4)
    models = {}
    expected_sizes = dict(sq10=10471526400, nvfp4=15036265248)
    for arm, path in model_paths.items():
        stat = path.stat()
        if stat.st_size != expected_sizes[arm]:
            raise ValueError(f"{arm} model size differs from the verified comparison")
        models[arm] = dict(path=str(path.resolve()), bytes=stat.st_size, modified_ns=stat.st_mtime_ns)
    immutable(record, dict(source=SOURCE, user_prompt_sha256=PROMPT_DIGEST, input_ids=ids,
                           template_sha256=digest(args.template), tokenizer_sha256=digest(args.tokenizer),
                           engine=str(args.engine.resolve()), engine_sha256=digest(args.engine),
                           system_prompt=None, reasoning_effort="none", context=args.context,
                           budget=args.budget, temperature=0, seed=SEED, repeat_penalty=1,
                           engine_options=engine_options(args), models=models,
                           arm_order=["sq10", "nvfp4"]))
    return ids, model_paths


def candidate(content):
    fences = list(FENCE.finditer(content))
    strict = len(fences) == 1 and content.strip() == fences[0][0].strip()
    document = fences[0][1] if len(fences) == 1 else content
    match = DOCUMENT.search(document)
    if strict and re.match(r"\s*<!doctype\s+html\b", document, re.I):
        return document, strict, match is not None
    if match:
        return match[0], strict, True
    return None, strict, False


def competing_windows_process():
    return any((proc.info["name"] or "").casefold() in ENGINES
               for proc in psutil.process_iter(("name",)))


def await_gpu(gpu, deadline):
    available_since = None
    while time.monotonic() < deadline:
        memory = gpu.memory()
        occupied = (memory["device_free_bytes"] < 12000 * 2**20 or competing_inference()
                    or competing_windows_process())
        if occupied:
            available_since = None
        elif available_since is None:
            available_since = time.monotonic()
        elif time.monotonic() - available_since >= 10:
            return True
        time.sleep(5)
    return False


def run_arm(args, ids, tokenizer, arm, model):
    root = args.out / arm
    gpu = Nvml()
    deadline = time.monotonic() + args.wait_minutes * 60
    while await_gpu(gpu, deadline):
        folder = root / stamp()
        result = None
        started = None
        error = None
        print(f"{arm}: starting Strata {folder.name}", flush=True)
        try:
            with native(args, model, folder) as peer:
                print(f"{arm}: generating the published prompt", flush=True)
                started = time.perf_counter()
                result = peer.generate(ids, args.budget, SEED)
                result["generation_wall_seconds"] = time.perf_counter() - started
        except (OSError, ValueError, RuntimeError, Timeout) as exc:
            error = str(exc)
        trace = folder / "protocol.log"
        restart = result is None and error in ADMISSION_ERRORS
        if result is None:
            tokens = []
            if trace.is_file():
                tokens = [int(value) for value in re.findall(r"^> T (\d+)", trace.read_text(encoding="utf-8"), re.M)]
            if not tokens and (isinstance(error, str) and (error in ADMISSION_ERRORS or "could not be acquired" in error)):
                print(f"{arm}: GPU admission changed, waiting again ({error})", flush=True)
                continue
            result = dict(output_ids=tokens, input_tokens=len(ids), output_tokens=len(tokens), stop="interrupted",
                          generation_wall_seconds=None if started is None else time.perf_counter() - started)
        channels = visible_and_reasoning(result["output_ids"], tokenizer, result["stop"])
        html, strict, complete = candidate(channels["content"])
        if html is not None:
            (folder / "index.html").write_bytes(html.encode("utf-8"))
        immutable(folder / "answer.json", dict(**result, strict_html_envelope=strict, complete_document=complete,
                                              html_bytes=len(html.encode("utf-8")) if html is not None else None,
                                              error=error))
        (folder / "visible.txt").write_bytes(channels["content"].encode("utf-8"))
        save(root / "result.json", dict(status="saved", attempt=folder.name, **{
            k: v for k, v in result.items() if k != "output_ids"}))
        print(f"{arm}: {result['output_tokens']} generated tokens, {result['stop']}, HTML={html is not None}", flush=True)
        if restart:
            print(f"{arm}: preserving the partial generation and waiting to restart from the frozen prompt", flush=True)
            continue
        return
    root.mkdir(parents=True, exist_ok=True)
    save(root / "admission.json", dict(status="blocked", error="No stable GPU admission within the wait window",
                                       wait_minutes=args.wait_minutes))
    print(f"{arm}: GPU admission blocked", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run"))
    for option in ("engine", "sq10", "nvfp4", "out", "tokenizer", "template", "expert-cache-dir"):
        parser.add_argument(f"--{option}", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=16384)
    parser.add_argument("--context", type=int, default=24576)
    parser.add_argument("--wait-minutes", type=int, default=30)
    parser.add_argument("--expert-vram-gib", type=float, default=6)
    parser.add_argument("--expert-ram-gib", type=float, default=4)
    parser.add_argument("--prefill-chunk", type=int, default=128)
    parser.add_argument("--minimum-cold-mib", type=int, default=256)
    args = parser.parse_args()
    if args.budget <= 0 or args.wait_minutes <= 0 or not args.expert_cache_dir.is_dir():
        parser.error("Use a positive budget and wait interval, and an existing scratch directory")
    args.out.mkdir(parents=True, exist_ok=True)
    tokenizer = Tokenizer.from_file(str(args.tokenizer))
    ids, models = freeze(args, tokenizer)
    print(f"Frozen {len(ids)} input tokens and a {args.budget}-token generation cap", flush=True)
    if args.action == "run":
        for arm, model in models.items():
            prior = args.out / arm / "result.json"
            if prior.is_file():
                data = read(prior)
                if data.get("stop") in {"eos", "limit"}:
                    continue
            run_arm(args, ids, tokenizer, arm, model)


if __name__ == "__main__":
    main()
