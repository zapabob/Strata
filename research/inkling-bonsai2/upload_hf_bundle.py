"""Verify a prepared Inkling model directory, then optionally upload its listed files."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath


def verify(folder):
    root=folder.resolve(strict=True)
    entries={}
    for line in (root/'SHA256SUMS').read_text(encoding='utf8').splitlines():
        value,name=line.split('  ',1)
        relative=PurePosixPath(name)
        if (len(value)!=64 or any(c not in '0123456789abcdef' for c in value)
                or not name or '\\' in name or ':' in name or relative.is_absolute()
                or '..' in relative.parts or name in entries):
            raise ValueError('Invalid checksum entry')
        path=(root/relative).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError('File outside upload directory')
        with path.open('rb') as handle:
            if hashlib.file_digest(handle,'sha256').hexdigest()!=value:
                raise ValueError(f'Content differs from the prepared file: {name}')
        entries[name]=path
    if not {'README.md','LICENSE','provenance.json','.gitattributes'} <= entries.keys():
        raise ValueError('Incomplete Hugging Face model directory')
    if sum(name.endswith('.gguf') and '/' not in name and not name.startswith('mmproj-') for name in entries)!=1:
        raise ValueError('Expected one text GGUF per model repository')
    expected={'README.md','LICENSE','provenance.json','.gitattributes','benchmarks.json','runtime/build.ps1',
              'runtime/compile-strata.ps1','runtime/strata-native.patch','runtime/strata-revision.txt','runtime/LICENSE.Strata',
              'runtime/inkling-pq2.patch','runtime/upstream-revision.txt','runtime/LICENSE.llama.cpp',
              'mmproj-Inkling-2-Mini-F16.gguf'}
    text_file=next(name for name in entries if name.endswith('.gguf') and not name.startswith('mmproj-'))
    if set(entries)!=expected|{text_file}:
        raise ValueError('Unexpected files in the upload list')
    entries['SHA256SUMS']=root/'SHA256SUMS'
    return entries


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder',type=Path)
    p.add_argument('--upload-to',metavar='OWNER/REPOSITORY')
    p.add_argument('--public',action='store_true',help='Create a new repository with public visibility')
    a=p.parse_args()
    if a.public and not a.upload_to:
        p.error('--public applies to --upload-to')
    files=verify(a.folder)
    print(f'Verified {len(files)} upload files',flush=True)
    if not a.upload_to:
        return
    from huggingface_hub import CommitOperationAdd,HfApi
    from huggingface_hub.utils import validate_repo_id
    validate_repo_id(a.upload_to)
    if a.upload_to.count('/')!=1:
        p.error('An explicit owner and repository are required')
    api=HfApi()
    api.create_repo(a.upload_to,repo_type='model',private=not a.public,exist_ok=True)
    info=api.model_info(a.upload_to)
    commit=api.create_commit(repo_id=a.upload_to,repo_type='model',parent_commit=info.sha,
        operations=[CommitOperationAdd(path_in_repo=k,path_or_fileobj=v) for k,v in files.items()],
        commit_message='Add validated Inkling 2 Mini PQ2_0 GGUF and model card')
    published=api.model_info(a.upload_to,revision=commit.oid,files_metadata=True)
    index={f.rfilename:f for f in published.siblings}
    for name,path in files.items():
        if name not in index or index[name].size!=path.stat().st_size:
            raise RuntimeError(f'Hub did not confirm the uploaded size for {name}')
        if name.endswith('.gguf'):
            lfs=index[name].lfs
            if lfs is None or not lfs.sha256:
                raise RuntimeError(f'Hub did not return a content digest for {name}')
            expected=next(line.split('  ',1)[0] for line in (a.folder/'SHA256SUMS').read_text().splitlines()
                          if line.split('  ',1)[1]==name)
            if lfs.sha256!=expected:
                raise RuntimeError(f'Hub did not confirm the uploaded digest for {name}')
    print(commit.commit_url)


if __name__=='__main__':
    main()
