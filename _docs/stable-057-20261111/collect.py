"""Collect public-safe evidence, retaining failed attempts separately."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-057-20261111-codex')
HERE = Path(__file__).resolve().parent

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def completed(prefix):
    matches = []
    for path in (OUT / 'receipts').glob('*.json'):
        if not re.fullmatch(re.escape(prefix) + r'(?:-r[1-9]\d*)?', path.stem):
            continue
        value = load(path)
        if value['passed'] and value['run']['job_active_after'] == 0:
            matches.append((value['finished'], path, value))
    assert matches, 'Missing successful contained check: ' + prefix
    _, path, value = max(matches)
    return path.stem, {'passed': True, 'receiptSHA256': digest(path), 'ownedProcessesAfter': 0,
                       'resourceDiagnostics': value['run']['memory_diagnostics']}

def main():
    receipts = dict(completed(name) for name in (
        'app-build', 'focused-skills-final', 'learning-unit-final', 'btw-skills-harness-final',
        'btw-isolated-final', 'nsis-cleanup-final', 'private-backup', 'extract-self-test',
        'install', 'installed-ui', 'bundle', 'normal-start', 'normal-unload', 'publication-snapshot', 'release-upload',
        'release-publish', 'release-readback'))
    for suffix in ('', '.ja', '.zh-CN', '.de', '.fr', '.es', '.pt-BR', '.pl'):
        text = (ROOT / ('README' + suffix + '.md')).read_text(encoding='utf-8')
        for required in ('https://github.com/Niko1221/Strata', 'https://github.com/ggml-org/llama.cpp',
                         'https://github.com/sahenjp/RustXNG', '0.5.7', '/btw', '/deepresearch'):
            assert required in text, suffix + ': ' + required
    failed = {}
    for path in sorted((OUT / 'receipts').glob('*.json')):
        value = load(path)
        if not value['passed']:
            failed[path.stem] = {'passed': False, 'receiptSHA256': digest(path),
                                'status': value.get('run', {}).get('status', 'ADMISSION_REFUSED')}
    ui = load(OUT / 'installed-ui-verified.json')
    assert ui['ok'] and ui['actualInstalledExe'] and ui['mockModelOnly'] and ui['realRustxng']
    normal = load(OUT / 'normal-start.json')
    assert normal['ok'] and normal['workflowLearning'] and normal['automaticSkillApplication']
    bundle = load(OUT / 'bundle-verified.json')
    assert bundle['ok'] and bundle['allMemberHashesMatched']
    public = load(OUT / 'PUBLIC_VERIFICATION.json')
    assert public['ok'] and public['serverDigestsMatched'] and public['prerelease'] is False
    assert public['mutableLatestAliasMatches'] and public['latest'] == 'v0.5.7'
    draft = load(OUT / 'draft-verified.json')
    assert draft['ok']
    report = {'releaseQualified': False, 'appBuild': load(OUT / 'app-build.json'),
        'nsisShellBinding': load(OUT / 'nsis-shell-binding.json'), 'installed': load(OUT / 'installed.json'),
        'backup': load(OUT / 'backup.json'), 'installedWebView2': ui, 'normalStartup': normal,
        'normalUnloadAfterUserApproval': load(OUT / 'normal-unload.json'),
        'readmeLanguagesChecked': 8, 'packagedSelfTestsPassed': 13, 'nsisCleanupScenariosPassed': 6,
        'quality': load(OUT / 'assets/QUALITY.json'), 'signedFeed': load(OUT / 'signed-feed-check.json'),
        'cloudCIObservation': load(OUT / 'exact-sha-ci.json'),
        'bundle': bundle, 'public': public, 'receipts': receipts, 'preservedFailedAttempts': failed,
        'note': 'Private inventories, user content and credentials are excluded. Expanded pre-existing failures remain unqualified.'}
    with (HERE / 'LOCAL_VERIFICATION.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False); stream.write('\n')
    assert not (HERE / 'PUBLIC_VERIFICATION.json').exists()
    shutil.copy2(OUT / 'PUBLIC_VERIFICATION.json', HERE / 'PUBLIC_VERIFICATION.json')
    print('Collected installed-app, workflow, archive and anonymous public verification; eight README languages checked.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    if parser.parse_args().execute: main()
    else: print(json.dumps({'execute': False, 'output': 'LOCAL_VERIFICATION.json'}))
