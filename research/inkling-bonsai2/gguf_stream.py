"""Read GGUF v3 directories through a buffered stream, leaving model data on disk."""
import math
import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Extent:
    name: str
    shape: tuple
    tensor_type: int
    data_offset: int
    n_elements: int
    n_bytes: int


def directory(path, quant_sizes, header_only=False):
    path = Path(path)
    file_size = path.stat().st_size
    widths = {0: 1, 1: 1, 2: 2, 3: 2, 4: 4, 5: 4, 6: 4, 7: 1, 10: 8, 11: 8, 12: 8}
    fields = {}
    extents = []
    with path.open("rb", buffering=1024 * 1024) as f:
        def read(n):
            if n < 0 or n > 8 * 1024**2:
                raise ValueError("Excessive GGUF directory field")
            data = f.read(n)
            if len(data) != n:
                raise EOFError("Truncated GGUF directory")
            return data

        def number(fmt):
            return struct.unpack("<" + fmt, read(struct.calcsize("<" + fmt)))[0]

        def skip(n):
            if n < 0 or f.tell() + n > file_size:
                raise EOFError("Invalid GGUF metadata extent")
            f.seek(n, 1)

        def string():
            return read(number("Q")).decode("utf-8")

        def value(kind, keep=False):
            if kind == 8:
                if keep:
                    return string()
                skip(number("Q"))
            elif kind == 9:
                subtype, count = number("I"), number("Q")
                if subtype in widths:
                    skip(count * widths[subtype])
                elif subtype == 8 and count <= file_size // 8:
                    for _ in range(count):
                        skip(number("Q"))
                else:
                    raise ValueError("Invalid GGUF array")
            elif kind in widths:
                raw = read(widths[kind])
                if keep:
                    return int.from_bytes(raw, "little")
            else:
                raise ValueError("Unknown GGUF metadata type")

        if read(4) != b"GGUF" or number("I") != 3:
            raise ValueError("Expected a little-endian GGUF v3 file")
        tensor_count, fields_count = number("Q"), number("Q")
        if tensor_count > file_size // 24 or fields_count > file_size // 12:
            raise ValueError("Excessive GGUF directory count")
        for _ in range(fields_count):
            key, kind = string(), number("I")
            if key in fields:
                raise ValueError("Duplicate GGUF key " + key)
            fields[key] = value(kind, key in {"general.alignment", "general.architecture", "spin8.version",
                                              "inkling_quant.revision", "inkling_quant.profile", "inkling_quant.source"})
        alignment = fields.get("general.alignment", 32)
        if not isinstance(alignment, int) or alignment <= 0 or alignment & (alignment - 1):
            raise ValueError("Invalid tensor alignment")
        names = set()
        for _ in range(tensor_count):
            name, dimensions = string(), number("I")
            if not 1 <= dimensions <= 4 or name in names:
                raise ValueError("Invalid GGUF tensor " + name)
            names.add(name)
            shape = tuple(number("Q") for _ in range(dimensions))
            kind, offset = number("I"), number("Q")
            group, byte_count = quant_sizes[kind]
            if not all(shape) or shape[0] % group or offset % alignment:
                raise ValueError("Misaligned tensor " + name)
            elements = math.prod(shape)
            extents.append(Extent(name, shape, kind, offset, elements, elements // group * byte_count))
        start = (f.tell() + alignment - 1) & -alignment
    end = start
    for tensor in sorted(extents, key=lambda t: t.data_offset):
        tensor.data_offset += start
        if tensor.data_offset < end:
            raise ValueError("Overlapping tensor " + tensor.name)
        end = tensor.data_offset + tensor.n_bytes
    if not header_only and (end > file_size or file_size - end >= alignment):
        raise ValueError("GGUF tensor extents do not cover the file")
    return fields, extents
