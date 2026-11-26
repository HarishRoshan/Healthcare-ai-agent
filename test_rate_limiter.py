
from unittest.mock import patch

from aura_rate_limiter import SlidingWindowRateLimiter


def test_requests_within_limit():
    limiter = SlidingWindowRateLimiter()

    for _ in range(5):
        assert limiter.allow("user1", 5, 60) == (True, 0)


def test_excessive_requests_blocked():
    limiter = SlidingWindowRateLimiter()

    for _ in range(5):
        limiter.allow("user1", 5, 60)

    allowed, retry_after = limiter.allow("user1", 5, 60)

    assert allowed is False
    assert 1 <= retry_after <= 60


def test_independent_users():
    limiter = SlidingWindowRateLimiter()

    for _ in range(5):
        limiter.allow("user1", 5, 60)

    assert limiter.allow("user1", 5, 60)[0] is False
    assert limiter.allow("user2", 5, 60)[0] is True


def test_window_expiration():
    limiter = SlidingWindowRateLimiter()

    with patch("aura_rate_limiter.time.monotonic") as clock:

        clock.return_value = 100.0

        for _ in range(5):
            limiter.allow("user1", 5, 60)

        assert limiter.allow("user1", 5, 60)[0] is False

        clock.return_value = 161.0

        assert limiter.allow("user1", 5, 60) == (True, 0)


def test_memory_limit():
    limiter = SlidingWindowRateLimiter(max_keys=2)

    assert limiter.allow("user1", 5, 60)[0] is True
    assert limiter.allow("user2", 5, 60)[0] is True
    assert limiter.allow("user3", 5, 60)[0] is False

    assert len(limiter.requests) == 2


def test_expired_keys_removed():
    limiter = SlidingWindowRateLimiter(max_keys=2)

    with patch("aura_rate_limiter.time.monotonic") as clock:

        clock.return_value = 100.0

        limiter.allow("user1", 5, 60)
        limiter.allow("user2", 5, 60)

        clock.return_value = 161.0

        assert limiter.allow("user3", 5, 60)[0] is True
        assert len(limiter.requests) == 1
