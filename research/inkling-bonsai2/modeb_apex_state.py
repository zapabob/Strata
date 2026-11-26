"""Keep one recoverable, token-verified CUDA slot per unfinished Apex problem."""

import math
import os
from pathlib import Path
import shutil

import requests

from benchmark_generation import read, save


CHUNK_TOKENS = 2048
SYSTEM_DISK_FLOOR = 5 * 2**30
MODEL_DISK_FLOOR = (1808 * 2**30 + 99) // 100


def slot_action(url, action, filename):
    response = requests.post(f"{url}/slots/0?action={action}", json={"filename": filename}, timeout=(10, 120))
    response.raise_for_status()
    data = response.json()
    if data["id_slot"] != 0 or data["filename"] != filename:
        raise ValueError("The slot operation returned a different cache identity")
    return data


def checkpointed_completion(url, row, seed, key, slot_dir, ledger, bytes_per_cached_token, complete,
                           start_tokens=CHUNK_TOKENS):
    prompt = row["ids"]
    budget = row["budget"]
    history = read(ledger) if ledger.exists() else None
    previous = None
    ids = []
    segments = []
    system_volume = Path(os.environ["SystemRoot"]).anchor
    reserve = SYSTEM_DISK_FLOOR if slot_dir.resolve().anchor.casefold() == system_volume.casefold() else MODEL_DISK_FLOOR
    if history:
        ids, segments = history["output_ids"], history["segments"]
        if history["input_ids"] != prompt or not 0 < len(ids) < budget:
            raise ValueError("Invalid saved Apex token trajectory")
        previous = slot_dir / f"{key}-{len(ids)}.bin"
        if previous.stat().st_size != history["saved"]["n_written"]:
            raise ValueError("Saved Apex slot extent changed")
        restored = slot_action(url, "restore", previous.name)
        if (restored["n_restored"] != history["saved"]["n_saved"]
                or restored["n_read"] != history["saved"]["n_written"]):
            raise ValueError("Restored Apex slot differs from the checkpoint")

    while len(ids) < budget:
        limit = min(max(start_tokens, len(ids)), CHUNK_TOKENS, budget - len(ids))
        result = complete(url, prompt + ids, limit, seed, cache_prompt=bool(ids))
        if ids and result["timings"].get("cache_n", 0) < len(prompt) + len(ids) - 1:
            raise ValueError("Apex continuation did not use its saved token-state prefix")
        if result["stop"] == "limit" and len(result["output_ids"]) != limit:
            raise ValueError("Apex token count differs from the checkpoint budget")
        ids.extend(result["output_ids"])
        segments.append({k: result[k] for k in ("elapsed_seconds", "timings", "output_tokens")})
        if result["stop"] == "eos" or len(ids) == budget:
            return dict(output_ids=ids, input_tokens=len(prompt), stop=result["stop"],
                        output_tokens=sum(s["output_tokens"] for s in segments),
                        elapsed_seconds=sum(s["elapsed_seconds"] for s in segments),
                        timings=segments[-1]["timings"], checkpoint_segments=segments)

        new_slot = slot_dir / f"{key}-{len(ids)}.bin"
        estimate = math.ceil(1.2 * bytes_per_cached_token * (len(prompt) + len(ids))) + 16 * 2**20
        if shutil.disk_usage(slot_dir).free < reserve + estimate:
            raise RuntimeError("The disk reserve is too small for the next Apex slot snapshot")
        saved = slot_action(url, "save", new_slot.name)
        if (saved["n_saved"] < len(prompt) + len(ids) - 1
                or saved["n_written"] != new_slot.stat().st_size
                or shutil.disk_usage(slot_dir).free < reserve):
            raise RuntimeError("Apex slot snapshot failed its extent or reserve check")
        save(ledger, dict(input_ids=prompt, output_ids=ids, segments=segments, saved=saved))
        if previous:
            previous.unlink()
        previous = new_slot
        print(key, "saved", len(ids), "generated tokens and matching KV state", flush=True)


def discard_completed_checkpoint(slot_dir, key, ledger):
    if ledger.exists():
        n = len(read(ledger)["output_ids"])
        (slot_dir / f"{key}-{n}.bin").unlink(missing_ok=True)
        ledger.unlink()
