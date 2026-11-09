"""Stage authenticated fixed runtimes in C: while preserving every previous resource file."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'component'))
from core import (ROOT, RESOURCES, REFERENCE, NODE, copy_tree, inventory, no_links,
                  production_modules, require, verify_payload, write_new)

WORK = ROOT / '_docs/local-archive/2026-11-09-pre-main/resource-staging'
NOTICES = Path('H:/Strata/worktrees/main-integration-20261106/apps/desktop/src-tauri/resources/notices')


def tick() -> None:
    require(shutil.disk_usage('C:/').free >= 5 * 1024**3, 'C: floor reached')
    require(shutil.disk_usage('H:/').free >= 10 * 1024**3, 'H: floor reached')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    require(ROOT == Path('C:/Users/downl/Documents/ChatGPT/Strata'), 'Primary checkout required')
    for path in (ROOT, RESOURCES, REFERENCE, NOTICES, WORK):
        no_links(path)
    require(not WORK.exists(), 'Retain previous resource preparation')
    if not args.execute:
        print('Plan: verify signed reference, copy fixed runtimes/notices, preserve old C: trees by rename; delete zero files.')
        return
    tick()
    ec, signing, _ = production_modules()
    verify_payload(REFERENCE, ec, signing, signed=True)
    WORK.mkdir(parents=True)
    backend = WORK / 'fresh-local-backends'
    backend.mkdir()
    for name in ('prism', 'turboquant'):
        copy_tree(REFERENCE / 'local-backends' / name, backend / name, tick)
    for name in ('.gitignore', 'README.md'):
        shutil.copy2(RESOURCES / 'local-backends' / name, backend / name)
    notices = WORK / 'fresh-notices'
    copy_tree(NOTICES, notices, tick)
    shutil.copy2(RESOURCES / 'notices/.gitignore', notices / '.gitignore')
    records = {}
    for name, pending in (('local-backends', backend), ('notices', notices)):
        current = RESOURCES / name
        before, after = inventory(current, tick), inventory(pending, tick)
        current.rename(WORK / ('prior-' + name))
        require(inventory(WORK / ('prior-' + name), tick) == before, 'Prior resource changed')
        pending.rename(current)
        require(inventory(current, tick) == after, 'New resource changed')
        records[name] = {'before': before, 'after': after, 'previous': str(WORK / ('prior-' + name))}
    subprocess.run([str(NODE), str(HERE / 'component/verify.mjs'), str(ROOT), str(RESOURCES),
                    'siblings', '-', '-'], cwd=ROOT, check=True, timeout=180)
    write_new(WORK / 'result.json', {'ok': True, 'deletedFiles': 0, 'resources': records})
    print('Fixed sibling runtimes and notices verified; all prior resource files retained.')


if __name__ == '__main__':
    main()
