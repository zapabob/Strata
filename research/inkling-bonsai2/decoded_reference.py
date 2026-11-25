"""Use selected deployed GGUF weights in the original Transformers calculation graph."""
import json
from pathlib import Path
import sys

import numpy as np
import torch

from infer import DTYPES, OfficialSafetensors
from spin8_clifford import sylvester


COMPONENTS=frozenset(("embedding","head","attention","gate","up","down"))
EXPERT=frozenset(("gate","up","down"))
CONDITIONS={
    "source":frozenset(), "full":COMPONENTS, "experts":EXPERT, "nonexperts":COMPONENTS-EXPERT,
    "gate-up":frozenset(("gate","up")), "experts-attention":EXPERT|{"attention"},
    "embedding-head":frozenset(("embedding","head")), **{k:frozenset((k,)) for k in COMPONENTS},
}


def components(mode):
    if mode.startswith("restore-"):
        return COMPONENTS-CONDITIONS[mode.removeprefix("restore-")]
    return CONDITIONS[mode]


def tensor_components(t):
    if t["name"]=="token_embd.weight": return {"embedding"}
    if t["name"]=="output.weight": return {"head"}
    if t["type"]=="Q4_K" and ".attn_" in t["name"]: return {"attention"}
    if t["type"]=="PQ2_0":
        if t["raw"].endswith(".w13_weight"): return {"gate","up"}
        if t["raw"].endswith(".w2_weight"): return {"down"}
    raise ValueError(f"Unclassified lossy tensor {t['name']}")


class DecodedOfficial(OfficialSafetensors):
    def __init__(self, root, gguf_path, manifest_path, llama, mode, restored=()):
        super().__init__(root)
        sys.path.insert(0,str(Path(llama)/"gguf-py"))
        import gguf
        meta=json.loads(manifest_path.read_bytes())
        if (meta["revision"]!=self.original.revision or meta["bytes"]!=gguf_path.stat().st_size or
                meta["integrity"]["code_counts"][3] or meta["profile"]!="balanced"):
            raise ValueError("A verified official conventional balanced GGUF is required")
        self.path=gguf_path
        self.gg=gguf
        self.enabled=components(mode)
        self.restored=set(restored)
        self.entries={t["raw"]:t for t in meta["tensors"] if t["type"] in ("Q4_K","Q6_K","PQ2_0")}
        if len(self.entries)!=194 or sum(t["type"]=="PQ2_0" for t in self.entries.values())!=48:
            raise ValueError("Unexpected lossy tensor set")
        if any(t["mse"]!=0. for t in meta["tensors"] if t["type"] in ("BF16","F32")):
            raise ValueError("A floating tensor changed in the baseline export")
        self.logical={key:tensor_components(t) for key,t in self.entries.items()}
        # Integer ternary sums with Walsh signs are exactly representable in FP32.
        self.h=torch.from_numpy(np.sign(sylvester(128)).astype(np.float32))
        self.matrices={}

    def read(self,key,device,start=0,count=None):
        t=self.entries.get(key)
        selected=self.enabled & self.logical.get(key,set())
        if not selected:
            return super().read(key,device,start,count)
        geom=self.physical[key]["origin"]
        if list(t["shape"])!=list(geom):
            raise ValueError(f"Unsupported tensor coordinate change at {key}")
        count=geom[0]-start if count is None else count
        if not 0<=start<start+count<=geom[0]:
            raise ValueError("Invalid tensor slice")
        row_bytes=t["bytes"]//geom[0]
        typ=DTYPES[self.physical[key]["dtype"]]
        if t["type"]=="PQ2_0":
            if count!=1: raise ValueError("Read one physical expert at a time")
            layer=int(key.split(".layers.")[1].split(".")[0])
            if (layer,start) in self.restored: return super().read(key,device,start,count)
        shape=(count,*geom[1:])
        partial=selected!=self.logical[key]
        out=super().read(key,device,start,count) if partial else torch.empty(shape,device=device,dtype=typ)
        with self.path.open("rb") as handle:
            handle.seek(t["offset"]+start*row_bytes)
            if t["type"]=="PQ2_0":
                width=geom[-1]
                rows=geom[1]
                # The fused GGUF stores gate rows followed by up rows; the source interleaves them.
                gate_up=key.endswith("w13_weight")
                transform=self.matrices.get(str(device))
                if transform is None:
                    transform=self.h.to(device)
                    self.matrices[str(device)]=transform
                if partial and (not gate_up or rows%2 or selected not in ({"up"},{"gate"})):
                    raise ValueError("Unsupported partial expert projection")
                begin=rows//2 if selected=={"up"} else 0
                end=rows//2 if selected=={"gate"} else rows
                handle.seek(t["offset"]+start*row_bytes+begin*(width//128)*34)
                chunk=1152
                for first in range(begin,end,chunk):
                    length=min(chunk,end-first)
                    data=np.fromfile(handle,dtype=np.uint8,count=length*width//128*34).reshape(-1,34)
                    if len(data)!=length*width//128: raise IOError("Truncated PQ2_0 rows")
                    packed=torch.from_numpy(data).to(device)
                    codes=packed[:,2:]
                    trits=torch.stack(tuple((codes>>shift)&3 for shift in (0,2,4,6)),dim=-1).reshape(-1,128)
                    scale=packed[:,:2].contiguous().view(torch.float16).float()
                    physical=((trits.float()-1) @ transform)*(scale*(128**-.5))
                    values=physical.reshape(length,width).to(typ)
                    if gate_up:
                        ids=torch.arange(first,first+length,device=device)
                        dest=(ids%(rows//2))*2+ids//(rows//2)
                        out[0].index_copy_(0,dest,values)
                    else:
                        out[0,first:first+length]=values
            else:
                if not(key in ("model.llm.embed.weight","model.llm.unembed.weight") or
                       (".attn." in key and key.endswith(".weight"))):
                    raise ValueError(f"Review the converter's coordinate mapping for {key}")
                chunk=max(1,4*1024**2//(geom[-1]*4))
                for first in range(0,count,chunk):
                    length=min(chunk,count-first)
                    data=np.fromfile(handle,dtype=np.uint8,count=length*row_bytes).reshape(length,row_bytes)
                    dense=self.gg.quants.dequantize(data,self.gg.GGMLQuantizationType[t["type"]])
                    if dense.shape!=(length,geom[-1]):
                        raise ValueError("Decoded dense projection has the wrong shape")
                    out[first:first+length]=torch.from_numpy(dense).to(device=device,dtype=typ)
        return out
