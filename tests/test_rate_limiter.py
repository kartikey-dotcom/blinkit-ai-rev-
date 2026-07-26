import pytest
import asyncio
import time
from backend.llm_rate_limiter import GoogleAIStudioRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_rpm_gap_enforcement():
    limiter = GoogleAIStudioRateLimiter(rpm_limit=60, min_gap_seconds=0.1)

    t0 = time.time()
    await limiter.acquire_slot(estimated_tokens=100)
    t1 = time.time()
    await limiter.acquire_slot(estimated_tokens=100)
    t2 = time.time()

    elapsed = t2 - t1
    assert elapsed >= 0.09  # Enforces ~0.1s min gap between calls


@pytest.mark.asyncio
async def test_rate_limiter_tpm_tracking():
    limiter = GoogleAIStudioRateLimiter(rpm_limit=60, tpm_limit=5000, min_gap_seconds=0.01)

    # Acquire slots up to token limit
    await limiter.acquire_slot(estimated_tokens=2000)
    await limiter.acquire_slot(estimated_tokens=2000)

    current_tpm = limiter.get_current_tpm()
    assert current_tpm == 4000
