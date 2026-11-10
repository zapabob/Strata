"""Generate fresh 055 delivery adapters; default is a read-only, hash-bound plan.

Historical artifacts and recipes stay intact. This only prepares code: signing,
building, model execution, installation and publication remain explicit phases.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from prepare import FROZEN, HISTORY, checked_replace
from native import OUT, ROOT, require, sha

NATIVE_COMMIT = 'b995af139cc823537489b886bc1e8602cf10301c'
OLD_COMMIT = '7bb2497400b8ea40d5d07f5244f010d3aa5eacc0'
DEST = OUT / 'adapters/delivery-ui-search-r1'
APP_NAME = 'app-native055-ui-search'
GROUPS = {
    'component': ('core.py', 'quality.py', 'compose.py', 'deps.py', 'verify.mjs'),
    'app': ('common.py', 'adapter.py', 'build.py', 'recipes.py', 'upgrade.py',
            'probe.py', 'verify-native.mjs', 'isolate-host-home.mjs',
            'q36-projection-acceptance.mjs', 'workspace-files-acceptance.mjs',
            'close-qa-window.py'),
}


def transform(group: str, name: str, text: str) -> str:
    """Keep independent Control and engine versions separate during adaptation."""
    if group == 'app' and name == 'common.py':
        text = checked_replace(text,
            "PRODUCT, CONTROL, ENGINE = '0.5.4-local.1', '0.5.5', '0.5.4'",
            "PRODUCT, CONTROL, ENGINE = '__PRODUCT__', '__CONTROL__', '__ENGINE__'")
        text = checked_replace(text,
            "PATH=str(NODE.parent) + ';C:/Users/downl/.cargo/bin;' + env['PATH']",
            "PATH=str(NODE.parent) + ';C:/Users/downl/.cargo/bin;C:/Windows/System32/WindowsPowerShell/v1.0;' + env['PATH']")
    if group == 'app' and name == 'recipes.py':
        text = checked_replace(text, '"controlVersion=\'0.5.5\'"', '"controlVersion=\'__CONTROL__\'"')
    if group == 'component' and name == 'compose.py':
        text = checked_replace(text,
            '(ROOT / "CONTROL_VERSION").read_text().strip() == "0.5.5"',
            '(ROOT / "CONTROL_VERSION").read_text().strip() == "__CONTROL__"')
    text = text.replace(r'0\.5\.4', r'0\.5\.5').replace('0.5.4', '0.5.5')
    text = text.replace('__PRODUCT__', '0.5.5-local.1').replace('__CONTROL__', '0.5.6').replace('__ENGINE__', '0.5.5')
    text = text.replace(HISTORY.as_posix(), OUT.as_posix())
    text = text.replace((OUT / 'adapters/app').as_posix(), (DEST / 'app').as_posix())
    text = text.replace(OLD_COMMIT, NATIVE_COMMIT)
    text = text.replace('native-054-source-20261110', FROZEN.name)
    text = text.replace('app-native054', APP_NAME).replace('component-054', 'component-055-ui-search')
    text = text.replace('component-staging-054', 'component-staging-055-ui-search').replace('control-staging-054', 'control-staging-055-ui-search')
    if group == 'component' and name == 'quality.py':
        text = text.replace('/adapters/native-r2', '/adapters/native')
        # This candidate must repair the old findings. The historical validator's
        # ability to record a genuine FAIL remains, but cannot admit this package.
        text = checked_replace(text, '    resource_pass = spill["passed"]',
            '    resource_pass = spill["passed"]\n'
            '    require(resource_pass is True and not violations and passed(phases["spill"]),\n'
            '            "055 requires a completed passing unchanged resource guard")')
        numerical = '''    numerical = load(base.parent / "gpu-final-results-final-r1.json")
    numerical_driver = load(base.parent / "receipts/gpu-final-numerical-r1.json")
    expected_cases = {"libraries", "expdec", "grouped", "dflash-17", "dflash-18", "dflash-21",
                      "qsa-selftest", "qsa-boundary", "qsa-active"}
    expected_cases.update(f"w4a8-{cfg}-{arm}" for cfg in range(4) for arm in ("old", "new", "wide"))
    require(passed(numerical_driver) and numerical.get("diagnosticOnly") is False
            and numerical.get("passed") is True and numerical.get("sourceCommit") == NATIVE_COMMIT
            and numerical.get("releaseQualified") is False
            and len(numerical["cases"]) == len(expected_cases)
            and {row["case"] for row in numerical["cases"]} == expected_cases
            and all(row["passed"] is True for row in numerical["cases"]),
            "Completed source-bound final numerical checks required")
    require(all(numerical["binding"][key] == package[key] for key in numerical["binding"]),
            "Final numerical binary binding differs")
    tested = numerical["testedBuildFiles"]
    require(tested and tested.get("Release/strata.exe") == engine
            and tested.get("Release/strata-q36.exe") == package["q36SHA256"],
            "Final numerical tested binaries differ")
    for name, checksum in tested.items():
        require(name.startswith("Release/") and ".." not in Path(name).parts
                and sha(base.parent / "native-build" / name) == checksum,
                "Final numerical tested artifact changed")
    for name in ("gpu-final-results-final-r1.json", "receipts/gpu-final-numerical-r1.json"):
        path = base.parent / name
        evidence["finalNumerical/" + name] = {"path": str(path), "sha256": sha(path)}
'''
        text = checked_replace(text, '    return {"nativeFunctionalChecksPassed": True,',
            numerical + '    return {"nativeFunctionalChecksPassed": True, "finalNumericalChecksPassed": True,')
    if group == 'app' and name == 'recipes.py':
        text += ('\n\nfrom repair_qa import repair_qa\n'
                 '_repair_base_qa = qa\n'
                 'def qa(kind, target, attempt, work):\n'
                 '    return repair_qa(_repair_base_qa(kind, target, attempt, work), kind, HERE)\n')
    if group == 'app' and name == 'upgrade.py':
        text = checked_replace(text, "        if kind == 'q36':",
            "        if kind == 'prism':\n"
            "            require(result.get('actualSupervisorAgent') is True and result.get('agentCycles') == 2\n"
            "                    and result.get('actualTeardownChecks') == 2, 'Actual supervisor agent/restart/exit evidence required')\n"
            "        if kind == 'q36':")
        text = checked_replace(text,
            "            projection = result.get('projectionAcceptance', {})",
            "            require(files.get('bulkDelete', {}).get('ok') is True, 'Actual packaged bulk-delete acceptance required')\n"
            "            projection = result.get('projectionAcceptance', {})")
        text = checked_replace(text, 'private-backups/local-054-20261110-opencode', 'private-backups/local-055-20261110-opencode')
        text = checked_replace(text,
            "OLD_COMPONENT = LOCAL / 'components/engine/0.5.3-windows-x86_64-cuda-cuda13'",
            "OLD_COMPONENT = LOCAL / 'components/engine/0.5.4-windows-x86_64-cuda-cuda13'")
    if group == 'app' and name == 'isolate-host-home.mjs':
        text = checked_replace(text, 'upstream-0213-20261109-opencode', OUT.name)
    if group == 'app' and name == 'workspace-files-acceptance.mjs':
        text = "import {packagedBulkDelete} from './packaged-bulk-delete.mjs';\n" + text
        text = checked_replace(text,
            'await section.getByRole(\'button\',{name:`Rename ${created}`,exact:true}).click();',
            'await section.getByRole(\'button\',{name:`Actions for ${created}`,exact:true}).click();await page.getByRole(\'menuitem\',{name:\'Rename item\',exact:true}).click();')
        text = checked_replace(text,
            'await section.getByRole(\'button\',{name:`Move ${renamed} to trash`,exact:true}).click();',
            'await section.getByRole(\'button\',{name:`Actions for ${renamed}`,exact:true}).click();await page.getByRole(\'menuitem\',{name:\'Move to trash\',exact:true}).click();')
        text = checked_replace(text,
            "await section.getByRole('button',{name:'qa-old-folder',exact:true}).click();await section.getByText('This folder is empty.',{exact:true}).waitFor();",
            "await section.getByText('This folder is empty.',{exact:true}).waitFor();")
        text = checked_replace(text,
            "await page.setViewportSize({width:1600,height:1000});await language('en');await modelScreen();",
            "await page.setViewportSize({width:1600,height:1000});await language('en');const bulkDelete=await packagedBulkDelete({page,request,home,workspace});await modelScreen();")
        text = checked_replace(text, 'return {ok:true,noMocks:true,isolatedWorkspace:true,checks};',
            'return {ok:true,noMocks:true,isolatedWorkspace:true,checks:[...checks,...bulkDelete.checks],bulkDelete};')
    require(OLD_COMMIT not in text and HISTORY.as_posix() not in text, 'Stale delivery source/output identity')
    return text


def outputs() -> tuple[dict[str, str], dict]:
    result, records = {}, {}
    for group, names in GROUPS.items():
        for name in names:
            source = HISTORY / 'adapters' / group / name
            raw = source.read_bytes()
            text = transform(group, name, raw.decode('utf-8').replace('\r\n', '\n'))
            target = f'{group}/{name}'
            if name.endswith('.py'):
                compile(text, str(DEST / target), 'exec')
            result[target] = text
            records[target] = {'template': str(source), 'templateSHA256': hashlib.sha256(raw).hexdigest(),
                               'sha256': hashlib.sha256(text.encode()).hexdigest()}
    helper = Path(__file__).with_name('repair-qa.py')
    raw = helper.read_bytes()
    text = raw.decode('utf-8').replace('\r\n', '\n')
    compile(text, str(DEST / 'app/repair_qa.py'), 'exec')
    result['app/repair_qa.py'] = text
    records['app/repair_qa.py'] = {'template': str(helper), 'templateSHA256': hashlib.sha256(raw).hexdigest(),
                                 'sha256': hashlib.sha256(text.encode()).hexdigest()}
    helper = Path(__file__).with_name('packaged-bulk-delete.mjs')
    raw = helper.read_bytes()
    text = raw.decode('utf-8').replace('\r\n', '\n')
    result['app/packaged-bulk-delete.mjs'] = text
    records['app/packaged-bulk-delete.mjs'] = {'template': str(helper), 'templateSHA256': hashlib.sha256(raw).hexdigest(),
                                           'sha256': hashlib.sha256(text.encode()).hexdigest()}
    return result, {'nativeCommit': NATIVE_COMMIT, 'nativeRoot': str(FROZEN),
        'appOutput': str(OUT / APP_NAME), 'files': records,
        'releaseQualified': False, 'requiresFreshResourcePass': True,
        'historicalPassesCopied': False, 'runtimeActions': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    files, report = outputs()
    print(json.dumps({'execute': args.execute, **report}, indent=2))
    if not args.execute:
        return 0
    spec = importlib.util.spec_from_file_location('delivery_guard', ROOT / '_docs/local-053-20261109/native/common.py')
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    guard.BASE = OUT
    guard.require_current_job(ROOT)
    require(all(not (DEST / group).exists() for group in GROUPS), 'Fresh delivery adapter roots required')
    require(sha(FROZEN / 'VERSION') == sha(ROOT / 'VERSION'), 'Candidate version differs from native freeze')
    require(DEST.parent.is_dir() and not DEST.exists(), 'Fresh delivery revision required')
    DEST.mkdir()
    for group in GROUPS:
        (DEST / group).mkdir()
    for name, text in files.items():
        with (DEST / name).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    guard.save(OUT / 'delivery-adapter-provenance-ui-search-r1.json', report, fresh=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
