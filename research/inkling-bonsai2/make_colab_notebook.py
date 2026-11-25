"""Build the portable notebook from the source files exercised by the local study."""
import argparse
import base64
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import subprocess
import zipfile


def build(args):
    args.output=args.output.resolve()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    src=Path(__file__).resolve().parent
    public=["source.py","official_weights.py","spin8_quantizer.py","spin8_triality.py","spin8_clifford.py",
            "spin8_continuous.py","spin8_cuda.py","spin8_encode.cu","check_original_cuda.py","check_spin8_cuda.py",
            "check_covariance_cuda.py","calibrate_inkling2.py","calibration_text.json","phase3_study.py",
            "benchmark_spin8_ablation.py","activation_optimisation.py","infer.py","gguf_stream.py",
            "quantize_inkling2_pq2.py","verify_pq2.py","benchmark_inkling2.py","packed_replay.py",
            "recurrent_sensitivity.py","phase3_policy.py","colab_workflow.py"]
    contents={n:(src/n).read_bytes() for n in public}
    for name in ("source.json","headers.json","hf_quant_config.json"):
        contents["checkpoint/"+name]=(args.source/name).read_bytes()
    def current(repo):
        return subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()
    versions=dict(checkpoint=json.loads(contents["checkpoint/source.json"])["revision"],transformers=current(args.transformers),
                  llama=current(args.llama),inference_dependencies=[f"{n}=={importlib.metadata.version(n)}" for n in
                       ("huggingface-hub","tokenizers","safetensors","regex","typer")])
    contents["versions.json"]=json.dumps(versions,indent=2).encode()
    contents["spin8_hadamard.cu"]=(args.llama/"ggml/src/ggml-cuda/spin8_hadamard.cu").read_bytes()
    native=subprocess.check_output(["git","-c","core.safecrlf=false","-C",str(args.llama),"diff","--no-ext-diff","--binary","HEAD","--","ggml","gguf-py","src","include","tools/llama-bench"])
    if b"diff --git a/src/spin8-basis.h" not in native:raise ValueError("The archive lacks the native Spin(8) basis source")
    contents["native.patch"]=native
    contents["bundle-index.json"]=json.dumps({k:hashlib.sha256(v).hexdigest() for k,v in sorted(contents.items())},indent=2).encode()
    memory=io.BytesIO()
    with zipfile.ZipFile(memory,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,body in sorted(contents.items()):
            zi=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(zi,body)
    archive=memory.getvalue();sig=hashlib.sha256(archive).hexdigest()
    payload=base64.b64encode(archive).decode()
    cells=[]
    def cell(kind,identifier,body,metadata=None):
        data=dict(cell_type=kind,id=identifier,metadata=metadata or {},source=body.strip().splitlines(keepends=True))
        if kind=="code":data.update(execution_count=None,outputs=[])
        cells.append(data)
    cell("markdown","overview","""# Inkling 2 Mini · A100 calibration and PQ2_0 quantisation

Run the next cell. It identifies the physical GPU, checks a known 34-byte ternary group and records the result. An A100 runs the selected workload. A CPU or another GPU produces a recorded skip before model download or compilation.

The default calibration uses the original publisher's NVFP4 and MXFP8 weights. It measures the CUDA codec and gathers four calibration and four held-out sequences. The GGUF mode also builds the patched llama.cpp runtime, converts the conventional Hadamard baseline and scores native logits. The embedded archive contains the research code, public checkpoint metadata and the native source patch. Model weights are fetched from the publisher on the eligible runtime.

Each recurrent visit retains its physical layer and expert identity. The status cell locates the JSON receipts. A fresh Colab VM has its own local storage. Save the receipts and the resulting GGUF before releasing a completed run.""")
    bootstrap=r'''#@title Run the selected workload
MODE = "calibrate" #@param ["inspect", "kernel", "calibrate", "gguf"]
import base64, hashlib, io, json, os, subprocess, sys, tempfile, uuid, zipfile
from pathlib import Path

default_root = Path("/content/inkling-pq2-work") if Path("/content").is_dir() else Path(tempfile.gettempdir()) / "inkling-pq2-work"
workspace = Path(os.environ.get("INKLING_NOTEBOOK_WORKSPACE", default_root))
workspace.mkdir(parents=True, exist_ok=True)
bundle = base64.b64decode(PAYLOAD, validate=True)
expected = FINGERPRINT
if hashlib.sha256(bundle).hexdigest() != expected:
    raise ValueError("The embedded research archive failed its integrity check.")
package = workspace / ("code-" + expected[:16])
package.mkdir(exist_ok=True)
with zipfile.ZipFile(io.BytesIO(bundle)) as z:
    entries = json.loads(z.read("bundle-index.json"))
    if set(z.namelist()) != set(entries) | {"bundle-index.json"}:
        raise ValueError("The archive contains an unexpected member.")
    for name in z.namelist():
        target = (package / name).resolve()
        if not target.is_relative_to(package.resolve()):
            raise ValueError("An archive path escaped its working directory.")
        data = z.read(name)
        if name in entries and hashlib.sha256(data).hexdigest() != entries[name]:
            raise ValueError("The embedded file did not match its manifest: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != data:
            target.write_bytes(data)
results = workspace / "results"
run_id = uuid.uuid4().hex
completed = subprocess.run([sys.executable, "-u", str(package / "colab_workflow.py"),
                            "--root", str(results), "--mode", MODE], check=False,
                           env=dict(os.environ, INKLING_NOTEBOOK_RUN_ID=run_id))
record = results / "run-status.json"
run_status = json.loads(record.read_text()) if record.exists() else {"status": "FAILED", "error": "No receipt was written."}
if run_status.get("run_id") != run_id:
    raise RuntimeError("The workload did not produce a fresh receipt.")
print("Measurement status:", run_status["status"])
print("Receipt:", record)
if run_status["status"].startswith("SKIPPED"):
    print("This allocation supplied", run_status["device"].get("device") or "a CPU", "and the A100 experiment was skipped.")
elif completed.returncode:
    print("The workload did not pass.", run_status.get("failed_stage", ""), run_status.get("error", run_status.get("reason", "")))'''
    cell("code","run-workload",bootstrap.replace("PAYLOAD",repr(payload)).replace("FINGERPRINT",repr(sig)),{"cellView":"form"})
    cell("markdown","receipt-note","""### Read the latest receipt

This cell also runs in a fresh kernel. If the workload has not started, it reports that state. A compilation, import, numerical or model failure retains its stage and diagnostic log.""")
    cell("code","show-receipt",r'''import json, os, tempfile
from pathlib import Path
base = Path("/content/inkling-pq2-work") if Path("/content").is_dir() else Path(tempfile.gettempdir()) / "inkling-pq2-work"
receipt = Path(os.environ.get("INKLING_NOTEBOOK_WORKSPACE", base)) / "results" / "run-status.json"
if receipt.is_file():
    report = json.loads(receipt.read_text())
    print(json.dumps({k: report[k] for k in ("status", "mode", "device", "portable_codec", "failed_stage", "error", "reason") if k in report}, indent=2))
else:
    print("NOT_STARTED — run the workload cell to create a measurement receipt.")''')
    cell("markdown","references","""### Reproducibility

Colab's available accelerators vary. The runtime identity check uses both the device name and compute capability. The compiler must list sm_80 before the notebook builds an A100 binary. A separate Python environment supplies the pinned source decoder while keeping the installed CUDA-enabled PyTorch. Calibration and evaluation files have independent token sequences. The kernel check measures the codec and transform. The GGUF mode scores the actual model.

[Google Colab resource availability](https://research.google.com/colaboratory/faq.html#gpu-availability) · [Colab runtime versions](https://research.google.com/colaboratory/runtime-version-faq.html) · [NVIDIA compute capabilities](https://developer.nvidia.com/cuda/gpus) · [NVIDIA compiler options](https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/index.html) · [PyTorch device capability](https://docs.pytorch.org/docs/2.14/generated/torch.cuda.get_device_capability.html) · [Original Inkling checkpoint](https://huggingface.co/thinkingmachines/Inkling-2-Mini) · [PrismML binary formats](https://github.com/PrismML-Eng/Bonsai-demo/blob/main/MODEL-FORMATS.md)""")
    notebook=dict(nbformat=4,nbformat_minor=5,metadata=dict(kernelspec={"display_name":"Python 3","language":"python","name":"python3"},
                  accelerator="GPU",colab={"name":"Inkling2_PQ2_Quantisation_A100.ipynb","gpuType":"A100","provenance":[]}),cells=cells)
    import nbformat
    nbformat.validate(nbformat.from_dict(notebook))
    args.output.write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding="utf8")
    print(f"{args.output} ({args.output.stat().st_size:,} bytes; {len(cells)} cells)")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("source","llama","transformers","output"):p.add_argument("--"+key,type=Path,required=True)
    build(p.parse_args())
