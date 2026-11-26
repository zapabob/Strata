"""Generate the published Pagoda Bench task on a running local SC117 Strata server."""

import argparse
from ipaddress import ip_address
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit

import requests

from benchmark_pagoda import PROMPT_DIGEST, SOURCE, candidate, published_prompt


MODEL = "inkling-2-mini-sc117-sq-10"


def local_base(value):
    url = urlsplit(value)
    if (url.scheme != "http" or not url.hostname or not ip_address(url.hostname).is_loopback
            or url.username or url.password or url.path.rstrip("/") != "/v1"
            or url.query or url.fragment):
        raise ValueError("Use the running Strata server's loopback HTTP /v1 address")
    return value.rstrip("/")


def run(args):
    base = local_base(args.base_url)
    prompt = published_prompt()
    packet = dict(model=MODEL, messages=[dict(role="user", content=prompt)], max_tokens=args.max_tokens,
                  reasoning_effort=args.reasoning_effort, reasoning_budget_tokens=args.reasoning_budget,
                  temperature=args.temperature, seed=args.seed, stream=True, stream_options={"include_usage": True})
    args.out.mkdir(parents=True, exist_ok=False)
    protocol = {key: value for key, value in packet.items() if key != "messages"}
    protocol.update(source=SOURCE, published_prompt_sha256=PROMPT_DIGEST, system_prompt=None, base_url=base)
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")

    finish = None
    usage = None
    reasoning_chars = 0
    first_visible = None
    content = []
    error = None
    started = time.perf_counter()
    try:
        with requests.Session() as session, (args.out / "visible.txt").open(
            "x", encoding="utf-8", newline=""
        ) as visible:
            session.trust_env = False
            key = os.environ.get("STRATA_API_KEY")
            if key:
                session.headers["Authorization"] = f"Bearer {key}"
            models = session.get(base + "/models", allow_redirects=False, timeout=10)
            models.raise_for_status()
            if models.is_redirect or not any(item["id"] == MODEL for item in models.json()["data"]):
                raise RuntimeError("The local endpoint did not advertise the expected SC117 model")
            started = time.perf_counter()
            print("SC117 request submitted", flush=True)
            with session.post(base + "/chat/completions", json=packet, stream=True,
                              timeout=(10, 300), allow_redirects=False) as response:
                response.raise_for_status()
                if response.is_redirect:
                    raise RuntimeError("The local endpoint redirected the generation request")
                for line in response.iter_lines(chunk_size=256):
                    if not line.startswith(b"data: "):
                        continue
                    if line == b"data: [DONE]":
                        break
                    event = json.loads(line[6:])
                    if "error" in event:
                        raise RuntimeError("Strata reported a stream error")
                    if event.get("usage"):
                        usage = event["usage"]
                    for choice in event.get("choices", []):
                        delta = choice.get("delta", {})
                        reasoning_chars += len(delta.get("reasoning_content") or delta.get("reasoning") or "")
                        fragment = delta.get("content") or ""
                        if fragment:
                            if first_visible is None:
                                first_visible = time.perf_counter() - started
                                print(f"Visible output began after {first_visible:.1f} s", flush=True)
                            content.append(fragment)
                            visible.write(fragment)
                            visible.flush()
                        if choice.get("finish_reason"):
                            finish = choice["finish_reason"]
    except (requests.RequestException, ValueError, KeyError, RuntimeError) as exc:
        error = str(exc)
    html, strict, complete = candidate("".join(content))
    if html is not None:
        (args.out / "index.html").write_bytes(html.encode("utf-8"))
    result = dict(finish_reason=finish, usage=usage, generation_wall_seconds=time.perf_counter() - started,
                  first_visible_seconds=first_visible, reasoning_chars=reasoning_chars,
                  strict_html_envelope=strict, complete_document=complete,
                  html_bytes=len(html.encode("utf-8")) if html is not None else None, error=error)
    (args.out / "answer.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)
    return 0 if complete and finish and error is None else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-tokens", type=int, default=14000)
    parser.add_argument("--reasoning-budget", type=int, default=2304)
    parser.add_argument("--reasoning-effort", choices=("none", "minimal", "low"), default="minimal")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=47)
    args = parser.parse_args()
    if not 0 < args.reasoning_budget < args.max_tokens or not 0 <= args.temperature <= 2:
        parser.error("The reasoning budget must leave room for visible output")
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
