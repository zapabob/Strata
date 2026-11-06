"""Report only counts/hashes/sizes of inputs rejected by the small-state backup guard."""
import json
from pathlib import Path
from prepare_build import OUT, sha
roots=[Path('C:/Users/downl/.strata/data'),Path('C:/Users/downl/AppData/Roaming/Strata'),Path('C:/Users/downl/AppData/Local/Strata/install'),Path('C:/Users/downl/AppData/Local/Strata/launch'),Path('C:/Users/downl/AppData/Local/Strata/tuning'),Path('C:/Users/downl/AppData/Local/Strata/components/.updates')]
rows=[]
private=[]
for root in roots:
    for path in root.rglob('*'):
        if not path.is_file():continue
        size=path.stat().st_size
        if size >= 100*1024**2 or path.suffix.lower() in {'.gguf','.safetensors','.bin','.pack','.weights'}:
            row={'bytes':size,'sha256':sha(path),'large':size>=100*1024**2,'binSuffix':path.suffix.lower()=='.bin','ggufSuffix':path.suffix.lower()=='.gguf','otherWeightSuffix':path.suffix.lower() in {'.safetensors','.pack','.weights'},'modelDirectory':any(p.lower() in {'models','weights','cache','model-cache'} for p in path.parts),'logSuffix':path.suffix.lower()=='.log'}
            row.update(archiveSuffix=path.suffix.lower() in {'.zip','.tar','.gz','.7z','.exe'},databaseSuffix=path.suffix.lower() in {'.db','.sqlite','.sqlite3'},sourceRootIndex=roots.index(root))
            rows.append(row);private.append(dict(row,path=str(path)))
(Path('H:/Strata/private-backups/upgrade-052-local1-20261106-opencode')/'rejected-inputs-r2.json').write_text(json.dumps(private,indent=2))
(OUT/'backup-input-counts-r2.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'count':len(rows),'inputs':rows}))
