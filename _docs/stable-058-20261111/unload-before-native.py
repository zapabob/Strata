"""Normal app APIs only: stop observed 0.5.7 turns and unload for native validation."""
import argparse
import importlib.util
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--execute', action='store_true')
args = parser.parse_args()
if not args.execute:
    print(json.dumps({'execute': False, 'appVersion': '0.5.7', 'normalAppAPIsOnly': True, 'forceKills': False}))
else:
    spec = importlib.util.spec_from_file_location('normal_app_unload', Path(__file__).with_name('normal-unload.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main(expected_version='0.5.7', receipt_name='before-native-normal-unload-r1.json',
        authorization='User requested overwrite installation and approved normal stop/unload within this release workflow.')
