"""Generate isolated negative-control builds; never edit the working codec.

Each executable has exactly one deliberate arithmetic/layout fault. CTest must
observe failure on the real checked-API tests and independent golden fixtures.
Compile this bounded project with one job; no external dependency is required.
"""

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    """Write uniquely named mutant sources under an explicit build directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = (repo / "tqcodec/src/dialects.cpp").read_text(encoding="utf-8")
    faults = {
        "missing_normalization": [("0.08838834764831845f * b[i]", "1.0f * b[i]")],
        "flipped_sign": [("x[i] *= a[i];", "x[i] *= -a[i];")],
        "wrong_inverse": [
            ("inverse ? turbo_cpu_s2 : turbo_cpu_s1", "(void(inverse), turbo_cpu_s1)"),
            ("inverse ? turbo_cpu_s1 : turbo_cpu_s2", "turbo_cpu_s2"),
        ],
        "wrong_high_plane": [
            (
                "((p[34 + i / 8] >> (i % 8)) & 1) << 2",
                "((p[34 + i / 8] >> (i % 8)) & 1) << 1",
            )
        ],
        "legacy_turbo4": [("{128, 66, 2, 0, TQC_D_KV", "{128, 68, 2, 0, TQC_D_KV")],
        "double_F_in_pack": [
            (
                "turbo_pack(p->dialect, x, norm, packed);",
                "fwht(x, false); turbo_pack(p->dialect, x, norm, packed);",
            )
        ],
    }
    cmake = [
        "cmake_minimum_required(VERSION 3.24)",
        "project(dialect_faults LANGUAGES CXX)",
        "enable_testing()",
    ]
    manifest = {}
    for name, replacements in faults.items():
        text = source
        for old, new in replacements:
            if text.count(old) != 1:
                raise ValueError(f"Ambiguous fault injection: {name}")
            text = text.replace(old, new)
        path = output / f"{name}.cpp"
        if path.exists():
            raise FileExistsError(f"Preserve prior fault source: {path}")
        path.write_text(text, encoding="utf-8")
        manifest[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        test = (repo / "tqcodec/tests/dialects_test.cpp").as_posix()
        cmake += [
            f'add_executable({name} {name}.cpp "{test}")',
            f'target_include_directories({name} PRIVATE "{repo.as_posix()}/tqcodec/include"',
            f' "{repo.as_posix()}/tqcodec/src")',
            f"target_compile_features({name} PRIVATE cxx_std_17)",
            "if(MSVC)",
            f" target_compile_options({name} PRIVATE /W4 /WX /fp:strict)",
            "else()",
            f" target_compile_options({name} PRIVATE -ffp-contract=off -fno-fast-math)",
            "endif()",
            f"add_test(NAME {name} COMMAND {name}",
            f' "{repo.as_posix()}/tqcodec/tests/fixtures/dialects-v1.bin")',
            f"set_tests_properties({name} PROPERTIES WILL_FAIL TRUE)",
        ]
    (output / "CMakeLists.txt").write_text("\n".join(cmake) + "\n", encoding="utf-8")
    (output / "mutations.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
