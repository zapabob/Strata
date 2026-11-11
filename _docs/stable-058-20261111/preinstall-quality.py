"""Local installation gates only; final publication still requires the full native audit."""
from pathlib import Path
from core import BASE, NATIVE, NATIVE_COMMIT, NATIVE_ROOT, MANIFEST, load, require, sha

def finished(run, exit_code=0):
    return (run.get('status') == 'FINISHED' and run.get('native_exit_code') == exit_code
            and run.get('contained_before_resume') is True and run.get('termination_confirmed') is True
            and run.get('job_active_after') == 0 and run.get('observed_dropped_bytes') == 0)

def passed(row):
    return row.get('passed') is True and finished(row.get('run', {}))

def validate():
    freeze = load(BASE / 'freeze.json')
    package = load(BASE / 'results/package.json')
    require(freeze['sourceCommit'] == package['nativeSourceCommit'] == NATIVE_COMMIT
            and Path(freeze['sourceRoot']) == NATIVE_ROOT and Path(package['component']) == NATIVE,
            'Actual native identity differs')
    adapters = BASE.parent / 'adapters/native-r2'
    require(all(sha(adapters / name) == checksum for name, checksum in freeze['adapters'].items()),
            'Frozen native adapters differ')
    bound = load(BASE / 'receipts/bind-phase.json')
    require(passed(bound) and bound['frozenIdentity'] == freeze, 'Bound native build required')
    evidence = {}
    for phase in ('stage', 'cpu', 'gpu', 'sanitizer', 'spill'):
        path = BASE / f'receipts/{phase}-phase.json'
        row = load(path)
        require(passed(row) and row['frozenIdentity'] == freeze, 'Local native gate failed: ' + phase)
        evidence[phase] = {'sha256': sha(path), 'passed': True}
    for name, field in (('strata.exe', 'strataSHA256'), ('strata-q36.exe', 'q36SHA256'),
                        ('native-build.json', 'nativeBuildSHA256')):
        require(sha(NATIVE / name) == package[field], 'Tested native bytes changed')
    require(sha(NATIVE / MANIFEST) == package['manifestSHA256'], 'Native manifest changed')
    spill = load(BASE / 'results/spill.json')
    require(spill['passed'] is True and all(passed(row) for row in spill['cases']), 'Resource guard failed')
    numerical = load(BASE.parent / 'gpu-final-results-final-r1.json')
    require(passed(load(BASE.parent / 'receipts/gpu-final-numerical-r1.json'))
            and numerical['passed'] is True and numerical['diagnosticOnly'] is False
            and numerical['sourceCommit'] == NATIVE_COMMIT and len(numerical['cases']) == 21
            and all(row['passed'] for row in numerical['cases'])
            and all(numerical['binding'][key] == package[key] for key in numerical['binding']),
            'All source-bound final numerical checks required')
    for name, checksum in numerical['testedBuildFiles'].items():
        require(sha(BASE.parent / 'native-build' / name) == checksum, 'Numerically tested build changed')
    return {'localInstallationGatesPassed': True, 'finalNumericalChecksPassed': True,
            'nativeResourceGuard': {'status': 'PASS', 'passed': True, 'violations': []},
            'modelProtocolsPendingAtInstallationPreparation': True,
            'publicationRequiresSeparateFullNativeAudit': True,
            'releaseQualified': False, 'fullWindowQualified': False,
            'generalQualityQualified': False, 'newNativeQualified': False, 'evidence': evidence}
