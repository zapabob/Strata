"""Copy build-time third-party notices into a fresh, hash-inventoried directory."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[3]
ENGINE = ROOT / "engine"
PACKAGING = ROOT / "tools/packaging"
VECTOR_DATA = ROOT / "terminal/data/experimental-speed-projection"

def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("out","cuda-dir","node-dir","host-node-modules","control-dir","microsoft-documents"):
        parser.add_argument("--"+name,required=True,type=Path)
    args=parser.parse_args()
    out=args.out.resolve()
    if out.exists():
        raise SystemExit("Notice stages are immutable; use a fresh output directory")
    entries={}
    def copy(source,name,expected=None):
        source=Path(source)
        if not source.is_file() or source.is_symlink() or source.stat().st_size>8*1024*1024:
            raise ValueError("Missing, linked or oversized notice: "+str(source))
        if expected and sha(source)!=expected:
            raise ValueError("Pinned vendor notice changed: "+name)
        target=out/name
        if not target.resolve().is_relative_to(out) or name in entries:
            raise ValueError("Unsafe or duplicate notice member")
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        entries[name]=sha(target)
    copy(ROOT/"LICENSE","Strata-MIT.txt")
    copy(ENGINE/"third_party/strata-ggml/LICENSE","ggml-MIT.txt")
    copy(ENGINE/"third_party/libstrix/NOTICE.md","libstrix-NOTICE.md")
    q38=ENGINE/"q38/src"
    copy(q38/"LICENSE-formats.txt","Q38-formats-MIT.txt")
    copy(q38/"tqcodec/DIALECT_LICENSE.txt","Turbo-dialects-MIT.txt")
    spin8=q38/"spin8/third_party/sha256"
    copy(spin8/"LICENSE","Spin8-SHA256-LICENSE.txt")
    copy(spin8/"PROVENANCE.md","Spin8-SHA256-PROVENANCE.md")
    copy(spin8/"rotate-bits/LICENSE.md","Spin8-rotate-bits-LICENSE.md")
    copy(args.cuda_dir/"EULA.txt","NVIDIA-EULA.txt")
    copy(args.cuda_dir/"LICENSE","NVIDIA-LICENSE.txt")
    copy(args.node_dir/"LICENSE","Node-LICENSE.txt","ed34dd8e3f0a78dbaf00d0444ce8e285b015b765379c2e17880455f70370f8e9")
    copy(PACKAGING/"hakua-third-party-notices.md","README.md")
    qwen=json.loads((VECTOR_DATA/"PROVENANCE.json").read_text(encoding="utf-8"))["license"]
    copy(VECTOR_DATA/"LICENSE","Qwen-Community-License-1.0.txt",qwen["sha256"])
    vendor=json.loads((PACKAGING/"microsoft-2022-notice-sources.json").read_text(encoding="utf-8"))
    for item in vendor:
        if not re.fullmatch(r"[A-Za-z0-9.-]+",item["file"]):
            raise ValueError("Unsafe vendor notice name")
        copy(args.microsoft_documents/item["file"],item["file"],item["sha256"])
    for package in ("react","react-dom","scheduler","katex","prismjs","pdfjs-dist","html-to-image"):
        folder=args.host_node_modules/package
        found=False
        for source in sorted(folder.rglob("*")):
            if source.is_file() and re.match(r"^(license|licence|notice|copying)",source.name,re.I):
                copy(source,"gui/"+package+"/"+source.relative_to(folder).as_posix())
                found=True
        if not found:
            raise ValueError("Missing GUI dependency licence: "+package)
    python=args.control_dir/"python"
    python_licenses=[p for p in python.iterdir() if p.is_file() and p.name.upper().startswith("LICENSE")]
    if not python_licenses:
        raise ValueError("Missing Python licence")
    for source in python_licenses:
        copy(source,"python/"+source.name)
    site=python/"Lib/site-packages"
    for info in sorted(site.glob("*.dist-info")):
        for source in sorted(info.rglob("*")):
            if source.is_file() and (re.match(r"^(license|licence|notice|copying)",source.name,re.I) or "licenses" in source.relative_to(info).parts):
                copy(source,"python/distributions/"+info.name+"/"+source.relative_to(info).as_posix())
    (out/"NOTICES.json").write_text(json.dumps({"schema":1,"microsoftSources":vendor,"qwenSource":qwen,"files":entries},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"notices":len(entries),"directory":str(out)}))

if __name__=="__main__":
    main()
