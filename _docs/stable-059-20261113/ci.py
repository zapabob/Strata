"""Read every required workflow and its actual jobs on the exact application source commit."""
import argparse
import importlib.util
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-059-20261113-codex')
GH = 'C:/Program Files/GitHub CLI/gh.exe'
EXPECTED = {'Checks', 'Docs', 'Backend compile checks', 'Native preview CPU checks',
            'Portable monitor client', 'Minimal serving runtime', 'Config snapshot', 'Deploy GitHub Pages'}
EXPECTED_CHECKS = {
    'Windows / pinned Harness context and guard integration',
    *{f'{os} / {step}' for os in ('Windows', 'Linux') for step in ('Python tools/', 'Python serve/', 'Python tests/', 'host typecheck + test + build')},
    'Windows / cpu CMake preset (MSVC)', 'Linux / cpu CMake preset',
    'macOS / Python tools/', 'macOS / host typecheck + test + build',
}

def gh(*args):
    return json.loads(subprocess.check_output([GH, *args, '--repo', 'zapabob/Strata'], cwd=ROOT, timeout=120))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--commit', required=True)
parser.add_argument('--app-commit')
parser.add_argument('--record', action='store_true')
args = parser.parse_args()
assert len(args.commit) == 40 and all(c in '0123456789abcdef' for c in args.commit)
runs = gh('run', 'list', '--commit', args.commit, '--limit', '60', '--json',
          'databaseId,headSha,workflowName,status,conclusion,createdAt,url')
selected = {}
for run in sorted(runs, key=lambda row: row['createdAt'], reverse=True):
    if run['workflowName'] in EXPECTED:
        selected.setdefault(run['workflowName'], run)
for run in selected.values():
    actual = gh('run', 'view', str(run['databaseId']), '--json', 'headSha,status,conclusion,jobs')
    assert actual['headSha'] == args.commit
    run['jobs'] = [{key: job[key] for key in ('databaseId', 'name', 'status', 'conclusion', 'url')} for job in actual['jobs']]
missing = sorted(EXPECTED - selected.keys())
ok = not missing and all(run['status'] == 'completed' and run['conclusion'] == 'success'
    and run['jobs'] and all(job['status'] == 'completed' and job['conclusion'] == 'success' for job in run['jobs'])
    for run in selected.values())
if 'Checks' in selected:
    ok = ok and {job['name'] for job in selected['Checks']['jobs']} == EXPECTED_CHECKS
record = {'ok': ok, 'sourceCommit': args.commit, 'observedUTC': datetime.now(timezone.utc).isoformat(),
          'missingWorkflows': missing, 'workflows': selected, 'allJobsRequiredIncludingMacOS': True}
print(json.dumps({'ok': ok, 'missing': missing, 'workflows': {name: {
    'run': run['databaseId'], 'status': run['status'], 'conclusion': run['conclusion'],
    'jobs': [{'name': job['name'], 'status': job['status'], 'conclusion': job['conclusion']} for job in run['jobs']]
} for name, run in selected.items()}}, indent=2))
if args.record:
    assert ok, 'Every workflow and every actual job must pass before release'
    app_commit = args.app_commit or json.loads((OUT / 'app-build.json').read_text())['sourceCommit']
    spec = importlib.util.spec_from_file_location('runtime_equivalence', Path(__file__).with_name('runtime-equivalence.py'))
    binding = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(binding)
    record['appSourceCommit'] = app_commit
    record['runtimeSourceEquivalence'] = binding.verify(args.commit, app_commit)
    with (OUT / 'ci-verified.json').open('x', encoding='utf-8') as stream:
        json.dump(record, stream, indent=2)
