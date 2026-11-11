"""Derive a fresh delivery recipe without changing the completed 0.5.6 evidence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OLD = ROOT / '_docs/search-056-20261111'

for name in ('delivery.py', 'publish.py', 'qa-installed.mjs'):
    text = (OLD / name).read_text(encoding='utf-8')
    text = text.replace('search-056-20261111-codex-r3', 'skills-057-20261111-codex')
    text = text.replace('search-056-20261111-codex', 'skills-057-20261111-codex')
    text = text.replace('search-056-20261111', 'skills-057-20261111')
    text = text.replace('0.5.6-local.1', '0.5.7-local.1')
    if name == 'delivery.py':
        text = text.replace("'receipts/nsis-cleanup-r3.json'", "'receipts/nsis-cleanup-final.json'")
        text = text.replace("'passed': 37, 'failed': 0, 'optionalSkipped': 3", "'passed': 65, 'failed': 0, 'optionalSkipped': 5")
        text = text.replace("'realHarnessResearchTests': {'passed': 2, 'failed': 0}", "'realHarnessWorkflowTests': {'passed': 14, 'failed': 0}")
        text = text.replace("'broadHostSuite': {'passed': 2013", "'prior056BroadHostSuite': {'passed': 2013")
        text = text.replace('/btw asks a separate tool-free question.', '/btw delegates a separate tool-free question to a real subagent. In Skills, enable\nworkflow learning and automatic application independently. Review status and undo\nare available. The same task model reviews redacted metadata in one extra request.\nManual edits, workspace scope and approvals are preserved.')
        text = text.replace('Strata: https://github.com/Niko1221/Strata', 'Workflow skills: https://github.com/zapabob/Strata/blob/main/docs/WORKFLOW_SKILLS.md\nHermes Agent: https://github.com/NousResearch/hermes-agent\nStrata: https://github.com/Niko1221/Strata')
    if name == 'publish.py':
        text = text.replace('side questions and RustXNG Full', 'subagents and learning workflow skills')
        text = text.replace('Strata-release-readback/0.5.6', 'Strata-release-readback/0.5.7')
    if name == 'qa-installed.mjs':
        text = text.replace('056', '057').replace("STRATA_AGENT:'off',", '')
    with (HERE / name).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
print('Prepared fresh 0.5.7 delivery, publication and installed-UI recipes.')
