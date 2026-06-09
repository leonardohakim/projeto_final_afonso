import pytest

import breakers
from breakers import CircuitBreaker


def test_successful_call_keeps_breaker_closed():
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=10)

    result = cb.call(lambda: "ok")

    assert result == "ok"
    assert cb.fail_count == 0
    assert cb.opened_at is None


def test_failure_increments_fail_count_before_threshold(monkeypatch):
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=10)
    monkeypatch.setattr(breakers.time, "time", lambda: 100.0)

    def fail():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        cb.call(fail)

    assert cb.fail_count == 1
    assert cb.opened_at is None


def test_opens_after_reaching_failure_threshold(monkeypatch):
    cb = CircuitBreaker(failure_threshold=2, recovery_seconds=30)
    monkeypatch.setattr(breakers.time, "time", lambda: 1234.0)

    def fail():
        raise ValueError("boom")

    for _ in range(2):
        with pytest.raises(ValueError, match="boom"):
            cb.call(fail)

    assert cb.fail_count == 2
    assert cb.opened_at == 1234.0


def test_open_breaker_blocks_calls_inside_recovery_window(monkeypatch):
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=30)
    cb.opened_at = 100.0
    cb.fail_count = 1
    monkeypatch.setattr(breakers.time, "time", lambda: 120.0)

    called = False

    def downstream():
        nonlocal called
        called = True
        return "should not run"

    with pytest.raises(RuntimeError, match="Circuit open"):
        cb.call(downstream)

    assert called is False


def test_half_open_allows_successful_probe_after_timeout(monkeypatch):
    cb = CircuitBreaker(failure_threshold=1, recovery_seconds=30)
    cb.opened_at = 100.0
    cb.fail_count = 1
    monkeypatch.setattr(breakers.time, "time", lambda: 131.0)

    result = cb.call(lambda: "recovered")

    assert result == "recovered"
    assert cb.fail_count == 0
    assert cb.opened_at is None


def test_half_open_probe_failure_restarts_counter(monkeypatch):
    cb = CircuitBreaker(failure_threshold=3, recovery_seconds=30)
    cb.opened_at = 100.0
    cb.fail_count = 2
    monkeypatch.setattr(breakers.time, "time", lambda: 140.0)

    def fail_again():
        raise ValueError("probe failed")

    with pytest.raises(ValueError, match="probe failed"):
        cb.call(fail_again)

    assert cb.fail_count == 3
    assert cb.opened_at == 140.0