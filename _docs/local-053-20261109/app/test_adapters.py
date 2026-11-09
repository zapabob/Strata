"""Low-impact adapter contract checks: no package, model, process, or profile operations."""
from __future__ import annotations

import ast
import contextlib
import io
from unittest import TestCase, main
from unittest.mock import patch

import adapter
from common import *
import recipes
import upgrade


class AdapterContracts(TestCase):
    def test_python_syntax_without_bytecode(self) -> None:
        for path in HERE.glob('*.py'):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))

    def test_every_plan_is_side_effect_free(self) -> None:
        for step in adapter.STEPS:
            with self.subTest(step=step), patch.object(sys, 'argv', ['adapter.py', step]), patch.object(adapter, 'approved_source', side_effect=AssertionError('gate reached')), patch.object(adapter, 'staged', side_effect=AssertionError('staging reached')), patch.object(adapter, 'guarded', side_effect=AssertionError('execution reached')), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(adapter.main(), 0)
                self.assertFalse(json.loads(output.getvalue())['wouldExecute'])

    def test_execute_fails_before_side_effects_without_review(self) -> None:
        with patch.object(sys, 'argv', ['adapter.py', 'install', '--execute']), patch.object(adapter, 'guarded', side_effect=AssertionError('execution reached')):
            with self.assertRaisesRegex(RuntimeError, 'Full reviewed commit'):
                adapter.main()

    def test_replacement_refuses_drift(self) -> None:
        for text in ['absent', 'needle needle']:
            with self.assertRaisesRegex(RuntimeError, 'Historical recipe drift'):
                recipes.replace(text, 'needle', 'replacement')

    def test_all_generated_javascript_contracts_and_syntax(self) -> None:
        scripts = [('qualify', recipes.qualify())]
        for target in ['candidate', 'installed']:
            for kind in ['q36', 'prism']:
                work = OUT / 'qa' / f'{target}-{kind}-r2'
                source = recipes.qa(kind, target, 'r2', work)
                scripts.append((f'{target}-{kind}', source))
                self.assertIn('connectOverCDP', source)
                self.assertIn("'x-strata-client':'ui',Origin:base", source)
                self.assertIn('isolate-host-home.mjs', source)
                self.assertIn('actualShellAndHost=true', source)
                self.assertIn('installedExeTest:' + str(target == 'installed').lower(), source)
                self.assertNotIn(recipes.OLD_OUT, source)
                self.assertNotIn('plan.target', source)
                self.assertNotIn('0.5.2', source)
                if kind == 'q36':
                    self.assertIn("name:'Model version'", source)
                    self.assertIn("name:/^More versions/", source)
                    self.assertIn("name:'Legacy'", source)
                else:
                    self.assertIn('PrismML 0.4.1 · 1965755c', source)
                    self.assertIn("'56'", source)
                    self.assertIn(INSTALLED.as_posix() if target == 'installed' else (OUT / 'extracted').as_posix(), source)
        for name, source in scripts:
            with self.subTest(recipe=name):
                run = subprocess.run([str(NODE), '--input-type=module', '--check'], input=source, text=True, encoding='utf-8', capture_output=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stderr)

    def test_resource_floors_boundaries(self) -> None:
        sample = dict(ramBytes=3 * 1024**3, commitBytes=4 * 1024**3, cFreeBytes=5 * 1024**3, hFreeBytes=10 * 1024**3)
        self.assertEqual(blockers(sample), [])
        for key in sample:
            below = dict(sample)
            below[key] -= 1
            self.assertEqual(len(blockers(below)), 1)

    def test_candidate_receipt_cannot_satisfy_installed_acceptance(self) -> None:
        def receipt(path: Path) -> dict:
            if path.name == 'app-build.json':
                return dict(sourceCommit='a' * 40, installer='H:/candidate.exe', sha256='hash')
            if path.name == 'app-qualification.json':
                return dict(sourceCommit='a' * 40, ok=True, installerSHA256='hash')
            return dict(sourceCommit='a' * 40, ok=True, target='candidate')
        with patch.object(upgrade, 'load', side_effect=receipt), patch.object(upgrade, 'sha', return_value='hash'):
            with self.assertRaisesRegex(RuntimeError, 'Target-specific GUI evidence'):
                upgrade.acceptance('a' * 40, 'installed')

    def test_prelaunch_refuses_new_user_files(self) -> None:
        def receipt(path: Path) -> dict:
            if path.name == 'backup.json':
                return dict(preflightSHA256='hash')
            return dict(files=[], userInventory={'old': 'hash'})
        with patch.object(upgrade, 'load', side_effect=receipt), patch.object(upgrade, 'sha', return_value='hash'), patch.object(upgrade, 'user_hashes', return_value={'old': 'hash', 'new': 'new-hash'}):
            with self.assertRaisesRegex(RuntimeError, 'User membership/bytes'):
                upgrade.preflight()

    def test_existing_nsis_claim_prevents_spawn(self) -> None:
        pre = dict(installedManaged={'shell': 'old'}, registration={'old': 'registration'})
        with patch.object(upgrade, 'quiescent'), patch.object(upgrade, 'preflight', return_value=pre), patch.object(upgrade, 'payload', return_value=pre['installedManaged']), patch.object(upgrade, 'registration', return_value=pre['registration']), patch.object(upgrade, 'load', return_value=dict(installer='H:/candidate.exe', sha256='hash')), patch.object(upgrade, 'sha', return_value='hash'), patch.object(upgrade, 'write_new', side_effect=FileExistsError('exclusive claim')), patch.object(upgrade.subprocess, 'run') as run:
            with self.assertRaises(FileExistsError):
                upgrade.install()
            run.assert_not_called()

    def test_preload_isolates_real_node_homedir_and_rejects_normal_home(self) -> None:
        module = (HERE / 'isolate-host-home.mjs').as_uri()
        home = OUT / 'qa/installed-q36-r2/e2e-profile'
        env = dict(os.environ, STRATA_HOME=str(home))
        run = subprocess.run([str(NODE), '--import=' + module, '--input-type=module', '-e', "import os from 'node:os';import assert from 'node:assert/strict';assert.equal(os.homedir(),process.env.STRATA_HOME);"], env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        env['STRATA_HOME'] = 'C:/Users/downl/.strata'
        run = subprocess.run([str(NODE), '--import=' + module, '-e', 'process.exit(0)'], env=env, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(run.returncode, 0)


if __name__ == '__main__':
    main(verbosity=2)
