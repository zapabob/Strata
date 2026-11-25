"""Replay the real loop graph with canonical compressed expert weights and independently controllable routing."""
import ctypes as ct
import sys
import types
from collections import OrderedDict

import numpy as np
import torch

from spin8_cuda import Kernels
from spin8_quantizer import Basis


class PackedReplay:
    def __init__(self,model,llama,library,cache_gib):
        sys.path.insert(0,str(llama/"gguf-py"))
        import gguf
        self.reader=gguf.GGUFReader(model)
        self.tensors={t.name:t for t in self.reader.tensors}
        fields=self.reader.fields
        self.bases={};self.names={}
        if "spin8.version" in fields:
            reps=fields["spin8.representation"].contents();angles=fields["spin8.rotation_parameters"].contents()
            v=fields["spin8.version"].contents()
            if v not in (1,2):raise ValueError("Unknown Spin(8) contract")
            for i,rep in enumerate(reps):
                self.bases[i]=Basis(rep,theta=float(angles[i]) if v==1 else 0.,
                                    parameters=tuple(angles[i*28:i*28+28]) if v==2 else ())
            ids=fields["spin8.basis_id"].contents()
            for i,n in enumerate(fields["spin8.tensor_names"].contents()):self.names[n]=ids[i*128:i*128+128]
        elif fields["prism.hadamard.sign_mode"].contents()!="identity" or fields["prism.hadamard.block_size"].contents()!=128:
            raise ValueError("This replay expects the documented H128 control")
        self.cache=OrderedDict();self.size=0;self.cap=int(cache_gib*2**30)
        self.kernels=Kernels(library)
        self.fn=self.kernels.lib.spin8_weight_product
        self.fn.argtypes=[ct.c_void_p]*3+[ct.c_int]*3+[ct.c_void_p];self.fn.restype=ct.c_int

    def product(self,name,e,x):
        t=self.tensors[name];width,rows,experts=map(int,t.shape)
        if int(t.tensor_type)!=142 or experts!=128 or x.shape[-1]!=width:raise ValueError("Wrong routed geometry")
        key=(name,e)
        if key not in self.cache:
            bytes_per=t.n_bytes//128
            while self.cache and (self.size+bytes_per>self.cap or torch.cuda.mem_get_info()[0]<bytes_per+2**30):
                _,old=self.cache.popitem(last=False);self.size-=old.numel()
            p=torch.from_numpy(np.asarray(t.data).view(np.uint8).reshape(128,-1)[e].copy()).cuda()
            if bytes_per<=self.cap:self.cache[key]=p;self.size+=bytes_per
        else:
            p=self.cache[key];self.cache.move_to_end(key)
        b=self.bases[self.names[name][e]] if name in self.names else Basis("hadamard")
        rot=self.kernels.rotate(x.float(),b);out=torch.empty((len(x),rows),dtype=torch.float32,device=x.device)
        code=self.fn(p.data_ptr(),rot.data_ptr(),out.data_ptr(),rows,width,len(x),torch.cuda.current_stream().cuda_stream)
        if code:raise RuntimeError(f"Compressed projection failed with CUDA error {code}")
        return out.to(x.dtype)

    def install(self,model,observer):
        for idx,layer in enumerate(model.model.language_model.layers):
            def forward(module,x,ids,weights,layer=idx):
                ids,weights=observer.begin(layer,x,ids,weights)
                out=torch.zeros_like(x,dtype=torch.float32)
                for e in ids.unique().tolist():
                    tok,slot=torch.where(ids==e)
                    gu=self.product(f"blk.{layer}.ffn_gate_up_exps.weight",e,x[tok])
                    gate,up=gu.chunk(2,dim=-1)
                    mid=module.act_fn(gate,up);observer.down(layer,e,tok,slot,mid)
                    y=self.product(f"blk.{layer}.ffn_down_exps.weight",e,mid)
                    out.index_add_(0,tok,(y*weights[tok,slot,None]).float())
                return out.to(x.dtype)
            layer.mlp.experts.forward=types.MethodType(forward,layer.mlp.experts)
