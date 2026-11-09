"""Preserve pre-main local files by same-volume moves; default is a read-only plan."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / '_docs/local-archive/2026-11-09-pre-main'
UNITS = (
    '_docs/2026-11-02_qwen36-engine-died-host-experts{Cursor}.md',
    '_docs/2026-11-04_q36-docs-pr2-32gb-ram{Cursor}.md',
    '_docs/2026-11-05_PR4989レビューパッケージ監査_Composer.md',
    '_docs/2026-11-05_PR4989通常push反映_Composer.md',
    '_docs/2026-11-05_gguf-loading-repair-release_Codex.md',
    '_docs/2026-11-05_gpt6-pro-native-assessment_Codex.md',
    '_docs/2026-11-05_gpt6-pro-native-consultation_Codex.md',
    '_docs/2026-11-05_gpt6-pro-native-response_Codex.md',
    '_docs/2026-11-05_native-blackwell-gdn_Codex.md',
    '_docs/2026-11-05_playwright-gguf-runtime-audit_Codex.md',
    '_docs/2026-11-07_Strata-handoff_OpenCode.md',
    '_docs/evidence', '_docs/intake', '_tmp_pr4989_review',
    'apps/desktop/src-tauri/resources/control-pre041-20261105',
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def no_links(path: Path) -> None:
    for part in (path, *path.parents):
        require(not part.is_symlink() and not part.is_junction(), 'Linked path refused')


def inventory(path: Path) -> dict[str, str]:
    no_links(path)
    files = [path] if path.is_file() else []
    if path.is_dir():
        for directory, dirs, names in os.walk(path, followlinks=False):
            for name in dirs + names:
                no_links(Path(directory) / name)
            files.extend(Path(directory) / name for name in names)
    result = {}
    for item in sorted(files):
        with item.open('rb') as stream:
            checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
        result[item.relative_to(path).as_posix() if item != path else '.'] = checksum
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    require(ROOT == Path('C:/Users/downl/Documents/ChatGPT/Strata'), 'Primary checkout required')
    require(not ARCHIVE.exists(), 'Prior archive must be retained; no overwrite')
    no_links(ARCHIVE)
    for name in UNITS:
        path = ROOT / name
        no_links(path)
        require(path.exists(), 'Expected local input absent: ' + name)
        tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', name], cwd=ROOT)
        require(not tracked, 'Tracked source cannot be moved: ' + name)
    if not args.execute:
        print(json.dumps({'execution': False, 'archive': str(ARCHIVE), 'units': UNITS,
                          'deletesFiles': False, 'overwritesFiles': False}, ensure_ascii=True))
        return
    records = [{'source': name, 'target': 'files/' + name, 'files': inventory(ROOT / name)}
               for name in UNITS]
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir()
    with (ARCHIVE / 'before.json').open('x', encoding='utf-8') as stream:
        json.dump(records, stream, indent=2)
    with (ARCHIVE / 'moves.jsonl').open('x', encoding='utf-8') as journal:
        for record in records:
            source, target = ROOT / record['source'], ARCHIVE / record['target']
            require(inventory(source) == record['files'], 'Source changed before move')
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not target.exists() and source.drive == target.drive, 'Fresh same-volume move required')
            source.rename(target)
            require(inventory(target) == record['files'], 'Moved content differs; inspect retained archive')
            journal.write(json.dumps({'source': record['source'], 'target': record['target'], 'verified': True}) + '\n')
            journal.flush()
            os.fsync(journal.fileno())
    count = sum(len(record['files']) for record in records)
    with (ARCHIVE / 'result.json').open('x', encoding='utf-8') as stream:
        json.dump({'ok': True, 'units': len(records), 'files': count,
                   'allHashesMatched': True, 'deletedFiles': 0}, stream, indent=2)
    print(json.dumps({'ok': True, 'archive': str(ARCHIVE), 'units': len(records), 'files': count,
                      'allHashesMatched': True, 'deletedFiles': 0}))


if __name__ == '__main__':
    main()
