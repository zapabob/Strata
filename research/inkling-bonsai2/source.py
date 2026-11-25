"""Fetch the ablated Inkling safetensors, with bounded range reads and verified resume."""

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

REPO = "yanauto/Inkling-2-Mini-heretic-full"
CHUNK = 16 * 1024**2
LOCAL=threading.local()


def session():
    if not hasattr(LOCAL,"http"):LOCAL.http=requests.Session()
    return LOCAL.http


def atomic_bytes(path,data):
    path=Path(path)
    stage=path.with_suffix(path.suffix+".tmp")
    with stage.open("wb") as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    stage.replace(path)


def download(url):
    for attempt in range(5):
        try:
            with session().get(url,timeout=(15,90)) as response:
                response.raise_for_status();return response.content
        except requests.RequestException:
            if attempt==4:raise
            time.sleep(2**attempt)


def retry_range(http,url,offset,size):
    stop=offset+size-1
    for attempt in range(5):
        try:
            headers={"Range":f"bytes={offset}-{stop}","Accept-Encoding":"identity"}
            # Hub redirects are range-sensitive. A distinct query also distinguishes intermediary caches.
            with http.get(url,params={"range_start":offset,"range_end":stop},headers=headers,
                          stream=True,timeout=(15,100)) as response:
                response.raise_for_status()
                interval=re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)",response.headers.get("Content-Range",""))
                if response.status_code!=206 or not interval or tuple(map(int,interval.groups()[:2]))!=(offset,stop):
                    raise IOError("The source did not return the requested byte interval")
                data=response.raw.read(size+1)
                if len(data)!=size:raise IOError("Incorrect length for the source range")
                return data
        except (requests.RequestException,OSError):
            if attempt==4:raise
            time.sleep(2**attempt)


def check_resources(output,remaining):
    import psutil
    gib=2**30
    if psutil.virtual_memory().available<3*gib:raise RuntimeError("The physical RAM reserve was reached")
    if shutil.disk_usage(output).free<10*gib+remaining:raise RuntimeError("The destination disk reserve would be exceeded")
    if os.name=="nt":
        import ctypes
        from ctypes import wintypes
        class Memory(ctypes.Structure):
            _fields_=[("length",wintypes.DWORD),("load",wintypes.DWORD)]+[(name,ctypes.c_uint64) for name in
                     ("physical","free","commit","free_commit","virtual","free_virtual","unused")]
        m=Memory();m.length=ctypes.sizeof(m)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):raise OSError("Windows memory query failed")
        if m.free_commit<4*gib:raise RuntimeError("The Windows commit reserve was reached")
        if shutil.disk_usage(os.environ.get("SystemDrive","C:")+"/").free<5*gib:raise RuntimeError("The system disk reserve would be exceeded")


def await_capacity(root, size):
    reported = False
    started=time.monotonic()
    timeout=float(os.environ.get("INKLING_CAPACITY_TIMEOUT","0"))
    while True:
        try:
            check_resources(root, size)
            if reported:
                print("Resource reserve restored. Resuming source reads.", flush=True)
            return
        except RuntimeError as exc:
            if timeout>0 and time.monotonic()-started>=timeout:raise TimeoutError(str(exc)) from exc
            if not reported:
                print(f"Waiting before allocating the next range: {exc}", flush=True)
                reported = True
            time.sleep(12)


