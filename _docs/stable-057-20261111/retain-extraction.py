"""Retain the bounded, failed first extraction before a fresh attempt."""
import hashlib
import json
from pathlib import Path

OUT = Path('H:/Strata/releases/stable-057-20261111-codex').resolve(strict=True)
receipt = OUT / 'receipts/extract-self-test.json'
result = json.loads(receipt.read_text(encoding='utf-8-sig'))
assert not result['passed'] and result['run']['job_active_after'] == 0
assert result['run']['termination_confirmed'] and result['run']['exit_code'] == 1
assert 'timed out after 180.0 seconds' in (OUT / 'receipts/extract-self-test.txt').read_text(encoding='utf-8')
source = OUT / 'extracted'
target = OUT / 'extracted-r1-timeout'
assert source.is_dir() and not source.is_symlink() and not source.is_junction()
assert source.resolve().is_relative_to(OUT) and target.resolve().is_relative_to(OUT)
assert not target.exists() and target.parent.resolve() == OUT
source.rename(target)
record = {'ok': True, 'originalDirectory': str(source), 'retainedDirectory': str(target),
          'failedReceiptSHA256': hashlib.sha256(receipt.read_bytes()).hexdigest(),
          'ownedProcessesAfterFailure': 0, 'filesDeleted': 0,
          'note': 'Only an atomic directory rename within the checked release output; retry extracts fresh bytes.'}
with (OUT / 'retained-extraction-r1.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, indent=2)
print(json.dumps(record))
