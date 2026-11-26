"""Prepare byte-identical Mode B GGUF splits for a cross-volume MoE trial."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys

from gguf_stream import directory
from source import atomic_bytes


CHUNK = 16 * 2**20
SYSTEM_RESERVE = 5 * 2**30
MODEL_VOLUME_RESERVE = (1808 * 2**30 + 99) // 100
NVME_LAYERS = (0, 1, 2, 3)


def string(value):
    encoded = value.encode("utf-8")
    return struct.pack("<Q", len(encoded)) + encoded


def align(size, alignment):
    return (size + alignment - 1) & -alignment


def header(metadata, tensors, index, count, alignment):
    metadata = dict(metadata)
    for key, encoded in (("split.no", struct.pack("<IH", 2, index)),
                         ("split.count", struct.pack("<IH", 2, 2)),
                         ("split.tensors.count", struct.pack("<Ii", 5, count))):
        metadata[key] = string(key) + encoded
    data = bytearray(struct.pack("<4sIQQ", b"GGUF", 3, len(tensors), len(metadata)))
    for value in metadata.values():
        data.extend(value)
    offset = 0
    for tensor in tensors:
        data.extend(string(tensor.name))
        shape = tensor.shape
        data.extend(struct.pack("<I" + "Q" * len(shape) + "IQ", len(shape), *shape, tensor.tensor_type, offset))
        offset += align(tensor.n_bytes, alignment)
    data.extend(bytes(align(len(data), alignment) - len(data)))
    return data, len(data) + offset


def payload(stream, tensor, output=None):
    stream.seek(tensor.data_offset)
    remaining = tensor.n_bytes
    digest = hashlib.sha256()
    while remaining:
        data = stream.read(min(remaining, CHUNK))
        if not data:
            raise EOFError(f"Incomplete tensor {tensor.name}")
        if output is not None:
            output.write(data)
        digest.update(data)
        remaining -= len(data)
    return digest.hexdigest()


def read_model(model, sizes):
    manifest = json.loads(model.with_suffix(".manifest.json").read_bytes())
    if model.stat().st_size != manifest["bytes"]:
        raise ValueError(f"Model length changes for {model.name}")
    metadata = {}
    fields, tensors = directory(model, sizes, metadata_records=metadata)
    if (fields.get("general.architecture") != "inkling2_loop" or len(tensors) != 752
            or any(key.startswith("split.") for key in fields)):
        raise ValueError(f"Expected a single-file Inkling Mode B model in {model.name}")
    return metadata, tensors, fields.get("general.alignment", 32)


def write_shard(path, model, tensors, data, size, alignment, sizes, reserve):
    if shutil.disk_usage(path.parent).free < reserve + size:
        raise OSError(f"Insufficient storage reserve for {path}")
    stage = path.with_suffix(".gguf.partial")
    if path.exists():
        raise FileExistsError(path)
    expected = {}
    with model.open("rb") as source, stage.open("xb") as output:
        output.write(data)
        for tensor in tensors:
            if shutil.disk_usage(path.parent).free < reserve + tensor.n_bytes:
                raise OSError(f"Storage reserve reached while staging {path.name}")
            expected[tensor.name] = payload(source, tensor, output)
            output.write(bytes(align(tensor.n_bytes, alignment) - tensor.n_bytes))
        output.flush()
        os.fsync(output.fileno())
    _, copied = directory(stage, sizes)
    if (stage.stat().st_size != size or
            [(t.name, t.shape, t.tensor_type) for t in copied] !=
            [(t.name, t.shape, t.tensor_type) for t in tensors]):
        raise ValueError(f"Split GGUF directory verification failed for {path.name}")
    with stage.open("rb") as source:
        if any(payload(source, tensor) != expected[tensor.name] for tensor in copied):
            raise ValueError(f"Split GGUF payload verification failed for {path.name}")
    print(f"Verified {path.name} ({size:,} bytes, {len(tensors)} tensors)", flush=True)
    return stage, expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("old", "nvfp4", "upstream", "backbone-dir", "nvme-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.upstream / "gguf-py"))
    from gguf import GGML_QUANT_SIZES, GGMLQuantizationType

    roots = (args.backbone_dir.resolve(), args.nvme_dir.resolve())
    if not roots[0].drive or not roots[1].drive or roots[0].drive.upper() == roots[1].drive.upper():
        raise ValueError("Expected separate Windows volumes for backbone and Expert shard")
    models = {"old": args.old.resolve(), "nvfp4": args.nvfp4.resolve()}
    loaded = {arm: read_model(path, GGML_QUANT_SIZES) for arm, path in models.items()}
    names = {f"blk.{layer}.ffn_{projection}_exps.weight"
             for layer in NVME_LAYERS for projection in ("gate_up", "down")}
    banks = {arm: [t for t in tensors if t.name in names] for arm, (_, tensors, _) in loaded.items()}
    signatures = {arm: {t.name: (t.shape, t.tensor_type, t.n_bytes) for t in group}
                  for arm, group in banks.items()}
    if (set(signatures["old"]) != names or signatures["old"] != signatures["nvfp4"]
            or any(t.tensor_type != GGMLQuantizationType.NVFP4 for t in banks["nvfp4"])
            or loaded["old"][2] != loaded["nvfp4"][2]):
        raise ValueError("The selected NVFP4 Expert banks are incompatible")

    alignment = loaded["nvfp4"][2]
    plans = []
    for arm, (metadata, tensors, _) in loaded.items():
        tensors_to_write = [t for t in tensors if t.name not in names]
        data, size = header(metadata, tensors_to_write, 0, len(tensors), alignment)
        plans.append((arm, roots[0] / f"{arm}-backbone.gguf", tensors_to_write, data, size))
    shared = banks["nvfp4"]
    metadata = loaded["nvfp4"][0]
    alignment_record = {"general.alignment": metadata["general.alignment"]} if "general.alignment" in metadata else {}
    data, size = header(alignment_record, shared, 1, 752, alignment)
    plans.append(("shared", roots[1] / "expert-layers-0-3.gguf", shared, data, size))
    report_path = roots[0] / "nvme-expert-shards.json"
    report = dict(architecture="inkling2_loop", physical_expert_layers=list(NVME_LAYERS),
                  originals={arm: str(path) for arm, path in models.items()},
                  shards={arm: dict(path=str(path), bytes=n, tensors=len(tensors))
                          for arm, path, tensors, _, n in plans})
    print(json.dumps(report, indent=2), flush=True)
    required_backbone = sum(plan[4] for plan in plans[:-1]) + MODEL_VOLUME_RESERVE
    if (shutil.disk_usage(roots[0].anchor).free < required_backbone
            or shutil.disk_usage(roots[1].anchor).free < size + SYSTEM_RESERVE):
        raise OSError("The backbone or NVMe volume has insufficient free space")
    if args.dry_run:
        return

    for root in roots:
        root.mkdir(parents=True, exist_ok=True)
    if report_path.exists() or any(path.exists() or path.with_suffix(".gguf.partial").exists()
                                    for _, path, _, _, _ in plans):
        raise FileExistsError("The selected staging paths already contain a model or staged bytes")
    with models["old"].open("rb") as old, models["nvfp4"].open("rb") as nvfp4:
        old_hashes = {t.name: payload(old, t) for t in banks["old"]}
        if old_hashes != {t.name: payload(nvfp4, t) for t in shared}:
            raise ValueError("Shared Expert shard payloads differ between the two original models")
    complete = []
    for arm, path, tensors, data, n in plans:
        stage, hashes = write_shard(path, models["nvfp4" if arm == "shared" else arm], tensors, data, n,
                                    alignment, GGML_QUANT_SIZES,
                                    SYSTEM_RESERVE if arm == "shared" else MODEL_VOLUME_RESERVE)
        if arm == "shared" and hashes != old_hashes:
            raise ValueError("Shared Expert shard no longer matches the old model")
        complete.append((stage, path))
    for stage, path in complete:
        stage.rename(path)
    report["verified_payloads"] = 752 * len(models)
    report["shared_tensor_payloads"] = len(shared)
    atomic_bytes(report_path, (json.dumps(report, indent=2) + "\n").encode("utf-8"))
    print(f"Published split verification at {report_path}", flush=True)


if __name__ == "__main__":
    main()
