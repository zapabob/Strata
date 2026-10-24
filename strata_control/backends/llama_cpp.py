"""strata_control/backends/llama_cpp.py - Generic llama.cpp backend adapter."""
from __future__ import annotations

from dataclasses import dataclass
from strata_control.bundle_identity import VerifiedBundle
from strata_control.backend_contracts import BackendCapabilities


@dataclass(frozen=True)
class LlamaCppLaunchPlan:
    backend_id: str = "llama-cpp"
    binary_path: str = "llama-server"
    args: list[str] = None
    is_dense_only: bool = True


def build_llama_cpp_plan(bundle: VerifiedBundle, port: int = 18502) -> LlamaCppLaunchPlan:
    arch = bundle.bundle.architecture.lower()
    if arch in ("dsv41", "deepseek2", "deepseek"):
        raise ValueError(f"Generic llama.cpp backend does not support DeepSeek MoE architecture '{arch}'")

    args = [
        "-m", bundle.verified_files[0].path,
        "--port", str(port),
        "--host", "127.0.0.1",
    ]
    return LlamaCppLaunchPlan(args=args)
