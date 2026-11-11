"""Prepare a fresh parent-approved native attempt, retaining the refused GPU admission."""
import hashlib
import json
from pathlib import Path

OUT = Path('H:/Strata/releases/stable-058-20261111-codex')
receipt = json.loads((OUT / 'before-native-normal-unload-r1.json').read_text())
assert receipt['ok'] and receipt['normalAppAPIsOnly'] and not receipt['forceKills']
assert not (OUT / 'native-evidence-r2').exists()
rows = {}
for group in ('native', 'component'):
    source = OUT / 'adapters' / group
    target = OUT / 'adapters' / (group + '-r2')
    target.mkdir()
    for path in source.iterdir():
        if path.suffix not in ('.py', '.mjs'):
            continue
        original = path.read_bytes()
        text = original.decode('utf-8').replace('native-evidence', 'native-evidence-r2').replace('/adapters/native', '/adapters/native-r2')
        text = text.replace('/component-058', '/component-058-r2').replace('component-staging-058', 'component-staging-058-r2')
        if path.suffix == '.py':
            compile(text, str(target / path.name), 'exec')
        (target / path.name).write_text(text, encoding='utf-8', newline='\n')
        rows[str(target / path.name)] = {'template': str(path), 'templateSHA256': hashlib.sha256(original).hexdigest(),
            'sha256': hashlib.sha256((target / path.name).read_bytes()).hexdigest()}
source = OUT / 'adapters/gpu.py'
target = OUT / 'adapters/gpu-r2.py'
text = source.read_text(encoding='utf-8').replace("'native-evidence'", "'native-evidence-r2'").replace('adapters/native/', 'adapters/native-r2/')
assert not target.exists()
target.write_text(text, encoding='utf-8', newline='\n')
rows[str(target)] = {'template': str(source), 'templateSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
with (OUT / 'native-retry-preparation-r2.json').open('x', encoding='utf-8') as stream:
    json.dump({'reason': 'Original model admission refused while another Strata model used the GPU; normal unload completed.',
        'freshEvidence': str(OUT / 'native-evidence-r2'), 'retainedOriginalEvidence': str(OUT / 'native-evidence'),
        'resourceFloorsUnchanged': True, 'repeatAllFunctionalGates': True,
        'reuseActualBuildThroughAuthoritativeBind': True, 'files': rows}, stream, indent=2)
print(json.dumps({'ok': True, 'freshNativeAttempt': 'r2', 'adapters': len(rows)}))
