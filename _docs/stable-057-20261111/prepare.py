"""Prepare a fresh stable release without altering retained candidate artifacts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CANDIDATE = ROOT / '_docs/skills-057-20261111'

for name in ('VERSION', 'apps/host/package.json', 'apps/host/package-lock.json',
             'apps/desktop/package.json', 'apps/desktop/package-lock.json',
             'apps/desktop/src-tauri/Cargo.toml', 'apps/desktop/src-tauri/Cargo.lock'):
    path = ROOT / name
    text = path.read_text(encoding='utf-8')
    assert '0.5.7-local.1' in text, 'Unexpected app version: ' + name
    path.write_text(text.replace('0.5.7-local.1', '0.5.7'), encoding='utf-8', newline='\n')

for name in ('run.py', 'build.py', 'delivery.py', 'publish.py', 'collect.py',
             'qa-installed.mjs', 'normal-start.py', 'nsis-check.mjs', 'checks.mjs',
             'harness-tests.mjs', 'btw-tests.mjs', 'RELEASE_NOTES.md'):
    text = (CANDIDATE / name).read_text(encoding='utf-8')
    text = text.replace('skills-057-20261111-codex', 'stable-057-20261111-codex')
    text = text.replace('_docs/skills-057-20261111', '_docs/stable-057-20261111')
    text = text.replace('0.5.7-local.1', '0.5.7')
    if name == 'delivery.py':
        text = text.replace("'realHarnessWorkflowTests': {'passed': 14", "'realHarnessWorkflowTests': {'passed': 15")
        text = text.replace("'finalScopedBtwLifecycle': {'passed': 2", "'finalScopedBtwLifecycle': {'passed': 3")
        text = text.replace('Windows preview', 'Windows stable fork release')
        text = text.replace('Stable 0.5.1 and GitHub Latest stay unchanged.', 'This app is the 0.5.7 stable fork release. Historical releases and immutable tags remain available.')
    if name == 'RELEASE_NOTES.md':
        text = text.replace('Windows\npreview', 'Windows\nstable release')
        text = text.replace('The preview retains', 'The stable app retains')
        text = text.replace('Stable 0.5.1,\nGitHub Latest, the latest alias and all historical assets remain unchanged.',
                            'This release becomes GitHub Latest and the mutable latest alias. All historical\nreleases, assets and immutable tags remain unchanged.')
        text = text.replace('2026-11-11_workflow-skill-learning_Codex.md', '2026-11-11_stable-057-release_Codex.md')
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)

titles = {
    'README.ja.md': ('新しいプレビュー 0.5.7', '正式版 0.5.7'),
    'README.zh-CN.md': ('新预览版 0.5.7', '正式版 0.5.7'),
    'README.de.md': ('Neue Vorschau 0.5.7', 'Stabile Version 0.5.7'),
    'README.fr.md': ('Nouvelle préversion 0.5.7', 'Version stable 0.5.7'),
    'README.es.md': ('Nueva versión preliminar 0.5.7', 'Versión estable 0.5.7'),
    'README.pt-BR.md': ('Nova prévia 0.5.7', 'Versão estável 0.5.7'),
    'README.pl.md': ('Nowa wersja próbna 0.5.7', 'Wersja stabilna 0.5.7'),
}
for name in ['README.md', *titles, 'INSTALL.md', 'docs/HAKUA_INSTALL.md', 'docs/WORKFLOW_SKILLS.md']:
    path = ROOT / name
    text = path.read_text(encoding='utf-8').replace('0.5.7-local.1', '0.5.7')
    text = text.replace('2026-11-11_workflow-skill-learning_Codex.md', '2026-11-11_stable-057-release_Codex.md')
    if name in titles:
        text = text.replace(*titles[name]).replace('Stable / GitHub Latest: 0.5.1.', 'Stable / GitHub Latest: 0.5.7.')
    if name == 'README.md':
        text = text.replace('**0.5.7 preview**', '**0.5.7 stable release**')
        text = text.replace('Previous preview / stable', 'Previous preview / previous stable')
        text = text.replace('The preview delivery', 'The stable delivery').replace("Stable GitHub Latest and the\nstable feed stay unchanged.", 'This release becomes GitHub Latest. The independently\nsigned native/Control packages and their feed bytes are retained.')
        text = text.replace("this preview's", "this release's")
    if name == 'INSTALL.md':
        text = text.replace('新しい `0.5.7` プレビュー', '正式版 `0.5.7`').replace('安定版 `0.5.1`', '以前の安定版 `0.5.1`')
    if name == 'docs/HAKUA_INSTALL.md':
        text = text.replace('The 0.5.7 preview', 'Stable 0.5.7')
    if name == 'docs/WORKFLOW_SKILLS.md':
        text = text.replace('In the 0.5.7 preview', 'In version 0.5.7')
    path.write_text(text, encoding='utf-8', newline='\n')

print('Prepared product 0.5.7, fresh stable delivery recipes and eight README languages.')
