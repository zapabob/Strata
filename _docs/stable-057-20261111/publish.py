"""Stable fork publication, guarded mutable alias promotion and anonymous readback."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request

ROOT = Path('C:/Users/downl/Documents/ChatGPT/Strata')
OUT = Path('H:/Strata/releases/stable-057-20261111-codex')
ASSETS = OUT / 'assets'
GH = 'C:/Program Files/GitHub CLI/gh.exe'
REPO = 'zapabob/Strata'
TAG = 'v0.5.7'


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


def get_release() -> dict:
    # GitHub's tag endpoint omits drafts, even for this authenticated owner.
    rows = api('releases?per_page=100')
    require(len(rows) < 100, 'Bounded release inventory required')
    matches = [row for row in rows if row['tag_name'] == TAG]
    require(len(matches) == 1, 'Exactly one release for the immutable tag required')
    return matches[0]


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
    require(all(tags.get(tag) == row for tag, row in before['tags'].items() if tag != 'refs/tags/latest'), 'A prior immutable tag changed')
    latest = release_identity(api('releases/latest'))
    stable = rows.get(TAG)
    promoted = stable is not None and not stable['draft'] and not stable['prerelease']
    if promoted:
        require(latest == stable, 'GitHub Latest does not select the formal release')
        target = api('git/ref/tags/' + TAG)['object']
        require(tags.get('refs/tags/latest') in (before['tags']['refs/tags/latest'], target), 'Unexpected mutable alias change')
    else:
        require(latest == before['latest'] and tags.get('refs/tags/latest') == before['tags']['refs/tags/latest'], 'Stable state changed before publication')
    return {'priorReleasesUnchanged': len(before['releases']), 'priorImmutableTagsUnchanged': len(before['tags']) - 1,
            'latest': latest['tag_name'], 'historicalAssetsUnchanged': True}


def snapshot_local_alias() -> None:
    remote = api('git/ref/tags/latest')['object']['sha']
    require(remote == load('publication-before.json')['tags']['refs/tags/latest']['sha'], 'Remote alias changed since publication snapshot')
    local = subprocess.check_output(['git', 'rev-parse', 'refs/tags/latest'], cwd=ROOT, text=True).strip()
    peeled = subprocess.check_output(['git', 'rev-parse', 'refs/tags/latest^{commit}'], cwd=ROOT, text=True).strip()
    save('local-alias-before.json', {'localObject': local, 'peeledCommit': peeled, 'remoteObject': remote,
         'note': 'Retain the independently stale local cache; promote only this explicitly observed mutable alias with compare-and-swap.'})
    print('Recorded local and remote mutable alias identities without changing either.', flush=True)


def promote_alias() -> dict:
    before = load('publication-before.json')['tags']['refs/tags/latest']['sha']
    target = api('git/ref/tags/' + TAG)['object']['sha']
    current = api('git/ref/tags/latest')['object']['sha']
    require(current in (before, target), 'The mutable latest alias changed since the snapshot')
    local = subprocess.check_output(['git', 'rev-parse', 'refs/tags/latest'], cwd=ROOT, text=True).strip()
    local_before = load('local-alias-before.json')['localObject']
    require(local in (local_before, target), 'An unrelated local alias change must be preserved')
    if current != target:
        subprocess.run(['git', 'push', '--force-with-lease=refs/tags/latest:' + before,
                        'origin', target + ':refs/tags/latest'], cwd=ROOT, check=True, timeout=120)
    if local != target:
        subprocess.run(['git', 'update-ref', 'refs/tags/latest', target, local], cwd=ROOT, check=True, timeout=30)
    require(api('git/ref/tags/latest')['object']['sha'] == target, 'Latest alias did not match the immutable release tag')
    return {'oldRemoteObject': before, 'oldLocalObject': local_before, 'newObject': target, 'leaseGuarded': True, 'immutableTag': TAG}


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
    gh('release', 'create', TAG, '--repo', REPO, '--draft', '--latest=false', '--verify-tag',
       '--title', 'Hakua / Strata 0.5.7 — subagents and learning workflow skills',
       '--notes-file', str(ROOT / '_docs/stable-057-20261111/RELEASE_NOTES.md'))
    # No clobber: a failed attempt leaves its draft and existing assets reviewable.
    for name in sorted(records, key=lambda name: records[name]['bytes']):
        print('Uploading ' + name, flush=True)
        gh('release', 'upload', TAG, str(ASSETS / name), '--repo', REPO)
    verify_draft()


def verify_draft() -> None:
    records = local_assets()
    release = get_release()
    require(release['draft'] and not release['prerelease'], 'Expected unpublished formal release')
    verify_remote(release, records)
    source = subprocess.check_output(['git', 'rev-parse', TAG + '^{commit}'], cwd=ROOT, text=True).strip()
    remote = subprocess.check_output(['git', 'ls-remote', '--tags', 'origin', 'refs/tags/' + TAG + '^{}'], cwd=ROOT, text=True)
    require(remote.split()[0] == source, 'Remote annotated tag must still match')
    save('draft-verified.json', {'ok': True, 'id': release['id'], 'tagCommit': source, 'assets': records,
                                 'unchanged': unchanged()})
    print('Draft asset sizes and server SHA-256 digests matched.', flush=True)


def resume_upload(attempt: str) -> None:
    """Keep completed draft assets after a contained resource stop; upload only absent names."""
    require(re.fullmatch(r'r[2-9][0-9]*', attempt), 'Explicit fresh upload retry required')
    failed = load('receipts/release-upload.json')
    require(not failed['passed'] and failed['run']['status'] == 'RESOURCE_PRESSURE'
            and failed['run']['job_active_after'] == 0, 'Retained contained first upload failure required')
    records = local_assets()
    unchanged()
    require(gh('api', 'user', '--jq', '.login').strip() == 'zapabob', 'Expected release owner')
    release = get_release()
    require(release['draft'] and not release['prerelease'], 'Resume only the unpublished formal draft')
    observed = {row['name']: row for row in release['assets']}
    require(set(observed) <= set(records), 'Unexpected draft asset must be preserved for review')
    for name, row in observed.items():
        require(row['state'] == 'uploaded' and row['size'] == records[name]['bytes']
                and row['digest'] == 'sha256:' + records[name]['sha256'],
                'Incomplete or changed draft asset requires review: ' + name)
    save('upload-resume-before-' + attempt + '.json', {
        'id': release['id'], 'retainedAssets': release_identity(release)['assets'],
        'failedReceiptSHA256': sha(OUT / 'receipts/release-upload.json'),
        'note': 'No completed asset is deleted, replaced or uploaded again; resource floors stay unchanged.'})
    for name in sorted(set(records) - set(observed), key=lambda name: records[name]['bytes']):
        print('Uploading absent draft asset ' + name, flush=True)
        gh('release', 'upload', TAG, str(ASSETS / name), '--repo', REPO)
    verify_draft()


def verify_remote(release: dict, records: dict) -> None:
    observed = {row['name']: row for row in release['assets']}
    require(set(observed) == set(records), 'Remote asset membership differs')
    for name, row in records.items():
        require(observed[name]['state'] == 'uploaded' and observed[name]['size'] == row['bytes']
                and observed[name]['digest'] == 'sha256:' + row['sha256'],
                'Remote size or SHA-256 mismatch: ' + name)


def publish() -> None:
    draft = load('draft-verified.json')
    records = local_assets()
    release = get_release()
    require(release['id'] == draft['id'] and not release['prerelease'], 'Expected exact verified formal release')
    verify_remote(release, records)
    unchanged()
    if release['draft']:
        gh('release', 'edit', TAG, '--repo', REPO, '--draft=false', '--prerelease=false', '--latest=true')
    release = get_release()
    require(not release['draft'] and not release['prerelease'], 'Formal publication did not complete')
    verify_remote(release, records)
    alias = promote_alias()
    save('published.json', {'ok': True, 'url': release['html_url'], 'id': release['id'],
                            'publishedAt': release['published_at'], 'prerelease': False, 'mutableLatestAlias': alias,
                            'unchanged': unchanged()})
    print(release['html_url'], flush=True)


def readback(attempt: str = 'r1') -> None:
    require(load('published.json')['ok'], 'Published formal release required')
    records = local_assets()
    release = get_release()
    verify_remote(release, records)
    require(re.fullmatch(r'r[1-9][0-9]*', attempt), 'Explicit readback attempt required')
    target = OUT / ('anonymous-readback' if attempt == 'r1' else 'anonymous-readback-' + attempt)
    target.mkdir()

    def download(asset: dict) -> tuple:
        name = asset['name']
        path = target / name
        prior = OUT / 'anonymous-readback' / name
        if attempt != 'r1' and prior.is_file() and prior.stat().st_size == records[name]['bytes'] and sha(prior) == records[name]['sha256']:
            # Preserve the resource-stopped attempt. Reuse only completely read-back,
            # size/hash-verified public files; partial files remain untouched there.
            shutil.copy2(prior, path)
            print('Reused complete anonymous readback ' + name, flush=True)
            return name, records[name]
        request = urllib.request.Request(asset['browser_download_url'], headers={'User-Agent': 'Strata-release-readback/0.5.7'})
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

    with ThreadPoolExecutor(max_workers=1) as pool:
        observed = dict(pool.map(download, release['assets']))
    stable = {}
    stable_dir = target / 'stable-latest'
    stable_dir.mkdir()
    for name in ('strata-feed.json', 'strata-feed.json.sig'):
        expected = records[name]
        request = urllib.request.Request(f'https://github.com/{REPO}/releases/latest/download/{name}',
                                         headers={'User-Agent': 'Strata-release-readback/0.5.7'})
        with urllib.request.urlopen(request, timeout=60) as source:
            data = source.read(1024 * 1024 + 1)
        require(len(data) == expected['bytes'] and hashlib.sha256(data).hexdigest() == expected['sha256'],
                'Stable latest/download bytes do not match the formal release')
        (stable_dir / name).write_bytes(data)
        stable[name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    check = unchanged()
    require(check['latest'] == TAG and api('git/ref/tags/latest')['object']['sha'] == api('git/ref/tags/' + TAG)['object']['sha'], 'Stable release/alias readback mismatch')
    save('PUBLIC_VERIFICATION.json', {'ok': True, 'url': release['html_url'], 'tag': TAG,
                                     'anonymousDownloads': observed, 'stableLatestAnonymousDownloads': stable,
                                     'serverDigestsMatched': True, 'prerelease': False, 'mutableLatestAliasMatches': True, **check})
    print('Every public download matched the frozen local SHA-256.', flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['snapshot', 'snapshot-local-alias', 'upload', 'resume-upload', 'verify-draft', 'publish', 'readback'])
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--attempt', default='r1')
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({'execute': False, 'action': args.action, 'tag': TAG}))
        return
    if args.action == 'resume-upload':
        resume_upload(args.attempt)
    elif args.action == 'readback':
        readback(args.attempt)
    else:
        globals()[args.action.replace('-', '_')]()


if __name__ == '__main__':
    main()
