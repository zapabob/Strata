"""Parent-run local053 phases. Plans/help never build, install, launch, or create outputs."""
from __future__ import annotations

import argparse
import time
from common import *
import recipes

STEPS = ['build-control', 'build-app', 'qualify', 'qa-q36', 'qa-prism', 'backup', 'install', 'verify', 'activate', 'normal-start']


def execute(args: argparse.Namespace, commit: str) -> None:
    from upgrade import acceptance, payload, user_hashes, NEW_COMPONENT
    if args.step.startswith('build-'):
        import build
        (build.build_control if args.step == 'build-control' else build.build_app)(commit)
    elif args.step == 'qualify':
        destination = OUT / f'qualify-{args.attempt}.mjs'
        with destination.open('x', encoding='utf-8') as stream:
            stream.write(recipes.qualify())
        subprocess.run([str(NODE), '--expose-gc', str(destination), '--execute', '--reviewed-commit', commit], cwd=ROOT, env=build_env(), check=True, timeout=600)
    elif args.step.startswith('qa-'):
        kind = args.step[3:]
        qa = load(OUT / 'app-qualification.json')
        require(qa['ok'] and qa['sourceCommit'] == commit, 'Fresh candidate qualification required')
        app = INSTALLED if args.target == 'installed' else OUT / 'extracted'
        require(payload(app) == load(OUT / 'qualified-payload.json'), 'Actual target payload differs')
        if args.target == 'installed':
            require(load(OUT / 'installed-payload.json')['beforeFirstLaunch'] and load(OUT / 'native-activated.json')['ok'], 'Overwrite, prelaunch verification and signed activation must precede installed GUI QA')
            require(inventory(NEW_COMPONENT) == inventory(SIGNED), 'Actual imported native component differs')
        acceptance_path = OUT / f'{args.target}-{kind}-e2e.json'
        require(not acceptance_path.exists(), 'Target already passed; do not replay')
        work = OUT / 'qa' / f'{args.target}-{kind}-{args.attempt}'
        work.parent.mkdir(exist_ok=True)
        work.mkdir()
        users_before = user_hashes()
        if kind == 'q36':
            fixture = recipes.prepare_q36(work, app, commit)
            home = fixture['home']
        else:
            home = str(work / 'prism-e2e-profile')
        destination = work / 'qa.mjs'
        source = recipes.qa(kind, args.target, args.attempt, work)
        with destination.open('x', encoding='utf-8') as stream:
            stream.write(source)
        origin = RUNTIME / ('qa-q36-r14.mjs' if kind == 'q36' else 'qa-prism-r5.mjs')
        write_new(work / 'recipe.json', dict(origin=str(origin), originSHA256=sha(origin), recipeSHA256=sha(destination), target=args.target,
                  sourceCommit=commit, shellPath=str(app / 'strata-desktop.exe'), historicalPassesCopied=False))
        run = subprocess.run([str(NODE), str(destination), '--execute', '--reviewed-commit', commit], cwd=ROOT, env=build_env(), check=False, timeout=1400)
        receipt = work / f'{"functional-e2e" if kind == "q36" else "prism-e2e"}-{args.attempt}.json'
        result = load(receipt)
        require(run.returncode == 0 and result['ok'], 'GUI QA failed; retain attempt diagnostics')
        require(user_hashes() == users_before, 'Normal user data changed during isolated GUI QA')
        result.update(home=home, work=str(work), recipeSHA256=sha(destination), attemptReceiptSHA256=sha(receipt))
        result.update(userHashesUnchanged=True, userFilesChecked=len(users_before), userInventorySHA256=digest(users_before))
        native = load(OUT / 'staged-native.json')
        result.update(appSourceCommit=commit, controlSourceCommit=load(OUT / 'control-build.json')['sourceCommit'],
                      nativeSourceCommit=native['nativeSourceCommit'], stagedReceiptSHA256=sha(OUT / 'staged-native.json'),
                      releaseQualified=False, quality=native['quality'])
        require(payload(app) == load(OUT / 'qualified-payload.json'), 'Actual target bytes changed during QA')
        write_new(acceptance_path, result)
    else:
        import upgrade
        acceptance(commit)
        {'backup': upgrade.backup, 'install': upgrade.install, 'verify': upgrade.verify_installed,
         'activate': upgrade.activate, 'normal-start': upgrade.normal_start}[args.step]()


