"""Optional CUDA implementation for checked ternary fitting and PQ2_0 decoding."""

import ctypes
from pathlib import Path

import numpy as np


class CudaCodec:
    def __init__(self, path):
        self.lib = ctypes.CDLL(str(Path(path).resolve(strict=True)))
        ptr, cint = ctypes.c_void_p, ctypes.c_int
        self.fit = self.lib.hy4_pq_fit
        self.fit.argtypes = [ptr, ptr, cint, cint, cint, cint, ptr]
        self.fit.restype = cint
        self.unpack = self.lib.hy4_pq_decode
        self.unpack.argtypes = [ptr, ptr, cint, cint, cint, cint, cint, ptr, ptr]
        self.unpack.restype = cint

    def encode(self, data, original, direction, block):
        source = np.frombuffer(data, dtype="<u2").reshape(-1, original)
        physical = len(direction)
        output = np.empty((len(source), physical // 128 * 34), dtype=np.uint8)
        status = self.fit(
            source.ctypes.data,
            direction.ctypes.data,
            len(source),
            original,
            physical,
            block,
            output.ctypes.data,
        )
        if status:
            raise RuntimeError(f"CUDA ternary fit failed with status {status}")
        return output

    def decode(self, data, count, tensor, direction, device, dtype):
        import torch

        raw = torch.frombuffer(bytearray(data), dtype=torch.uint8).to(device)
        out = torch.empty(
            (count, tensor["original_width"]),
            device=device,
            dtype=dtype or torch.bfloat16,
        )
        if out.dtype not in (torch.float32, torch.bfloat16):
            raise ValueError(f"Unsupported inverse-basis output {out.dtype}")
        status = self.unpack(
            raw.data_ptr(),
            direction.data_ptr(),
            count,
            out.shape[1],
            tensor["shape"][-1],
            tensor["block"],
            int(out.dtype == torch.bfloat16),
            out.data_ptr(),
            torch.cuda.current_stream(device).cuda_stream,
        )
        if status:
            raise RuntimeError(
                f"CUDA inverse PQ2_0 transform failed with status {status}"
            )
        return out
