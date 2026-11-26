
import math
import time
from collections import deque
from threading import Lock


class SlidingWindowRateLimiter:

    def __init__(self, max_keys=10000):
        self.requests = {}
        self.lock = Lock()
        self.max_keys = max_keys

    def allow(self, key, limit, window_seconds=60):

        with self.lock:
            now = time.monotonic()
            cutoff = now - window_seconds

            if key not in self.requests:

                # Remove inactive request histories
                if len(self.requests) >= self.max_keys:
                    expired = [
                        k for k, history in self.requests.items()
                        if not history or history[-1] <= cutoff
                    ]

                    for k in expired:
                        del self.requests[k]

                # Prevent unlimited memory growth
                if len(self.requests) >= self.max_keys:
                    return False, window_seconds

                self.requests[key] = deque()

            history = self.requests[key]

            # Remove expired requests
            while history and history[0] <= cutoff:
                history.popleft()

            # Reject requests exceeding the limit
            if len(history) >= limit:
                retry_after = math.ceil(
                    window_seconds - (now - history[0])
                )

                return False, max(1, retry_after)

            # Record the accepted request
            history.append(now)

            return True, 0
