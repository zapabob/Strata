"""Require the original complete native audit before publishing the already-installed exact payload."""
import json
from pathlib import Path
import sys

OUT = Path('H:/Strata/releases/stable-059-20261113-codex')
sys.path.insert(0, str(OUT / 'adapters/component-r2'))
from core import RESOURCES, NAME, MANIFEST, digest, inventory, load, require, sha
from quality import validate

quality = validate()
staged = load(OUT / 'app-059-components/staged-native.json')
tree = inventory(RESOURCES / 'engine-bundle' / NAME)
require(staged['ok'] and digest(tree) == staged['payloadInventorySHA256']
        and tree[MANIFEST] == staged['signedManifestSHA256']
        and tree['strata.exe'] == staged['engineSHA256'], 'Exact preinstall native payload changed')
record = {'ok': True, 'nativeSourceCommit': staged['nativeSourceCommit'],
          'engineSHA256': staged['engineSHA256'], 'signedManifestSHA256': staged['signedManifestSHA256'],
          'quality': quality, 'samePayloadAsLocalInstallation': True, 'releaseQualified': False}
with (OUT / 'native-final-verified.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, indent=2)
print(json.dumps({'ok': True, 'completeNativeAudit': True, 'payloadUnchanged': True}))
