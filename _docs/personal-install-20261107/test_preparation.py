"""Preparation gate tests only. No build, signing, user-data access or model execution."""
import unittest
from unittest.mock import patch
import common

class PreparationGateTests(unittest.TestCase):
    def test_all_resource_floors_are_independent_and_inclusive(self):
        exact={'ramBytes':3*1024**3,'commitBytes':4*1024**3,'cFreeBytes':5*1024**3,'hFreeBytes':10*1024**3}
        self.assertEqual(common.blockers(exact),[])
        for field in exact:
            with self.subTest(field=field):
                below=dict(exact);below[field]-=1
                self.assertEqual(len(common.blockers(below)),1)

    def test_missing_review_is_rejected_before_git_or_execution(self):
        with patch.object(common,'git') as git:
            for value in [None,'', 'c780cc84','--approved']:
                with self.assertRaises(RuntimeError):common.approved_source(value)
            git.assert_not_called()

    def test_stale_or_dirty_review_cannot_reach_build(self):
        commit='a'*40
        with patch.object(common,'git',return_value='b'*40):
            with self.assertRaisesRegex(RuntimeError,'HEAD'):common.approved_source(commit)
        with patch.object(common,'git',side_effect=[commit,'apps/host/server/index.mjs']):
            with self.assertRaisesRegex(RuntimeError,'freeze'):common.approved_source(commit)
        with patch.object(common,'git',side_effect=[commit,'','unreviewed.py']):
            with self.assertRaisesRegex(RuntimeError,'freeze'):common.approved_source(commit)

    def test_previous_native_override_cannot_leak_into_current_root_build(self):
        injected={key:'old-c50-root' for key in ['STRATA_NATIVE_SOURCE_ROOT','STRATA_NATIVE_SOURCE_COMMIT','STRATA_NATIVE_MANIFEST_SHA256']}
        with patch.dict(common.os.environ,injected),patch.object(common.Path,'mkdir'):
            env=common.build_env()
        self.assertTrue(all(key not in env for key in injected))
        self.assertEqual(env['CARGO_BUILD_JOBS'],'1')
        self.assertEqual(env['NODE_OPTIONS'],'--max-old-space-size=1024')
        self.assertTrue(env['TEMP'].startswith('H:'))
        self.assertTrue(env['PSModuleAnalysisCachePath'].startswith('H:'))

    def test_quality_receipt_cannot_turn_resource_failure_into_release_pass(self):
        quality={'sourceCommit':common.NATIVE_COMMIT,'manifestSHA256':common.UNSIGNED_MANIFEST,'strataSHA256':common.ENGINE_SHA,
                 'nativeFunctionalChecksPassed':True,'suitePassed':17,'releaseQualified':True,'resourceGuard':'FAIL','resourceViolations':[0]*4}
        with patch.object(common,'load',return_value=quality):
            with self.assertRaisesRegex(RuntimeError,'failure'):common.quality_record()
        quality['releaseQualified']=False
        with patch.object(common,'load',return_value=quality),patch.object(common,'sha',return_value='c'*64):
            record=common.quality_record()
        self.assertIs(record['releaseQualified'],False);self.assertEqual(record['resourceViolationCount'],4)

    def test_normal_handoff_preserves_automatic_override_without_global_change(self):
        old='C:/fixture/previous-generic/llama-server.exe'
        with patch.dict(common.os.environ,{'STRATA_LLAMA_SERVER':old,'WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS':'qa-only'}):
            env=common.normal_app_env()
            self.assertEqual(env['STRATA_LLAMA_SERVER'],old)
            self.assertNotIn('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS',env)
            self.assertEqual(common.os.environ['STRATA_LLAMA_SERVER'],old)

if __name__=='__main__':unittest.main()
