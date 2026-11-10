"""Checked 055 adaptation of the immutable, already exercised 054 release recipes."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_COMMIT = 'c1ceee69e4d5d9e65f9a62b0a8ff10f8b93b3d4c'
APP_COMMIT = '35863deadec1bfa0fc7f250c111d219bb3344b57'
INSTALLER_SHA = 'c2eac64146485720f2fef61e5fe3a2824e48fa15b1c1887a03761fa0ac90becf'


def replace(text: str, before: str, after: str, count: int = 1) -> str:
    if text.count(before) != count:
        raise ValueError('Reviewed release anchor changed: ' + before[:100])
    return text.replace(before, after)


def install(scope: dict, name: str) -> None:
    path = ROOT / '_docs/release-054-20261110' / name
    text = path.read_text(encoding='utf-8')
    frozen = subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{TEMPLATE_COMMIT}:_docs/release-054-20261110/{name}'], timeout=30).decode('utf-8')
    if text != frozen.replace('\r\n', '\n'):
        raise ValueError('Historical release recipe changed')
    text = text.replace('0.5.5', '__CONTROL__').replace('0.5.4', '0.5.5').replace('__CONTROL__', '0.5.6')
    text = text.replace('public-054-20261110-opencode', 'public-055-20261111-opencode')
    text = text.replace('upstream-0213-20261109-opencode/app-native054', 'repair-055-20261110-opencode/app-native055-ui-search')
    text = text.replace('release-054-20261110', 'release-055-20261111')
    text = text.replace('85a78234cfcdccd8741cc921677802aba1869e44', APP_COMMIT)
    text = text.replace('ae05518656ee5afdf92665f5dd71a06a69425ae1957a9ac31468d8a4a1790750', INSTALLER_SHA)
    text = text.replace('20261110000100', '20261111000100')
    if name == 'prepare.py':
        text = replace(text, 'CUDA resource guard has 12 violations.', 'CUDA resource guard passes with zero violations.')
        text = replace(text, '"prismRestartWarmupTimeoutObserved": True,',
            '"historical054PrismWarmupTimeoutRetained": True, "historicalPrismCauseEstablished": False,\n'
            '        "installedPrismRestartAndActualAgentPassed": True, "installedBulkDeletePassed": True,\n'
            '        "browserMcpCoordinateChecksPassed": True, "publicSearchSitesQualified": False,')
        text = text.replace('userFilesPreservedDuringMeasuredUpgrade": 4028', 'userFilesPreservedDuringMeasuredUpgrade": 4078')
        text = replace(text, '"recipe_sha256": sha(Path(__file__))}',
            '"recipe_sha256": sha(Path(__file__)), "adapter_sha256": sha(Path(__file__).with_name("adapt.py")),\n'
            '        "recipe_template_commit": "' + TEMPLATE_COMMIT + '"}')
        text = replace(text, '"-mx=5", "-md=64m", "-mmt=5"', '"-mx=0", "-mmt=1"')
        text = replace(text, '    return folder, receipt, build', '''    q36 = load(BUILD / "installed-q36-e2e.json")
    prism = load(BUILD / "installed-prism-e2e.json")
    enabled = load(BUILD / "normal-browser-search-enabled.json")
    require(all(row["sourceCommit"] == build["sourceCommit"] and row["installedExeTest"] is True
                and row["actualWebView2"] is True and row["userHashesUnchanged"] is True for row in (q36, prism)),
            "Actual source-bound installed GUI evidence required")
    require(q36["workspaceFilesAcceptance"]["bulkDelete"]["ok"] is True
            and q36["workspaceFilesAcceptance"]["bulkDelete"]["confirmedChats"] >= 26,
            "Installed bulk deletion evidence missing")
    require(prism["actualSupervisorAgent"] is True and prism["agentCycles"] == 2
            and prism["actualTeardownChecks"] == 2, "Installed actual agent/restart evidence missing")
    require(enabled["passed"] and enabled["browserEnabled"] and enabled["modelsUnloaded"],
            "Normal browser/search setup not verified")
    quality = receipt["quality"]
    require(quality["nativeResourceGuard"]["passed"] is True and not quality["nativeResourceGuard"]["violations"]
            and quality["finalNumericalChecksPassed"] is True, "Final native resource/numerical gate missing")
    return folder, receipt, build''')
    elif name == 'verify.py':
        text = replace(text, 'len(quality["nativeResourceGuard"]["violations"]) == 12',
            'quality["nativeResourceGuard"]["passed"] is True and not quality["nativeResourceGuard"]["violations"]\n'
            '              and quality["installedBulkDeletePassed"] is True and quality["installedPrismRestartAndActualAgentPassed"] is True')
        text = replace(text, '    docs_check(prepared)',
            '    p.require(source["adapter_sha256"] == p.sha(Path(__file__).with_name("adapt.py")), "Release adapter changed")\n    docs_check(prepared)')
        text = text.replace('"nvidia_driver": "621.01"', '"nvidia_driver": "621.14"')
    elif name != 'publish.py':
        raise ValueError('Unknown explicit release recipe')
    compile(text, str(Path(scope['__file__'])), 'exec')
    scope['recipe_template_sha256'] = hashlib.sha256(frozen.encode()).hexdigest()
    exec(compile(text, str(Path(scope['__file__'])), 'exec'), scope)
