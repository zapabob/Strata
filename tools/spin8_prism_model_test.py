"""Run the real-model C++ probe, deriving sidecars from its loaded bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import threading
import time

from spin8_prism_process import controlled_environment, library_receipts
from spin8_query_sidecar import Bindings, Layer, LayerSpec, encode


def make_sidecars(directory: Path) -> None:
    """Use independently measured model/config bindings, never guessed hashes."""
    info = json.loads((directory / "bindings.json").read_text(encoding="utf-8"))
    actual = info["bindings"]
    assert actual["models"] == ["0ab2a1f237b73e5002ecd8c9b764249b90ee59eca749a6226c44bb43b1036a13"]
    for field in ("profile", "position"):
        assert hashlib.sha256(bytes.fromhex(actual[field + "EncodingHex"])).hexdigest() == actual[field]
    assert len(actual["layers"]) == 16
    assert all(layer["q_heads"] == 24 and layer["kv_heads"] == 4 and layer["head_width"] == 256 for layer in actual["layers"])
    bindings = Bindings(tuple(bytes.fromhex(h) for h in actual["models"]),
                        bytes.fromhex(actual["profile"]), bytes.fromhex(actual["position"]))
    variants: dict[str, list[Layer]] = {"zero": [], "nonzero": []}
    for geometry in actual["layers"]:
        spec = LayerSpec(**geometry)
        counts = spec.parameter_counts()
        win = struct.pack(f"<{counts[0]}f", *(
            0.002 * math.sin(i + 3 * spec.layer_index) for i in range(counts[0])
        ))
        bin_data = bytes(counts[1] * 4)
        variants["zero"].append(Layer(spec, win, bin_data, bytes(counts[2]*4), bytes(counts[3]*4)))
        wout = struct.pack(f"<{counts[2]}f", *(
            0.03 * math.cos(i + spec.layer_index) for i in range(counts[2])
        ))
        bout = struct.pack(f"<{counts[3]}f", *(
            0.04 * math.sin(i + 1 + spec.layer_index) for i in range(counts[3])
        ))
        variants["nonzero"].append(Layer(spec, win, bin_data, wout, bout))
    for name, layers in variants.items():
        (directory / f"{name}.sp8q").write_bytes(encode(bindings, layers))
    wrong = Bindings((bytes([1])*32, *bindings.models[1:]), bindings.profile, bindings.position)
    (directory / "wrong-binding.sp8q").write_bytes(encode(wrong, variants["zero"]))
    wrong_profile = Bindings(bindings.models, bytes([2])*32, bindings.position)
    (directory / "wrong-profile.sp8q").write_bytes(encode(wrong_profile, variants["zero"]))
    wrong_position = Bindings(bindings.models, bindings.profile, bytes([3])*32)
    (directory / "wrong-position.sp8q").write_bytes(encode(wrong_position, variants["zero"]))
    missing_layer = variants["zero"][1:]
    (directory / "wrong-geometry.sp8q").write_bytes(encode(bindings, missing_layer))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=1800.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    environment, removed = controlled_environment()
    (args.output / "environment.json").write_text(json.dumps({"removedNames": removed}), encoding="utf-8")
    with (args.output / "stderr.log").open("w", encoding="utf-8") as errors, (
        args.output / "stdout.log"
    ).open("w", encoding="utf-8") as output:
        process = subprocess.Popen(
            [str(args.binary), str(args.model), str(args.output)], env=environment,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors,
            text=True, encoding="utf-8", errors="replace",
        )
        timed_out = threading.Event()

        def stop_overdue() -> None:
            timed_out.set()
            process.terminate()

        timer = threading.Timer(args.timeout, stop_overdue)
        timer.daemon = True
        timer.start()
        try:
            assert process.stdout and process.stdin
            for line in process.stdout:
                output.write(line)
                output.flush()
                if line.strip() == "SPIN8_BINDINGS_READY":
                    make_sidecars(args.output)
                    process.stdin.write("SIDECARS_READY\n")
                    process.stdin.flush()
            result = process.wait(timeout=30)
            if timed_out.is_set():
                raise TimeoutError(f"model probe exceeded {args.timeout} seconds")
            return result
        except BaseException:
            process.terminate()
            process.wait(timeout=30)
            raise
        finally:
            timer.cancel()
            output.flush()
            (args.output / "run.json").write_text(json.dumps({
                "binary": str(args.binary),
                "binarySha256": hashlib.sha256(args.binary.read_bytes()).hexdigest(),
                "model": str(args.model), "startEpoch": started,
                "elapsedSeconds": time.time() - started,
                "returncode": process.returncode, "timedOut": timed_out.is_set(),
                "libraries": library_receipts((args.output / "stdout.log").read_text(encoding="utf-8")),
            }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
