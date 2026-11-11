"""Bounded anonymous public range probe; retains diagnostics without signed URLs."""
import json
from pathlib import Path
import time
import urllib.request

name = 'Strata-0.5.6-local.1-windows-x64.tar.7z'
request = urllib.request.Request('https://github.com/zapabob/Strata/releases/download/v0.5.6-local.1/' + name + '?strata_readback=range-probe',
                                 headers={'User-Agent': 'Strata-release-readback/0.5.6', 'Range': 'bytes=0-1048575'})
started = time.monotonic()
with urllib.request.urlopen(request, timeout=30) as response:
    data = response.read(1024 * 1024)
    result = {'status': response.status, 'contentLength': response.headers.get('Content-Length'),
              'contentRange': response.headers.get('Content-Range'), 'bytes': len(data),
              'seconds': time.monotonic() - started}
with Path('H:/Strata/releases/search-056-20261111-codex/public-range-probe.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(result))
