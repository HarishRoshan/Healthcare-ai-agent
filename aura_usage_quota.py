
import os
import sqlite3

from pathlib import Path
from datetime import datetime, timezone
from contextlib import closing


DAILY_LIMIT = 50
MONTHLY_LIMIT = 1000

DATABASE_PATH = Path(
    os.environ.get(
        "AURA_USAGE_DB_PATH",
        str(Path(__file__).resolve().parent / "aura_usage.db"),
    )
)


class UsageQuotaExceeded(RuntimeError):
    """Raised when the global usage quota is exhausted."""


class UsageQuota:

    def __init__(
        self,
        db_path=DATABASE_PATH,
        daily_limit=DAILY_LIMIT,
        monthly_limit=MONTHLY_LIMIT,
    ):
        if daily_limit < 1 or monthly_limit < 1:
            raise ValueError("Quota limits must be positive")

        self.db_path = Path(db_path)
        self.daily_limit = daily_limit
        self.monthly_limit = monthly_limit

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.initialize_database()

    def initialize_database(self):

        with closing(sqlite3.connect(
            self.db_path, timeout=10
        )) as conn:

            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_counts (
                    period_type TEXT NOT NULL,
                    period_key TEXT NOT NULL,
                    request_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (period_type, period_key)
                )
            """)

            conn.commit()

    def reserve_request(self):

        now = datetime.now(timezone.utc)

        day = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")

        with closing(sqlite3.connect(
            self.db_path, timeout=10
        )) as conn:

            try:
                conn.execute("BEGIN IMMEDIATE")

                daily_count = self._get_count(
                    conn, "daily", day
                )

                monthly_count = self._get_count(
                    conn, "monthly", month
                )

                if daily_count >= self.daily_limit:
                    raise UsageQuotaExceeded(
                        "Daily usage quota exceeded"
                    )

                if monthly_count >= self.monthly_limit:
                    raise UsageQuotaExceeded(
                        "Monthly usage quota exceeded"
                    )

                self._increment(conn, "daily", day)
                self._increment(conn, "monthly", month)

                conn.commit()

                return {
                    "daily_used": daily_count + 1,
                    "monthly_used": monthly_count + 1,
                    "daily_limit": self.daily_limit,
                    "monthly_limit": self.monthly_limit,
                }

            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def _get_count(conn, period_type, period_key):

        row = conn.execute("""
            SELECT request_count
            FROM usage_counts
            WHERE period_type = ?
            AND period_key = ?
        """, (period_type, period_key)).fetchone()

        return row[0] if row else 0

    @staticmethod
    def _increment(conn, period_type, period_key):

        conn.execute("""
            INSERT INTO usage_counts (
                period_type,
                period_key,
                request_count
            )
            VALUES (?, ?, 1)
            ON CONFLICT(period_type, period_key)
            DO UPDATE SET
                request_count = request_count + 1
        """, (period_type, period_key))
