"""Retry transient provider errors without changing eval inputs or scores."""
from types import SimpleNamespace

import pytest

import run_eval


class ProviderFailure(Exception):
    def __init__(self, code, details=None, headers=None):
        self.code = code
        self.details = details
        self.response = SimpleNamespace(headers=headers or {})


def test_retry_respects_google_retry_info_and_records_wait(monkeypatch):
    waits = []
    monkeypatch.setattr(run_eval.time, "sleep", waits.append)
    failure = ProviderFailure(429, {"error": {"details": [
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "20s"},
    ]}})
    attempts = []

    def call():
        attempts.append(1)
        if len(attempts) == 1:
            raise failure
        return "success"

    events = []
    result = run_eval.call_with_retries(call, max_retries=2, retry_delay=15, retry_events=events)

    assert result == "success"
    assert len(attempts) == 2
    assert waits == [21.0]
    assert events == [{"status": 429, "retry": 1, "wait_seconds": 21.0}]


def test_retries_stop_at_limit_and_increase_wait(monkeypatch):
    waits = []
    monkeypatch.setattr(run_eval.time, "sleep", waits.append)
    attempts = []

    def call():
        attempts.append(1)
        raise ProviderFailure(503)

    with pytest.raises(ProviderFailure):
        run_eval.call_with_retries(call, max_retries=2, retry_delay=2, retry_events=[])

    assert len(attempts) == 3
    assert waits == [2, 4]


@pytest.mark.parametrize("code", [400, 401, 403])
def test_permanent_errors_are_not_retried(monkeypatch, code):
    waits = []
    monkeypatch.setattr(run_eval.time, "sleep", waits.append)

    def call():
        raise ProviderFailure(code)

    events = []
    with pytest.raises(ProviderFailure):
        run_eval.call_with_retries(call, max_retries=3, retry_delay=15, retry_events=events)

    assert waits == []
    assert events == []


def test_disabled_retries_make_one_attempt_and_never_wait(monkeypatch):
    waits = []
    monkeypatch.setattr(run_eval.time, "sleep", waits.append)

    def call():
        raise ProviderFailure(429)

    with pytest.raises(ProviderFailure):
        run_eval.call_with_retries(call, max_retries=0, retry_delay=15, retry_events=[])

    assert waits == []


def test_retry_after_header_is_respected_and_long_wait_is_split(monkeypatch):
    waits = []
    monkeypatch.setattr(run_eval.time, "sleep", waits.append)
    attempts = []

    def call():
        attempts.append(1)
        if len(attempts) == 1:
            raise ProviderFailure(503, headers={"Retry-After": "65"})
        return "success"

    result = run_eval.call_with_retries(call, max_retries=1, retry_delay=1, retry_events=[], max_retry_wait=90)

    assert result == "success"
    assert waits == [30, 30, 5]


def test_hours_long_retry_after_is_recorded_without_waiting(monkeypatch):
    waits = []
    monkeypatch.setattr(run_eval.time, "sleep", waits.append)
    events = []

    def call():
        raise ProviderFailure(429, headers={"Retry-After": "14130"})

    with pytest.raises(ProviderFailure):
        run_eval.call_with_retries(call, max_retries=3, retry_delay=15, retry_events=events)

    assert waits == []
    assert events == [{
        "status": 429, "retry": 1, "wait_seconds": 14130.0,
        "skipped": True, "reason": "retry_wait_exceeds_limit",
    }]
