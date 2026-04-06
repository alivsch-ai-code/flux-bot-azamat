import time

from src.presentation.http import http_routes


def test_rate_limited_blocks_after_threshold_and_resets_with_window():
    http_routes._rate_hits.clear()
    bucket = "test"
    key = "127.0.0.1"
    max_requests = 3
    window = 1

    assert http_routes._rate_limited(bucket, key, max_requests, window) is False
    assert http_routes._rate_limited(bucket, key, max_requests, window) is False
    assert http_routes._rate_limited(bucket, key, max_requests, window) is False
    # 4th hit in same window -> blocked
    assert http_routes._rate_limited(bucket, key, max_requests, window) is True

    time.sleep(1.05)
    # After window expiry should allow again
    assert http_routes._rate_limited(bucket, key, max_requests, window) is False

