"""Compare actual sm120 instruction bytes beyond the two repaired schedules."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = Path('H:/Strata/releases/repair-055-20261110-opencode')
OLD = Path('H:/Strata/releases/upstream-0213-20261109-opencode/native-build/strata_kernels.dir/Release/dflash2.obj')
NEW = BASE / 'native-build/strata_kernels.dir/Release/dflash2.obj'


def main() -> int:
    spec = importlib.util.spec_from_file_location('sass_repair_guard', ROOT / '_docs/local-053-20261109/native/common.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE = BASE
    guard.require_current_job(ROOT)
    sys.path.insert(0, str(ROOT / 'tools'))
    import check_cuda_spills as spills
    dump, demangler = spills.find_tools(str(guard.CUDA / 'bin/cuobjdump.exe'))

    def functions(path: Path) -> dict:
        text = subprocess.check_output([dump, '--dump-sass', str(path)], timeout=60).decode('utf-8', errors='strict')
        words, current = {}, None
        for line in text.splitlines():
            match = re.search(r'^\s*Function\s*:\s*(\S+)', line)
            if match:
                current = match.group(1)
                guard.require(current not in words, 'Duplicate architecture/function entry')
                words[current] = []
            elif current:
                words[current].extend(re.findall(r'/\*\s*(0x[0-9a-fA-F]+)\s*\*/', line))
        names = spills.demangle(demangler, sorted(words))
        guard.require(names and len(words) == 83 and all(words.values()), 'Incomplete SASS parse')
        return {names[key]: hashlib.sha256(bytes.fromhex(''.join(value.removeprefix('0x') for value in values))).hexdigest() for key, values in words.items()}

    old, new = functions(OLD), functions(NEW)
    guard.require(old.keys() == new.keys(), 'DFlash kernel membership changed')
    changed = [name for name in old if old[name] != new[name]]
    allowed = [name for name in old if re.search(r'gemm4_rows_kernel<\(int\)8, \(int\)1, \(int\)(?:4|8)>', name)]
    passed = len(allowed) == 2 and set(changed) <= set(allowed)
    guard.save(BASE / 'dflash-default-sass.json', {'passed': passed, 'sm': 'sm_120', 'kernels': len(old),
        'changed': changed, 'expectedChanged': allowed, 'unchangedInstructionBytes': len(old) - len(changed),
        'oldObjectSHA256': guard.sha(OLD), 'newObjectSHA256': guard.sha(NEW), 'old': old, 'new': new}, fresh=True)
    print(json.dumps({'passed': passed, 'kernels': len(old), 'changed': changed, 'unchanged': len(old) - len(changed)}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
