"""Produce bounded native cache capsules from independently pinned receipts.

This is an internal diagnostic producer, not a signing system. It rechecks the
1.5 GB dense/source spans because the old receipt has no dense mtime identity.
The original large shards are NOT rehashed. Their pinned full-hash receipt is
reused only with the independently selected paths, raw hashes and exact metadata.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def trusted_json(path: Path, expected: str) -> dict:
    if path.stat().st_size>16*1024*1024: raise ValueError("receipt exceeds bound")
    with path.open("rb") as f: data=f.read(16*1024*1024+1)
    if len(data)>16*1024*1024 or sha(data)!=expected:
        raise ValueError("independently expected receipt SHA mismatch")
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError("duplicate receipt field")
            result[key]=value
        return result
    return json.loads(data.decode("utf-8-sig"),object_pairs_hook=unique)

def validate_source(record: dict, selected: Path, expected: str) -> tuple:
    import verify_native_pack_binding as V
    stat=selected.stat()
    mtime=record.get("mtime_ns")
    if mtime is None: mtime=V.receipt_mtime_ns(record["last_write_utc"])
    if not (selected.resolve()==Path(record["path"]).resolve() and
            record["sha256"]==record["expected_sha256"]==expected and
            record["matches"] is True and record["metadata_unchanged"] is True and
            stat.st_size==record["bytes"] and stat.st_mtime_ns==mtime):
        raise ValueError("actual selected source differs from independent receipt")
    return expected,stat.st_size,stat.st_mtime_ns//100

def u32(x): return struct.pack("<I",x)
def u64(x): return struct.pack("<Q",x)
def text(s: str) -> bytes:
    b=s.encode("utf-8",errors="strict")
    if not b or len(b)>32768 or b"\0" in b: raise ValueError("invalid capsule path")
    return u32(len(b))+b

def position_digest(n_rot: int, base: float) -> bytes:
    # Initial producer supports default-origin unscaled native RoPE only. The
    # native consumer independently serializes its actual resolved configuration.
    value=b"strata-native-position/v1\0"+struct.pack("<QQQ",0,n_rot,0)
    value+=struct.pack("<8d",base,1.,0.,262144.,0.,1.,32.,1.)
    return hashlib.sha256(value).digest()

def metadata(path: Path, content_hash: bool) -> bytes:
    before=path.stat()
    if content_hash and before.st_size>32*1024*1024: raise ValueError("metadata bound exceeded")
    digest=hashlib.sha256(path.read_bytes()).digest() if content_hash else bytes(32)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError("metadata changed during read")
    return struct.pack("<QQ",before.st_size,before.st_mtime_ns//100)+digest

def pack_metadata(pack: Path, expected: dict) -> dict:
    paths={str(p.relative_to(pack)):p for p in pack.rglob("*") if p.is_file() and p.name!="dense.bin"}
    if paths.keys()!=expected.keys(): raise ValueError("pack metadata file set differs")
    result={}
    for name,p in paths.items():
        if not p.resolve().is_relative_to(pack.resolve()) or p.stat().st_size>32*1024*1024:
            raise ValueError("pack metadata path or size exceeds bound")
        with p.open("rb") as f: data=f.read(32*1024*1024+1)
        if len(data)>32*1024*1024: raise ValueError("pack metadata grew beyond bound")
        result[name]=sha(data)
    return result

def produce(args) -> dict:
    import verify_native_pack_binding as V
    import gguf_reader as G
    source=trusted_json(args.source_receipt,args.source_receipt_sha256)
    old=trusted_json(args.pack_receipt,args.pack_receipt_sha256)
    if len(source["models"])!=len(args.source) or len(args.source)!=len(args.raw_sha256):
        raise ValueError("source count mismatch")
    records=[validate_source(r,p,h) for r,p,h in zip(source["models"],args.source,args.raw_sha256)]
    if Path(old["pack"]).resolve()!=args.pack.resolve() or old["source_receipt_sha256"]!=args.source_receipt_sha256:
        raise ValueError("selected pack/source receipt mismatch")
    # Fail before the bounded dense scan if any small metadata differs.
    actual=pack_metadata(args.pack,old["metadata_sha256"])
    if actual!=old["metadata_sha256"]: raise ValueError("current small pack metadata differs")
    current=V.verify(args.pack,args.source_receipt)
    for key in ("dense_bytes","dense_spans","experts","index_rows","native_dense_tensors","tokenizer","metadata_sha256"):
        if current[key]!=old[key]: raise ValueError("bounded pack validation differs: "+key)
    # The native reader derives this directory itself, from its selected GGUF.
    model=G.GGUFFile(args.source[0]);m=model.metadata;arch=m["general.architecture"]+"."
    if m.get(arch+"rope.scaling.type","none")!="none": raise ValueError("producer supports unscaled RoPE only")
    n=int(m[arch+"block_count"]);interval=int(m[arch+"full_attention_interval"])
    layers=[(l,int(m[arch+"attention.head_count"]),int(m[arch+"attention.head_count_kv"]),int(m[arch+"attention.key_length"])) for l in range(n) if l%interval==interval-1]
    position=position_digest(int(m[arch+"rope.dimension_count"]),float(m.get(arch+"rope.freq_base",1e7)))
    tail=u32(len(records))
    for p,(digest,size,time) in zip(args.source,records):
        tail+=text(str(p.resolve()))+bytes.fromhex(digest)+struct.pack("<QQ",size,time)+bytes(32)
    tail+=text(str(args.pack.resolve()))
    files=sorted([p for p in args.pack.rglob("*") if p.is_file()],key=lambda p:p.relative_to(args.pack).as_posix())
    tail+=u32(len(files))
    for p in files: tail+=text(p.relative_to(args.pack).as_posix())+metadata(p,p.name!="dense.bin")
    tail+=u32(len(layers))+b"".join(struct.pack("<4I",*s) for s in layers)+u64(0)
    outputs={}
    for name,representation in (("f32",1),("compressed",0)):
        capsule=b"STNCAP1\n"+struct.pack("<5I",1,3,1,representation,7)
        capsule+=struct.pack("<3dQQ",1/3,1/3,1/3,args.capacity,args.rows)
        capsule+=u32(2)+struct.pack("<IId",0,1,.37)+struct.pack("<IId",2,5,-.61)+position+tail
        path=args.output/name
        with path.with_suffix(".capsule").open("xb") as f: f.write(capsule)
        outputs[name]={"path":str(path.with_suffix(".capsule")),"sha256":sha(capsule),"bytes":len(capsule)}
    for r,p,h in zip(source["models"],args.source,args.raw_sha256): validate_source(r,p,h)
    result={"schema":"strata-native-capsule-production-v1","source_receipt_sha256":args.source_receipt_sha256,
            "pack_receipt_sha256":args.pack_receipt_sha256,"outputs":outputs,"normal_layers":layers,
            "position_sha256":position.hex(),"adapter":"identity v3; no sidecar; nontrivial three B views",
            "bounded_dense_recheck":current}
    with (args.output/"production.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("source-receipt","pack-receipt","pack","output"):parser.add_argument("--"+name,type=Path,required=True)
    for name in ("source-receipt-sha256","pack-receipt-sha256"):parser.add_argument("--"+name,required=True)
    parser.add_argument("--source",type=Path,action="append",required=True)
    parser.add_argument("--raw-sha256",action="append",required=True)
    parser.add_argument("--capacity",type=int,default=256)
    parser.add_argument("--rows",type=int,default=32)
    args=parser.parse_args()
    if not 0<args.rows<=args.capacity<=1048576: raise ValueError("invalid execution bounds")
    args.output.mkdir(exist_ok=False)
    print(json.dumps(produce(args)["outputs"],indent=2))
if __name__=="__main__":main()
