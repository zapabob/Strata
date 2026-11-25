"""Run the self-contained Colab notebook on the accelerator actually allocated by the provider."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def classify(name, capability):
    if name is None:
        return "SKIPPED_NO_CUDA"
    if "A100" not in name or tuple(capability) != (8, 0):
        return "SKIPPED_DEVICE_MISMATCH"
    return "READY_A100"


def device_info():
    try:
        import torch
        if not torch.cuda.is_available():
            return {"state": classify(None, ()), "torch": str(torch.__version__), "device": None}
        name = torch.cuda.get_device_name(0)
        cap = torch.cuda.get_device_capability(0)
        return dict(state=classify(name, cap), device=name, compute_capability=list(cap),
                    vram_bytes=torch.cuda.get_device_properties(0).total_memory,
                    torch=str(torch.__version__), torch_cuda=torch.version.cuda)
    except (ImportError, OSError, RuntimeError) as exc:
        return dict(state="BLOCKED_TORCH_RUNTIME", reason=str(exc))


def save(path, obj):
    temp=path.with_suffix(".tmp")
    temp.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding="utf8")
    temp.replace(path)


def codec_smoke():
    from spin8_quantizer import pack,unpack
    import numpy as np
    inputs=np.tile([-1,0,1,0],(1,32))
    data=pack(inputs,[1.])
    symbols,scale=unpack(data)
    valid=(data.shape==(1,34) and data[0,:2].tolist()==[0,60] and np.all(data[0,2:]==0x64)
           and np.array_equal(symbols,inputs) and float(scale[0])==1.)
    if not valid:raise ArithmeticError("Ternary byte ordering check failed")
    return dict(status="PASSED",group_weights=128,group_bytes=34,symbols=[-1,0,1])


def run(root,mode):
    package=Path(__file__).resolve().parent
    root.mkdir(parents=True,exist_ok=True)
    status_file=root/"run-status.json"
    info=dict(device=device_info(),mode=mode,stages={},run_id=os.environ.get("INKLING_NOTEBOOK_RUN_ID"),
              started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()))
    stage="portable codec"
    try:
        info["portable_codec"]=codec_smoke()
        if info["device"]["state"]!="READY_A100" or mode=="inspect":
            info["status"]=info["device"]["state"] if mode!="inspect" else "PROBE_COMPLETE"
            info["a100_measurements"]=0
            save(status_file,info)
            return info
        stage="resource preflight"
        import psutil
        nvcc=shutil.which("nvcc")
        root_free=shutil.disk_usage(root).free
        ram=psutil.virtual_memory().available
        info["preflight"]=dict(destination_free_bytes=root_free,available_ram=ram,nvcc=nvcc)
        if not nvcc or not shutil.which("git") or not shutil.which("cmake"):
            info.update(status="BLOCKED_TOOLCHAIN",reason="The runtime needs nvcc, Git and CMake.")
            save(status_file,info);return info
        caps=subprocess.check_output([nvcc,"--list-gpu-code"],text=True).split()
        if "sm_80" not in caps:
            info.update(status="BLOCKED_COMPILER_TARGET",reason="This nvcc does not list sm_80.")
            save(status_file,info);return info
        minimum_disk=9*2**30 if mode=="kernel" else 45*2**30
        if root_free<minimum_disk or ram<4*2**30:
            info.update(status="BLOCKED_CAPACITY",required_disk_bytes=minimum_disk,required_available_ram_bytes=4*2**30)
            save(status_file,info);return info
        locked=json.loads((package/"versions.json").read_text())
        env=os.environ.copy()
        env.update(PYTHONUTF8="1",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="2",INKLING_CAPACITY_TIMEOUT="180",
                   HF_HUB_DISABLE_PROGRESS_BARS="1",HF_HUB_DISABLE_TELEMETRY="1")
        config_id=hashlib.sha256((package/"bundle-index.json").read_bytes()).hexdigest()
        steps=root/("steps-"+config_id[:16]);steps.mkdir(exist_ok=True)
        def step(name,cmd,output,timeout=5400,cwd=None):
            nonlocal stage
            stage=name;out=[Path(v) for v in output]
            marker=steps/(name+".json");log=steps/(name+".log")
            if marker.is_file() and out and all(v.is_file() and v.stat().st_size>0 for v in out):
                saved=json.loads(marker.read_text())
                if saved["sizes"]==[v.stat().st_size for v in out]:
                    info["stages"][name]=dict(status="REUSED",log=str(log));return
            print(f"Running {name}",flush=True)
            start=time.monotonic()
            with log.open("w",encoding="utf8") as stream:
                result=subprocess.run(list(map(str,cmd)),cwd=cwd,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
            if result.returncode:
                with log.open("rb") as stream:
                    stream.seek(max(0,log.stat().st_size-3500))
                    tail=stream.read().decode("utf8",errors="replace")
                raise RuntimeError(f"{name} returned {result.returncode}. {tail}")
            if not all(v.is_file() and v.stat().st_size>0 for v in out):raise IOError(f"Missing output for {name}")
            receipt=dict(status="PASSED",seconds=time.monotonic()-start,sizes=[v.stat().st_size for v in out],log=str(log))
            save(marker,receipt);info["stages"][name]=receipt;save(status_file,info)
        # A separate interpreter keeps Colab's live torch and notebook imports intact.
        venv=root/"runtime-env";python=venv/"bin/python"
        if not python.is_file():
            step("create-environment",[sys.executable,"-m","venv","--system-site-packages",venv],[python],180)
        hf_url="https://codeload.github.com/huggingface/transformers/zip/"+locked["transformers"]
        hf_site=root/("hf-libraries-"+locked["transformers"][:12])
        step("transformers",[python,"-m","pip","install","--disable-pip-version-check","--target",hf_site,
                "--no-deps",hf_url],[hf_site/"transformers/models/inkling2_loop/modeling_inkling2_loop.py"],900)
        dep_site=root/("dependencies-"+locked["transformers"][:12])
        requirements=locked["inference_dependencies"]
        # --target is used with --no-deps for Transformers itself to preserve the host PyTorch/CUDA pairing.
        step("runtime-dependencies",[python,"-m","pip","install","--disable-pip-version-check","--target",dep_site,
             *requirements],[dep_site/"huggingface_hub/__init__.py",dep_site/"tokenizers/__init__.py"],1200)
        env["PYTHONPATH"]=os.pathsep.join([str(hf_site),str(dep_site),str(package)])
        step("check-imports",[python,"-c","from infer import OfficialSafetensors,load_graph; from transformers.core_model_loading import Inkling2LoopDequantizeExperts"],[],180)
        source=root/"official";source.mkdir(exist_ok=True)
        for asset in ("source.json","headers.json","hf_quant_config.json"):
            src=package/"checkpoint"/asset;dest=source/asset
            if not dest.exists():shutil.copyfile(src,dest)
        if json.loads((source/"source.json").read_bytes())["revision"]!=locked["checkpoint"]:
            raise ValueError("The on-disk model revision differs from this notebook")
        compiler=Path(nvcc).resolve()
        includes=[compiler.parent.parent/"include",Path("/usr/local/cuda/include")]
        flags=[]
        for inc in includes:
            for choice in (inc/"cccl/cccl",inc/"cccl",inc):
                if (choice/"cub/block/block_scan.cuh").is_file():
                    flags.append("-I"+str(choice));break
        library=root/"spin8-pq2.so"
        step("compile-sm80",[nvcc,"-std=c++17","-O3","-shared","-Xcompiler","-fPIC",
             "-gencode=arch=compute_80,code=sm_80",*flags,package/"spin8_hadamard.cu",package/"spin8_encode.cu","-o",library],[library],600)
        env["INKLING_SOURCE_CUDA"]=str(library);env["INKLING_SOURCE_CACHE_GIB"]="1.25"
        step("official-codec-parity",[python,package/"check_original_cuda.py","--source",source,"--kernels",library,
             "--output",root/"source-parity.json"],[root/"source-parity.json"],600)
        step("rotation-benchmark",[python,package/"check_spin8_cuda.py","--source",source,"--library",library,
             "--output",root/"sm80-rotation.json"],[root/"sm80-rotation.json"],600)
        if mode!="kernel":
            step("fetch-source",[python,package/"source.py","--repository","thinkingmachines/Inkling-2-Mini","--output",source,"--readers","6"],
                 [source/"model-00001-of-00001.safetensors",source/"model-00001-of-00001.safetensors.verified.json"],7200)
            if mode=="gguf":
                llama=root/("llama-"+locked["llama"][:12])
                if not (llama/".git").exists():
                    llama.mkdir(exist_ok=True)
                    step("git-init",["git","init",llama],[llama/".git/HEAD"])
                    step("git-upstream",["git","-C",llama,"remote","add","origin","https://github.com/ggml-org/llama.cpp.git"],[])
                if not (llama/"src/spin8-basis.h").is_file():
                    step("fetch-llama",["git","-C",llama,"fetch","--depth","1","origin",locked["llama"]],[llama/".git/FETCH_HEAD"],900)
                    step("checkout-llama",["git","-C",llama,"checkout","--detach","FETCH_HEAD"],[llama/"CMakeLists.txt"])
                    step("patch-llama",["git","-C",llama,"apply","--whitespace=nowarn",package/"native.patch"],[llama/"src/spin8-basis.h"])
                build=root/"native-build"
                step("configure",["cmake","-S",llama,"-B",build,"-DCMAKE_BUILD_TYPE=Release","-DGGML_CUDA=ON","-DGGML_NATIVE=OFF",
                     "-DCMAKE_CUDA_ARCHITECTURES=80-real","-DGGML_CUDA_FA=OFF","-DBUILD_SHARED_LIBS=ON","-DLLAMA_OPENSSL=OFF"],[build/"CMakeCache.txt"],600)
                step("build",["cmake","--build",build,"--parallel","4","--target","llama-completion","llama-bench","inkling-logits","llama-mtmd-cli"],
                     [build/"bin/llama-completion",build/"bin/inkling-logits",build/"bin/libggml-base.so"],10800)
                env["LD_LIBRARY_PATH"]=os.pathsep.join([str(build/"bin"),env.get("LD_LIBRARY_PATH","")])
                model=root/"Inkling-2-Mini-PQ2_0-Baseline.gguf"
                step("quantise",[python,package/"quantize_inkling2_pq2.py","--profile","balanced","--llama",llama,"--source",source,
                     "--output",model,"--ggml-base",build/"bin/libggml-base.so","--kernels",library],[model,model.with_suffix(".manifest.json")],18000)
            traces=root/"official-dynamic"
            step("actual-calibration",[python,package/"calibrate_inkling2.py","--original","--source",source,"--output",traces,
                 "--cache-gib","4"],[traces/"splits.json",traces/"holdout-3.npz"],14400)
            step("actual-covariance",[python,package/"check_covariance_cuda.py","--source",source,"--capture",traces/"calibration-0.npz",
                 "--library",library,"--output",root/"sm80-covariance.json"],[root/"sm80-covariance.json"])
            if mode=="gguf":
                step("heldout-native",[python,package/"benchmark_inkling2.py","native","--reference",traces,"--model",model,
                     "--bin",build/"bin","--output",root/"sm80-logits.json"],[root/"sm80-logits.json"],3600)
        info["status"]="PASSED";info["a100_measurements"]=2 if mode=="kernel" else 3
    except Exception as exc:
        info.update(status="FAILED",failed_stage=stage,error_type=type(exc).__name__,error=str(exc))
    save(status_file,info)
    return info


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True);p.add_argument("--mode",choices=("inspect","kernel","calibrate","gguf"),default="calibrate")
    args=p.parse_args();receipt=run(args.root,args.mode)
    print(json.dumps(receipt,indent=2,ensure_ascii=False),flush=True)
    sys.exit(1 if receipt["status"]=="FAILED" or receipt["status"].startswith("BLOCKED") else 0)
