"""Prepare explicit local-install composition; leave strict final native validation unchanged."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-058-20261111-codex')
source, target = OUT / 'adapters/component-r2', OUT / 'adapters/component-preinstall-r2'
assert not target.exists()
target.mkdir()
rows = {}
for path in source.iterdir():
    if path.suffix not in ('.py', '.mjs'):
        continue
    original = path.read_bytes()
    text = original.decode('utf-8').replace('component-058-r2', 'component-058-preinstall-r2')
    text = text.replace('component-staging-058-r2', 'component-staging-058-preinstall-r2')
    if path.name == 'compose.py':
        old = '''    require(BASE.is_dir() and RESOURCES.is_dir() and not (BASE / "active.json").exists(),
            "Parent must finish native Jobs first")'''
        new = '''    require(BASE.is_dir() and RESOURCES.is_dir(), "Native evidence/resources required")
    if (BASE / "active.json").exists():
        require(load(BASE / "active.json")["phase"] in ("model-bounded", "model-legacy7", "model-restart", "compare", "audit"),
                "Only read-only model qualification may overlap local composition; build and stage must finish first")'''
        assert old in text
        text = text.replace(old, new)
    if path.name == 'quality.py':
        text = Path(__file__).with_name('preinstall-quality.py').read_text(encoding='utf-8')
    if path.suffix == '.py':
        compile(text, str(target / path.name), 'exec')
    destination = target / path.name
    destination.write_text(text, encoding='utf-8', newline='\n')
    rows[path.name] = {'templateSHA256': hashlib.sha256(original).hexdigest(),
                       'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
with (OUT / 'preinstall-component-preparation-r2.json').open('x', encoding='utf-8') as stream:
    json.dump({'reason': 'User requested local overwrite installation before remaining model audit and cloud CI.',
               'finalPublicationGateUnchanged': True, 'files': rows}, stream, indent=2)
print(json.dumps({'ok': True, 'preparedLocalInstallComponent': True}))
