"""Tests für adaptive Debounce-Delays (Chat-Batching)."""

from src.presentation.telegram.handlers.chat_debounce import (
    DEBOUNCE_SECONDS,
    debounce_delay_seconds_for_count,
)


def test_debounce_immediate_at_five():
    assert debounce_delay_seconds_for_count(5) is None
    assert debounce_delay_seconds_for_count(10) is None


def test_debounce_sequence_matches_spec():
    assert debounce_delay_seconds_for_count(1) == DEBOUNCE_SECONDS[0] == 20
    assert debounce_delay_seconds_for_count(2) == DEBOUNCE_SECONDS[1] == 10
    assert debounce_delay_seconds_for_count(3) == DEBOUNCE_SECONDS[2] == 5
    assert debounce_delay_seconds_for_count(4) == DEBOUNCE_SECONDS[3] == 10
