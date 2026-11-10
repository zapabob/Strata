"""Rerun unchanged local gates after the AGENTS version-banner formatting fix."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

import prepare as p


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'execute': False, 'attempt': 'r2', 'assertionsChanged': False, 'retainFailedScratch': True}))
        return 0
    previous = p.load(p.BASE / 'receipts/verify-release-local-r1.json')
    p.require(previous['passed'] is False and previous['run']['termination_confirmed'] is True
              and previous['run']['job_active_after'] == 0, 'Failed local gate must be drained')
    p.require(not (p.BASE / 'verified-local.json').exists() and not (p.BASE / 'stable-before.json').exists(),
              'Do not replay a completed gate')
    scratch, retained = p.BASE / 'validation-local', p.BASE / 'attempts/validation-local-r1'
    p.require(scratch.is_dir() and not retained.exists(), 'Explicit retained scratch required')
    retained.parent.mkdir(exist_ok=True)
    scratch.rename(retained)
    p.save(p.BASE / 'local-r1-retained.json', {'failedReceiptSHA256': p.sha(p.BASE / 'receipts/verify-release-local-r1.json'),
        'retainedScratch': str(retained), 'reason': 'AGENTS version banner text did not match existing product checker'})
    guard = p.guard_module()
    env = guard.environment()
    gh = shutil.which('gh')
    p.require(gh, 'Authenticated gh required')
    env['PATH'] = str(Path(gh).parent) + ';' + env['PATH']
    row = guard.owned(p.ROOT, 'verify-release-local-r2', [sys.executable, '-B', str(Path(__file__).with_name('verify.py')),
        'local', '--execute', '--worker'], 1800, env=env, output_bytes=8 * 1024**2)
    print(json.dumps(row, indent=2))
    if not row['passed']:
        print(guard.text('verify-release-local-r2'))
    return 0 if row['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
