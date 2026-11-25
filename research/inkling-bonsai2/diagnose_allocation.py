"""Reproduce the initial Windows access-mask failure on an empty, private probe file."""
import argparse
import ctypes as ct
from ctypes import wintypes as win
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import psutil


def probe(root, header, llama):
    import msvcrt
    from gguf_stream import directory
    sys.path.insert(0, str(llama / "gguf-py"))
    import gguf
    volume = Path(root.anchor)
    k = ct.WinDLL("kernel32", use_last_error=True)
    ioctl = k.DeviceIoControl
    ioctl.argtypes = [win.HANDLE, win.DWORD, ct.c_void_p, win.DWORD, ct.c_void_p, win.DWORD,
                      ct.POINTER(win.DWORD), ct.c_void_p]
    ioctl.restype = win.BOOL
    def control(handle, opcode, arg=None):
        length = win.DWORD()
        ok = ioctl(msvcrt.get_osfhandle(handle.fileno()), opcode, ct.byref(arg) if arg else None,
                   ct.sizeof(arg) if arg else 0, None, 0, ct.byref(length), None)
        return 0 if ok else ct.get_last_error()
    name = ct.create_unicode_buffer(64)
    flags = win.DWORD()
    if not k.GetVolumeInformationW(str(volume), None, 0, None, None, ct.byref(flags), name, len(name)):
        raise ct.WinError(ct.get_last_error())
    fields, tensors = directory(header, gguf.GGML_QUANT_SIZES, header_only=True)
    end = max(t.data_offset+t.n_bytes for t in tensors)
    info = dict(time=time.strftime("%Y-%m-%dT%H:%M:%S%z"), volume=str(volume), filesystem=name.value,
                disk_free_bytes=shutil.disk_usage(root).free, temp_dir=tempfile.gettempdir(),
                temp_free_bytes=shutil.disk_usage(tempfile.gettempdir()).free,
                filesystem_sparse_support=bool(flags.value & 0x40), header_bytes=header.stat().st_size,
                tensor_count=len(tensors), highest_tensor_start=max(t.data_offset for t in tensors),
                planned_gguf_bytes=(end+31)//32*32, alignment=fields.get("general.alignment",32),
                data_buffers="one expert or at most 8 MiB of dense weights per write",
                original_failing_operation="FSCTL_SET_COMPRESSION(0), DeviceIoControl, 0x9C040")
    # A ctypes scalar holding zero is false in Python. The control call still needs its two bytes.
    uncompressed=(ct.c_uint16*1)(0)
    with tempfile.TemporaryDirectory(prefix="inkling-allocation-",dir=root) as folder:
        for label,mode in (("write_only","xb"),("read_write","x+b")):
            with (Path(folder)/label).open(mode) as f:
                error=control(f,0x9C040,uncompressed)
                info[label]={"set_compression_winerror":error}
                if mode=="x+b":
                    sparse=control(f,0x900C4)
                    info[label]["set_sparse_winerror"]=sparse
                    if sparse==0:
                        at=2**32+64
                        f.seek(at);f.write(b"PQ2");f.flush()
                        f.seek(at)
                        info[label]["verified_64bit_offset"]=at if f.read(3)==b"PQ2" else None
    class Mem(ct.Structure):
        _fields_=[("length",win.DWORD),("load",win.DWORD)]+[(s,ct.c_uint64) for s in
              ("total_phys","avail_phys","total_page","avail_page","total_virtual","avail_virtual","unused")]
    mem=Mem();mem.length=ct.sizeof(mem)
    if not k.GlobalMemoryStatusEx(ct.byref(mem)):raise ct.WinError(ct.get_last_error())
    info.update(available_ram=mem.avail_phys,available_commit=mem.avail_page,commit_limit=mem.total_page,
                process_available_virtual=mem.avail_virtual,process_private_bytes=psutil.Process().memory_info().private,
                process_open_handles=psutil.Process().num_handles())
    info["active_converters"]=[]
    for p in psutil.process_iter(["name","cmdline"]):
        if p.info["name"]=="python.exe" and any(a.endswith("quantize_inkling2_pq2.py") for a in p.info["cmdline"] or []):
            try:
                m=p.memory_info()
                info["active_converters"].append(dict(pid=p.pid,rss=m.rss,private_bytes=m.private,handles=p.num_handles()))
            except (psutil.AccessDenied,psutil.NoSuchProcess):
                continue
    return info


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("volume-path","header","llama","output"):p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(probe(a.volume_path.resolve(),a.header,a.llama),indent=2),encoding="utf8")
