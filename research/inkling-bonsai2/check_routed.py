"""Verify native routed matrix products against an independently decoded Inkling expert bank."""

import argparse
import json
import sys
from pathlib import Path

import torch
from torch.nn import functional as F

from convert import ARCH, ASSETS, PREFIX
from routed import TernaryExperts
from source import await_capacity
from weight_store import Packed


def run(args):
    sys.path.insert(0, str(args.gguf_python.resolve(strict=True)))
    import gguf

    # Opening a partial here is restricted to a whole bank previously committed by the quantiser.
    import sqlite3

    dbpath = args.gguf.parent / "progress.sqlite"
    with sqlite3.connect(dbpath.as_uri() + "?mode=ro", uri=True) as db:
        keys = {x[0] for x in db.execute("select name from tensors")}
    if not args.gguf.name.endswith(".partial"):
        raise ValueError("This component check is for the in-progress GGUF")
    await_capacity(args.output.parent, 0)
    store = Packed(
        args.gguf,
        gguf,
        args.prism_bin,
        args.assets,
        partial=True,
        cuda_codec=args.cuda_codec,
        architecture=ARCH,
        prefix=PREFIX,
        asset_names=ASSETS,
    )
    banknames = [
        f"model.llm.layers.0.mlp.experts.{p}" for p in ("w13_weight", "w2_weight")
    ]
    if not all(store.physical[k]["name"] in keys for k in banknames):
        raise ValueError("The whole layer-zero expert bank has not yet been written")
    # Check the actual tensor contents against its committed digest before exercising it.
    import hashlib

    with (
        sqlite3.connect(dbpath.as_uri() + "?mode=ro", uri=True) as db,
        args.gguf.open("rb") as f,
    ):
        for k in banknames:
            t = store.physical[k]
            f.seek(t["offset"])
            digest = hashlib.blake2b(digest_size=20)
            left = t["bytes"]
            while left:
                data = f.read(min(8 * 1024**2, left))
                if not data:
                    raise ValueError("Truncated bank")
                digest.update(data)
                left -= len(data)
            if (
                digest.hexdigest()
                != db.execute(
                    "select digest from tensors where name=?", (t["name"],)
                ).fetchone()[0]
            ):
                raise ValueError("Bank failed the read-back check")
    store.partial = False
    op = TernaryExperts(store, 0.5, "cuda")
    generator = torch.Generator(device="cuda").manual_seed(412)
    ids = torch.tensor([[3, 25], [69, 3]], dtype=torch.int64, device="cuda")
    metrics = []
    for k in banknames:
        t = store.physical[k]
        _, rows, width = t["origin"]
        x = torch.randn((2, width), generator=generator, device="cuda").bfloat16()
        y = op.product(k, x, ids, 2).float()
        references = []
        for sample, e in enumerate(ids.flatten().tolist()):
            item = store.raw(k, rows * e, rows)
            # Use the vendor CPU decoder and the explicit inverse transform as the independent control.
            fast = store.fused
            store.fused = None
            try:
                w = store.decode(item, "cuda", torch.float32)
            finally:
                store.fused = fast
            references.append(F.linear(x[sample // 2].float(), w))
        ref = torch.stack(references)
        rel = ((y - ref).norm() / ref.norm()).item()
        metrics.append(
            dict(
                bank=k,
                input_shape=list(x.shape),
                routing=ids.tolist(),
                relative_l2=rel,
                cosine=F.cosine_similarity(y.flatten(), ref.flatten(), dim=0).item(),
            )
        )
    passed = all(m["relative_l2"] < 0.004 and m["cosine"] > 0.99998 for m in metrics)
    args.output.write_text(json.dumps(dict(passed=passed, cases=metrics), indent=2))
    if not passed:
        raise ValueError(str(metrics))
    print(json.dumps(metrics), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for k in ("gguf", "gguf-python", "prism-bin", "assets", "cuda-codec", "output"):
        p.add_argument("--" + k, type=Path, required=True)
    with torch.inference_mode():
        run(p.parse_args())
