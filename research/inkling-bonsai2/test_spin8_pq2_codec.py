import ctypes
import os
from pathlib import Path
import numpy as np
import pytest
from spin8_quantizer import Basis, decode, fit, fit_for_activations, pack, unpack


def test_bit_order_and_corruption():
    symbols = np.tile([-1, 0, 1, 0], (3, 32))
    payload = pack(symbols, [1, .5, 2])
    assert (payload[:, 2:] == 0x64).all()
    assert payload[0, :2].tolist() == [0, 60]
    assert np.all(unpack(payload)[0] == symbols)
    payload[1, 6] = 255
    with pytest.raises(ValueError):
        unpack(payload)


def test_scale_fit_and_zero_group():
    rng = np.random.default_rng(76)
    w = rng.normal(size=(9, 256)).astype(np.float32)
    w[0] = 0
    a = rng.random(256)
    opt = decode(fit(w, a), w.shape)
    raw = decode(fit(w, method="absmax"), w.shape)
    assert np.sum(a * (w-opt)**2) <= np.sum(a * (w-raw)**2)
    assert not opt[0].any()
    assert not decode(fit(w, np.zeros(256)), w.shape).any()
    assert fit_for_activations(w, Basis("P"), [w, w*2, w*.1]).shape == (18, 34)


def test_independent_prism_decoder_and_packer():
    default = Path("C:/Users/downl/AppData/Local/Programs/llama-prism/0.4.1/bin/ggml-base.dll")
    path = Path(os.environ.get("PRISM_GGML_BASE", str(default)))
    if not path.is_file():
        pytest.skip("Set PRISM_GGML_BASE to the independent vendor library")
    folder = os.add_dll_directory(str(path.parent)) if os.name == "nt" else None
    lib = ctypes.CDLL(str(path))
    decoder = lib.dequantize_row_pq2_0
    encoder = lib.quantize_row_pq2_0_ref
    for f in (decoder, encoder):
        f.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int64]
        f.restype = None
    w = np.random.default_rng(99).normal(size=(10, 1152)).astype(np.float32)
    payload = fit(Basis("M").apply(w))
    recovered = np.empty_like(w)
    decoder(payload.ctypes.data, recovered.ctypes.data, w.size)
    np.testing.assert_array_equal(recovered, decode(payload, w.shape))
    independent = np.empty_like(payload)
    encoder(recovered.ctypes.data, independent.ctypes.data, w.size)
    np.testing.assert_array_equal(payload, independent)
    if folder:
        folder.close()
