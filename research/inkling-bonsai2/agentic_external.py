"""Preserve and reproduce the published 128K baseline at an immutable revision."""
import argparse
import hashlib
import json
from pathlib import Path

from filelock import FileLock
import requests

from source import atomic_bytes, check_resources, download, fetch_large_files


REPO = "drofn/Inkling-2-Mini-16GB-GGUF"
MODEL = "Inkling-2-Mini-16GB-128K.gguf"
DOCUMENTS = ("recipes/128K.tensor-types.txt", "recipes/README.md", "README.md",
             "measurements/fit_tests.csv", "measurements/kld_summary.csv")


def acquire(folder):
    folder.mkdir(parents=True, exist_ok=True)
    identity = folder / "upstream.json"
    if not identity.exists():
        response = requests.get(f"https://huggingface.co/api/models/{REPO}?blobs=true", timeout=30)
        response.raise_for_status()
        info = response.json()
        files = {r["rfilename"]: r for r in info["siblings"]}
        spec = dict(repository=REPO, revision=info["sha"], name=MODEL,
                    size=files[MODEL]["size"], sha256=files[MODEL]["lfs"]["sha256"])
        atomic_bytes(identity, json.dumps(spec, indent=2).encode())
    spec = json.loads(identity.read_bytes())
    if spec["repository"] != REPO or spec["name"] != MODEL:
        raise ValueError("Different external baseline")
    prefix = f"https://huggingface.co/{REPO}/resolve/{spec['revision']}"
    for name in DOCUMENTS:
        dest = folder / name
        if not dest.exists():
            dest.parent.mkdir(exist_ok=True)
            atomic_bytes(dest, download(prefix + "/" + name))
    partial = (folder / (MODEL + ".partial"))
    if not (folder / MODEL).exists():
        check_resources(folder, spec["size"] - (partial.stat().st_size if partial.exists() else 0))
    fetch_large_files(folder, prefix, {MODEL: spec}, 6)
    with (folder / MODEL).open("rb") as f:
        if hashlib.file_digest(f, "sha256").hexdigest() != spec["sha256"]:
            raise ValueError("External GGUF failed its published content digest")
    print("Verified independent published GGUF", spec["size"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    folder = parser.parse_args().folder
    folder.mkdir(parents=True, exist_ok=True)
    with FileLock(str(folder / "fetch.lock")):
        acquire(folder)
