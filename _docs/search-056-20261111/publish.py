"""Explicit prerelease publication with immutable asset and anonymous readback checks."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path('C:/Users/downl/Documents/ChatGPT/Strata')
OUT = Path('H:/Strata/releases/search-056-20261111-codex')
ASSETS = OUT / 'assets'
GH = 'C:/Program Files/GitHub CLI/gh.exe'
REPO = 'zapabob/Strata'
TAG = 'v0.5.6-local.1'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def save(name: str, value: dict) -> None:
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding='utf-8-sig'))


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def gh(*args: str) -> str:
    result = subprocess.run([GH, *args], cwd=ROOT, check=True, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=1500)
    return result.stdout


def api(path: str):
    return json.loads(gh('api', f'repos/{REPO}/{path}'))


def release_identity(row: dict) -> dict:
    return {key: row[key] for key in ('id', 'tag_name', 'draft', 'prerelease')} | {
        'assets': {asset['name']: {key: asset.get(key) for key in ('id', 'size', 'digest')}
                   for asset in row['assets']}}


def snapshot() -> None:
    require(gh('api', 'user', '--jq', '.login').strip() == 'zapabob', 'Expected release owner')
    rows = api('releases?per_page=100')
    require(len(rows) < 100 and not any(row['tag_name'] == TAG for row in rows), 'Fresh tag and bounded inventory required')
    tags = api('git/refs/tags')
    latest = api('releases/latest')
    require(latest['tag_name'] == 'v0.5.1', 'Stable Latest differs from the agreed baseline')
    save('publication-before.json', {'releases': {row['tag_name']: release_identity(row) for row in rows},
                                     'tags': {row['ref']: row['object'] for row in tags},
                                     'latest': release_identity(latest)})
    print('Recorded prior releases, asset identities, tags and stable Latest.', flush=True)


def unchanged() -> dict:
    before = load('publication-before.json')
    rows = {row['tag_name']: release_identity(row) for row in api('releases?per_page=100')}
    require(all(rows.get(tag) == row for tag, row in before['releases'].items()), 'A prior release or asset changed')
    tags = {row['ref']: row['object'] for row in api('git/refs/tags')}
    require(all(tags.get(tag) == row for tag, row in before['tags'].items()), 'A prior tag changed')
    latest = release_identity(api('releases/latest'))
    require(latest == before['latest'], 'Stable Latest changed')
    return {'priorReleasesUnchanged': len(before['releases']), 'priorTagsUnchanged': len(before['tags']),
            'latest': latest['tag_name'], 'stableAssetsUnchanged': True}


def local_assets() -> dict:
    bundle = load('bundle-verified.json')
    require(bundle['ok'] and bundle['allMemberHashesMatched'], 'Verified archive required')
    records = bundle['assets']
    require({path.name for path in ASSETS.iterdir()} == set(records), 'Unexpected release file membership')
    for name, row in records.items():
        path = ASSETS / name
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], 'Local asset changed: ' + name)
    return records


def upload() -> None:
    records = local_assets()
    unchanged()
    require(gh('api', 'user', '--jq', '.login').strip() == 'zapabob', 'Expected release owner')
    source = subprocess.check_output(['git', 'rev-parse', TAG + '^{commit}'], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', '--tags', 'origin', 'refs/tags/' + TAG + '^{}'], cwd=ROOT, text=True)
    require(remote.split()[0] == source, 'Immutable annotated tag must already be pushed')
    gh('release', 'create', TAG, '--repo', REPO, '--draft', '--prerelease', '--latest=false', '--verify-tag',
       '--title', 'Hakua / Strata 0.5.6-local.1 — side questions and RustXNG Full',
       '--notes-file', str(ROOT / '_docs/search-056-20261111/RELEASE_NOTES.md'))
    # No clobber: a failed attempt leaves its draft and existing assets reviewable.
    for name in sorted(records, key=lambda name: records[name]['bytes']):
        print('Uploading ' + name, flush=True)
        gh('release', 'upload', TAG, str(ASSETS / name), '--repo', REPO)
    release = api('releases/tags/' + TAG)
    require(release['draft'] and release['prerelease'], 'Expected unpublished prerelease')
    verify_remote(release, records)
    save('draft-verified.json', {'ok': True, 'id': release['id'], 'tagCommit': source, 'assets': records,
                                 'unchanged': unchanged()})
    print('Draft asset sizes and server SHA-256 digests matched.', flush=True)


def verify_remote(release: dict, records: dict) -> None:
    observed = {row['name']: row for row in release['assets']}
    require(set(observed) == set(records), 'Remote asset membership differs')
    for name, row in records.items():
        require(observed[name]['size'] == row['bytes'] and observed[name]['digest'] == 'sha256:' + row['sha256'],
                'Remote size or SHA-256 mismatch: ' + name)


def publish() -> None:
    draft = load('draft-verified.json')
    records = local_assets()
    release = api('releases/tags/' + TAG)
    require(release['id'] == draft['id'] and release['draft'], 'Expected exact verified draft')
    verify_remote(release, records)
    unchanged()
    gh('release', 'edit', TAG, '--repo', REPO, '--draft=false', '--prerelease', '--latest=false')
    release = api('releases/tags/' + TAG)
    require(not release['draft'] and release['prerelease'], 'Prerelease publication did not complete')
    verify_remote(release, records)
    save('published.json', {'ok': True, 'url': release['html_url'], 'id': release['id'],
                            'publishedAt': release['published_at'], 'unchanged': unchanged()})
    print(release['html_url'], flush=True)


def readback() -> None:
    require(load('published.json')['ok'], 'Published prerelease required')
    records = local_assets()
    release = api('releases/tags/' + TAG)
    verify_remote(release, records)
    target = OUT / 'anonymous-readback'
    target.mkdir()

    def download(asset: dict) -> tuple:
        name = asset['name']
        path = target / name
        request = urllib.request.Request(asset['browser_download_url'], headers={'User-Agent': 'Strata-release-readback/0.5.6'})
        digest = hashlib.sha256()
        size = 0
        # Public URL only; no auth or cookies. Preserve even failed downloads.
        with urllib.request.urlopen(request, timeout=60) as source, path.open('xb') as stream:
            while chunk := source.read(1024 * 1024):
                size += len(chunk)
                require(size <= records[name]['bytes'], 'Public download exceeded expected bytes')
                digest.update(chunk)
                stream.write(chunk)
        observed = {'bytes': size, 'sha256': digest.hexdigest()}
        require(observed == records[name], 'Anonymous readback mismatch: ' + name)
        print('Read back ' + name, flush=True)
        return name, observed

    with ThreadPoolExecutor(max_workers=2) as pool:
        observed = dict(pool.map(download, release['assets']))
    check = unchanged()
    save('PUBLIC_VERIFICATION.json', {'ok': True, 'url': release['html_url'], 'tag': TAG,
                                     'anonymousDownloads': observed, 'serverDigestsMatched': True, **check})
    print('Every public download matched the frozen local SHA-256.', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'upload', 'publish', 'readback'])
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'execute': False, 'action': args.action, 'tag': TAG}))
        return
    globals()[args.action]()


if __name__ == '__main__':
    main()