def capture(root, readers, repository=REPO):
    root.mkdir(parents=True, exist_ok=True)
    manifest = root / "source.json"
    if not manifest.exists():
        response = requests.get(
            f"https://huggingface.co/api/models/{repository}?blobs=true", timeout=30
        )
        response.raise_for_status()
        info = response.json()
        files = {
            s["rfilename"]: dict(size=s["size"], sha256=s.get("lfs", {}).get("sha256"))
            for s in info["siblings"]
            if s["rfilename"].endswith((".safetensors", ".json", ".jinja"))
        }
        atomic_bytes(
            manifest,
            json.dumps(
                dict(repository=repository, revision=info["sha"], files=files), indent=2
            ).encode(),
        )
    info = json.loads(manifest.read_bytes())
    if info["repository"] != repository:
        raise ValueError("Wrong source repository")
    prefix = f"https://huggingface.co/{repository}/resolve/{info['revision']}"
    files = info["files"]
    headers = {}
    for name, f in files.items():
        if Path(name).name != name:
            raise ValueError("Unexpected nested asset name")
        url = f"{prefix}/{name}"
        if name.endswith(".safetensors"):
            header_bytes = struct.unpack("<Q", retry_range(session(), url, 0, 8))[0]
            if not 0 < header_bytes < 8 * 1024**2:
                raise ValueError("Unexpected safetensors header extent")
            header = json.loads(retry_range(session(), url, 8, header_bytes))
            header.pop("__metadata__", None)
            if (
                max(t["data_offsets"][1] for t in header.values()) + 8 + header_bytes
                != f["size"]
            ):
                raise ValueError("Header and published extent differ")
            headers[name] = dict(base=8 + header_bytes, tensors=header)
        elif not (root / name).exists():
            b = download(url)
            if len(b) != f["size"]:
                raise ValueError(f"Invalid asset length for {name}")
            atomic_bytes(root / name, b)
    atomic_bytes(root / "headers.json", json.dumps(headers).encode())
    with ThreadPoolExecutor(max_workers=readers) as pool:
        for name in headers:
            f = files[name]
            url = f"{prefix}/{name}"
            path = root / name
            size = f["size"]
            if path.exists():
                if (
                    path.stat().st_size != size
                    or not (root / (name + ".verified.json")).is_file()
                ):
                    raise ValueError(f"Unverified pre-existing source file: {path}")
                continue
            part = path.with_suffix(".safetensors.partial")
            digest = hashlib.sha256()
            mark = part.with_suffix(".checkpoint.json")
            start = json.loads(mark.read_bytes())["bytes"] if mark.is_file() else 0
            with part.open("r+b" if part.exists() else "w+b") as out:
                if out.seek(0, 2) < start:
                    raise ValueError("Source shorter than its verified checkpoint")
                out.truncate(start)
                out.seek(0)
                while out.tell() < start:
                    digest.update(out.read(min(CHUNK, start - out.tell())))
                if (
                    mark.is_file()
                    and digest.hexdigest() != json.loads(mark.read_bytes())["digest"]
                ):
                    raise ValueError("Source checkpoint mismatch")
                tasks = deque()
                spans = iter(range(start, size, CHUNK))

                def fetch(at):
                    return retry_range(session(), url, at, min(size - at, CHUNK))

                def enqueue():
                    at = next(spans, None)
                    if at is not None:
                        tasks.append((at, pool.submit(fetch, at)))

                for _ in range(readers):
                    await_capacity(root, CHUNK)
                    enqueue()
                last = start
                while tasks:
                    at, fut = tasks.popleft()
                    data = fut.result()
                    enqueue()
                    if out.tell() != at:
                        raise ValueError("Non-contiguous download")
                    await_capacity(root, len(data))
                    if out.write(data) != len(data):
                        raise OSError("Short safetensors write")
                    digest.update(data)
                    pos = at + len(data)
                    if pos - last >= 256 * 1024**2 or pos == size:
                        out.flush()
                        os.fsync(out.fileno())
                        atomic_bytes(
                            mark,
                            json.dumps(
                                dict(bytes=pos, digest=digest.hexdigest())
                            ).encode(),
                        )
                        print(f"{name} {pos / 1e9:.2f}/{size / 1e9:.2f} GB", flush=True)
                        last = pos
            if not f["sha256"] or digest.hexdigest() != f["sha256"]:
                raise ValueError(f"Publisher integrity check failed for {name}")
            receipt = root / (name + ".verified.json")
            atomic_bytes(
                receipt,
                json.dumps(dict(bytes=size, matched_publisher_digest=True)).encode(),
            )
            # A streaming reader may still hold the verified source on Windows.
            for attempt in range(60):
                try:
                    part.rename(path)
                    break
                except PermissionError:
                    if attempt == 59:
                        raise
                    time.sleep(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--readers", type=int, default=8, choices=range(1, 17))
    p.add_argument("--repository", choices=(REPO, "thinkingmachines/Inkling-2-Mini"), default=REPO)
    args = p.parse_args()
    capture(args.output, args.readers, args.repository)
