"""Loopback-guarded OpenAI-compatible HTTP client for local Strata servers.

Refuses non-loopback targets by default so TSI evaluation never transmits data
to external APIs without explicit user opt-in.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
import urllib.request

from . import DEFAULT_API_BASE_URL

LOGGER = logging.getLogger("strata.tsi.client")

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def validate_base_url(base_url: str, *, allow_non_loopback: bool = False) -> str:
    """Validate URL scheme and enforce loopback-only access by default."""
    cleaned = base_url.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r} in {base_url!r}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError(f"Missing hostname in URL: {base_url!r}")
    if not allow_non_loopback and host not in LOOPBACK_HOSTS:
        raise ValueError(
            f"Refusing non-loopback endpoint {host!r} by default. "
            "Pass --allow-non-loopback explicitly to opt in."
        )
    return cleaned


@dataclass(frozen=True)
class CompletionResponse:
    """Structured response and timing telemetry for one chat completion call."""

    content: str
    reasoning_content: str
    finish_reason: str | None
    model: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    wall_seconds: float
    prompt_per_second: float | None
    predicted_per_second: float | None
    timed_out: bool = False
    api_error: str | None = None


class LocalOpenAIClient:
    """Minimal stdlib OpenAI Chat Completions client targeting a local Strata server."""

    def __init__(
        self,
        base_url: str = DEFAULT_API_BASE_URL,
        *,
        api_key: str = "",
        timeout_s: float = 120.0,
        allow_non_loopback: bool = False,
    ) -> None:
        self.base_url = validate_base_url(base_url, allow_non_loopback=allow_non_loopback)
        self.api_key = api_key
        self.timeout_s = max(1.0, float(timeout_s))

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def fetch_models(self) -> list[str]:
        """Query GET /v1/models on the local server (best-effort)."""
        req = urllib.request.Request(f"{self.base_url}/v1/models", headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=min(10.0, self.timeout_s)) as resp:
                payload = json.loads(resp.read().decode("utf-8", errors="replace"))
            data = payload.get("data", [])
            if isinstance(data, list):
                return [str(item.get("id", "")) for item in data if isinstance(item, dict) and item.get("id")]
        except (OSError, URLError, ValueError) as exc:
            LOGGER.debug("GET /v1/models unavailable at %s: %s", self.base_url, exc)
        return []

    def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        max_tokens: int,
        model: str | None = None,
        temperature: float = 0.0,
        seed: int | None = 42,
        reasoning_effort: str | None = None,
    ) -> CompletionResponse:
        """Issue one non-streaming POST /v1/chat/completions request."""
        body: dict[str, Any] = {
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "stream": False,
        }
        if model:
            body["model"] = model
        if seed is not None:
            body["seed"] = int(seed)
        if reasoning_effort is not None and reasoning_effort != "":
            body["reasoning_effort"] = reasoning_effort

        raw_body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=raw_body,
            headers=self._headers(),
            method="POST",
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            elapsed = time.perf_counter() - t0
            data = json.loads(raw)
        except socket.timeout as exc:
            return CompletionResponse(
                content="",
                reasoning_content="",
                finish_reason=None,
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                wall_seconds=time.perf_counter() - t0,
                prompt_per_second=None,
                predicted_per_second=None,
                timed_out=True,
                api_error=f"socket timeout: {exc}",
            )
        except HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="replace")[:300]
            except OSError:
                pass
            return CompletionResponse(
                content="",
                reasoning_content="",
                finish_reason=None,
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                wall_seconds=time.perf_counter() - t0,
                prompt_per_second=None,
                predicted_per_second=None,
                api_error=f"HTTP {exc.code}: {err_body or exc.reason}",
            )
        except (URLError, OSError, ValueError) as exc:
            is_to = isinstance(getattr(exc, "reason", None), socket.timeout) or "timed out" in str(exc).lower()
            return CompletionResponse(
                content="",
                reasoning_content="",
                finish_reason=None,
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                wall_seconds=time.perf_counter() - t0,
                prompt_per_second=None,
                predicted_per_second=None,
                timed_out=is_to,
                api_error=f"request error: {exc}",
            )

        choices = data.get("choices") or []
        first = choices[0] if choices and isinstance(choices[0], dict) else {}
        msg = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = str(msg.get("content") or "")
        reasoning = str(msg.get("reasoning_content") or "")
        finish_reason = first.get("finish_reason")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        prompt_toks = int(usage.get("prompt_tokens") or 0)
        comp_toks = int(usage.get("completion_tokens") or 0)
        total_toks = int(usage.get("total_tokens") or (prompt_toks + comp_toks))
        timings = data.get("timings") if isinstance(data.get("timings"), dict) else {}
        pp_tps = float(timings["prompt_per_second"]) if timings.get("prompt_per_second") is not None else None
        tg_tps = float(timings["predicted_per_second"]) if timings.get("predicted_per_second") is not None else None

        return CompletionResponse(
            content=content,
            reasoning_content=reasoning,
            finish_reason=str(finish_reason) if finish_reason is not None else None,
            model=str(data.get("model") or model or ""),
            prompt_tokens=prompt_toks,
            completion_tokens=comp_toks,
            total_tokens=total_toks,
            wall_seconds=elapsed,
            prompt_per_second=pp_tps,
            predicted_per_second=tg_tps,
        )
