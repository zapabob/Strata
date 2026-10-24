"""strata_control/model_registry.py - Atomic manifest transaction registry for verified ModelBundles."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

from strata_control.bundle_identity import VerifiedBundle


@dataclass(frozen=True)
class RegistryReceipt:
    registered: bool
    model_set_id: str
    manifest_path: str
    registered_at: str
    canonical_hash: str


class ModelRegistry:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.registry_file = root_dir / "registry-manifest.json"
        self.root_dir.mkdir(parents=True, exist_ok=True)
        if not self.registry_file.exists():
            self._write_atomic({})

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.registry_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_atomic(self, data: dict[str, Any]) -> None:
        tmp = self.registry_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.registry_file)

    def register(self, verified: VerifiedBundle) -> RegistryReceipt:
        """Atomically register a verified bundle manifest."""
        current = self._read()
        now_iso = datetime.now(timezone.utc).isoformat()

        entry = {
            "model_set_id": verified.model_set_id,
            "canonical_hash": verified.canonical_hash,
            "registered_at": now_iso,
            "architecture": verified.bundle.architecture,
            "dialect": verified.bundle.dialect,
            "files": [
                {
                    "role": f.role,
                    "ordinal": f.ordinal,
                    "path": f.path,
                    "file_size": f.file_size,
                    "sha256": f.sha256,
                }
                for f in verified.verified_files
            ],
        }

        current[verified.model_set_id] = entry
        self._write_atomic(current)

        return RegistryReceipt(
            registered=True,
            model_set_id=verified.model_set_id,
            manifest_path=str(self.registry_file),
            registered_at=now_iso,
            canonical_hash=verified.canonical_hash,
        )

    def get(self, model_set_id: str) -> dict[str, Any] | None:
        return self._read().get(model_set_id)
