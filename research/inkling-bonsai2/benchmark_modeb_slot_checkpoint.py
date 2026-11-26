"""Validate exact greedy continuation across an Inkling CUDA server restart."""

import argparse
from pathlib import Path
import shutil

from benchmark_generation import local_server, read, save
from benchmark_modeb_mathematics import apex_completion
from benchmark_modeb_nvfp4 import BATCH, MICROBATCH, SERVER_FLAGS, stamp
from modeb_apex_state import slot_action


def probe(args, protocol, arm, model):
    folder = args.out / arm
    folder.mkdir(parents=True, exist_ok=True)
    result = folder / "parity.json"
    if result.exists():
        return read(result)
    capacity = protocol["context"]
    seed = protocol["seed"]
    ids = protocol["items"]["apex2025-2"]["ids"]
    controls = sorted(folder.glob("*/control.json"), reverse=True)
    attempt = controls[0].parent if controls else folder / stamp()
    attempt.mkdir(exist_ok=True)
    filename = "prefix.bin"
    opts = dict(batch=BATCH, ubatch=MICROBATCH,
                extra=(*SERVER_FLAGS, "--slot-save-path", str(attempt)), exclusive_gpu=True)
    if controls:
        state = read(controls[0])
        whole, first, saved = state["whole"], state["first"], state["checkpoint"]
        if state["ids"] != ids or saved["n_written"] != (attempt / filename).stat().st_size:
            raise ValueError("The recorded continuation control does not match its cache")
    else:
        if shutil.disk_usage(attempt).free < 19 * 2**30:
            raise RuntimeError("Insufficient disk reserve for a slot checkpoint probe")
        with local_server(args.server, model, attempt / "before", 1, capacity, **opts) as url:
            whole = apex_completion(url, ids, 128, seed)
            first = apex_completion(url, ids, 64, seed)
            if (whole["stop"] != "limit" or len(whole["output_ids"]) != 128 or first["stop"] != "limit"
                    or first["output_ids"] != whole["output_ids"][:64]):
                raise ValueError("The short control did not generate the expected common prefix")
            saved = slot_action(url, "save", filename)
            if (saved["n_saved"] < len(ids) + 63
                    or saved["n_written"] != (attempt / filename).stat().st_size):
                raise ValueError("The saved state does not cover the controlled prefix")
            save(attempt / "control.json", dict(ids=ids, whole=whole, first=first, checkpoint=saved))
    with local_server(args.server, model, attempt / ("after-" + stamp()), 1, capacity, **opts) as url:
        restored = slot_action(url, "restore", filename)
        if restored["n_restored"] != saved["n_saved"] or restored["n_read"] != saved["n_written"]:
            raise ValueError("The restored state has a different extent")
        resumed = apex_completion(url, ids + first["output_ids"], 64, seed, cache_prompt=True)
    cache_n = resumed["timings"].get("cache_n", 0)
    verified = (resumed["stop"] == "limit" and cache_n >= len(ids) + 63
                and resumed["output_ids"] == whole["output_ids"][64:])
    outcome = dict(model=model.name, input_tokens=len(ids), prefix_tokens=64, suffix_tokens=64,
                   saved=saved, restored=restored, cached_tokens=cache_n, resumed=resumed,
                   token_for_token_equal=verified, receipt=str(attempt))
    save(attempt / "outcome.json", outcome)
    if not verified:
        raise ValueError("A restarted server did not reproduce the continuous greedy tokens with a cached prefix")
    save(result, outcome)
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("old", "new", "server", "protocol", "out"):
        parser.add_argument("--" + flag, required=True, type=Path)
    args = parser.parse_args()
    protocol = read(args.protocol)
    validation = {}
    for arm, model in (("nvfp4", args.new), ("old", args.old)):
        validation[arm] = probe(args, protocol, arm, model)
        print(arm, "exact continuation confirmed", validation[arm]["cached_tokens"], "cached input tokens", flush=True)
    save(args.out / "parity.json", validation)


if __name__ == "__main__":
    main()