def guarded(args: argparse.Namespace) -> int:
    """Contain only this invocation; continuous unchanged floors; retain every failure."""
    sys.path.insert(0, str(ROOT))
    from serve import winjob
    receipts = OUT / 'receipts'
    receipts.mkdir(exist_ok=True)
    name = f'{args.step}-{args.target}-{args.attempt}'
    path = receipts / f'{name}.json'
    require(not path.exists(), 'Fresh phase receipt required')
    report = dict(ok=False, ownedOnly=True, resourceFloorsGiB=dict(ram=3, commit=4, c=5, h=10), abort=None)
    child = None
    started = time.monotonic()
    try:
        with (receipts / f'{name}.txt').open('x', encoding='utf-8') as log, (receipts / f'{name}-resources.jsonl').open('x', encoding='utf-8') as samples:
            command = [str(PYTHON), '-B', str(HERE / 'adapter.py'), args.step, '--execute', '--worker', '--reviewed-commit', args.reviewed_commit,
                       '--native-source-root', args.native_source_root, '--target', args.target, '--attempt', args.attempt]
            worker = 'import json,subprocess,sys;assert sys.stdin.readline().strip()=="GO";raise SystemExit(subprocess.call(json.loads(sys.argv[1])))'
            child = subprocess.Popen([str(PYTHON), '-B', '-c', worker, json.dumps(command)], cwd=ROOT, env=build_env(), stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            require(winjob.contain(child), 'Owned child containment failed')
            child.stdin.write('GO\n')
            child.stdin.flush()
            child.stdin.close()
            while child.poll() is None:
                sample = resources()
                failures = blockers(sample)
                if time.monotonic() - started > args.seconds:
                    failures.append('deadline')
                samples.write(json.dumps(dict(sample, elapsedSeconds=time.monotonic() - started, blockers=failures)) + '\n')
                samples.flush()
                if failures:
                    report['abort'] = failures
                    winjob.terminate()
                    break
                time.sleep(1)
            report['exitCode'] = child.wait(timeout=15)
            report['ok'] = report['exitCode'] == 0 and report['abort'] is None
    except BaseException as error:
        report['errorType'] = type(error).__name__
        raise
    finally:
        winjob.terminate()
        if child and child.poll() is None:
            child.kill()
            child.wait(timeout=10)
        report['seconds'] = round(time.monotonic() - started, 3)
        write_new(path, report)
        print(json.dumps(report))
    return 0 if report['ok'] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step', choices=STEPS)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--execute', action='store_true')
    mode.add_argument('--plan', action='store_true', help='Read-only plan (also the default)')
    parser.add_argument('--reviewed-commit')
    parser.add_argument('--native-source-root')
    parser.add_argument('--target', choices=['candidate', 'installed'], default='candidate')
    parser.add_argument('--attempt', default='r1')
    parser.add_argument('--seconds', type=int, default=3000)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    require(bool(re.fullmatch('r[1-9][0-9]*', args.attempt)) and 1 <= args.seconds <= 3600, 'Invalid attempt/deadline')
    if not args.execute:
        print(json.dumps(dict(wouldExecute=False, step=args.step, target=args.target, output=str(OUT),
              product=PRODUCT, control=CONTROL, native=ENGINE, requiresReviewedCleanSource=True,
              requiresParentSignedReceipt=True, releaseQualified=False, normalLaunchOutsideGuard=args.step == 'normal-start')))
        return 0
    commit = approved_source(args.reviewed_commit)
    require_resources()
    require(args.native_source_root is not None and Path(args.native_source_root).is_absolute(), 'Explicit native source root required')
    # This variable exists only in this helper/children, never in a global config.
    os.environ['LOCAL053_NATIVE_SOURCE_ROOT'] = args.native_source_root
    staged()
    if args.step == 'normal-start':
        require(not args.worker, 'Normal launch must be outside QA containment')
        execute(args, commit)
        return 0
    if args.worker:
        execute(args, commit)
        return 0
    return guarded(args)


if __name__ == '__main__':
    raise SystemExit(main())
