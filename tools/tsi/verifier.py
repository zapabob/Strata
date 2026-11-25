"""Independent multi-level verifier architecture for NKAT-URT TSI (Stage B, Section 13).

Explicitly separates five verification levels:
- UNVERIFIED
- EXACT_ANSWER_VERIFIED
- DETERMINISTIC_TEST_VERIFIED
- NUMERICAL_CERTIFICATE_VERIFIED
- FORMAL_PROOF_VERIFIED

No model-generated code is ever executed with eval() or exec(), and LLM self-grading
can never grant FORMAL_PROOF_VERIFIED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import logging
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Literal, Sequence

LOGGER = logging.getLogger("strata.tsi.verifier")

VERIFIER_MODULE_VERSION = "tsi-verifier-1.0"


class VerificationLevel(str, Enum):
    """Strict five-level verification hierarchy (Section 13)."""

    UNVERIFIED = "UNVERIFIED"
    EXACT_ANSWER_VERIFIED = "EXACT_ANSWER_VERIFIED"
    DETERMINISTIC_TEST_VERIFIED = "DETERMINISTIC_TEST_VERIFIED"
    NUMERICAL_CERTIFICATE_VERIFIED = "NUMERICAL_CERTIFICATE_VERIFIED"
    FORMAL_PROOF_VERIFIED = "FORMAL_PROOF_VERIFIED"


OutcomeKind = Literal[
    "verified_pass",
    "verified_fail",
    "unverified_no_answer",
    "truncated_budget",
    "format_error",
    "timeout_error",
    "api_error",
    "verifier_error",
]


@dataclass(frozen=True)
class VerificationResult:
    """Independent verification outcome for one candidate response."""

    verified: bool
    verification_level: VerificationLevel
    outcome: OutcomeKind
    verifier_name: str
    extracted_answer: str | None
    extraction_source: str
    detail: str
    verifier_version: str = VERIFIER_MODULE_VERSION


# --------------------------------------------------------------------------- Safe parsing
_FINAL_RE = re.compile(r"FINAL_ANSWER\s*[:=]\s*([^\r\n]+)", re.IGNORECASE)
_FRAC_TEX_RE = re.compile(r"^\\(?:d|t)?frac\{([+-]?\d+)\}\{([+-]?\d+)\}$")
_INT_RE = re.compile(r"^[+-]?\d+$")
_RATIONAL_RE = re.compile(r"^[+-]?\d+(?:/[+-]?\d+)?$")
_DEC_RE = re.compile(r"^[+-]?\d+\.\d+$")


def _extract_last_boxed(text: str) -> str | None:
    """Extract the content of the last balanced \\boxed{...} expression."""
    marker = "\\boxed{"
    idx = text.rfind(marker)
    if idx < 0:
        return None
    pos = idx + len(marker)
    depth = 1
    chars: list[str] = []
    while pos < len(text) and depth > 0:
        ch = text[pos]
        if ch == "{":
            depth += 1
            chars.append(ch)
        elif ch == "}":
            depth -= 1
            if depth > 0:
                chars.append(ch)
        else:
            chars.append(ch)
        pos += 1
    if depth != 0:
        return None
    return "".join(chars).strip()


def extract_candidate_answer(text: str) -> tuple[str | None, str]:
    """Extract a canonical answer string without guessing from arbitrary prose."""
    if not text or not text.strip():
        return None, "none"
    boxed = _extract_last_boxed(text)
    if boxed is not None and boxed != "":
        return boxed, "boxed"
    matches = _FINAL_RE.findall(text)
    if matches:
        ans = matches[-1].strip().strip("$").rstrip(".")
        if ans:
            return ans, "final_answer_line"
    return None, "none"


def normalise_token(raw: str) -> str:
    s = raw.strip().strip("$").strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1].strip()
    return s.replace("\\,", "").replace(" ", "")


def parse_int(raw: str) -> int | None:
    s = normalise_token(raw)
    if _INT_RE.match(s):
        return int(s)
    return None


def parse_rational(raw: str) -> Fraction | None:
    s = normalise_token(raw)
    m = _FRAC_TEX_RE.match(s)
    if m:
        num, den = int(m.group(1)), int(m.group(2))
        if den == 0:
            return None
        return Fraction(num, den)
    if _RATIONAL_RE.match(s):
        if "/" in s:
            num_s, den_s = s.split("/", 1)
            den = int(den_s)
            if den == 0:
                return None
            return Fraction(int(num_s), den)
        return Fraction(int(s), 1)
    if _DEC_RE.match(s):
        return Fraction(s)
    return None


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def verify_structured_task(
    verifier_type: str,
    spec: dict[str, Any],
    response_text: str,
    *,
    finish_reason: str | None = None,
    api_error: str | None = None,
    timed_out: bool = False,
) -> VerificationResult:
    """Independently verify a response against a structured task specification."""
    if timed_out:
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="timeout_error",
            verifier_name=verifier_type,
            extracted_answer=None,
            extraction_source="none",
            detail=api_error or "request timed out",
        )
    if api_error:
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="api_error",
            verifier_name=verifier_type,
            extracted_answer=None,
            extraction_source="none",
            detail=api_error,
        )

    if verifier_type == "lean4_proof":
        return verify_lean4_proof(
            proof_text=response_text,
            required_theorem_signature=str(spec.get("theorem_signature", "")),
            allowed_axioms=tuple(spec.get("allowed_axioms", ())),
            timeout_s=float(spec.get("timeout_s", 30.0)),
            lean_binary=str(spec.get("lean_binary", "lean")),
        )

    extracted, source = extract_candidate_answer(response_text)
    if extracted is None:
        if finish_reason == "length":
            return VerificationResult(
                verified=False,
                verification_level=VerificationLevel.UNVERIFIED,
                outcome="truncated_budget",
                verifier_name=verifier_type,
                extracted_answer=None,
                extraction_source="none",
                detail="Generation stopped at token budget before emitting a canonical answer marker.",
            )
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="unverified_no_answer",
            verifier_name=verifier_type,
            extracted_answer=None,
            extraction_source="none",
            detail="No \\boxed{...} or FINAL_ANSWER: marker found in assistant output.",
        )

    try:
        return _dispatch_deterministic_verifier(verifier_type, spec, extracted, source)
    except Exception as exc:  # noqa: BLE001 - isolate verifier faults cleanly
        LOGGER.warning("Verifier fault for verifier_type=%s: %s", verifier_type, exc)
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="verifier_error",
            verifier_name=verifier_type,
            extracted_answer=extracted,
            extraction_source=source,
            detail=f"verifier exception: {exc}",
        )


def _dispatch_deterministic_verifier(
    verifier_type: str,
    spec: dict[str, Any],
    extracted: str,
    source: str,
) -> VerificationResult:
    if verifier_type == "exact_int":
        val = parse_int(extracted)
        if val is None:
            return VerificationResult(
                False, VerificationLevel.UNVERIFIED, "format_error", verifier_type, extracted, source, "Expected an exact integer."
            )
        exp = int(spec["expected"])
        if val == exp:
            return VerificationResult(
                True,
                VerificationLevel.EXACT_ANSWER_VERIFIED,
                "verified_pass",
                verifier_type,
                extracted,
                source,
                f"exact_int matched {exp}",
            )
        return VerificationResult(
            False, VerificationLevel.UNVERIFIED, "verified_fail", verifier_type, extracted, source, f"got {val}, expected {exp}"
        )

    if verifier_type == "exact_rational":
        val_q = parse_rational(extracted)
        if val_q is None:
            return VerificationResult(
                False,
                VerificationLevel.UNVERIFIED,
                "format_error",
                verifier_type,
                extracted,
                source,
                "Expected an exact rational a/b.",
            )
        exp_q = Fraction(str(spec["expected"]))
        if val_q == exp_q:
            return VerificationResult(
                True,
                VerificationLevel.EXACT_ANSWER_VERIFIED,
                "verified_pass",
                verifier_type,
                extracted,
                source,
                f"exact_rational matched {exp_q}",
            )
        return VerificationResult(
            False, VerificationLevel.UNVERIFIED, "verified_fail", verifier_type, extracted, source, f"got {val_q}, expected {exp_q}"
        )

    if verifier_type == "predicate_euler_poly_composite":
        val = parse_int(extracted)
        if val is None:
            return VerificationResult(
                False,
                VerificationLevel.UNVERIFIED,
                "format_error",
                verifier_type,
                extracted,
                source,
                "Expected a positive integer n.",
            )
        lo = int(spec.get("min_n", 1))
        hi = int(spec.get("max_n", 100000))
        if not (lo <= val <= hi):
            return VerificationResult(
                False, VerificationLevel.UNVERIFIED, "verified_fail", verifier_type, extracted, source, f"n={val} outside [{lo}, {hi}]"
            )
        poly = val * val + val + 41
        if poly > 1 and not _is_prime(poly):
            return VerificationResult(
                True,
                VerificationLevel.NUMERICAL_CERTIFICATE_VERIFIED,
                "verified_pass",
                verifier_type,
                extracted,
                source,
                f"n={val} -> {poly} is composite",
            )
        return VerificationResult(
            False, VerificationLevel.UNVERIFIED, "verified_fail", verifier_type, extracted, source, f"n={val} -> {poly} is prime"
        )

    if verifier_type == "predicate_linear_diophantine":
        parts = normalise_token(extracted).split(",")
        if len(parts) != 2:
            return VerificationResult(
                False, VerificationLevel.UNVERIFIED, "format_error", verifier_type, extracted, source, "Expected two integers x,y."
            )
        x_val = parse_int(parts[0])
        y_val = parse_int(parts[1])
        if x_val is None or y_val is None:
            return VerificationResult(
                False,
                VerificationLevel.UNVERIFIED,
                "format_error",
                verifier_type,
                extracted,
                source,
                "Could not parse integer pair x,y.",
            )
        lo = int(spec["min_v"])
        hi = int(spec["max_v"])
        a = int(spec["a"])
        b = int(spec["b"])
        c = int(spec["c"])
        if not (lo <= x_val <= hi and lo <= y_val <= hi):
            return VerificationResult(
                False,
                VerificationLevel.UNVERIFIED,
                "verified_fail",
                verifier_type,
                extracted,
                source,
                f"({x_val},{y_val}) outside [{lo},{hi}]",
            )
        lhs = a * x_val + b * y_val
        if lhs == c:
            return VerificationResult(
                True,
                VerificationLevel.NUMERICAL_CERTIFICATE_VERIFIED,
                "verified_pass",
                verifier_type,
                extracted,
                source,
                f"{a}*{x_val}+({b})*{y_val}={lhs}=={c}",
            )
        return VerificationResult(
            False,
            VerificationLevel.UNVERIFIED,
            "verified_fail",
            verifier_type,
            extracted,
            source,
            f"{a}*{x_val}+({b})*{y_val}={lhs}!={c}",
        )

    if verifier_type == "deterministic_polynomial_roots":
        # Verify an unordered set of exact integer roots against deterministic test evaluations P(r) == 0.
        coeffs = [int(c) for c in spec["coefficients_desc"]]
        expected_count = int(spec["expected_root_count"])
        raw_parts = [p for p in normalise_token(extracted).split(",") if p]
        parsed: list[int] = []
        for p in raw_parts:
            v = parse_int(p)
            if v is None:
                return VerificationResult(
                    False,
                    VerificationLevel.UNVERIFIED,
                    "format_error",
                    verifier_type,
                    extracted,
                    source,
                    f"Non-integer root token {p!r}.",
                )
            parsed.append(v)
        unique_roots = sorted(set(parsed))
        if len(unique_roots) != expected_count:
            return VerificationResult(
                False,
                VerificationLevel.UNVERIFIED,
                "verified_fail",
                verifier_type,
                extracted,
                source,
                f"Expected {expected_count} distinct integer roots, got {unique_roots}.",
            )
        for r in unique_roots:
            val = 0
            for c in coeffs:
                val = val * r + c
            if val != 0:
                return VerificationResult(
                    False,
                    VerificationLevel.UNVERIFIED,
                    "verified_fail",
                    verifier_type,
                    extracted,
                    source,
                    f"Deterministic test failed: P({r}) = {val} != 0.",
                )
        return VerificationResult(
            True,
            VerificationLevel.DETERMINISTIC_TEST_VERIFIED,
            "verified_pass",
            verifier_type,
            extracted,
            source,
            f"All {expected_count} roots passed deterministic polynomial evaluation.",
        )

    raise ValueError(f"Unsupported verifier_type: {verifier_type!r}")


# --------------------------------------------------------------------------- Isolated Lean 4 adapter
_LEAN_FORBIDDEN_RE = re.compile(
    r"\b(?:sorry|admit|unsafe|implemented_by|extern)\b|@\[(?:implemented_by|extern)\]",
)
_LEAN_AXIOM_RE = re.compile(r"^\s*(?:private\s+|protected\s+)?axiom\s+([A-Za-z_][A-Za-z0-9_'.]*)", re.MULTILINE)


def verify_lean4_proof(
    *,
    proof_text: str,
    required_theorem_signature: str,
    allowed_axioms: Sequence[str] = (),
    timeout_s: float = 30.0,
    lean_binary: str = "lean",
) -> VerificationResult:
    """Verify a Lean 4 proof in an isolated temporary directory using the Lean kernel.

    Never grants FORMAL_PROOF_VERIFIED without:
    1. Exact presence of `required_theorem_signature`,
    2. Rejection of `sorry`, `admit`, `unsafe`, `implemented_by`, `extern`, and any
       unlisted `axiom` declarations,
    3. Exit code 0 from an actual Lean kernel invocation.
    """
    if not required_theorem_signature.strip():
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="verifier_error",
            verifier_name="lean4_proof",
            extracted_answer=None,
            extraction_source="lean4",
            detail="required_theorem_signature must be fixed and non-empty.",
        )

    if required_theorem_signature.strip() not in proof_text:
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="verified_fail",
            verifier_name="lean4_proof",
            extracted_answer=None,
            extraction_source="lean4",
            detail="Target theorem signature missing or altered in candidate proof.",
        )

    forb = _LEAN_FORBIDDEN_RE.search(proof_text)
    if forb:
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="verified_fail",
            verifier_name="lean4_proof",
            extracted_answer=None,
            extraction_source="lean4",
            detail=f"Forbidden Lean construct detected: {forb.group(0)!r}.",
        )

    allowed_set = set(allowed_axioms)
    for m in _LEAN_AXIOM_RE.finditer(proof_text):
        ax_name = m.group(1)
        if ax_name not in allowed_set:
            return VerificationResult(
                verified=False,
                verification_level=VerificationLevel.UNVERIFIED,
                outcome="verified_fail",
                verifier_name="lean4_proof",
                extracted_answer=None,
                extraction_source="lean4",
                detail=f"Unauthorised axiom declaration detected: {ax_name!r}.",
            )

    resolved = shutil.which(lean_binary)
    if resolved is None:
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="verifier_error",
            verifier_name="lean4_proof",
            extracted_answer=None,
            extraction_source="lean4",
            detail=f"Lean kernel binary {lean_binary!r} not installed; FORMAL_PROOF_VERIFIED not granted.",
        )

    lean_version = "unknown"
    try:
        ver_proc = subprocess.run(
            [resolved, "--version"],
            capture_output=True,
            text=True,
            timeout=10.0,
            check=False,
        )
        if ver_proc.returncode == 0 and ver_proc.stdout.strip():
            lean_version = ver_proc.stdout.strip().splitlines()[0]
    except OSError:
        pass

    try:
        with tempfile.TemporaryDirectory(prefix="tsi_lean_") as tmp_dir:
            proof_file = Path(tmp_dir) / "CandidateProof.lean"
            proof_file.write_text(proof_text, encoding="utf-8")
            proc = subprocess.run(
                [resolved, str(proof_file)],
                cwd=tmp_dir,
                capture_output=True,
                text=True,
                timeout=max(1.0, float(timeout_s)),
                check=False,
            )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="timeout_error",
            verifier_name="lean4_proof",
            extracted_answer=None,
            extraction_source="lean4",
            detail=f"Lean kernel timed out after {timeout_s:.1f}s.",
            verifier_version=lean_version,
        )
    except OSError as exc:
        return VerificationResult(
            verified=False,
            verification_level=VerificationLevel.UNVERIFIED,
            outcome="verifier_error",
            verifier_name="lean4_proof",
            extracted_answer=None,
            extraction_source="lean4",
            detail=f"Lean invocation failed: {exc}",
            verifier_version=lean_version,
        )

    if proc.returncode == 0:
        return VerificationResult(
            verified=True,
            verification_level=VerificationLevel.FORMAL_PROOF_VERIFIED,
            outcome="verified_pass",
            verifier_name="lean4_proof",
            extracted_answer="lean4_kernel_ok",
            extraction_source="lean4",
            detail="Verified by Lean kernel with zero errors and no sorry/unauthorised axioms.",
            verifier_version=lean_version,
        )
    err_msg = (proc.stderr or proc.stdout or "non-zero exit").strip()[:400]
    return VerificationResult(
        verified=False,
        verification_level=VerificationLevel.UNVERIFIED,
        outcome="verified_fail",
        verifier_name="lean4_proof",
        extracted_answer=None,
        extraction_source="lean4",
        detail=f"Lean kernel rejected proof (rc={proc.returncode}): {err_msg}",
        verifier_version=lean_version,
    )
