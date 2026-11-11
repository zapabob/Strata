"""Run scoped Python repair checks from the source root under the parent guard."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
MODES = {
    'focused': ['-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tools/test_release_manifest.py', 'tools/test_bench_results_index.py', 'tools/test_check_links.py',
        'tools/test_settings_register.py', 'tools/test_source_nul_bytes.py', 'tools/test_setup_disk_room.py',
        'tools/test_run_native_validation_step.py', 'tools/test_native_model_resource_guard.py',
        'serve/test_q36_memory_contract.py'],
    'tools': ['tools/check', '--only', 'py-tools', '--keep', '--scratch', 'H:/Strata/releases/stable-058-20261111-codex/py-tools-r1'],
    'terminal': ['-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/terminal/test_install_scripts_env.py', 'tests/terminal/test_preview_overlay.py',
        'tests/terminal/test_tui2_023_versions.py', 'tests/terminal/test_tuiqa_version.py',
        'tests/terminal/test_updater.py', 'tests/regression/test_regression_spin8_triality.py',
        'tests/packaging/test_backend_packages.py', 'tests/tuning/test_offline.py',
        'tests/test_strata_memory.py', 'tests/test_hermes_strata_plugin.py'],
}
MODES['terminal-first'] = [*MODES['terminal'], '-x']
MODES['repair-final'] = ['-m', 'pytest', '-q', '-p', 'no:cacheprovider',
    'tools/test_capability_table.py', 'tools/test_bench_results_index.py', 'tools/test_release_manifest.py',
    'tests/test_strata_memory.py', 'tests/terminal/test_install_scripts_env.py', 'serve/test_q36_memory_contract.py']
MODES['ci-followup'] = ['-m', 'pytest', '-q', '-p', 'no:cacheprovider',
    'tests/snapshot/test_entry_points_agree.py',
    'tools/test_strata_mcp.py::MixedGraphics::test_windows_lists_an_amd_card_and_not_the_integrated_radeon']
environment = dict(os.environ, STRATA_TEST_NODE_EXE=str(ROOT / 'apps/desktop/src-tauri/resources/node/node.exe'), PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
raise SystemExit(subprocess.call([sys.executable, '-X', 'utf8', '-B', *MODES[sys.argv[1]]], cwd=ROOT, env=environment))
