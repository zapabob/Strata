"""Preserve the first Control build and stage a fresh build after the MCP reap fix."""
import hashlib
import json
from pathlib import Path

OUT = Path('H:/Strata/releases/stable-058-20261111-codex')
source = OUT / 'adapters/app'
target = OUT / 'adapters/app-control-r2'
assert not target.exists()
target.mkdir()
rows = {}
for path in source.iterdir():
    if path.suffix not in ('.py', '.mjs'):
        continue
    original = path.read_bytes()
    text = original.decode('utf-8').replace('app-058-components', 'app-058-control-r2')
    text = text.replace('control-staging-058', 'control-staging-058-r2')
    if path.suffix == '.py':
        compile(text, str(target / path.name), 'exec')
    destination = target / path.name
    destination.write_text(text, encoding='utf-8', newline='\n')
    rows[path.name] = {'templateSHA256': hashlib.sha256(original).hexdigest(),
                       'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
with (OUT / 'control-retry-preparation-r2.json').open('x', encoding='utf-8') as stream:
    json.dump({'reason': 'Rebuild actual Control sources after owned MCP install-job reaping fix.',
               'priorBuildRetained': str(OUT / 'app-058-components/control-build.json'),
               'newBuild': str(OUT / 'app-058-control-r2/control-build.json'), 'files': rows}, stream, indent=2)
print(json.dumps({'ok': True, 'preparedControlAttempt': 'r2', 'files': len(rows)}))
