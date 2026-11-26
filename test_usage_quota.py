
from concurrent.futures import ThreadPoolExecutor

import pytest

from aura_usage_quota import (
    UsageQuota,
    UsageQuotaExceeded,
)


def test_request_allowed(tmp_path):
    quota = UsageQuota(tmp_path / "usage.db")

    result = quota.reserve_request()

    assert result["daily_used"] == 1
    assert result["monthly_used"] == 1


def test_daily_limit(tmp_path):
    quota = UsageQuota(
        tmp_path / "usage.db",
        daily_limit=2,
        monthly_limit=10,
    )

    quota.reserve_request()
    quota.reserve_request()

    with pytest.raises(UsageQuotaExceeded):
        quota.reserve_request()


def test_monthly_limit(tmp_path):
    quota = UsageQuota(
        tmp_path / "usage.db",
        daily_limit=10,
        monthly_limit=2,
    )

    quota.reserve_request()
    quota.reserve_request()

    with pytest.raises(UsageQuotaExceeded):
        quota.reserve_request()


def test_quota_persistence(tmp_path):
    path = tmp_path / "usage.db"

    first = UsageQuota(path)
    first.reserve_request()

    second = UsageQuota(path)
    result = second.reserve_request()

    assert result["daily_used"] == 2
    assert result["monthly_used"] == 2


def test_independent_databases(tmp_path):
    first = UsageQuota(tmp_path / "first.db")
    second = UsageQuota(tmp_path / "second.db")

    first.reserve_request()

    result = second.reserve_request()

    assert result["daily_used"] == 1


def test_invalid_limits(tmp_path):
    with pytest.raises(ValueError):
        UsageQuota(
            tmp_path / "usage.db",
            daily_limit=0,
        )

    with pytest.raises(ValueError):
        UsageQuota(
            tmp_path / "usage.db",
            monthly_limit=0,
        )


def test_concurrent_requests(tmp_path):
    quota = UsageQuota(
        tmp_path / "usage.db",
        daily_limit=5,
        monthly_limit=100,
    )

    def reserve():
        try:
            quota.reserve_request()
            return True
        except UsageQuotaExceeded:
            return False

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(
            pool.map(lambda _: reserve(), range(20))
        )

    assert results.count(True) == 5
    assert results.count(False) == 15


def test_rejected_request_not_counted(tmp_path):
    path = tmp_path / "usage.db"

    quota = UsageQuota(
        path,
        daily_limit=1,
        monthly_limit=10,
    )

    quota.reserve_request()

    with pytest.raises(UsageQuotaExceeded):
        quota.reserve_request()

    quota = UsageQuota(
        path,
        daily_limit=10,
        monthly_limit=10,
    )

    result = quota.reserve_request()

    assert result["daily_used"] == 2
    assert result["monthly_used"] == 2
