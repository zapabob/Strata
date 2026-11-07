"""Read only GGUF metadata/tensor directory for the reported load failure."""
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from gguf_reader import GGUFFile

path = Path(sys.argv[1])
before = path.stat()
model = GGUFFile(path)
arch = model.metadata.get("general.architecture")
selected = {
    key: value for key, value in model.metadata.items()
    if key in ("general.architecture", "general.name", "general.file_type", "general.size_label")
    or key.endswith((".block_count", ".nextn_predict_layers", ".full_attention_interval", ".context_length"))
}
layers = Counter()
for tensor in model.tensors:
    match = re.match(r"blk\.(\d+)\.", tensor.name)
    if match:
        layers[int(match[1])] += 1
outside = [t.name for t in model.tensors if t.expected_bytes() is not None
           and model.data_start + t.offset + t.expected_bytes() > before.st_size]
after = path.stat()
assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
print(json.dumps({
    "bytes": before.st_size, "headerBytes": model.data_start, "version": model.version,
    "metadata": selected, "tensorCount": len(model.tensors), "types": model.by_type(),
    "layerTensorCounts": dict(sorted(layers.items())), "knownTensorsOutsideFile": outside,
    "requestedTensorPresent": any(t.name == "blk.32.attn_norm.weight" for t in model.tensors),
    "lastLayerTensorNames": [t.name for t in model.tensors
                             if (m := re.match(r"blk\.(\d+)\.", t.name)) and int(m[1]) >= 31],
    "fileUnchanged": True,
}, ensure_ascii=False, indent=2))
