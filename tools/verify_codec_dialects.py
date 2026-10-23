"""Generate bounded standalone pinned C oracles and deterministic byte fixtures.

No new codec code is read or imported. Run --prepare, compile generated CMake
project, then --fixtures. Existing files are never deleted. Pinned repositories
must be clean; no fetching or dependency installation is performed.
"""

import argparse
import hashlib
import json
import logging
from pathlib import Path
import random
import re
import struct
import subprocess

PINS = {
    "thetom": "643956891dfdf51aecdbd05ca508dd21e21e8195",
    "prism": "73bfe6cc485554822f80c473a3c0c4f25e80f41b",
    "native": "3cf03257f219afbe7334045ff7c6a06ac68c627d",
}
SPECS = {
    "thetom": [(i, f"turbo{i+1}_0", 128, 18 + 16 * i) for i in range(1, 6)]
    + [(6, "tq3_1s", 32, 16), (7, "tq4_1s", 32, 20)],
    "prism": [(8, "pq2_0", 128, 34), (9, "ptq1_0", 128, 28), (10, "q2_0", 64, 18)],
    "native": [(11, "q2_0", 64, 18)],
}


def digest(path: Path) -> str:
    """Hash a small source or fixture file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function(source: str, name: str) -> str:
    """Extract one complete original function without editing its arithmetic."""
    match = re.search(r"(?m)^void " + re.escape(name) + r"\([^\n]+\) \{", source)
    if match is None:
        raise ValueError(f"Missing pinned function: {name}")
    end, depth = match.end(), 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[match.start() : end]


def driver(kind: str) -> str:
    """Build file IO around original encoder and decoder functions."""
    cases = []
    for ident, name, width, size in SPECS[kind]:
        cases.append(f"""case {ident}: {{
            block_{name} blocks[2];
            if(n % {width} || n > 2*{width}) return 6;
            nb=(n/{width})*sizeof(block_{name});
            if(sizeof(block_{name})!={size}) return 7;
            if(mode==2) {{ if(fread(blocks,1,nb,in)!=nb)return 8; }}
            else quantize_row_{name}_ref(src,blocks,n);
            memcpy(packed,blocks,nb);
            dequantize_row_{name}(blocks,decoded,n);
            break;
        }}""")
    scalar = (
        """
        oracle_scalar=(mode==1);
        if(oracle_scalar) {
            if(id>5 || n!=128)return 10;
            memcpy(oracle_coords,x,sizeof(oracle_coords));
            memset(original,0,sizeof(original));original[0]=norm;src=original;
            norm=sqrtf(norm*norm);
        }
    """
        if kind == "thetom"
        else "if(mode==1)return 10;"
    )
    return r"""
