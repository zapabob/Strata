"""Execute a frozen, parent-approved candidate only inside the existing native Job guard.

This helper is never used for original-server restoration. Default invocation is help.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import time

import foundation as f


def bounded_steps(manifest: dict) -> dict:
    """Handshake before executing candidate code; fail closed on containment or telemetry loss."""
    from serve import winjob

    began = time.monotonic()
    report = {'ok': False, 'steps': [], 'abort': None}
    process = None
    contained = False
    try:
        f.need(f.resource_status()['ok'], 'resource_floor')
        for number, step in enumerate(manifest['steps']):
            f.need(f.resource_status()['ok'], 'resource_floor')
            for identity in manifest['files']:
                f.need(f.file_identity(Path(identity['path']), digest=True) == identity, 'candidate_file_drift')
            start = time.monotonic()
            worker = (
                'import json,subprocess,sys; '
                'sys.stdin.readline().strip()=="GO" or sys.exit(125); '
                'raise SystemExit(subprocess.call(json.loads(sys.argv[1]),shell=False))'
            )
            with f.private_path(f'candidate-{number:02d}.log').open('xb') as log:
                env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
                env.update(step.get('env', {}))
                # Nothing from the captured original-server environment is passed to tests.
                process = subprocess.Popen(
                    [sys.executable, '-B', '-c', worker, json.dumps(step['argv'])],
                    cwd=step['cwd'],
                    env=env,
                    stdin=subprocess.PIPE,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                f.need(winjob.contain(process), 'candidate_containment_failed')
                contained = True
                process.stdin.write(b'GO\n')
                process.stdin.flush()
                process.stdin.close()
                while process.poll() is None:
                    now = time.monotonic()
                    f.need(
                        now - start < step['timeoutSeconds'] and now - began < manifest['windowSeconds'],
                        'candidate_timeout',
                    )
                    f.need(f.resource_status()['ok'], 'resource_floor')
                    time.sleep(1)
                report['steps'].append({'index': number, 'exitCode': process.returncode})
                f.need(process.returncode == 0, 'candidate_nonzero_exit')
        report['ok'] = True
    except Exception as error:
        report['abort'] = str(error) if isinstance(error, f.Blocked) else type(error).__name__
    finally:
        # The job contains only this guard's handshake workers and their descendants.
        terminated = winjob.terminate()
        if contained and not terminated:
            report['ok'] = False
            report['abort'] = 'candidate_job_cleanup_failed'
        if process is not None:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=15)
        report['elapsedSeconds'] = round(time.monotonic() - began, 3)
        f.write_private('candidate-result.json', report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    f.need(args.execute, 'explicit_execute_required')
    manifest = f.read_private('frozen-candidate.json', args.manifest_sha256)
    claim = f.read_private('execution-claim.json')
    f.need(claim['manifestSHA256'] == args.manifest_sha256, 'execution_claim_mismatch')
    result = bounded_steps(manifest)
    logging.info(json.dumps({'candidateOk': result['ok'], 'abort': result['abort']}))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    try:
        raise SystemExit(main())
    except Exception as error:
        logging.error(
            json.dumps({'ok': False, 'code': str(error) if isinstance(error, f.Blocked) else type(error).__name__})
        )
        raise SystemExit(1) from None
