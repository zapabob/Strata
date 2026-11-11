"""Prepare independent fork versions and retain the upstream reference manifest."""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = '0.5.8'

manifest_file = ROOT / 'docs/data/release.json'
old = json.loads(manifest_file.read_text(encoding='utf-8'))
upstream = old.get('upstream', old)
upstream.pop('_about', None)
manifest = {
    '_about': 'Current Hakua Windows fork source release. Upstream references and immutable historical installers are declared independently; the checker never rewrites their URLs.',
    'tag': 'v' + PRODUCT, 'product_version': PRODUCT, 'control_version': PRODUCT, 'engine_version': PRODUCT,
    'installer_names': ['Strata-{v}-windows-x64-setup.exe'],
    'assets': [f'Strata-{PRODUCT}-windows-x64-setup.exe', f'Strata-{PRODUCT}-windows-x64.tar.7z'],
    'upstream': upstream,
    'historical_releases': [
        {'tag': 'v' + version, 'product_version': version, 'assets': [f'Strata-{version}-windows-x64-setup.exe']}
        for version in ('0.5.0', '0.5.1', '0.5.7')
    ],
}
manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
for relative in ('apps/host/package.json', 'apps/host/package-lock.json', 'apps/desktop/package.json', 'apps/desktop/package-lock.json'):
    path = ROOT / relative
    text = path.read_text(encoding='utf-8')
    path.write_text(text.replace('"version": "0.5.7"', '"version": "0.5.8"'), encoding='utf-8', newline='\n')
for relative in ('apps/desktop/src-tauri/Cargo.toml', 'apps/desktop/src-tauri/Cargo.lock'):
    path = ROOT / relative
    path.write_text(path.read_text(encoding='utf-8').replace('version = "0.5.7"', 'version = "0.5.8"'), encoding='utf-8', newline='\n')
(ROOT / 'VERSION').write_text(PRODUCT + '\n', encoding='utf-8', newline='\n')
(ROOT / 'CONTROL_VERSION').write_text(PRODUCT + '\n', encoding='utf-8', newline='\n')
path = ROOT / 'strata_cli/__init__.py'
path.write_text(path.read_text(encoding='utf-8').replace('PRODUCT_VERSION = "0.5.5-local.1"', 'PRODUCT_VERSION = "0.5.8"'), encoding='utf-8', newline='\n')

# Preserve the entire old register and add only the ten missing source reads.
# Regeneration output supplies exact source positions, not performance claims.
path = ROOT / 'data/settings-register.json'
generated = json.loads(path.read_text(encoding='utf-8'))
original = json.loads(subprocess.check_output(['git', 'show', 'HEAD:data/settings-register.json'], cwd=ROOT))
known = {entry['name'] for entry in original['settings']}
for entry in generated['settings']:
    if entry['name'] not in known:
        site = entry['reads'][0]
        entry.update(status='unsure', owner='Hakua fork', note=f"Read at {site['file']}:{site['line']}. Recorded from source; backend behavior and performance are not newly qualified by the 0.5.8 test repair.")
        original['settings'].append(entry)
original['settings'].sort(key=lambda entry: entry['name'])
path.write_text(json.dumps(original, indent=1, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