#include <stdio.h>
int main(int argc,char **argv) {
    if(argc!=3)return 1;
    const uint32_t endian=1;
    if(*(const unsigned char *)&endian!=1)return 2;
    FILE *in=fopen(argv[1],"rb"),*out=fopen(argv[2],"wb");
    if(!in || !out)return 3;
    uint32_t id,mode,n,nb;
    float norm,x[256],original[256],decoded[256];
    unsigned char packed[196];
    while(fread(&id,4,1,in)==1) {
        if(fread(&mode,4,1,in)!=1||fread(&n,4,1,in)!=1||fread(&norm,4,1,in)!=1)return 4;
        if(n==0||n>256||mode>2||fread(x,4,n,in)!=n)return 5;
        const float *src=x;
        (void)original;
        SCALAR_SETUP
        switch(id) { CASES default:return 9; }
        if(fwrite(&id,4,1,out)!=1||fwrite(&mode,4,1,out)!=1||fwrite(&n,4,1,out)!=1||
           fwrite(&norm,4,1,out)!=1||fwrite(x,4,n,out)!=n||fwrite(&nb,4,1,out)!=1||
           fwrite(packed,1,nb,out)!=nb||fwrite(decoded,4,n,out)!=n)return 11;
    }
    if(ferror(in)||ferror(out))return 12;
    fclose(in);return fclose(out)?13:0;
}
""".replace("SCALAR_SETUP", scalar).replace("CASES", "\n".join(cases))


def prepare(args: argparse.Namespace) -> None:
    """Verify source pins and generate independent bounded C translation units."""
    manifest: dict[str, object] = {
        "sources": {},
        "equality": "encoder bytes and decoded F32 bits, including signed zero",
    }
    cmake = [
        "cmake_minimum_required(VERSION 3.24)",
        "project(dialect_oracles LANGUAGES C)",
    ]
    for kind, pin in PINS.items():
        root = Path(getattr(args, kind)).resolve()
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"], text=True
        )
        if head != pin or dirty:
            raise ValueError(f"{kind}: wrong revision or dirty oracle source")
        ggml = root / "ggml"
        path = (
            ggml
            / "src"
            / ("ggml-turbo-quant.c" if kind == "thetom" else "ggml-quants.c")
        )
        source = path.read_text(encoding="utf-8")
        files = [
            path,
            ggml / "src/ggml-common.h",
            ggml / "src/ggml-impl.h",
            ggml / "src/ggml-quants.h",
            ggml / "include/ggml.h",
            root / "LICENSE",
        ]
        manifest["sources"][kind] = {
            "revision": head,
            "sha256": {str(p.relative_to(root)): digest(p) for p in files},
        }
        if kind == "thetom":
            # The original scalar packing functions remain verbatim. A harness-only
            # hook at the transform entry permits direct centroid/bit-plane probes.
            needle = "static void turbo_cpu_fwht(float * x, int group_size) {"
            if source.count(needle) != 1:
                raise ValueError("Ambiguous transform hook")
            source = (
                "static int oracle_scalar;\nstatic float oracle_coords[128];\n"
                + source.replace(
                    needle,
                    needle
                    + "\n    if (oracle_scalar) {"
                    + " memcpy(x, oracle_coords, 128*sizeof(float)); return; }",
                )
            )
        else:
            original = source
            source = (
                '#include "ggml-quants.h"\n#include "ggml-impl.h"\n'
                "#include <math.h>\n#include <string.h>\n"
            )
            if kind == "prism":
                source += "static const size_t ptq1_0_stages[3] = {32, 16, 8};\n"
            for _, name, _, _ in SPECS[kind]:
                source += function(original, f"quantize_row_{name}_ref") + "\n"
                source += function(original, f"dequantize_row_{name}") + "\n"
        output = args.output / f"{kind}.c"
        output.write_text("#undef NDEBUG\n" + source + driver(kind), encoding="utf-8")
        cmake += [
            f"add_executable({kind} {kind}.c)",
            f'target_include_directories({kind} PRIVATE "{ggml.as_posix()}/include"'
            f' "{ggml.as_posix()}/src")',
            f"target_compile_definitions({kind} PRIVATE _CRT_SECURE_NO_WARNINGS)",
            "if(MSVC)",
            f" target_compile_options({kind} PRIVATE /fp:strict /W3 /utf-8)",
            "else()",
            f" target_compile_options({kind} PRIVATE -ffp-contract=off -fno-fast-math -UNDEBUG)",
            f" target_link_libraries({kind} PRIVATE m)",
            "endif()",
        ]
    (args.output / "CMakeLists.txt").write_text(
        "\n".join(cmake) + "\n", encoding="utf-8"
    )
    manifest["generated_sha256"] = {p.name: digest(p) for p in args.output.glob("*.c")}
    (args.output / "source-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def f32(value: float) -> float:
    """Round fixture arithmetic to IEEE F32."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def fixtures(args: argparse.Namespace) -> None:
    """Generate deterministic probes, invoke independent oracles, hash receipts."""
    manifest: dict[str, object] = {"seed": 1234, "files": {}}
    for kind, specs in SPECS.items():
        data = bytearray()
        count = 0
        rng = random.Random(1234)
        for ident, _, width, blockbytes in specs:

            def append(
                values: list[float],
                mode: int = 0,
                norm: float = 1.0,
                payload: bytes = b"",
            ) -> None:
                nonlocal count
                data.extend(struct.pack("<IIIf", ident, mode, len(values), norm))
                data.extend(struct.pack(f"<{len(values)}f", *values))
                data.extend(payload)
                count += 1

            for value in [0.0, -0.0, 1.0, -1.0, 1e-12, -1e-12, 2**-24, 2**-14]:
                append([value] * width)
            append([(-1.0 if i % 2 else 1.0) for i in range(width)])
            append([(i - width / 2) / 17 for i in range(2 * width)])
            for lane in range(width):
                for sign in [-1.0, 1.0]:
                    values = [0.0] * width
                    values[lane] = sign
                    append(values)
            for _ in range(32):
                append([rng.uniform(-3, 3) for _ in range(width)])
            # Half boundaries, including halfway ties and adjacent F32 values.
            for v in [
                2**-25,
                2**-24,
                2**-14,
                0.999755859375,
                1.00048828125,
                1.00146484375,
                2049.0,
                65504.0,
            ]:
                word = struct.unpack("<I", struct.pack("<f", v))[0]
                for delta in [-1, 0, 1]:
                    val = struct.unpack("<f", struct.pack("<I", word + delta))[0]
                    if val > 65504:
                        continue
                    values = [0.0] * width
                    values[0] = val
                    append(values)
            if ident <= 5:
                # Exact thresholds are read only from the pinned source, never
                # new implementation tables. Probe below, at, and above each.
                text = (Path(args.thetom) / "ggml/src/ggml-turbo-quant.c").read_text(
                    encoding="utf-8"
                )
                bits = ident + 1
                if bits <= 4:
                    block = text.split(
                        f"static int nearest_centroid_{bits}bit(float val) {{", 1
                    )[1].split("\n}", 1)[0]
                    mids = [
                        float(v) for v in re.findall(r"val <\s*(-?[0-9.]+)f", block)
                    ]
                else:
                    block = text.split(f"static const float TURBO{bits}_MID[", 1)[
                        1
                    ].split("};", 1)[0]
                    mids = [float(v) for v in re.findall(r"(-?[0-9.]+)f", block)]
                for mid in mids:
                    for delta in [-(2**-25), 0, 2**-25]:
                        append([f32(mid + delta)] * width, mode=1)
                for lane in range(width):
                    values = [0.0] * width
                    values[lane] = -0.5 if lane % 2 else 0.5
                    append(values, mode=1)
            # Arbitrary legal bit patterns exercise every lane/plane and finite
            # half decoding independently of what the encoder emits.
            offset = 26 if ident == 9 else 0
            for half in [0, 0x8000, 1, 0x3FF, 0x400, 0x3555, 0x3C00, 0x7BFF]:
                for pattern in [0, 0x55, 0xAA, 0xFF]:
                    payload = bytearray([pattern] * blockbytes)
                    payload[offset : offset + 2] = struct.pack("<H", half)
                    if ident in [6, 7]:
                        payload[2:4] = struct.pack("<H", half)
                    append([0.0] * width, mode=2, payload=payload)
        inp, out = (
            args.output / f"{kind}-input.bin",
            args.output / f"{kind}-fixtures.bin",
        )
        inp.write_bytes(data)
        executable = args.output / "build" / "Release" / f"{kind}.exe"
        if not executable.exists():
            executable = args.output / "build" / kind
        subprocess.run([str(executable), str(inp), str(out)], check=True)
        manifest["files"][kind] = {
            "records": count,
            "input_sha256": digest(inp),
            "output_sha256": digest(out),
            "executable_sha256": digest(executable),
        }
        logging.info("%s: %d oracle records", kind, count)
    (args.output / "fixture-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def golden(args: argparse.Namespace) -> None:
    """Keep a small deterministic selection from independently produced fixtures."""
    selected = bytearray()
    for kind in SPECS:
        data = (args.output / f"{kind}-fixtures.bin").read_bytes()
        offset = 0
        counts: dict[tuple[int, int], int] = {}
        while offset < len(data):
            ident, mode, width = struct.unpack_from("<III", data, offset)
            payload_offset = offset + 16 + 4 * width
            nbytes = struct.unpack_from("<I", data, payload_offset)[0]
            end = payload_offset + 4 + nbytes + 4 * width
            key = (ident, mode)
            index = counts.get(key, 0)
            if (mode == 0 and index in [0, 1, 2, 3, 10, 41]) or (
                mode > 0 and index in [0, 3]
            ):
                selected.extend(data[offset:end])
            counts[key] = index + 1
            offset = end
    args.golden.parent.mkdir(parents=True, exist_ok=True)
    args.golden.write_bytes(selected)
    logging.info("golden: %d bytes, sha256 %s", len(selected), digest(args.golden))


def main() -> None:
    """Parse explicit pinned-source and output paths; never fetch dependencies."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--thetom", type=Path, required=True)
    parser.add_argument("--prism", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--fixtures", action="store_true")
    parser.add_argument("--golden", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.prepare:
        prepare(args)
    if args.fixtures:
        fixtures(args)
    if args.golden:
        golden(args)


if __name__ == "__main__":
    main()
