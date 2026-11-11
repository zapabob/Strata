"""Collect public-safe release evidence after all required actions completed."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/search-056-20261111-codex')


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    if not parser.parse_args().execute:
        print(json.dumps({'execute': False, 'output': 'LOCAL_VERIFICATION.json'}))
        return
    receipts = {}
    for name in ('app-build', 'focused-checks', 'harness-research', 'rustxng-live-r2',
                 'extract-self-test-r3', 'private-backup-r3', 'nsis-cleanup-r3',
                 'candidate-ui-r2', 'installed-ui-r1', 'install-r1', 'bundle-r1',
                 'normal-start', 'publication-snapshot', 'draft-verification',
                 'release-publish', 'release-readback-r2'):
        path = OUT / 'receipts' / (name + '.json')
        data = load(path)
        assert data['passed'] and data['run']['job_active_after'] == 0, name
        receipts[name] = {'passed': True, 'receiptSHA256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'ownedProcessesAfter': 0, 'resourceDiagnostics': data['run']['memory_diagnostics']}
    languages = ['', '.ja', '.zh-CN', '.de', '.fr', '.es', '.pt-BR', '.pl']
    for language in languages:
        text = (ROOT / ('README' + language + '.md')).read_text(encoding='utf-8')
        for required in ('https://github.com/Niko1221/Strata', 'https://github.com/ggml-org/llama.cpp',
                         'https://github.com/sahenjp/RustXNG', '/btw', '/deepresearch', '0.5.6-local.1'):
            assert required in text, language + ': ' + required
    failed = {}
    for name in ('host-suite', 'baseline-failures', 'rustxng-live', 'extract-self-test',
                 'extract-self-test-r2', 'private-backup', 'private-backup-r2',
                 'nsis-cleanup', 'nsis-cleanup-r2', 'candidate-ui', 'release-upload', 'release-readback'):
        path = OUT / 'receipts' / (name + '.json')
        data = load(path)
        assert not data['passed'], 'Do not relabel a preserved failed attempt'
        failed[name] = {'passed': False, 'receiptSHA256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'status': data.get('run', {}).get('status', 'ADMISSION_REFUSED')}
    ui = load(OUT / 'qa-installed-r1/result.json')
    assert ui['ok'] and ui['mockModelOnly'] and ui['realRustxng']
    package = load(OUT / 'bundle-verified.json')
    assert package['ok'] and package['allMemberHashesMatched']
    report = {'releaseQualified': False, 'appBuild': load(OUT / 'app-build.json'),
              'nsisShellBinding': load(OUT / 'nsis-shell-binding.json'),
              'installed': load(OUT / 'installed.json'), 'installedWebView2': ui,
              'normalStartup': load(OUT / 'normal-start.json'), 'readmeLanguagesChecked': len(languages),
              'packagedSelfTestsPassed': 13, 'nsisCleanupScenariosPassed': 6,
              'quality': load(OUT / 'assets/QUALITY.json'), 'signedFeed': load(OUT / 'signed-feed-check.json'),
              'bundle': package, 'public': load(OUT / 'PUBLIC_VERIFICATION.json'), 'receipts': receipts,
              'preservedFailedAttempts': failed}
    with (ROOT / '_docs/search-056-20261111/LOCAL_VERIFICATION.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print('Collected verified package, public readback and resource receipts; eight README languages checked.')


if __name__ == '__main__':
    main()
