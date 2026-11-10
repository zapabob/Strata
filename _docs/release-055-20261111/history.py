"""Read-only preservation check of stable/Latest and the earlier054 release assets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

import prepare as p
from verify import gh_json, stable_snapshot


def worker() -> None:
    p.guard_module().require_current_job(p.ROOT)
    p.require(stable_snapshot() == p.load(p.BASE / 'stable-before.json'), 'Stable/Latest snapshot changed')
    expected = p.load(Path('H:/Strata/releases/public-054-20261110-opencode/prepared.json'))['assets']
    release = gh_json('api', 'repos/zapabob/Strata/releases/tags/v0.5.4-local.1')
    p.require(release['id'] == 439895291 and release['prerelease'] and not release['draft'], 'Historical054 release identity changed')
    current = {asset['name']: asset for asset in release['assets']}
    p.require(set(current) == set(expected), 'Historical054 asset membership changed')
    for name, item in expected.items():
        p.require(current[name]['size'] == item['bytes'] and current[name]['digest'] == 'sha256:' + item['sha256'],
                  'Historical054 asset bytes differ from preserved publication')
    tag = gh_json('api', 'repos/zapabob/Strata/git/ref/tags/v0.5.4-local.1')['object']
    p.require(tag['type'] == 'tag' and tag['sha'] == '3eb250a563920880da012af9a633fa50b332e0d0', 'Historical054 annotated tag changed')
    result = {'passed': True, 'stableLatestAliasAndAssetsUnchanged': True,
        'historical054ReleaseID': release['id'], 'historical054AssetsMatched': len(expected),
        'historical054TagUnchanged': True, 'remoteWrites': False}
    p.save(p.BASE / 'historical-assets-verified.json', result)
    print(json.dumps(result))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--record', action='store_true', help='Compare the tracked public summary with immutable readback receipts')
    args = parser.parse_args()
    if args.record:
        expected = p.load(p.BASE / 'verified-public.json')
        actual = p.load(Path(__file__).with_name('PUBLIC_VERIFICATION.json'))
        p.require(all(actual[key] == value for key, value in expected.items()), 'Tracked public summary differs')
        historical = p.load(p.BASE / 'historical-assets-verified.json')
        p.require(actual['historical054AssetsMatched'] == historical['historical054AssetsMatched']
                  and actual['historical054TagUnchanged'] == historical['historical054TagUnchanged'], 'Tracked history differs')
        print(json.dumps({'trackedRecordMatches': True, 'anonymousAssets': len(actual['anonymousDownloads']), 'remoteWrites': False}))
        return 0
    if not args.execute:
        print(json.dumps({'execute': False, 'historicalRelease': 'v0.5.4-local.1', 'remoteWrites': False}))
        return 0
    if args.worker:
        worker()
        return 0
    gh = shutil.which('gh')
    p.require(gh, 'Authenticated gh required')
    guard = p.guard_module()
    env = guard.environment()
    env['PATH'] = str(Path(gh).parent) + ';' + env['PATH']
    result = guard.owned(p.ROOT, 'verify-history-r1', [sys.executable, '-B', str(Path(__file__)), '--execute', '--worker'],
        120, env=env, output_bytes=2 * 1024**2)
    print(json.dumps(result, indent=2))
    if not result['passed']:
        print(guard.text('verify-history-r1'))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
