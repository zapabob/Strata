"""Behavioral failure fixtures; IDs here are protocol stand-ins, never model inputs."""

from __future__ import annotations

import json

import pytest

from contracts import Exchange, EXPECTED, exact_answer, ids_sha, roundtrip, validate_input
from qa import Native, floor_error

FIRST = "DONE 3 3072 34000.0 1800.0 stop 0 0 0 0 0 0 0 0.0 3072 0"
CONTINUED = "DONE 3 3114 400.0 1800.0 stop 0 0 3074 0 0 0 0 0.0 40 0"
CANCEL = "DONE 1 3072 34000.0 50.0 cancel 0 0 0 0 0 0 0 0.0 3072 0"


def response(exchange: Exchange, done: str, fresh: int, tokens: tuple[int, ...] = (19, 23, 29)) -> dict:
    for n in range(512, fresh, 512):
        exchange.feed(f"PP {n} {fresh} 1000 100.0")
    exchange.feed(f"PP {fresh} {fresh} 2000 100.0")
    for token in tokens:
        exchange.feed(f"T {token}")
    exchange.feed(done)
    return exchange.finish()


def test_complete_3072_input_is_count_receipt_not_hash_proof() -> None:
    row = response(Exchange(3072), FIRST, 3072)
    assert row["submittedCount"] == row["nativePromptCount"] == row["nativeFreshReadCount"] == 3072
    assert row["generatedIds"] == [19, 23, 29]
    assert row["protocolCountReceipt"] and not row["cryptographicConsumedInputProof"]


def test_owner_reuse_and_cancel_boundaries() -> None:
    response(Exchange(3072), FIRST, 3072)
    response(Exchange(3114, 3072, 3075), CONTINUED, 40)
    with pytest.raises(ValueError, match="reuse boundary"):
        response(Exchange(3114), CONTINUED, 40)  # different owner must read all
    response(Exchange(3072, cancel=True), CANCEL, 3072, (19,))
    with pytest.raises(ValueError, match="reuse boundary"):
        response(Exchange(3114), CONTINUED, 40)  # post-cancel and restart must not retain owner state


