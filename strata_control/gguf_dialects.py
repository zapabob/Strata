"""strata_control/gguf_dialects.py - Quantization dialects and architecture definitions."""
from __future__ import annotations

from enum import Enum
from typing import NamedTuple


class DialectType(str, Enum):
    STANDARD = "standard"
    PRISM = "prism"
    TURBOQUANT = "turboquant"
    DEEPSEEK_DSV41 = "dsv41"


class QuantDialect(NamedTuple):
    type_id: int
    name: str
    dialect: DialectType
    block_size: int
    type_size: int


# Standard GGML types
STANDARD_DIALECTS = {
    0: QuantDialect(0, "F32", DialectType.STANDARD, 1, 4),
    1: QuantDialect(1, "F16", DialectType.STANDARD, 1, 2),
    2: QuantDialect(2, "Q4_0", DialectType.STANDARD, 32, 18),
    3: QuantDialect(3, "Q4_1", DialectType.STANDARD, 32, 20),
    8: QuantDialect(8, "Q8_0", DialectType.STANDARD, 32, 34),
}

# Prism / Bonsai / TurboQuant custom type mappings
PRISM_DIALECTS = {
    1001: QuantDialect(1001, "PQ2_0", DialectType.PRISM, 64, 18),
    1002: QuantDialect(1002, "PTQ1_0", DialectType.PRISM, 64, 10),
    2001: QuantDialect(2001, "TQ4_1S", DialectType.TURBOQUANT, 32, 20),
    2002: QuantDialect(2002, "TQ3_0S", DialectType.TURBOQUANT, 32, 15),
}


def resolve_dialect_type(type_id: int, explicit_dialect: str | None = None) -> QuantDialect:
    """Resolve a numeric quant type id into its QuantDialect, requiring explicit dialect on collisions."""
    if explicit_dialect == "prism" and type_id in PRISM_DIALECTS:
        return PRISM_DIALECTS[type_id]
    if explicit_dialect == "turboquant" and type_id in PRISM_DIALECTS:
        return PRISM_DIALECTS[type_id]
    if type_id in STANDARD_DIALECTS:
        return STANDARD_DIALECTS[type_id]
    if type_id in PRISM_DIALECTS:
        return PRISM_DIALECTS[type_id]
    raise ValueError(f"Unknown quantization type id: {type_id} (explicit_dialect={explicit_dialect})")
