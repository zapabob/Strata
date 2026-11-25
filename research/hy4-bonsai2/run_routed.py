"""Resume the 41 bank pairs from a single pinned Hy4 checkpoint on Windows."""

from __future__ import annotations

import argparse
import json
import msvcrt
import os
import subprocess
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from stream_routed import EXPERTS, KINDS, ROW_BYTES, WIDTH, check_resources


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def record(path, state):
    part = path.with_suffix(".tmp")
    part.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(part, path)


def verified(folder, layer, kind, revision):
    source = read_json(folder / "source.json")
    receipt = read_json(folder / "conversion.json")
    rows = EXPERTS * KINDS[kind][0]
    model = folder / "routed-experts.gguf"
    transfer = folder / "assembled.json"
    standalone = model.is_file()
    if (
        source["source_tensor"] != f"model.layers.{layer}.mlp.experts.{kind}"
        or source["revision"] != revision
        or source["stored_experts"] != EXPERTS
        or source["shape"] != [EXPERTS, KINDS[kind][0], WIDTH]
        or receipt["pq2_tensor_bytes"] != rows * ROW_BYTES
        or receipt["rows"] != rows
        or (standalone and receipt["output_bytes"] != model.stat().st_size)
    ):
        raise ValueError(f"Invalid full-bank receipt in {folder}")
    if standalone:
        with model.open("rb") as f:
            if f.read(8) != b"GGUF\x03\x00\x00\x00":
                raise ValueError(f"Invalid bank GGUF header in {folder}")
    else:
        moved = read_json(transfer)
        parent = Path(moved["model_directory"])
        candidate = parent / "Hy4-Bonsai2-PQ2_0.gguf"
        if not candidate.exists():
            candidate = candidate.with_suffix(".gguf.partial")
        expected = source.get("target_tensors") or [source["target_tensor"]]
        if (
            moved["revision"] != revision
            or set(moved["tensors"]) != set(expected)
            or not candidate.is_file()
        ):
            raise ValueError(f"Missing integrated bank {folder}")
        with sqlite3.connect(
            f"{(parent / 'progress.sqlite').as_uri()}?mode=ro", uri=True
        ) as db:
            amount = sum(
                db.execute(
                    "SELECT coalesce(sum(size),0) FROM chunks WHERE name=?", (n,)
                ).fetchone()[0]
                for n in expected
            )
        if amount != receipt["pq2_tensor_bytes"]:
            raise ValueError(f"Incomplete integrated bank {folder}")


def run(args, revision):
    output = args.output.resolve()
    first = args.first_layer.resolve(strict=True)
    state = {"revision": revision, "complete_banks": [], "total_banks": 82}
    path = output / "routed-status.json"
    for layer in range(1, 42):
        for kind, suffix in (("down_proj", "down"), ("gate_up_proj", "gate-up")):
            name = f"layer-{layer}-{suffix}"
            folder = (first if layer == 1 else output) / name
            state.update(
                active=name, updated_utc=datetime.now(timezone.utc).isoformat()
            )
            record(path, state)
            if layer > 1 and not (folder / "conversion.json").exists():
                folder.mkdir(exist_ok=True)
                cmd = [
                    sys.executable,
                    "-u",
                    str(Path(__file__).with_name("stream_routed.py")),
                    "--layer",
                    str(layer),
                    "--matrix",
                    kind,
                    "--revision",
                    revision,
                    "--range-workers",
                    str(args.range_workers),
                    "--output",
                    str(folder),
                    "--gguf-python",
                    str(args.gguf_python),
                    "--prism-bin",
                    str(args.prism_bin),
                ]
                delays = (5, 15, 30, 60, 60, 60)
                if args.cuda_codec:
                    cmd.extend(["--cuda-codec", str(args.cuda_codec)])
                for attempt in range(len(delays) + 1):
                    check_resources(output, 0)
                    with (folder / "worker.log").open("ab") as log:
                        result = subprocess.run(
                            cmd, stdout=log, stderr=subprocess.STDOUT
                        )
                    if result.returncode == 0:
                        break
                    if attempt == len(delays):
                        raise RuntimeError(
                            f"{name} exited {result.returncode}. See {folder / 'worker.log'}"
                        )
                    time.sleep(delays[attempt])
            verified(folder, layer, kind, revision)
            # Only discard this run's reproducible staging after the encoder's full
            # byte comparison and receipt. The input and the previous pilot are preserved.
            staged = folder / "tensor.pq2_0.part"
            if layer > 1 and folder.resolve().parent == output and staged.is_file():
                staged.unlink()
            state["complete_banks"].append(name)
            record(path, state)
    state.update(active=None, updated_utc=datetime.now(timezone.utc).isoformat())
    record(path, state)


def main():
    p = argparse.ArgumentParser()
    for name in ("first-layer", "output", "gguf-python", "prism-bin"):
        p.add_argument(f"--{name}", type=Path, required=True)
    p.add_argument("--range-workers", type=int, choices=range(1, 5), default=4)
    p.add_argument("--cuda-codec", type=Path)
    args = p.parse_args()
    if args.output.resolve() == args.first_layer.resolve():
        p.error("Use a separate destination for the remaining banks")
    args.output.mkdir(parents=True, exist_ok=True)
    revision = read_json(args.first_layer / "layer-1-down" / "source.json")["revision"]
    with (args.output / "run.lock").open("a+b") as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            run(args, revision)
        except Exception as exc:
            record(
                args.output / "routed-error.json",
                {"reason": str(exc), "utc": datetime.now(timezone.utc).isoformat()},
            )
            raise
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