@pytest.mark.parametrize(
    "done,match",
    [
        (FIRST.replace("3072 34000", "3071 34000"), "truncated"),
        (FIRST.replace("3072 0", "3071 0"), "fresh"),
        (FIRST.replace("DONE 3", "DONE 2"), "generated"),
        (FIRST.replace(" stop ", " nonfinite "), "finish"),
        (FIRST.replace("34000.0", "nan"), "nonfinite"),
        (FIRST.replace("1800.0", "inf"), "nonfinite"),
    ],
)
def test_invalid_native_receipts_fail(done: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        response(Exchange(3072), done, 3072)


def test_empty_output_is_failure_even_with_correct_counts() -> None:
    with pytest.raises(ValueError, match="empty"):
        response(Exchange(3072), FIRST.replace("DONE 3", "DONE 0"), 3072, ())


@pytest.mark.parametrize("line", ["ERR CUDA nonfinite logits", "PP 1 3072 nan 2", "PP 3073 3072 2 3", "T -1", "DONE 0"])
def test_malformed_and_native_error_lines_fail(line: str) -> None:
    with pytest.raises(ValueError):
        Exchange(3072).feed(line)


def test_cancellation_must_acknowledge_actual_stop() -> None:
    with pytest.raises(ValueError, match="finish"):
        response(Exchange(3072, cancel=True), FIRST, 3072)
    with pytest.raises(ValueError, match="finish"):
        response(Exchange(3072), CANCEL, 3072, (19,))


def test_pp_counts_fresh_not_capacity_or_reused_prefix() -> None:
    with pytest.raises(ValueError, match="PP does not account"):
        response(Exchange(3114, 3072, 3075), CONTINUED, 3114)
    e = Exchange(3072)
    e.feed("PP 1024 3072 2 3")
    with pytest.raises(ValueError, match="regression"):
        e.feed("PP 512 3072 3 4")


def test_input_never_silently_truncated_or_output_budget_lowered() -> None:
    validate_input([1] * 3072, 3072)
    for ids, count, budget in (
        ([1] * 3071, 3072, 128),
        ([1] * 3966, 3966, 128),
        ([1] * 3072, 3072, 127),
        ([], 0, 128),
        ([True], 1, 128),
    ):
        with pytest.raises(ValueError):
            validate_input(ids, count, budget)
    assert ids_sha([1, 2]) != ids_sha([2, 1])


def test_roundtrip_rejects_lossy_encoder() -> None:
    class Lossy:
        def encode(self, text: str, parse_special: bool) -> list[int]:
            return [1]

        def decode(self, ids: list[int], errors: str) -> str:
            return "lost suffix"

    with pytest.raises(ValueError, match="roundtrip"):
        roundtrip(Lossy(), "original complete input")


def test_retrieval_oracle_accepts_only_exact_three_pairs() -> None:
    good = json.dumps(EXPECTED)
    assert exact_answer(good + "<|im_end|>", "<|im_end|>")
    for bad in (
        "reasoning " + good,
        "<think>" + good + "</think>",
        "```json\n" + good + "\n```",
        good + good,
        json.dumps({**EXPECTED, "extra": "value"}),
        json.dumps({**EXPECTED, "middle": "wrong"}),
        '{"begin":"wrong",' + good[1:],
        "",
    ):
        assert not exact_answer(bad, "<|im_end|>")


@pytest.mark.parametrize("key,minimum", [("available_ram", 3), ("commit_headroom", 4), ("C_free", 5), ("H_free", 10)])
def test_every_resource_floor_is_enforced_at_exact_boundary(key: str, minimum: int) -> None:
    r = {"available_ram": 3 * 1024**3, "commit_headroom": 4 * 1024**3, "C_free": 5 * 1024**3, "H_free": 10 * 1024**3}
    assert floor_error(r) is None
    r[key] = minimum * 1024**3 - 1
    assert floor_error(r) == key + " floor"


def test_request_records_failed_retrieval_without_reclassifying_it(monkeypatch: object) -> None:
    """Exercise the same request helper used at runtime; no process/model/tokenizer created."""
    from pathlib import Path
    import qa

    records = []
    monkeypatch.setattr(qa, "save", lambda path, row: records.append(dict(row)))
    native = object.__new__(Native)
    native.out, native.label = Path("fixture-only"), "fixture"
    sent = []
    native.send = sent.append
    lines = iter(["PP 3 3 1 1", "T 19", "DONE 1 3 1 1 stop 0 0 0 0 0 0 0 0.0 3 0"])
    native.line = lambda: next(lines)

    class Text:
        tokens = ["<|im_end|>"]
        special_ids = {"tokenizer.ggml.eos_token_id": 0}

        def decode(self, ids: list[int], errors: str) -> str:
            return '{"begin":"ALPHA7K","middle":"wrong","end":"CHARLIE4P"}'

    prompt = dict(ids=[1, 2, 3], actualInputCount=3, orderedIdsSHA256=ids_sha([1, 2, 3]))
    result = native.request("retrieval-fixture", prompt, "a" * 64, Text())
    assert result["protocolPassed"] and result["retrievalPassed"] is False
    assert result["status"] == records[-1]["status"] == "RETRIEVAL_FAIL"
    assert records[0]["status"] == "IN_PROGRESS"
    assert sent == ["GEN 128 cache_scope=" + "a" * 64 + " 1,2,3"]


@pytest.mark.parametrize("stalls", [False, True])
def test_owned_cleanup_sends_protocol_stop_and_eof_before_handle_fallback(monkeypatch: object, stalls: bool) -> None:
    from pathlib import Path
    import subprocess
    import qa

    events = []
    monkeypatch.setattr(qa, "save", lambda path, row: None)

    class Stream:
        def close(self) -> None:
            events.append("close")

    class Process:
        stdin = Stream()
        returncode = None

        def poll(self) -> int | None:
            return self.returncode

        def wait(self, timeout: int) -> int:
            events.append("wait")
            if stalls and "terminate-held-handle" not in events:
                raise subprocess.TimeoutExpired("fixture only", timeout)
            self.returncode = 0
            return 0

        def terminate(self) -> None:
            events.append("terminate-held-handle")

    native = object.__new__(Native)
    native.out, native.label = Path("fixture-only"), "fixture"
    native.closed, native.record, native.errors, native.threads = False, {}, [], []
    native.proc, native.samples, native.sent = Process(), Stream(), Stream()
    native.send = events.append
    row = native.close()
    assert events[:3] == ["STOP", "close", "wait"]
    assert ("terminate-held-handle" in events) == stalls
    assert row["normalStopAttempted"] and row["ownedProcessReaped"] and row["exitCode"] == 0


def test_unscoped_gen_omits_carrier_after_populated_scoped_request(monkeypatch: object) -> None:
    from pathlib import Path
    import qa

    monkeypatch.setattr(qa, "save", lambda path, row: None)
    native = object.__new__(Native)
    native.out, native.label = Path("fixture-only"), "fixture"
    sent = []
    native.send = sent.append
    lines = iter(["PP 3 3 1 1", "T 19", "DONE 1 3 1 1 stop 0 0 0 0 0 0 0 0.0 3 0"] * 2)
    native.line = lambda: next(lines)

    class Text:
        tokens = ["<|im_end|>"]
        special_ids = {"tokenizer.ggml.eos_token_id": 0}

        def decode(self, ids: list[int], errors: str) -> str:
            return json.dumps(EXPECTED)

    prompt = dict(ids=[1, 2, 3], actualInputCount=3, orderedIdsSHA256=ids_sha([1, 2, 3]))
    native.request("seed-owner-B", prompt, "b" * 64, Text())
    row = native.request("missing-identity-unscoped", prompt, None, Text())
    assert sent[-1] == "GEN 128 1,2,3"
    assert "cache_scope" not in sent[-1]
    assert row["scopeCarrierPresent"] is False and row["nativeReuseCount"] == 0
    assert row["nativeFreshReadCount"] == row["submittedCount"] == 3


def test_all_seven_cases_including_unscoped_are_mandatory() -> None:
    import qa

    rows = [dict(name=name, protocolPassed=True, retrievalPassed=True,
                 scopeCarrierPresent=name != "missing-identity-unscoped",
                 nativeReuseCount=0, nativeFreshReadCount=3071, submittedCount=3071) for name in qa.CASES]
    qa.require_cases(rows)
    with pytest.raises(ValueError, match="mandatory"):
        qa.require_cases([r for r in rows if r["name"] != "missing-identity-unscoped"])
    rows[3]["scopeCarrierPresent"] = True
    with pytest.raises(ValueError, match="unscoped"):
        qa.require_cases(rows)


def activity_snapshot(engines: list | None = None, turns: int = 0, running: int = 0, waiting: int = 0) -> dict:
    return dict(engineProcesses=[] if engines is None else engines,
                hosts=[dict(activeTurns=turns, runningRequests=running, queuedRequests=waiting)])


@pytest.mark.parametrize("snapshot", [
    activity_snapshot([dict(pid=18608, created=123.0, owned=False)]),
    activity_snapshot(turns=1), activity_snapshot(running=1), activity_snapshot(waiting=1),
    {}, activity_snapshot([dict(pid=18608, created=123.0)]),
    dict(engineProcesses=[], hosts=[dict(activeTurns=0, runningRequests=None, queuedRequests=0)]),
])
def test_activity_preflight_refuses_engine_or_host_activity_and_unknown_telemetry(snapshot: dict) -> None:
    import qa

    guard = qa.ActivityGuard(reader=lambda: snapshot)
    with pytest.raises(ValueError, match="activity"):
        guard.preflight()


def test_activity_only_exempts_verified_owned_descendants() -> None:
    import qa

    qa.ActivityGuard(reader=lambda: activity_snapshot([dict(pid=1, created=12.0, owned=True)])).preflight()


@pytest.mark.parametrize("error", [OSError("private details"), TimeoutError("private endpoint")])
def test_activity_telemetry_exception_is_fail_closed_and_private(error: Exception) -> None:
    import qa

    def failed() -> dict:
        raise error

    with pytest.raises(ValueError, match="activity") as observed:
        qa.ActivityGuard(reader=failed).preflight()
    assert "private" not in str(observed.value)


@pytest.mark.parametrize("emergency", ["engine", "host", "telemetry"])
def test_production_controller_callbacks_signal_abort_then_owned_job_fallback(emergency: str) -> None:
    import qa

    now, writes, state = [0.0], [], [activity_snapshot()]

    def read() -> dict:
        if state[0] is None:
            raise OSError("private endpoint")
        return state[0]

    healthy = dict(available_ram=4 * 1024**3, commit_headroom=5 * 1024**3,
                   C_free=6 * 1024**3, H_free=11 * 1024**3)
    callbacks = qa.GuardCallbacks(
        qa.ActivityGuard(reader=read), resources=lambda: healthy, gpu=lambda: {}, clock=lambda: now[0],
        abort=lambda row: writes.append(row), sample_log=lambda row: None,
    )
    callbacks.preflight()
    callbacks.sample(None)
    state[0] = (activity_snapshot([dict(pid=18608, created=123.0, owned=False)]) if emergency == "engine"
                else activity_snapshot(running=1) if emergency == "host" else None)
    now[0] = 1.0
    callbacks.sample(None)
    assert len(writes) == 1 and writes[0]["normalStopGraceSeconds"] == 15
    assert "activity" in writes[0]["reason"]
    assert callbacks.tick() is None  # worker sees abort marker and sends STOP/EOF
    now[0] = 16.0
    assert callbacks.tick() is not None  # consumed by run_owned: reap ONLY its held Job
    callbacks.sample(None)
    assert len(writes) == 1  # never clear a latched abort when activity later vanishes


def test_production_controller_preflight_precedes_any_child_creation(monkeypatch: object) -> None:
    from pathlib import Path
    import qa
    import perf131k.windows_job as job

    calls = []
    monkeypatch.setattr(qa, "save", lambda path, row: None)
    monkeypatch.setattr(qa, "cpu_admit", lambda: {})
    monkeypatch.setattr(qa, "ActivityGuard", lambda: qa_guard)
    # Keep the fixture explicit: a failing preflight must return before GO or run_owned.
    class Refuse:
        def preflight(self) -> None:
            calls.append("preflight")
            raise ValueError("activity: external engine")

    qa_guard = Refuse()
    monkeypatch.setattr(job, "run_owned", lambda *args, **kwargs: calls.append("created"))
    assert qa.execute(Path("fixture-component"), Path("fixture-output")) == 1
    assert calls == ["preflight"]


@pytest.mark.parametrize("invalid", [None, float("nan"), True])
def test_controller_resource_telemetry_loss_also_latches_abort(invalid: object) -> None:
    import qa

    r = dict(available_ram=4 * 1024**3, commit_headroom=5 * 1024**3,
             C_free=6 * 1024**3, H_free=11 * 1024**3)
    writes = []
    callbacks = qa.GuardCallbacks(
        qa.ActivityGuard(reader=activity_snapshot), resources=lambda: dict(r), gpu=lambda: {},
        abort=writes.append, sample_log=lambda row: None,
    )
    callbacks.preflight()
    r["available_ram"] = invalid
    observed = callbacks.sample(None)
    assert writes[0]["reason"] == "resource telemetry unavailable"
    assert observed["resourceTelemetryUnavailable"] and observed["resourceValues"] == "last-known"


@pytest.mark.parametrize("name", ["strata.exe", "strata-q36.exe", "llama-server.exe"])
def test_production_reader_uses_identity_ancestry_not_pid_allowlists(monkeypatch: object, name: str) -> None:
    from types import SimpleNamespace
    import sys
    import activity

    root = SimpleNamespace(pid=900, create_time=lambda: 10.0)
    target = SimpleNamespace(pid=18608, info={"name": name}, create_time=lambda: 20.0, parents=lambda: [])
    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(
        Process=lambda pid: root, process_iter=lambda *args, **kwargs: [target]))
    monkeypatch.setitem(sys.modules, "installed_state", SimpleNamespace(shells=lambda: []))
    external = activity.read_snapshot()
    assert external["engineProcesses"][0]["owned"] is False
    with pytest.raises(ValueError, match="activity"):
        activity.ActivityGuard(reader=lambda: external).preflight()
    target.parents = lambda: [root]
    activity.ActivityGuard(reader=activity.read_snapshot).preflight()
    # Recycled ancestor PID with another creation time does not become owned.
    target.parents = lambda: [SimpleNamespace(pid=900, create_time=lambda: 9.0)]
    with pytest.raises(ValueError, match="activity"):
        activity.ActivityGuard(reader=activity.read_snapshot).preflight()


def test_production_reader_resolves_installed_host_readonly_and_validates_counts(monkeypatch: object) -> None:
    from types import SimpleNamespace
    import sys
    import activity

    root = SimpleNamespace(pid=900, create_time=lambda: 10.0)
    shell = SimpleNamespace(pid=901, info={"name": "strata-desktop.exe"},
                            create_time=lambda: 11.0, is_running=lambda: True)
    monkeypatch.setitem(sys.modules, "psutil", SimpleNamespace(
        Process=lambda pid: root, process_iter=lambda *args, **kwargs: [shell]))
    routes = []

    def get(base: str, route: str) -> dict:
        routes.append(route)
        return {"turns": []} if route == "/api/chat/active" else {"stats": {"running": 1, "waiting": 0}}

    monkeypatch.setitem(sys.modules, "installed_state", SimpleNamespace(
        shells=lambda: [shell], endpoint=lambda process: "http://127.0.0.1:1", get=get))
    with pytest.raises(ValueError, match="activity"):
        activity.ActivityGuard(reader=activity.read_snapshot).preflight()
    assert routes == ["/api/chat/active", "/api/serving"]
