import asyncio
import time
from typing import Optional
from backend.config import GEMINI_RPM_LIMIT, GEMINI_TPM_LIMIT, GEMINI_REQUEST_GAP_SECONDS


class GoogleAIStudioRateLimiter:
    """
    Asynchronous Rate Limiter enforcing Google AI Studio Gemini API Limits:
    - 60 Requests Per Minute (RPM) => Minimum 1.0 second delay between requests.
    - 100,000 Input Tokens Per Minute (TPM) => Sliding token window tracking.
    """

    def __init__(self, rpm_limit: int = GEMINI_RPM_LIMIT, tpm_limit: int = GEMINI_TPM_LIMIT, min_gap_seconds: float = GEMINI_REQUEST_GAP_SECONDS):
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.min_gap_seconds = min_gap_seconds
        self.last_request_timestamp: float = 0.0
        self.token_history: list = []  # List of tuples: (timestamp, token_count)
        self._lock = asyncio.Lock()

    def _clean_token_history(self, current_time: float):
        """Purge token history entries older than 60 seconds."""
        cutoff = current_time - 60.0
        self.token_history = [(ts, tokens) for ts, tokens in self.token_history if ts > cutoff]

    def get_current_tpm(self) -> int:
        """Calculate current total input tokens consumed in the last 60 seconds."""
        now = time.time()
        self._clean_token_history(now)
        return sum(tokens for _, tokens in self.token_history)

    async def acquire_slot(self, estimated_tokens: int = 1500):
        """
        Acquires execution slot enforcing 60 RPM and 100K TPM budget.
        Pauses asynchronously if limits are approached to prevent HTTP 429 errors.
        """
        async with self._lock:
            now = time.time()

            # 1. Enforce 60 RPM Minimum Throttling Gap (1.0 second min gap)
            time_since_last = now - self.last_request_timestamp
            if time_since_last < self.min_gap_seconds:
                sleep_duration = self.min_gap_seconds - time_since_last
                await asyncio.sleep(sleep_duration)
                now = time.time()

            # 2. Enforce 100,000 TPM Token Window Limit
            self._clean_token_history(now)
            current_tpm = sum(tokens for _, tokens in self.token_history)

            if current_tpm + estimated_tokens > self.tpm_limit:
                # Calculate sleep duration until oldest token batch expires
                oldest_ts = self.token_history[0][0]
                wait_time = max(1.0, 60.0 - (now - oldest_ts) + 0.1)
                print(f"[RateLimiter Warning] Approaching 100K TPM limit ({current_tpm} + {estimated_tokens} > {self.tpm_limit}). Pausing for {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
                now = time.time()
                self._clean_token_history(now)

            # Record request timestamp and tokens
            self.last_request_timestamp = now
            self.token_history.append((now, estimated_tokens))
