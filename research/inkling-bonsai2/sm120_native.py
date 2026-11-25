"""Run one native Windows benchmark and measure device-wide VRAM and process memory."""
import argparse
import contextlib
import ctypes as ct
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import time

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from native_model_resource_guard import PressurePolicy, available_memory, run_owned


class Nvml:
    class Memory(ct.Structure):
        _fields_=[(name,ct.c_uint64) for name in ("total","free","used")]

    def __init__(self):
        self.lib=ct.CDLL(str(Path(os.environ["SystemRoot"])/"System32/nvml.dll"))
        self.check(self.lib.nvmlInit_v2())
        self.device=ct.c_void_p()
        self.check(self.lib.nvmlDeviceGetHandleByIndex_v2(0,ct.byref(self.device)))
        name=ct.create_string_buffer(128)
        self.check(self.lib.nvmlDeviceGetName(self.device,name,len(name)))
        self.name=name.value.decode()

    @staticmethod
    def check(rc):
        if rc:
            raise RuntimeError(f"NVML returned {rc}")

    def memory(self):
        m=self.Memory()
        self.check(self.lib.nvmlDeviceGetMemoryInfo(self.device,ct.byref(m)))
        return dict(device_used_bytes=m.used,device_free_bytes=m.free,device_total_bytes=m.total)


class MemoryPolicy(PressurePolicy):
    def observe(self,sample,now):
        if sample["device_free_bytes"]<2**30:
            return "device_memory_pressure"
        if sample["destination_free_bytes"]<10*2**30 or sample["system_free_bytes"]<5*2**30:
            return "disk_space_pressure"
        return super().observe(sample,now)


def run(folder,cmd,min_free_mib,admission_timeout,timeout):
    folder.mkdir(parents=True,exist_ok=True)
    gpu=Nvml()
    pressure=MemoryPolicy(physical_floor_bytes=3*2**30,commit_floor_bytes=4*2**30,physical_grace_seconds=0)
    def telemetry():
        return dict(**available_memory(),**gpu.memory(),destination_free_bytes=shutil.disk_usage(folder).free,
                    system_free_bytes=shutil.disk_usage(Path(os.environ['SystemRoot']).anchor).free)
    start=time.monotonic()
    while True:
        sample=telemetry()
        if sample["device_free_bytes"]>=min_free_mib*2**20 and pressure.observe(sample,time.monotonic()) is None:
            break
        if time.monotonic()-start>=admission_timeout:
            raise TimeoutError(f"Available device memory is {sample['device_free_bytes']/2**20:.0f} MiB. Required {min_free_mib} MiB.")
        time.sleep(3)
    baseline=sample
    children=psutil.Process()
    peak_rss=0
    def measure():
        nonlocal peak_rss
        for p in children.children():
            try:peak_rss=max(peak_rss,p.memory_info().rss)
            except psutil.NoSuchProcess:pass
        return telemetry()
    trace=folder/"resources.jsonl"
    with (folder/"stdout.txt").open("x",encoding="utf8") as out,(folder/"stderr.log").open("x",encoding="utf8") as err:
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            result=run_owned(cmd,trace,folder/"process.json",timeout_seconds=timeout,sample=measure,policy=pressure)
    samples=[json.loads(s) for s in trace.read_text().splitlines()]
    summary=dict(gpu=gpu.name,started_utc=result["started_utc"],status=result["status"],reason=result["reason"],
         returncode=result["child_exit_code"],command=cmd,baseline_device_used_bytes=baseline["device_used_bytes"],
         peak_device_used_bytes=max([baseline["device_used_bytes"]]+[s["device_used_bytes"] for s in samples if "device_used_bytes" in s]),
         min_free_device_bytes=min([baseline["device_free_bytes"]]+[s["device_free_bytes"] for s in samples if "device_free_bytes" in s]),
         peak_process_working_set_bytes=peak_rss,samples=len(samples),sample_interval_seconds=1,
         finished_utc=datetime.now(timezone.utc).isoformat())
    (folder/"measurement.json").write_text(json.dumps(summary,indent=2))
    if summary["status"]!="exited" or summary["returncode"]:
        raise RuntimeError(f"Native run returned {summary['returncode']}, {summary['reason']}. See {folder}")
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--admit-mib",type=int,required=True)
    p.add_argument("--wait",type=int,default=1800)
    p.add_argument("--timeout",type=int,default=7200)
    p.add_argument("command",nargs=argparse.REMAINDER)
    args=p.parse_args()
    command=args.command[1:] if args.command and args.command[0]=="--" else args.command
    print(json.dumps(run(args.out,command,args.admit_mib,args.wait,args.timeout),indent=2))
