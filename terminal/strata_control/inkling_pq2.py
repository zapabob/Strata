"""Validate the basis and tensor directory of a local Inkling PQ2_0 GGUF."""
from pathlib import Path


def inspect_model(path: Path) -> int:
    from tools.gguf_reader import GGUFFile

    header = GGUFFile(path)
    meta = header.metadata
    contract = {
        "general.architecture": "inkling2_loop",
        "prism.hadamard.version": 1,
        "prism.hadamard.block_size": 128,
        "prism.hadamard.transform": "normalized-sylvester-walsh-hadamard",
        "prism.hadamard.axis": "input-last-dimension",
        "prism.hadamard.sign_mode": "identity",
    }
    if any(meta.get(k) != value for k, value in contract.items()):
        raise ValueError("Choose an Inkling 2 Mini GGUF with the conventional PQ2_0 Hadamard transform.")
    expected = {f"blk.{layer}.ffn_{projection}_exps.weight" for layer in range(24)
                for projection in ("gate_up", "down")}
    banks = [t for t in header.tensors if t.type_id == 142]
    named = meta.get("prism.hadamard.weight_names")
    transformed = {t.name for t in banks}
    if not transformed or not transformed.issubset(expected) or not expected.issubset({t.name for t in header.tensors}):
        raise ValueError("The GGUF must contain both routed banks for all 24 physical layers.")
    if (not isinstance(named, list) or any(not isinstance(n, str) for n in named)
            or len(named) != len(banks) or set(named) != transformed):
        raise ValueError("The Hadamard declarations must match the physical PQ2_0 expert banks.")
    if any(len(t.shape) != 3 or t.shape[-1] != 128 or t.shape[0] % 128 for t in banks):
        raise ValueError("A PQ2_0 expert bank has invalid dimensions.")
    end = path.stat().st_size - header.data_start
    previous_end = 0
    for tensor in sorted(header.tensors, key=lambda t: t.offset):
        size = tensor.elements // 128 * 34 if tensor.type_id == 142 else tensor.expected_bytes()
        if size is None or tensor.offset % header.alignment or tensor.offset < previous_end or tensor.offset + size > end:
            raise ValueError(f"The GGUF contains an invalid or unsupported tensor extent for {tensor.name}.")
        previous_end = tensor.offset + size
    limit = meta.get("inkling2_loop.context_length")
    if type(limit) is not int or limit <= 0:
        raise ValueError("The GGUF omits the Inkling maximum context length.")
    return limit
