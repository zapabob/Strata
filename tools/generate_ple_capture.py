"""Reconstruct private PLE parity inputs from original GGUF weights and CPU GGML.

The diagnostic dense.bin contains only the two PLE regions required by the
existing test. It is not an inference pack. No Strata numerical implementation
generates the expected outputs: ple_capture_oracle uses pinned CPU GGML.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

PIN = "3cf03257f219afbe7334045ff7c6a06ac68c627d"
LAYOUT = {"codes": 1017723776, "scales": 1024277376, "value": 1025219456}

def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            result.update(block)
    return result.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gguf", required=True, type=Path)
    parser.add_argument("--table", required=True, type=Path)
    parser.add_argument("--ggml-source", required=True, type=Path)
    parser.add_argument("--oracle", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "-C", str(args.ggml_source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(args.ggml_source), "status", "--porcelain"], text=True)
    if revision != PIN or dirty.strip():
        raise SystemExit("The independent GGML source must match the clean reviewed pin")
    if args.out.exists():
        raise SystemExit("Use a fresh output directory; diagnostic evidence is not overwritten")
    import numpy as np
    sys.path.insert(0, str(args.ggml_source / "gguf-py"))
    from gguf import GGUFReader
    from gguf_reader import GGUFFile
    source, table = GGUFFile(args.gguf), GGUFFile(args.table)
    upstream = GGUFReader(str(args.gguf))
    own = {t.name: t for t in source.tensors}
    vendor = {t.name: t for t in upstream.tensors}
    used = {}
    def raw(name, expected_type, expected_shape):
        tensor = own[name]
        if tensor.type_name != expected_type or tensor.shape != expected_shape:
            raise ValueError("Unexpected original weight: " + name)
        independent = vendor[name]
        absolute = source.data_start + tensor.offset
        if int(independent.data_offset) != absolute or list(independent.shape) != expected_shape:
            raise ValueError("The two GGUF metadata readers disagree: " + name)
        with args.gguf.open("rb") as stream:
            stream.seek(absolute)
            data = stream.read(tensor.expected_bytes())
        if len(data) != tensor.expected_bytes() or data != independent.data.tobytes():
            raise ValueError("The independent original tensor bytes disagree: " + name)
        used[name] = {"offset": absolute, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        return data
    d, heads, nt, taps, dilation, epsilon = 2560, 4, 4, 4, 3, 1e-6
    channels, history = d * heads, (taps - 1) * dilation
    expected_metadata = {'general.architecture': 'qwen4exp', 'qwen4exp.hyper_connection.count': heads,
                         'qwen4exp.ple.ngram_size': dilation, 'qwen4exp.ple.conv_kernel': taps}
    if any(source.metadata.get(name) != value for name, value in expected_metadata.items()):
        raise ValueError('The original model metadata has different PLE geometry')
    if np.float32(source.metadata.get('qwen4exp.attention.layer_norm_rms_epsilon', 0)) != np.float32(epsilon):
        raise ValueError('The original model has a different RMS epsilon')
    key_raw = raw("blk.1.ple_key.weight", "Q2_0", [d, channels])
    blocks = np.frombuffer(key_raw, dtype=np.uint8).reshape(-1, 18)
    codes, scales = blocks[:, 2:].copy(), blocks[:, :2].copy()
    values = ((codes[:, :, None] >> np.array([0, 2, 4, 6], dtype=np.uint8)) & 3).reshape(-1, 64)
    scale_f32 = scales.reshape(-1).view("<f2").astype("<f4")
    key = (values.astype("<f4") - np.float32(1)) * scale_f32[:, None]
    value_raw = raw("blk.1.ple_value.weight", "BF16", [d, d])
    value = (np.frombuffer(value_raw, dtype="<u2").astype("<u4") << 16).view("<f4")
    norms = [np.frombuffer(raw("blk.1.ple_norm_" + suffix + ".weight", "F32", [channels]), dtype="<f4")
             for suffix in ("key", "query", "conv")]
    conv = np.frombuffer(raw("blk.1.ple_conv1d.weight", "F16", [taps, channels]), dtype="<f2").astype("<f4")
    if table.data_start != 192 or args.table.stat().st_size != 28800138432:
        raise ValueError("The PLE table is not the reviewed artifact")
    codebook = np.array([-127, -104, -83, -65, -49, -35, -22, -10, 1, 13, 25, 38, 53, 69, 89, 113], dtype="<f4")
    embeddings, rows_used = [], []
    with args.table.open("rb") as stream:
        for token in range(nt):
            row_ids = [12345 + token * 16 + head for head in range(16)]
            rows_used.append(row_ids)
            for row in row_ids:
                stream.seek(table.data_start + row * 90)
                b = np.frombuffer(stream.read(90), dtype=np.uint8).reshape(5, 18)
                scale = b[:, :2].copy().reshape(-1).view("<f2").astype("<f4")
                packed = b[:, 2:]
                unpacked = np.concatenate((packed & 15, packed >> 4), axis=1)
                embeddings.append((codebook[unpacked] * scale[:, None]).reshape(-1))
    embedding = np.concatenate(embeddings).astype("<f4")
    rng = np.random.default_rng(20261030)
    hidden = rng.normal(0, 0.25, (nt, channels)).astype("<f4")
    past = rng.normal(0, 0.1, (channels, history)).astype("<f4")
    arrays = [embedding, hidden, key, value, *norms, conv, past]
    if any(not np.isfinite(array).all() for array in arrays):
        raise ValueError("Non-finite original weights or diagnostic inputs")
    args.out.mkdir(parents=True)
    dense = args.out / "dense.bin"
    with dense.open("xb") as stream:
        stream.seek(LAYOUT["codes"]); stream.write(codes.tobytes())
        stream.seek(LAYOUT["scales"]); stream.write(scales.tobytes())
        stream.seek(LAYOUT["value"]); stream.write(value.tobytes())
    input_path, output_path = args.out / "ple_in.bin", args.out / "ple_out.bin"
    with input_path.open("xb") as stream:
        stream.write(struct.pack("<5if", d, heads, nt, taps, dilation, epsilon))
        for array in arrays:
            stream.write(array.astype("<f4", copy=False).tobytes())
    command = [str(args.oracle.resolve()), str(input_path.resolve()), str(output_path.resolve()),
               str(args.gguf.resolve()), str(used["blk.1.ple_key.weight"]["offset"]),
               str(used["blk.1.ple_value.weight"]["offset"])]
    outcome = subprocess.run(command, capture_output=True, text=True, timeout=180)
    (args.out / "oracle.log").write_text(outcome.stdout + outcome.stderr, encoding="utf-8")
    if outcome.returncode:
        raise SystemExit("Independent GGML reference failed; see oracle.log")
    expected = 12 + 4 * nt * (5 * channels + d + heads)
    if output_path.stat().st_size != expected:
        raise ValueError("Unexpected reference output size")
    record = {"schema": 1, "ggmlCommit": revision, "oracleSha256": digest(args.oracle),
              "generatorSha256": digest(Path(__file__)), "sourceTensorBytes": used,
              "tableRows": rows_used, "syntheticHiddenHistorySeed": 20261030,
              "geometry": {"d": d, "heads": heads, "tokens": nt, "taps": taps, "dilation": dilation, "epsilon": epsilon},
              "files": {p.name: {"bytes": p.stat().st_size, "sha256": digest(p)} for p in [dense, input_path, output_path]},
              "scope": "Partial legacy PLE diagnostic pack and independent CPU GGML reference; not an inference pack or full-model quality test"}
    (args.out / "fixture.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"created": str(args.out), "independentReference": True, "nativeParityTested": False}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
