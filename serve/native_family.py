"""Select the serving family; this never establishes an engine capability."""

import re
from collections.abc import Mapping


def is_q36_config(cfg: Mapping[str, object]) -> bool:
    """Explicit runtime architecture wins; name hints serve only legacy configs.

    Host resolves catalog identities to a canonical architecture before launch.
    Old configurations without an architecture retain their executable/model
    hints. Capability negotiation and the child's receipts are still required.
    """
    arch = cfg.get("arch")
    if arch is not None and arch != "":
        return arch in ("qwen35moe", "qwen36")
    return "strata-q36" in str(cfg.get("exe", "")) or bool(
        re.search(r"qwen3\.6|qwen36|35b-a3b", str(cfg.get("model_name", "")), re.I)
    )
