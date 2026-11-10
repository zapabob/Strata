"""Verify the completed Copy archive after a retained resource-floor interruption."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

import prepare as p


def worker() -> None:
    p.guard_module().require_current_job(p.ROOT)
    failed = p.load(p.BASE / 'receipts/prepare-release.json')
    p.require(failed['passed'] is False and failed['run']['termination_confirmed'] is True
              and failed['run']['job_active_after'] == 0, 'Preserved failed worker must be drained')
    p.require(not (p.BASE / 'prepared.json').exists() and not (p.ASSETS / 'SHA256SUMS.txt').exists(), 'Fresh final receipt/checksums required')
    folder, receipt, _ = p.signed_source()
    p.verify_archives(folder, receipt)
    expected = {}
    for line in (p.ASSETS / 'BUNDLE-SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
        checksum, name = line.split('  ', 1)
        p.require(name not in expected and '/' not in name and '\\' not in name, 'Unsafe bundle entry')
        path = p.ASSETS / name
        p.require(p.sha(path) == checksum, 'Preserved asset changed')
        expected[name] = {'bytes': path.stat().st_size, 'sha256': checksum}
    p.require(set(expected) == {p.INSTALLER, p.ENGINE, p.CONTROL, 'strata-feed.json', 'strata-feed.json.sig',
        'install-manifest.txt', 'install.ps1', 'install.sh', 'INSTALL.md', 'QUALITY.json', 'SOURCE.json'}, 'Unexpected bundle membership')
    manifest = p.ASSETS / 'BUNDLE-SHA256SUMS.txt'
    expected[manifest.name] = {'bytes': manifest.stat().st_size, 'sha256': p.sha(manifest)}
    archive = p.ASSETS / p.ARCHIVE
    before = p.sha(archive)
    p.run(str(p.SEVEN), 't', str(archive), seconds=900)
    process = subprocess.Popen([str(p.SEVEN), 'x', '-so', str(archive), f'Strata-{p.VERSION}-windows-x64.tar'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    actual = {}
    with tarfile.open(fileobj=process.stdout, mode='r|') as bundle:
        for member in bundle:
            prefix = f'Strata-{p.VERSION}-windows-x64/'
            p.require(member.isfile() and member.name.startswith(prefix), 'Unsafe tar member')
            name = member.name[len(prefix):]
            p.require(name in expected and name not in actual, 'Unexpected tar member')
            actual[name] = {'bytes': member.size, 'sha256': hashlib.file_digest(bundle.extractfile(member), 'sha256').hexdigest()}
    while process.stdout.read(1024**2):
        pass
    process.stdout.close()
    p.require(process.wait(timeout=60) == 0 and actual == expected and p.sha(archive) == before, 'Complete archive readback differs')
    public = [*expected, p.ARCHIVE]
    p.require(all((p.ASSETS / name).stat().st_size < 2 * 1024**3 for name in public), 'GitHub asset bound exceeded')
    with (p.ASSETS / 'SHA256SUMS.txt').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(''.join(f'{p.sha(p.ASSETS / name)}  {name}\n' for name in public))
    public.append('SHA256SUMS.txt')
    result = {'ok': True, 'tag': p.TAG, 'prerelease': True, 'releaseQualified': False,
        'bundleReadbackMatched': True, 'sevenZipMode': 'Copy; no recompression',
        'priorFailedReceipt': 'receipts/prepare-release.json', 'finishRecipeSHA256': p.sha(Path(__file__)),
        'assets': {name: {'bytes': (p.ASSETS / name).stat().st_size, 'sha256': p.sha(p.ASSETS / name)} for name in public}}
    p.save(p.BASE / 'prepared.json', result)
    print(json.dumps(result, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'execute': False, 'out': str(p.BASE), 'recompression': False, 'completeReadbackRequired': True}))
        return 0
    if args.worker:
        worker()
        return 0
    guard = p.guard_module()
    report = guard.owned(p.ROOT, 'finish-release-readback-r1', [sys.executable, '-B', str(Path(__file__)), '--execute', '--worker'],
        1800, env=guard.environment(), output_bytes=16 * 1024**2)
    print(json.dumps(report, indent=2))
    if not report['passed']:
        print(guard.text('finish-release-readback-r1'))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
