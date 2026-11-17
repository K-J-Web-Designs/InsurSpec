from __future__ import annotations

import pytest
from insur_spec.core.circuit_breaker import CircuitBreaker


def test_circuit_breaker_trips_on_5th_strike():
    cb = CircuitBreaker(max_strikes=5)
    repeating_error = "SyntaxError: invalid syntax in claims_handler.py at line 42"

    for i in range(1, 5):
        report = cb.record_failure(repeating_error, remedy_attempted=f"Edit line 4{i}")
        assert report.tripped is False
        assert report.strike_count == i

    # 5th strike trips circuit breaker
    final_report = cb.record_failure(repeating_error, remedy_attempted="Edit line 45")
    assert final_report.tripped is True
    assert final_report.strike_count == 5
    assert len(final_report.suggested_human_actions) > 0


def test_circuit_breaker_resets_on_success():
    cb = CircuitBreaker(max_strikes=5)
    cb.record_failure("Error A")
    cb.record_failure("Error A")
    assert cb.strike_count == 2

    cb.record_success()
    assert cb.strike_count == 0


def test_log_truncation():
    raw_log = "\n".join(f"Log line {i}" for i in range(250))
    truncated = CircuitBreaker.truncate_log(raw_log, max_lines=100)
    assert len(truncated.splitlines()) < 110
    assert "truncated by InsurSpec Token Governor" in truncated
