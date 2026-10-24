"""strata_control/steering.py - Research steering vector mathematics (project, reflect, add) and profile manager."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class SteeringProfile:
    mode: str = "off"  # off, project, reflect, add
    vector: list[float] = None
    strength: float = 1.0
    layer_indices: list[int] = None
    hidden_dim: int = 4096


def apply_steering_transform(
    hidden_state: list[float],
    profile: SteeringProfile,
) -> list[float]:
    """Apply linear algebraic transformation to hidden state based on steering profile."""
    if profile.mode == "off" or profile.strength == 0.0 or not profile.vector:
        return list(hidden_state)

    v = profile.vector
    # Normalize v
    norm = math.sqrt(sum(x * x for x in v))
    if norm < 1e-12:
        return list(hidden_state)
    u = [x / norm for x in v]

    # Inner product (h . u)
    dot = sum(h * ui for h, ui in zip(hidden_state, u))

    if profile.mode == "project":
        # Projection: h - (h . u) u
        # Notice sign invariance: (-u) gives (-dot) * (-u) = dot * u, identically unchanged!
        return [h - profile.strength * dot * ui for h, ui in zip(hidden_state, u)]

    elif profile.mode == "reflect":
        # Reflection: h - 2 * (h . u) u (norm preserving, det = -1)
        return [h - 2.0 * profile.strength * dot * ui for h, ui in zip(hidden_state, u)]

    elif profile.mode == "add":
        # Bias addition: h + strength * u
        return [h + profile.strength * ui for h, ui in zip(hidden_state, u)]

    else:
        raise ValueError(f"Unknown steering mode: {profile.mode}")
