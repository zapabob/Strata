from __future__ import annotations
from pathlib import Path
import numpy as np
from heretic_hybrid_upgrade import encode_nvfp4_dense_matrix, GgmlCodec
from quantize_inkling2_pq2 import upstream

def test_nvfp4_dense_roundtrip() -> None:
    rng = np.random.default_rng(7)
    w = (rng.standard_normal((128, 64)) * 0.05).astype(np.float32)
    packed = encode_nvfp4_dense_matrix(w)
    g, _ = upstream(Path(r"H:\Strata\worktrees\inkling-llama-reference-20261125"))
    dll = Path(r"H:\Strata\builds\inkling-upstream-pq2-cuda135\bin\ggml-base.dll")
    codec = GgmlCodec(dll, g)
    recon = codec.dequant_np(packed, "NVFP4", w.shape)
    assert recon.shape == w.shape
    mse = float(np.mean((recon - w) ** 2))
    assert mse < 1e-4, mse
