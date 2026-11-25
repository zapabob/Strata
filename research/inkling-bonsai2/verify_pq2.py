"""Audit GGUF extents, every tensor digest and the physical type 142 symbol stream."""
import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path
import numpy as np


def verify(path,llama,ledger=None):
    sys.path.insert(0,str(Path(llama)/"gguf-py"))
    import gguf
    from gguf_stream import directory
    fields,tensors=directory(path,gguf.GGML_QUANT_SIZES)
    arch=fields["general.architecture"]
    if arch not in ("inkling2_loop","inkling2-loop-spin8"):
        raise ValueError("Unrecognised Inkling text architecture")
    if (arch=="inkling2-loop-spin8") != ("spin8.version" in fields):
        raise ValueError("Spin(8) contract mismatch")
    if arch=="inkling2-loop-spin8" and "prism.hadamard.version" in fields:
        raise ValueError("Conflicting transform contracts")
    db=sqlite3.connect(Path(ledger).resolve().as_uri()+"?mode=ro",uri=True) if ledger else None
    lut=np.array([[sum(((v>>b)&3)==j for b in (0,2,4,6)) for j in range(4)] for v in range(256)],np.int64)
    totals=np.zeros(4,np.int64); banks=0; all_params=0; last=0
    with Path(path).open("rb") as f:
        for t in sorted(tensors,key=lambda entry: entry.data_offset):
            physical=int(t.data_offset)
            if physical<last or physical+t.n_bytes>Path(path).stat().st_size:raise ValueError("Overlapping or truncated tensor")
            last=physical+t.n_bytes
            all_params+=int(t.n_elements)
            if db:
                rows=db.execute("select n,hash from done where name=? order by part",(t.name,)).fetchall()
                if sum(x[0] for x in rows)!=t.n_bytes:raise ValueError("Incomplete journal for "+t.name)
                f.seek(physical)
                for n,digest in rows:
                    h=hashlib.sha256()
                    while n:
                        chunk=f.read(min(n,4*1024**2))
                        if not chunk:raise EOFError(t.name)
                        h.update(chunk);n-=len(chunk)
                    if h.hexdigest()!=digest:raise ValueError("Tensor digest mismatch "+t.name)
            expert=t.name.endswith((".ffn_gate_up_exps.weight",".ffn_down_exps.weight"))
            if expert:
                banks+=1
                if len(t.shape)!=3 or t.shape[2]!=128 or int(t.tensor_type)!=142:raise ValueError("Wrong routed tensor "+t.name)
            if int(t.tensor_type)!=142:continue
            if int(t.shape[0])%128 or t.n_bytes*128!=t.n_elements*34:raise ValueError("Wrong PQ2_0 extent")
            f.seek(physical);blocks=int(t.n_elements)//128
            while blocks:
                batch=min(blocks,65536);blocks-=batch
                data=np.frombuffer(f.read(batch*34),np.uint8).reshape(batch,34)
                scales=data[:,:2].copy().view("<f2")
                if not np.isfinite(scales).all() or np.any(scales<0):raise ValueError("Bad scale in "+t.name)
                totals+=np.bincount(data[:,2:].ravel(),minlength=256)@lut
    if db:db.close()
    if banks!=48 or totals[3]!=0 or not totals[:3].all():raise ValueError("Missing physical banks or invalid physical code usage")
    size=Path(path).stat().st_size
    return dict(architecture=arch,expert_banks=banks,physical_experts_per_layer=128,code_counts=totals.tolist(),
                tensors=len(tensors),parameters=all_params,file_bytes=size,whole_file_bpw=8*size/all_params,
                digests_verified=ledger is not None)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path);p.add_argument("--llama",type=Path,required=True);p.add_argument("--ledger",type=Path)
    args=p.parse_args()
    print(json.dumps(verify(args.model,args.llama,args.ledger),indent=2))
