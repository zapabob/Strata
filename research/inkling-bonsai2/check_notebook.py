"""Execute the distributed notebook with an ordinary Jupyter kernel and assert actual receipt states."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import nbformat
from nbclient import NotebookClient


def one(path,folder,hide_cuda):
    nb=nbformat.read(path,as_version=4)
    nbformat.validate(nb)
    # Run the independently usable receipt cell first, then a normal full run, then the workload a second time.
    ordered=list(nb.cells);nb.cells=[deepcopy(c) for c in (ordered[3],*ordered,ordered[1],ordered[3])]
    for i,c in enumerate(nb.cells):c["id"]=f"executed-{i}"
    env=dict(os.environ,INKLING_NOTEBOOK_WORKSPACE=str(folder/"work"),PYTHONUTF8="1")
    if hide_cuda:env["CUDA_VISIBLE_DEVICES"]="-1"
    from jupyter_client.kernelspec import KernelSpecManager
    kernels=folder/"kernels";d=kernels/"inkling";d.mkdir(parents=True)
    (d/"kernel.json").write_text(json.dumps(dict(argv=[sys.executable,"-m","ipykernel_launcher","-f","{connection_file}"],
                        display_name="Inkling",language="python")))
    client=NotebookClient(nb,kernel_name="inkling",timeout=240,allow_errors=False)
    from jupyter_client import AsyncKernelManager
    client.km=AsyncKernelManager(kernel_name="inkling",kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]))
    try:
        client.execute(cwd=str(folder),env=env)
    finally:
        if client.km is not None and client.km.has_kernel:client._cleanup_kernel()
    out=["".join(o.get("text","") for o in c.get("outputs",[]) if o.get("output_type")=="stream") for c in nb.cells]
    status=json.loads((folder/"work/results/run-status.json").read_bytes())
    expected="SKIPPED_NO_CUDA" if hide_cuda else "SKIPPED_DEVICE_MISMATCH"
    if status["status"]!=expected or status["portable_codec"]["status"]!="PASSED" or status["a100_measurements"]!=0:
        raise AssertionError(status)
    if "NOT_STARTED" not in out[0] or sum("Measurement status: "+expected in s for s in out)!=2:
        raise AssertionError("One of the independent/repeated cells did not complete")
    return dict(observed_hardware=status["device"],status=status["status"],portable_codec=status["portable_codec"],
                workload_executions=2,cold_standalone_receipt=True,uncaught_cell_errors=0)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("notebook",type=Path);p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();results={}
    with tempfile.TemporaryDirectory(dir=a.output.parent,prefix="notebook-test-") as tmp:
        for key,hide in (("physical_rtx",False),("cpu_visible",True)):
            results[key]=one(a.notebook,Path(tmp)/key,hide)
    a.output.write_text(json.dumps(results,indent=2))
