"""Device-resident transform and ternary packing, with bounded per-expert workspaces."""

import ctypes as ct
import os
from pathlib import Path

import numpy as np
import torch

from spin8_quantizer import basis_matrix


class Kernels:
    def __init__(self, path):
        path=Path(path).resolve(strict=True)
        self.folder=os.add_dll_directory(str(path.parent)) if os.name=="nt" else None
        self.lib=ct.CDLL(str(path))
        ptr, integer, wide=ct.c_void_p, ct.c_int, ct.c_int64
        self.fn=self.lib.spin8_cuda_transform
        self.fn.argtypes=[ptr,ptr,ptr,wide,integer,ptr]
        self.fn.restype=integer
        self.fit=self.lib.spin8_fit_pq2
        self.fit.argtypes=[ptr,ptr,integer,integer,ptr,ptr]
        self.fit.restype=integer
        self.tables={}

    def table(self,b,device):
        key=(b,device)
        if key not in self.tables:
            self.tables[key]=torch.from_numpy(basis_matrix(b).astype(np.float32)).to(device)
        return self.tables[key]

    def original(self,parts,dtype=torch.bfloat16):
        weights,scale,amax,denom=parts
        nv=amax is not None
        n=weights.size*(2 if nv else 1)
        w=torch.from_numpy(np.array(weights,copy=True)).cuda()
        s=torch.from_numpy(np.array(scale,copy=True)).cuda()
        out=torch.empty((weights.shape[0],n//weights.shape[0]),device=w.device,dtype=dtype)
        if dtype not in (torch.float32,torch.bfloat16):raise ValueError("Unsupported reconstruction boundary")
        fn=self.lib.spin8_reconstruct_original
        fn.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_float,ct.c_int,ct.c_int,ct.c_int,ct.c_void_p,ct.c_void_p]
        fn.restype=ct.c_int
        status=fn(w.data_ptr(),s.data_ptr(),float(amax[0]/denom[0]) if nv else 1.,n,nv,dtype==torch.bfloat16,
                  out.data_ptr(),torch.cuda.current_stream().cuda_stream)
        if status:raise RuntimeError(f"Original reconstruction returned CUDA error {status}")
        return out

    def statistics(self,rotated,payload):
        stats=torch.empty((len(payload),5),device=rotated.device,dtype=torch.float64)
        fn=self.lib.spin8_pq2_statistics
        fn.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_int,ct.c_void_p,ct.c_void_p]
        fn.restype=ct.c_int
        status=fn(rotated.data_ptr(),payload.data_ptr(),len(payload),stats.data_ptr(),torch.cuda.current_stream().cuda_stream)
        if status:raise RuntimeError(f"Packed statistics returned CUDA error {status}")
        result=stats.sum(0).cpu().numpy()
        if result[-1]!=0 or not np.isfinite(result).all():raise ValueError("Invalid ternary reconstruction")
        return float(result[0]),result[1:].astype(np.int64).tolist()

    def rotate(self,x,b,reference=False):
        x=x.contiguous().float()
        if x.shape[-1]%b.block:
            raise ValueError("Transform dimension mismatch")
        r=self.table(b,x.device)
        if b.kind not in ("V","P","M","hadamard") or b.block!=128:
            return (x.reshape(-1,b.block) @ r.T).reshape(x.shape)
        y=torch.empty_like(x)
        status=self.fn(r.data_ptr(),x.data_ptr(),y.data_ptr(),x.numel()//128,reference,
                       torch.cuda.current_stream(x.device).cuda_stream)
        if status:
            raise RuntimeError(f"Spin(8) transform returned CUDA error {status}")
        return y

    def encode(self,x,b,importance=None,covariance=None):
        rot=self.rotate(x,b)
        rows,width=rot.reshape(-1,rot.shape[-1]).shape
        cov=None
        if covariance is not None:
            cov=torch.as_tensor(covariance,device=x.device,dtype=torch.float32).contiguous()
            if cov.shape!=(width//128,128,128) or not torch.isfinite(cov).all():
                raise ValueError("Invalid rotated input covariance")
            importance=cov.diagonal(dim1=-2,dim2=-1).clamp_min(0).flatten()
        h=None if importance is None else torch.as_tensor(importance,device=x.device,dtype=torch.float32).contiguous()
        if h is not None and (h.shape!=(width,) or not torch.isfinite(h).all() or (h<0).any()):
            raise ValueError("Invalid activation importance")
        if not torch.isfinite(rot).all():
            raise ValueError("Invalid rotated weights")
        out=torch.empty((rows*width//128,34),device=x.device,dtype=torch.uint8)
        status=self.fit(rot.data_ptr(),h.data_ptr() if h is not None else None,rows,width,out.data_ptr(),
                        torch.cuda.current_stream(x.device).cuda_stream)
        if status:
            raise RuntimeError(f"Ternary fitting returned CUDA error {status}")
        if cov is not None:
            refine=self.lib.spin8_refine_pq2
            refine.argtypes=self.fit.argtypes
            refine.restype=ct.c_int
            status=refine(rot.data_ptr(),cov.data_ptr(),rows,width,out.data_ptr(),torch.cuda.current_stream(x.device).cuda_stream)
            if status:raise RuntimeError(f"Correlated ternary fitting returned CUDA error {status}")
        return out,rot
