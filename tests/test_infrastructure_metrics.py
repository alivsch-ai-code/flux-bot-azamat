"""Tests für src.infrastructure.metrics."""
from src.infrastructure.metrics import record_timing, get_stats


class TestMetrics:
    def test_record_and_get_stats(self):
        record_timing("test_op", 0.5)
        stats = get_stats()
        assert "test_op" in stats
        assert stats["test_op"]["count"] >= 1
        assert stats["test_op"]["last"] == 0.5
        assert stats["test_op"]["total"] >= 0.5

    def test_multiple_records_accumulate(self):
        record_timing("acc_test", 1.0)
        record_timing("acc_test", 2.0)
        stats = get_stats()
        assert stats["acc_test"]["count"] >= 2
        assert stats["acc_test"]["total"] >= 3.0

    def test_get_stats_returns_copy(self):
        record_timing("copy_test", 0.1)
        s1 = get_stats()
        s1["copy_test"]["count"] = 999
        assert get_stats()["copy_test"]["count"] != 999
