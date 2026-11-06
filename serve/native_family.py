"""One adapter/contract admission invariant, without granting engine capability."""

import re
from collections.abc import Mapping
from dataclasses import dataclass


def _valid_sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def _private_cache_requirement(args: object) -> int:
    if args is None:
        return 0
    if not isinstance(args, (list, tuple)) or any(not isinstance(a, str) for a in args):
        raise ValueError("Q36 cache arguments must be a list of strings")
    if "--private-conversation-cache" in args:
        return 2
    return int(
        any(flag in args for flag in ("--prompt-cache", "--conversation-cache-mib"))
    )


@dataclass(frozen=True)
class NativeAdmission:
    """Validated requirements for one start, never proof supplied by an engine."""

    q36: bool
    private_cache: int = 0
    expected_kv_sha256: str | None = None
    generation: str | None = None

    def __post_init__(self) -> None:
        if type(self.q36) is not bool or type(self.private_cache) is not int:
            raise ValueError("Q36 admission requirements have invalid types")
        if self.private_cache not in (0, 1, 2):
            raise ValueError("Q36 private-cache requirement must be 0, 1 or 2")
        if not self.q36 and (
            self.private_cache
            or self.expected_kv_sha256 is not None
            or self.generation is not None
        ):
            raise ValueError("Native adapter conflicts with retained Q36 requirements")
        if self.expected_kv_sha256 is not None and not _valid_sha(
            self.expected_kv_sha256
        ):
            raise ValueError(
                "Q36 binary expectation must be a lowercase SHA-256 digest"
            )
        if self.generation is not None and (
            not isinstance(self.generation, str)
            or re.fullmatch(r"[a-zA-Z0-9-]{1,80}", self.generation) is None
        ):
            raise ValueError("Q36 launch generation is invalid")


def native_admission(cfg: Mapping[str, object]) -> NativeAdmission:
    """Resolve explicit/legacy identity and validate all consumed Q36 metadata.

    A retained contract may require Q36 verification when old configs omit arch.
    It cannot override a conflicting explicit adapter or establish capability:
    the actual binary and READY receipts still have to satisfy these requirements.
    """
    arch = cfg.get("arch")
    explicit = arch is not None and arch != ""
    if explicit:
        q36 = arch in ("qwen35moe", "qwen36")
    else:
        q36 = "strata-q36" in str(cfg.get("exe", "")) or bool(
            re.search(r"qwen3\.6|qwen36|35b-a3b", str(cfg.get("model_name", "")), re.I)
        )
    expected = generation = None
    run = cfg.get("q36_run")
    if run is not None:
        if not isinstance(run, Mapping):
            raise ValueError("q36_run must be a Q36 contract object or null")
        backend = run.get("backend")
        if not isinstance(backend, Mapping) or backend.get("family") != "qwen36":
            raise ValueError("q36_run.backend.family must identify qwen36")
        if explicit and not q36:
            raise ValueError(
                "arch conflicts with q36_run.backend.family; "
                "correct the adapter or clear the retained contract"
            )
        if type(run.get("schemaVersion")) is not int or run["schemaVersion"] != 1:
            raise ValueError("q36_run requires schemaVersion 1")
        q36 = True
        generation = run.get("generation")
        digest, claim = backend.get("binarySha256"), backend.get("kvCapability")
        if digest is not None and not _valid_sha(digest):
            raise ValueError("q36_run.backend.binarySha256 is invalid")
        if claim is not None:
            if (
                not isinstance(claim, Mapping)
                or claim.get("family") != "qwen35moe"
                or not _valid_sha(digest)
                or claim.get("binarySha256") != digest
            ):
                raise ValueError(
                    "q36_run KV expectation has inconsistent family/digest identity"
                )
            expected = digest
    # engine_args merges the user layer before starting. Neither layer may lose
    # its acknowledgement requirement while projecting the config to env.
    private = 0
    if q36:
        private = max(
            _private_cache_requirement(cfg.get("args")),
            _private_cache_requirement(cfg.get("user_args")),
        )
    return NativeAdmission(q36, private, expected, generation)


def is_q36_config(cfg: Mapping[str, object]) -> bool:
    """Return the validated identity; conflicting retained contracts are errors."""
    return native_admission(cfg).q36


def native_admission_from_env(
    env: Mapping[str, object], args: object = None
) -> NativeAdmission:
    """Validate the same invariant again at the constructor's captured boundary."""
    private = env.get("STRATA_REQUIRE_Q36_PRIVATE_CACHE", "0")
    if private not in ("0", "1", "2"):
        raise ValueError("Q36 private-cache environment requirement is invalid")
    if "STRATA_REQUIRE_Q36_KV" in env:
        flag = env["STRATA_REQUIRE_Q36_KV"]
        if flag not in ("0", "1"):
            raise ValueError("Q36 KV environment requirement is invalid")
        q36 = flag == "1"
    else:
        # Older callers supplied only the private-cache requirement. Keep that
        # check, without manufacturing typed-KV capability for a legacy binary.
        q36 = private != "0"
    admission = NativeAdmission(
        q36,
        int(private),
        env.get("STRATA_Q36_KV_HOST_SHA256"),
        env.get("STRATA_Q36_LAUNCH_GENERATION"),
    )
    if admission.q36 and admission.private_cache < _private_cache_requirement(args):
        raise ValueError(
            "Q36 private-cache requirement was lost from the runtime arguments"
        )
    return admission
