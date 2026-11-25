"""Compare CUDA reconstruction at both working precisions to the checkpoint and Transformers."""
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from official_weights import Original, reconstruct, reference_bf16
from spin8_cuda import Kernels
from spin8_quantizer import Basis, decode, unpack


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for key in ("source","kernels","output"):p.add_argument("--"+key,type=Path,required=True)
    a=p.parse_args();original=Original(a.source);kernels=Kernels(a.kernels);results=[]
    for layer,expert in ((6,7),(20,101)):
        for proj in ("w13","w2"):
            name=f"model.llm.layers.{layer}.mlp.experts.{proj}_weight"
            parts=original.parts(name,expert,0,32);full=reconstruct(parts)
            actual=kernels.original(parts,torch.float32);b16=kernels.original(parts)
            f32_diff=int(np.count_nonzero(actual.cpu().numpy().view(np.uint32)!=full.view(np.uint32)))
            bf16_diff=int(torch.count_nonzero(b16.cpu().view(torch.int16)!=reference_bf16(parts).view(torch.int16)))
            if f32_diff or bf16_diff:raise ArithmeticError((name,f32_diff,bf16_diff))
            row=dict(layer=layer,expert=expert,projection=proj,values=full.size,fp32_differing_bits_patterns=f32_diff,
                     reference_bf16_differing_bit_patterns=bf16_diff)
            if hasattr(kernels.lib,"spin8_pq2_statistics"):
                payload,rot=kernels.encode(actual,Basis("V"))
                err,counts=kernels.statistics(rot,payload)
                pbytes=payload.cpu().numpy()
                symbols,_=unpack(pbytes);ref=np.bincount(symbols.ravel()+1,minlength=4)
                yy=rot.cpu().numpy().astype(float)-decode(pbytes,full.shape)
                expected=float(np.sum(yy**2))
                if not np.array_equal(ref,counts) or not np.isclose(err,expected,rtol=1e-12):
                    raise ArithmeticError("GPU statistics disagree with independent decoded bytes")
                row["decoded_statistics_error"]=abs(err-expected)
            results.append(row)
    a.output.write_text(json.dumps(dict(device=torch.cuda.get_device_name(),results=results),indent=2))
