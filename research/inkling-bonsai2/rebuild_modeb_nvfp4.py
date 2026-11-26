"""Rebuild Inkling Heretic Mode B with source-derived NVFP4 attention matrices."""
import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import struct

from filelock import FileLock
import torch

from gguf_stream import directory
from quantize_inkling2_pq2 import Checkpoint, NativeMixed, mapped, upstream
from source import REPO, atomic_bytes, await_capacity


CHUNK = 16 * 1024**2
ATTENTION = frozenset(("attn_q", "attn_k", "attn_v", "attn_output", "attn_gate"))
PROFILE = "heretic-modeb-nvfp4"


def read_json(path):
    return json.loads(path.read_bytes())


def json_bytes(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode("utf-8")


def gguf_string(value):
    raw = value.encode("utf-8")
    return struct.pack("<Q", len(raw)) + raw


def string_field(name, value):
    return gguf_string(name) + struct.pack("<I", 8) + gguf_string(value)


def align(offset, alignment):
    return (offset + alignment - 1) & -alignment


def make_plan(args, gguf, model_cls, checkpoint):
    original_manifest = read_json(args.source / "source.json")
    verified = read_json(Path(str(checkpoint.file) + ".verified.json"))
    expected_bytes = original_manifest["files"][checkpoint.file.name]["size"]
    if checkpoint.repo != REPO or verified != {"bytes": expected_bytes, "matched_publisher_digest": True}:
        raise ValueError("Expected a verified Heretic source checkpoint")
    if checkpoint.file.stat().st_size != expected_bytes:
        raise ValueError("Unexpected source checkpoint length")
    baseline_manifest = read_json(args.baseline.with_suffix(".manifest.json"))
    if baseline_manifest["bytes"] != args.baseline.stat().st_size:
        raise ValueError("Mode B file length differs from its manifest")

    metadata = {}
    fields, tensors = directory(args.baseline, gguf.GGML_QUANT_SIZES, metadata_records=metadata)
    if (fields["general.architecture"] != "inkling2_loop"
            or fields["inkling_quant.source"] != checkpoint.repo
            or fields["inkling_quant.revision"] != checkpoint.revision):
        raise ValueError("Mode B and the source checkpoint have different provenance")
    pq2 = gguf.GGMLQuantizationType.PQ2_0
    nvfp4 = gguf.GGMLQuantizationType.NVFP4
    q6k = gguf.GGMLQuantizationType.Q6_K
    targets = {t.name for t in tensors if t.tensor_type == pq2}
    expected = {f"blk.{layer}.{projection}.weight" for layer in range(24) for projection in ATTENTION}
    if targets != expected:
        raise ValueError("The selected Mode B must have precisely 120 PQ2_0 attention matrices")
    head = {t.name: t.tensor_type for t in tensors if t.name in {"token_embd.weight", "output.weight"}}
    experts = [t for t in tensors if t.name.endswith((".ffn_gate_up_exps.weight", ".ffn_down_exps.weight"))]
    scales = {t.name for t in tensors if t.tensor_type == gguf.GGMLQuantizationType.F32 and t.shape == (128,)}
    if head != {"token_embd.weight": q6k, "output.weight": q6k}:
        raise ValueError("Mode B must contain the Q6_K embedding and output head")
    if (len(experts) != 48 or any(t.tensor_type != nvfp4 for t in experts)
            or any(t.name.removesuffix("weight") + "scale" not in scales for t in experts)):
        raise ValueError("Mode B does not provide all NVFP4 expert banks and outer scales")

    file_type = gguf.LlamaFileType.MOSTLY_NVFP4
    model = model_cls(checkpoint.path, file_type, args.output, model_name=args.output.stem)
    sources = {name: (raw, shape, layer) for raw, name, shape, _, layer in mapped(model, checkpoint)
               if name in targets}
    if set(sources) != targets:
        raise ValueError("An attention matrix has no mapping to the original checkpoint")
    entries = []
    for tensor in sorted(tensors, key=lambda t: t.data_offset):
        entry = dict(name=tensor.name, gguf_shape=list(tensor.shape),
                     old_type=gguf.GGMLQuantizationType(tensor.tensor_type).name,
                     new_type=gguf.GGMLQuantizationType(tensor.tensor_type).name,
                     old_bytes=tensor.n_bytes, bytes=tensor.n_bytes, old_offset=tensor.data_offset)
        if tensor.name in targets:
            raw, shape, layer = sources[tensor.name]
            group, block_bytes = gguf.GGML_QUANT_SIZES[nvfp4]
            if (len(shape) != 2 or tuple(reversed(shape)) != tensor.shape or shape[-1] % group
                    or checkpoint.header[raw]["dtype"] != "BF16"):
                raise ValueError(f"No compatible original BF16 matrix for {tensor.name}")
            entry.update(new_type=nvfp4.name, bytes=tensor.n_elements // group * block_bytes,
                         source_tensor=raw, source_type="BF16", physical_layer=layer)
        entries.append(entry)

    metadata = {key: value for key, value in metadata.items()
                if not key.startswith(("prism.hadamard.", "spin8."))}
    metadata["general.name"] = string_field("general.name", args.output.stem)
    if "general.basename" in metadata:
        metadata["general.basename"] = string_field("general.basename", args.output.stem)
    metadata["inkling_quant.profile"] = string_field("inkling_quant.profile", PROFILE)
    metadata["general.file_type"] = gguf_string("general.file_type") + struct.pack("<II", 4, int(file_type))
    alignment = fields.get("general.alignment", 32)
    header = bytearray(struct.pack("<4sIQQ", b"GGUF", 3, len(entries), len(metadata)))
    for record in metadata.values():
        header.extend(record)
    relative_end = 0
    for entry in entries:
        shape = entry["gguf_shape"]
        offset = align(relative_end, alignment)
        header.extend(gguf_string(entry["name"]))
        header.extend(struct.pack("<I" + "Q"*len(shape) + "IQ", len(shape), *shape,
                                  int(gguf.GGMLQuantizationType[entry["new_type"]]), offset))
        entry["relative_offset"] = offset
        relative_end = offset + entry["bytes"]
    header.extend(bytes(align(len(header), alignment) - len(header)))
    file_bytes = len(header) + align(relative_end, alignment)
    recipe = dict(schema="inkling-modeb-dense-nvfp4-v1", name=args.output.stem,
                  output_file=args.output.name, architecture=fields["general.architecture"],
                  source=dict(repository=checkpoint.repo, revision=checkpoint.revision,
                              verified_shard=checkpoint.file.name, bytes=expected_bytes),
                  baseline=dict(filename=args.baseline.name, bytes=baseline_manifest["bytes"],
                                sha256=baseline_manifest["sha256"]),
                  conversion=dict(input="Mapped original BF16 values", output="GGML NVFP4 (type 40)",
                                  quantiser="ggml_quantize_chunk", block_weights=64, block_bytes=36,
                                  transforms="Identity", other_tensors="Copy verified Mode B payload bytes"),
                  changed_tensors=len(targets), tensor_count=len(entries),
                  format_counts=dict(sorted(Counter(e["new_type"] for e in entries).items())),
                  file_bytes=file_bytes, growth_bytes=file_bytes - baseline_manifest["bytes"],
                  data_offset=len(header), tensors=entries)
    return recipe, header, metadata, model


def transfer(stream, count, digest, emit=None):
    if count < 0:
        raise ValueError("Invalid Mode B tensor offset")
    while count:
        block = stream.read(min(count, CHUNK))
        if not block:
            raise EOFError("Truncated Mode B payload")
        digest.update(block)
        if emit is not None:
            emit(block)
        count -= len(block)


def original_matrix(checkpoint, model, entry):
    name, _ = model.filter_tensors((entry["source_tensor"], None))
    tensors = dict(model.modify_tensors(checkpoint.raw(entry["source_tensor"]), name, entry["physical_layer"]))
    weight = tensors[entry["name"]]
    if list(reversed(weight.shape)) != entry["gguf_shape"] or not torch.isfinite(weight).all().item():
        raise ValueError("Invalid source weights for " + entry["name"])
    return weight


def write_or_verify(target, staged_bytes, block):
    """Verify an existing prefix before appending to an interrupted build."""
    reused = max(0, min(len(block), staged_bytes - target.tell()))
    if reused and target.read(reused) != block[:reused]:
        raise IOError("Existing staged bytes differ from the verified rendering")
    pending = block[reused:] if reused else block
    if pending and target.write(pending) != len(pending):
        raise OSError("Short GGUF write")


def rebuild(args, gguf, checkpoint, recipe, header, metadata, model):
    if args.output.exists():
        raise FileExistsError(args.output)
    stage = args.output.with_suffix(".gguf.resume.partial")
    existing = stage.exists()
    staged_bytes = stage.stat().st_size if existing else 0
    if staged_bytes > recipe["file_bytes"]:
        raise IOError("Existing staged file is larger than the planned GGUF")
    await_capacity(args.output.parent, recipe["file_bytes"] - staged_bytes)
    codec = NativeMixed(args.ggml_base.resolve(strict=True))
    baseline_hash, written_hash = hashlib.sha256(), hashlib.sha256()
    errors = {}
    with args.baseline.open("rb") as previous, stage.open("r+b" if existing else "x+b") as target:
        def emit(block):
            write_or_verify(target, staged_bytes, block)
            written_hash.update(block)

        emit(header)
        next_progress = 1024**3
        for entry in recipe["tensors"]:
            start = recipe["data_offset"] + entry["relative_offset"]
            if start < target.tell():
                raise IOError("New tensor offsets overlap")
            must_convert = "source_tensor" in entry
            if start >= next_progress or must_convert:
                await_capacity(args.output.parent, recipe["file_bytes"] - max(staged_bytes, target.tell()))
            if start >= next_progress:
                print(f"{start / 1024**3:.2f} GiB verified or written", flush=True)
                next_progress = (start // 1024**3 + 1) * 1024**3
            emit(bytes(start - target.tell()))
            transfer(previous, entry["old_offset"] - previous.tell(), baseline_hash)
            if not must_convert:
                transfer(previous, entry["old_bytes"], baseline_hash, emit)
                continue
            transfer(previous, entry["old_bytes"], baseline_hash)
            weight = original_matrix(checkpoint, model, entry)
            columns = weight.shape[-1]
            row_bytes = columns // 64 * 36
            square_error = 0.
            for first in range(0, weight.shape[0], 512):
                rows = weight[first:first + 512]
                packed, error = codec.encode(rows, gguf.GGMLQuantizationType.NVFP4, len(rows)*row_bytes)
                emit(packed)
                square_error += error
            if target.tell() != start + entry["bytes"]:
                raise IOError("Short NVFP4 tensor write")
            errors[entry["name"]] = square_error / math.prod(weight.shape)
        transfer(previous, recipe["baseline"]["bytes"] - previous.tell(), baseline_hash)
        emit(bytes(recipe["file_bytes"] - target.tell()))
        target.flush()
        os.fsync(target.fileno())

    if baseline_hash.hexdigest() != recipe["baseline"]["sha256"]:
        raise IOError("Mode B payload differs from its verified build")
    actual_metadata = {}
    _, tensors = directory(stage, gguf.GGML_QUANT_SIZES, metadata_records=actual_metadata)
    actual = [(t.name, list(t.shape), int(t.tensor_type), t.n_bytes, t.data_offset) for t in tensors]
    expected = [(e["name"], e["gguf_shape"], int(gguf.GGMLQuantizationType[e["new_type"]]),
                 e["bytes"], recipe["data_offset"] + e["relative_offset"]) for e in recipe["tensors"]]
    if actual_metadata != metadata or actual != expected or stage.stat().st_size != recipe["file_bytes"]:
        raise IOError("Final GGUF differs from the recipe")
    with stage.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != written_hash.hexdigest():
        raise IOError("File readback differs from the streamed writes")
    if args.output.exists():
        raise FileExistsError(args.output)
    stage.rename(args.output)
    count = sum(math.prod(e["gguf_shape"]) for e in recipe["tensors"]
                if not e["name"].endswith((".ffn_gate_up_exps.scale", ".ffn_down_exps.scale")))
    manifest = dict(file=args.output.name, bytes=recipe["file_bytes"], sha256=digest,
                    recipe=args.recipe.name, format_counts=recipe["format_counts"],
                    bitwise_reused_tensors=recipe["tensor_count"]-len(errors),
                    effective_file_bits_per_weight=recipe["file_bytes"]*8/count,
                    source_to_nvfp4_weight_mse=errors)
    atomic_bytes(args.output.with_suffix(".manifest.json"), json_bytes(manifest))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "build"))
    for name in ("source", "baseline", "llama", "output"):
        parser.add_argument("--"+name, type=Path, required=True)
    parser.add_argument("--ggml-base", type=Path)
    args = parser.parse_args()
    if args.output.suffix.lower() != ".gguf" or "bonsai2" in args.output.stem.casefold():
        parser.error("Use a new .gguf name without Bonsai2")
    if args.output.resolve() == args.baseline.resolve():
        parser.error("Output must differ from the existing Mode B GGUF")
    if args.action == "build" and args.ggml_base is None:
        parser.error("Building requires the NVFP4-capable --ggml-base library")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.recipe = args.output.parent / "quantisation_recipe.json"
    with FileLock(str(args.recipe)+".lock"), torch.inference_mode():
        gguf, model_cls = upstream(args.llama)
        args.source = args.source.resolve(strict=True)
        checkpoint = Checkpoint(args.source)
        recipe, header, metadata, model = make_plan(args, gguf, model_cls, checkpoint)
        if args.recipe.exists():
            if read_json(args.recipe) != recipe:
                raise ValueError("The checked-in-place recipe differs from the requested build")
        else:
            atomic_bytes(args.recipe, json_bytes(recipe))
        print(f"{recipe['changed_tensors']} tensors -> NVFP4; {recipe['file_bytes']:,} bytes", flush=True)
        if args.action == "build":
            rebuild(args, gguf, checkpoint, recipe, header, metadata, model)
            print(args.output, flush=True)


if __name__ == "__main__":
    main()
