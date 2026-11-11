"""Generate, review and apply actual configuration snapshots without loading models."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path('H:/Strata/releases/stable-058-20261111-codex')
sys.path.insert(0, str(ROOT))
os.environ['STRATA_SNAPSHOT_NODE'] = str(ROOT / 'apps/desktop/src-tauri/resources/node/node.exe')
from tests.snapshot.generate import main, GOLDEN

def changes(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(a.keys() | b.keys()):
            yield from changes(a.get(key), b.get(key), path + '/' + key)
    elif a != b:
        yield {'path': path, 'before': a, 'after': b}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('action', choices=('generate', 'apply'))
parser.add_argument('--attempt', choices=('r1', 'r2'), default='r1')
parser.add_argument('--set', action='append')
args = parser.parse_args()
suffix = '' if args.attempt == 'r1' else '-' + args.attempt
candidate = OUT / ('snapshot-candidate' + suffix)
review = OUT / ('snapshot-review' + suffix + '.json')
if args.action == 'generate':
    assert not candidate.exists()
    if args.attempt == 'r2':
        assert args.set == ['deepseek']
        shutil.copytree(OUT / 'snapshot-candidate', candidate)
    assert main(['--out', str(candidate), *[arg for value in (args.set or []) for arg in ('--set', value)]]) == 0
    rows = []
    for path in sorted(candidate.glob('*/*.json')):
        old = GOLDEN / path.relative_to(candidate)
        before = old.read_bytes()
        generated = json.loads(path.read_bytes())
        assert all('failed' not in value for value in generated['entries'].values()), 'A failed entry is not a golden snapshot'
        delta = list(changes(json.loads(before), generated))
        if delta:
            rows.append({'file': old.relative_to(ROOT).as_posix(), 'oldSHA256': hashlib.sha256(before).hexdigest(),
                         'newSHA256': hashlib.sha256(path.read_bytes()).hexdigest(), 'changes': delta})
    with review.open('x', encoding='utf-8') as stream:
        json.dump(rows, stream, indent=2)
    print(json.dumps({'changedFiles': len(rows), 'changes': sum(len(row['changes']) for row in rows)}))
else:
    rows = json.loads(review.read_text())
    for row in rows:
        old = ROOT / row['file']
        fresh = candidate / old.relative_to(GOLDEN)
        assert hashlib.sha256(old.read_bytes()).hexdigest() == row['oldSHA256']
        assert hashlib.sha256(fresh.read_bytes()).hexdigest() == row['newSHA256']
        shutil.copyfile(fresh, old)
    print(json.dumps({'appliedReviewedFiles': len(rows)}))
