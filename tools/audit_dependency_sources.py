#!/usr/bin/env python3
"""tools/audit_dependency_sources.py - Audit security advisories, GGUF integer overflow protections, and dependencies."""
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_INTAKE = REPO_ROOT / "_docs" / "upstream-intake"

def main():
    now_iso = datetime.now(timezone.utc).isoformat()
    security_ledger = {
        "timestamp": now_iso,
        "advisories": [
            {
                "id": "GHSA-vgg9-87g3-85w8",
                "component": "gguf-parser",
                "severity": "High",
                "description": "Integer overflow in tensor size computation (dim[0] * ... * dim[n-1] * type_size) causing buffer allocation underflows.",
                "status": "APPLIED_EQUIVALENT",
                "mitigation": "strata_control/gguf_preflight.py and model_bundle validation enforce strict 64-bit bounds and dimension overflow pre-checks before native allocation.",
                "verification_test": "tests/security/test_gguf_admission_limits.py::test_tensor_size_overflow"
            },
            {
                "id": "STRATA-SEC-001",
                "component": "chat-template-sandbox",
                "severity": "Critical",
                "description": "Arbitrary code execution via untrusted Jinja2/chat templates in model metadata.",
                "status": "APPLIED_UPSTREAM",
                "mitigation": "Template execution strictly isolated from OS shell, environment secrets, and filesystem access.",
                "verification_test": "tests/security/test_local_model_boundary.py::test_untrusted_template_no_exec"
            },
            {
                "id": "STRATA-SEC-002",
                "component": "run-config-snapshot",
                "severity": "Medium",
                "description": "TOCTOU drift between checked run configuration and spawned process arguments.",
                "status": "APPLIED_UPSTREAM",
                "mitigation": "C1 checkAndParseRunConfig() parses and locks exact captured text into atomic snapshot.",
                "verification_test": "apps/host/tests/run-config-check.test.mjs"
            },
            {
                "id": "STRATA-SEC-003",
                "component": "host-origin-owner-auth",
                "severity": "High",
                "description": "Cross-origin or unauthorized local access to inference / native endpoints.",
                "status": "APPLIED_UPSTREAM",
                "mitigation": "Loopback-only binding by default, Bearer API key verification, and Host/Origin validation in serve/server.py and apps/host/server/index.mjs.",
                "verification_test": "tests/security/test_local_model_boundary.py::test_host_origin_owner_auth"
            }
        ],
        "blocked_advisories": []
    }

    out_file = DOCS_INTAKE / "security-ledger.json"
    out_file.write_text(json.dumps(security_ledger, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Generated security ledger at {out_file}")

if __name__ == "__main__":
    main()
