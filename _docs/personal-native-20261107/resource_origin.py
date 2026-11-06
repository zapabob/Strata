"""Compare actual 0.5.1/r3 SASS resources and their recorded native build inputs."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

from guard import ROOT, OUT, CUDA
from qualify import sha

sys.path.insert(0, str(ROOT / "tools"))
import check_cuda_spills as spills

RUN = OUT / "followup-r3"
OLD = Path("H:/Strata/releases/strata-0.5.0/native-build-r1")
NEW = OUT / "native-build"
RELEASE051 = Path("H:/Strata/releases/strata-0.5.1/component-r1/0.5.1-windows-x86_64-cuda-cuda13")


def compiler(build: Path) -> dict:
    names = ("CMAKE_CUDA_COMPILER", "CMAKE_CUDA_COMPILER_VERSION", "CMAKE_CUDA_HOST_COMPILER_VERSION")
    text = (build / "CMakeFiles/4.4.0/CMakeCUDACompiler.cmake").read_text()
    return {name: re.search(r'set\(' + name + r' "([^"]*)"\)', text).group(1) for name in names}


def flags(build: Path) -> dict:
    tree = ET.parse(build / "strata_kernels.vcxproj")
    ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
    group = next(n for n in tree.findall("m:ItemDefinitionGroup", ns) if "Release|x64" in n.get("Condition", ""))
    cuda = group.find("m:CudaCompile", ns)
    return {n.tag.split("}")[-1]: (n.text or "") for n in cuda}


def normalized_flags(values: dict, build: Path, version: str) -> dict:
    cache = (build / "CMakeCache.txt").read_text()
    source = re.search(r"^CMAKE_HOME_DIRECTORY:[^=]+=(.*)$", cache, re.MULTILINE).group(1).strip()
    return {key: value.replace("\\", "/").replace(source.replace("\\", "/"), "<SOURCE>")
            .replace(build.as_posix(), "<BUILD>").replace(version, "<ENGINE_VERSION>")
            for key, value in values.items()}


def main() -> None:
    path = RUN / "resource-origin.json"
    assert RUN.is_dir() and not path.exists()
    old_record = json.loads((RELEASE051 / "native-build.json").read_text())
    new_record = json.loads((NEW / "Release/native-build.json").read_text())
    assert old_record["version"] == "0.5.1" and new_record["version"] == "0.5.2"
    assert sha(RELEASE051 / "strata.exe") == old_record["sha256"]
    assert sha(OLD / "Release/strata.exe") == old_record["sha256"]
    assert sha(NEW / "Release/strata.exe") == new_record["sha256"]
    old_compiler, new_compiler = compiler(OLD), compiler(NEW)
    old_flags, new_flags = flags(OLD), flags(NEW)
    # Retain the exact original vectors as well as the explicitly explained version-only comparison.
    old_normal = normalized_flags(old_flags, OLD, "0.5.1")
    new_normal = normalized_flags(new_flags, NEW, "0.5.2")
    flags_equal = old_normal == new_normal
    input_names = ("src/kernels/cuda/iq_kernels.cu", "src/kernels/cuda/dflash2.cu", "src/kernels/cuda/qsa_select.cu")
    source_ids = {name: {"old": old_record["sources"][name], "new": new_record["sources"][name],
                         "actual": sha(ROOT / name)} for name in input_names}
    # Compare the bound kernel/core header superset too, not just the named .cu files.
    related = [name for name in old_record["sources"] if name.startswith(("src/kernels/", "include/strata/kernels/", "include/strata/core/"))]
    changed = [name for name in related if old_record["sources"][name] != new_record["sources"].get(name)]
    dump, demangler = spills.find_tools(str(CUDA / "bin/cuobjdump.exe"))
    assert dump and demangler
    tables = {}
    artifacts = {"051-exe": RELEASE051 / "strata.exe", "051-kernels": OLD / "Release/strata_kernels.lib",
                 "r3-exe": NEW / "Release/strata.exe", "r3-kernels": NEW / "Release/strata_kernels.lib"}
    for name, artifact in artifacts.items():
        rows = spills.resource_usage(dump, str(artifact))
        assert rows
        names = spills.demangle(demangler, sorted({row[2] for row in rows}))
        assert names
        table = {}
        for obj, sm, func, cols in rows:
            key = spills.kernel_key(names[func])
            if not any(part in key for part in ("expdec_down_kernel", "gemm4_rows_kernel", "block_topk_reg_kernel")):
                continue
            record = {"kernel": names[func], "sm": sm, "resources": cols}
            identifier = sm + "|" + func
            assert identifier not in table or table[identifier] == record
            table[identifier] = record
        assert table
        tables[name] = table
    bad = {}
    for identifier, row in tables["r3-kernels"].items():
        allowed = spills.ALLOWED.get(spills.kernel_key(row["kernel"]), {}).get(row["sm"], (0, 0))
        cols = row["resources"]
        if cols.get("STACK", 0) > allowed[0] or cols.get("LOCAL", 0) > allowed[1]:
            bad[identifier] = {**row, "allowance": allowed,
                "same051Exe": tables["051-exe"].get(identifier) == row,
                "same051Library": tables["051-kernels"].get(identifier) == row,
                "sameR3Exe": tables["r3-exe"].get(identifier) == row}
    result = {"investigationComplete": True, "resourceGuardPassed": False,
              "oldEngineSHA256": old_record["sha256"], "newEngineSHA256": new_record["sha256"],
              "artifactSHA256": {name: sha(p) for name, p in artifacts.items()},
              "oldCompiler": old_compiler, "newCompiler": new_compiler,
              "oldReleaseCudaFlags": old_flags, "newReleaseCudaFlags": new_flags,
              "flagsEqualExceptEngineVersion": flags_equal, "sourceIdentities": source_ids,
              "flagNormalization": "source/build directory relocation and native engine version only",
              "normalizedFlagDifferences": {key: [old_normal.get(key), new_normal.get(key)]
                  for key in old_normal.keys() | new_normal.keys() if old_normal.get(key) != new_normal.get(key)},
              "relatedBoundInputsCompared": len(related), "changedRelatedBoundInputs": changed,
              "oldRecipe": old_record["recipe"], "newRecipe": new_record["recipe"],
              "violations": list(bad.values()), "selectedResourceTables": tables,
              "limitation": "Original compiler executable hashes were not recorded. Saved compiler paths/versions and Release CUDA properties are compared; actual preserved 0.5.1 SASS is independently inspected. No baseline is approved or changed."}
    result["preexisting051Instances"] = len(bad) == 4 and all(row["same051Exe"] and row["same051Library"] and row["sameR3Exe"] for row in bad.values())
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("investigationComplete", "resourceGuardPassed", "preexisting051Instances", "flagsEqualExceptEngineVersion", "changedRelatedBoundInputs", "violations")}), flush=True)


def correlate() -> None:
    original = RUN / "resource-origin.json"
    path = RUN / "resource-correlation.json"
    assert original.is_file() and not path.exists()
    raw = json.loads(original.read_text())
    indexes = {}
    for label, table in raw["selectedResourceTables"].items():
        index = {}
        for mangled_key, row in table.items():
            signature = row["sm"] + "|" + row["kernel"]
            # Never merge two anonymous functions on a shortened name. Require
            # one unique full demangled template/parameter signature per image.
            assert signature not in index, "Ambiguous cross-build kernel identity"
            index[signature] = (mangled_key, row)
        indexes[label] = index
    rows = []
    for violation in raw["violations"]:
        signature = violation["sm"] + "|" + violation["kernel"]
        found = {label: index[signature] for label, index in indexes.items()}
        rows.append({"kernel": violation["kernel"], "sm": violation["sm"],
                     "mangledIdentities": {label: pair[0] for label, pair in found.items()},
                     "resources": {label: pair[1]["resources"] for label, pair in found.items()},
                     "allResourcesEqual": all(pair[1]["resources"] == violation["resources"] for pair in found.values())})
    matched = (len(rows) == 4 and all(row["allResourcesEqual"] for row in rows)
               and raw["oldCompiler"] == raw["newCompiler"] and raw["flagsEqualExceptEngineVersion"]
               and not raw["changedRelatedBoundInputs"]
               and all(len(set(row.values())) == 1 for row in raw["sourceIdentities"].values()))
    result = {"sourceEvidenceSHA256": sha(original), "preexisting051Instances": matched,
              "resourceGuardPassed": False, "rows": rows,
              "identityNote": "Compiler-generated anonymous-namespace mangled identifiers differ across build directories. Join uses unique full demangled template/parameter signatures and exact SM, retaining every raw identity and every resource column.",
              "disposition": "Pre-existing in the exact preserved 0.5.1 executable and library; no kernel change or budget increase. Guard remains FAIL." if matched else "Unresolved; guard remains FAIL."}
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    correlate() if sys.argv[1:] == ["--correlate"] else main()
