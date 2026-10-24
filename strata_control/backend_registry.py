"""strata_control/backend_registry.py - Backend registration and deterministic routing engine."""
from __future__ import annotations

import hashlib
from typing import Any

from strata_control.bundle_identity import VerifiedBundle
from strata_control.backend_contracts import (
    BackendCapabilities,
    LoadRequest,
    ResolvedBackend,
)


class BackendRegistry:
    def __init__(self) -> None:
        self._backends: dict[str, BackendCapabilities] = {}

    def register_backend(self, caps: BackendCapabilities) -> None:
        self._backends[caps.backend_id] = caps

    def get(self, backend_id: str) -> BackendCapabilities | None:
        return self._backends.get(backend_id)

    def list_backends(self) -> list[str]:
        return list(self._backends.keys())

    def select_backend(
        self,
        bundle: VerifiedBundle,
        request: LoadRequest,
    ) -> ResolvedBackend:
        """Deterministically route a verified bundle to an approved local backend without fallback."""
        arch = bundle.bundle.architecture.lower()
        dialect = bundle.bundle.dialect.lower()

        # If a specific backend was explicitly requested by user
        if request.preferred_backend:
            target = self.get(request.preferred_backend)
            if not target:
                raise ValueError(f"Requested backend '{request.preferred_backend}' is not registered")
            
            # Strict validation: do not substitute or cloud-fallback!
            if arch not in [a.lower() for a in target.supported_architectures]:
                raise ValueError(
                    f"Manual backend '{target.backend_id}' does not support architecture '{arch}'. Substitution forbidden."
                )
            if dialect not in [d.lower() for d in target.supported_dialects]:
                raise ValueError(
                    f"Manual backend '{target.backend_id}' does not support dialect '{dialect}'."
                )
            return ResolvedBackend(
                backend_id=target.backend_id,
                capabilities=target,
                decision_reason=f"Manually selected backend '{target.backend_id}' matches architecture and dialect",
            )

        # Automatic deterministic selection based on geometry and dialect
        # Priority 1: DeepSeek architecture -> strata-dsv41
        if arch in ("dsv41", "deepseek", "deepseek2") and "strata-dsv41" in self._backends:
            ds_backend = self._backends["strata-dsv41"]
            return ResolvedBackend(
                backend_id="strata-dsv41",
                capabilities=ds_backend,
                decision_reason="Selected dedicated strata-dsv41 backend for DeepSeek architecture",
            )

        # Priority 2: Prism dialects (PQ2_0, PTQ1_0) -> prism
        if dialect in ("pq2_0", "ptq1_0") and "prism" in self._backends:
            prism_backend = self._backends["prism"]
            return ResolvedBackend(
                backend_id="prism",
                capabilities=prism_backend,
                decision_reason="Selected prism backend for PQ2_0 dialect",
            )

        # Priority 3: Native Qwen / Spin8 -> strata-native
        if arch in ("qwen2", "qwen") and "strata-native" in self._backends:
            native_backend = self._backends["strata-native"]
            return ResolvedBackend(
                backend_id="strata-native",
                capabilities=native_backend,
                decision_reason="Selected strata-native backend for Qwen architecture",
            )

        # Priority 4: Standard Dense GGUF -> llama-cpp
        if "llama-cpp" in self._backends:
            llama_backend = self._backends["llama-cpp"]
            if arch in [a.lower() for a in llama_backend.supported_architectures]:
                return ResolvedBackend(
                    backend_id="llama-cpp",
                    capabilities=llama_backend,
                    decision_reason="Selected llama-cpp backend for standard dense architecture",
                )

        raise ValueError(
            f"No suitable local backend found for architecture '{arch}' and dialect '{dialect}'. Cloud fallback is forbidden."
        )


def create_default_registry() -> BackendRegistry:
    """Create registry populated with standard Strata backends."""
    reg = BackendRegistry()
    reg.register_backend(
        BackendCapabilities(
            schema_version="1.0",
            backend_id="strata-native",
            binary_path="bin/strata-native",
            binary_sha256="native-sha",
            supported_architectures=("qwen2", "qwen"),
            supported_dialects=("standard", "tq4_1s", "tq3_0s"),
            supports_spin8=True,
        )
    )
    reg.register_backend(
        BackendCapabilities(
            schema_version="1.0",
            backend_id="strata-dsv41",
            binary_path="bin/strata-dsv41",
            binary_sha256="dsv41-sha",
            supported_architectures=("dsv41", "deepseek", "deepseek2"),
            supported_dialects=("standard", "iq4_nl"),
        )
    )
    reg.register_backend(
        BackendCapabilities(
            schema_version="1.0",
            backend_id="prism",
            binary_path="bin/prism",
            binary_sha256="prism-sha",
            supported_architectures=("qwen2", "llama"),
            supported_dialects=("pq2_0", "ptq1_0"),
        )
    )
    reg.register_backend(
        BackendCapabilities(
            schema_version="1.0",
            backend_id="llama-cpp",
            binary_path="bin/llama-server",
            binary_sha256="llama-sha",
            supported_architectures=("llama", "mistral", "phi3"),
            supported_dialects=("standard", "q4_k_m"),
        )
    )
    return reg

