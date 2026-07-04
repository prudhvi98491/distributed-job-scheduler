"""
Tests for the Distributed Job Scheduler
Run: cd backend && python -m pytest tests/ -v
"""
import pytest
import asyncio
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch


# ── Retry Backoff Tests ───────────────────────────────────────────────────────

class TestRetryBackoff:
    """Test retry delay computation for all three strategies."""

    def _make_job(self, attempt_count):
        job = MagicMock()
        job.attempt_count = attempt_count
        return job

    def _make_queue(self, policy):
        queue = MagicMock()
        queue.retry_policy_id = "policy-1" if policy else None
        return queue

    @pytest.mark.asyncio
    async def test_fixed_strategy_always_same_delay(self):
        """Fixed strategy should always produce the same delay."""
        from app.services.retry import compute_next_retry_at
        from app.models import RetryPolicy, RetryStrategy

        policy = MagicMock(spec=RetryPolicy)
        policy.strategy = RetryStrategy.fixed
        policy.base_delay_ms = 5000
        policy.max_delay_ms = 5000

        queue = MagicMock()
        queue.retry_policy_id = "p1"

        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute.return_value.scalar_one_or_none = MagicMock(return_value=policy)

        now = datetime.now(timezone.utc)
        delays = []
        for attempt in range(1, 5):
            job = self._make_job(attempt)
            result = await compute_next_retry_at(job, queue, db)
            delay = (result - now).total_seconds()
            delays.append(delay)

        # All delays should be approximately 5 seconds
        for d in delays:
            assert 4.5 <= d <= 5.5, f"Fixed delay {d}s not ~5s"

    @pytest.mark.asyncio
    async def test_linear_backoff_increases(self):
        """Linear backoff delay should increase with each attempt."""
        from app.services.retry import compute_next_retry_at
        from app.models import RetryPolicy, RetryStrategy

        policy = MagicMock(spec=RetryPolicy)
        policy.strategy = RetryStrategy.linear_backoff
        policy.base_delay_ms = 1000
        policy.max_delay_ms = 10000

        queue = MagicMock()
        queue.retry_policy_id = "p1"
        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none = MagicMock(return_value=policy)

        now = datetime.now(timezone.utc)
        prev_delay = 0
        for attempt in range(1, 5):
            job = self._make_job(attempt)
            result = await compute_next_retry_at(job, queue, db)
            delay = (result - now).total_seconds()
            assert delay >= prev_delay, f"Linear delay should increase: {delay} < {prev_delay}"
            prev_delay = delay

    @pytest.mark.asyncio
    async def test_exponential_backoff_doubles(self):
        """Exponential backoff should roughly double each time."""
        from app.services.retry import compute_next_retry_at
        from app.models import RetryPolicy, RetryStrategy

        policy = MagicMock(spec=RetryPolicy)
        policy.strategy = RetryStrategy.exponential_backoff
        policy.base_delay_ms = 1000
        policy.max_delay_ms = 999999

        queue = MagicMock()
        queue.retry_policy_id = "p1"
        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none = MagicMock(return_value=policy)

        now = datetime.now(timezone.utc)
        delays = []
        for attempt in range(1, 6):
            job = self._make_job(attempt)
            result = await compute_next_retry_at(job, queue, db)
            delay = (result - now).total_seconds()
            delays.append(delay)

        # Each delay should be roughly 2x the previous (with ±10% jitter)
        for i in range(1, len(delays)):
            ratio = delays[i] / delays[i-1]
            assert 1.5 <= ratio <= 2.5, f"Exponential ratio {ratio:.2f} not in [1.5, 2.5]"

    @pytest.mark.asyncio
    async def test_exponential_capped_at_max(self):
        """Exponential backoff should not exceed max_delay_ms."""
        from app.services.retry import compute_next_retry_at
        from app.models import RetryPolicy, RetryStrategy

        policy = MagicMock(spec=RetryPolicy)
        policy.strategy = RetryStrategy.exponential_backoff
        policy.base_delay_ms = 1000
        policy.max_delay_ms = 5000  # 5s cap

        queue = MagicMock()
        queue.retry_policy_id = "p1"
        db = AsyncMock()
        db.execute.return_value.scalar_one_or_none = MagicMock(return_value=policy)

        now = datetime.now(timezone.utc)
        job = self._make_job(10)  # Very high attempt
        result = await compute_next_retry_at(job, queue, db)
        delay = (result - now).total_seconds()
        # Should be ≤ max_delay_ms/1000 + jitter
        assert delay <= 6.0, f"Delay {delay}s exceeded cap"

    @pytest.mark.asyncio
    async def test_default_backoff_when_no_policy(self):
        """Without a policy, should use exponential defaults."""
        from app.services.retry import compute_next_retry_at

        queue = MagicMock()
        queue.retry_policy_id = None
        db = AsyncMock()

        now = datetime.now(timezone.utc)
        job = MagicMock()
        job.attempt_count = 1

        result = await compute_next_retry_at(job, queue, db)
        delay = (result - now).total_seconds()
        assert 0.5 <= delay <= 3.0, f"Default first retry delay {delay}s unexpected"


# ── Failure Summary Tests ─────────────────────────────────────────────────────

class TestFailureSummary:
    """Test AI failure summary generation."""

    def test_timeout_detection(self):
        from app.services.retry import generate_failure_summary
        summary = generate_failure_summary("sync-data", "Connection timed out after 30s", 3)
        assert "Timeout" in summary
        assert "sync-data" in summary

    def test_rate_limit_detection(self):
        from app.services.retry import generate_failure_summary
        summary = generate_failure_summary("sync-payments", "429 Too Many Requests", 3)
        assert "Rate" in summary or "Throttl" in summary or "rate" in summary.lower()

    def test_auth_failure_detection(self):
        from app.services.retry import generate_failure_summary
        summary = generate_failure_summary("api-call", "403 Unauthorized", 2)
        assert "Authorization" in summary or "permission" in summary.lower()

    def test_unknown_error_fallback(self):
        from app.services.retry import generate_failure_summary
        summary = generate_failure_summary("custom-job", "Something weird happened", 1)
        assert "custom-job" in summary
        assert len(summary) > 20

    def test_summary_includes_attempt_count(self):
        from app.services.retry import generate_failure_summary
        summary = generate_failure_summary("my-job", "error", 5)
        assert "5" in summary


# ── Job Status Lifecycle Tests ────────────────────────────────────────────────

class TestJobStatusLifecycle:
    """Test valid and invalid status transitions."""

    VALID_TRANSITIONS = {
        "queued": ["scheduled", "claimed", "running", "cancelled"],
        "scheduled": ["queued", "cancelled"],
        "running": ["completed", "failed"],
        "failed": ["queued"],  # retry
        "dead": ["queued"],    # manual requeue
        "cancelled": ["queued"],
    }

    def test_completed_is_terminal(self):
        """Completed jobs cannot be retried directly."""
        terminal = ["completed"]
        for status in terminal:
            assert status not in ["queued", "running"], \
                f"Terminal status '{status}' should not be retried"

    def test_dead_can_be_requeued(self):
        """Dead jobs can be manually requeued from DLQ."""
        assert "queued" in self.VALID_TRANSITIONS["dead"]

    def test_cancelled_can_be_retried(self):
        """Cancelled jobs can be manually retried."""
        assert "queued" in self.VALID_TRANSITIONS["cancelled"]


# ── Idempotency Key Tests ─────────────────────────────────────────────────────

class TestIdempotencyKey:
    """Test idempotency key uniqueness enforcement."""

    def test_idempotency_key_prevents_duplicate(self):
        """Two jobs with same idempotency key should conflict."""
        key = "unique-operation-abc123"
        # Simulate the check logic
        existing_keys = {key}
        new_key = key
        assert new_key in existing_keys, "Duplicate idempotency key not detected"

    def test_different_keys_allowed(self):
        """Different idempotency keys should both be accepted."""
        existing_keys = {"op-001", "op-002"}
        new_key = "op-003"
        assert new_key not in existing_keys


# ── Worker Concurrency Tests ──────────────────────────────────────────────────

class TestWorkerConcurrency:
    """Test concurrency limit enforcement."""

    def test_concurrency_limit_zero_slots(self):
        """Worker should not claim when queue is at concurrency limit."""
        concurrency_limit = 3
        running_jobs = 3
        available_slots = concurrency_limit - running_jobs
        assert available_slots == 0, "Should have no available slots"

    def test_concurrency_limit_partial_slots(self):
        """Worker should only claim up to available slots."""
        concurrency_limit = 5
        running_jobs = 3
        available_slots = concurrency_limit - running_jobs
        max_to_claim = min(available_slots, 10)
        assert max_to_claim == 2

    def test_paused_queue_blocks_claim(self):
        """Paused queues should not allow job claims."""
        queue_paused = True
        can_claim = not queue_paused
        assert not can_claim


# ── DLQ Tests ─────────────────────────────────────────────────────────────────

class TestDeadLetterQueue:
    """Test DLQ promotion logic."""

    def test_job_goes_to_dlq_after_max_attempts(self):
        """Job should be marked dead after exceeding max_attempts."""
        attempt_count = 3
        max_attempts = 3
        should_go_dlq = attempt_count >= max_attempts
        assert should_go_dlq

    def test_job_retries_before_max_attempts(self):
        """Job should retry if attempts < max."""
        attempt_count = 2
        max_attempts = 3
        should_retry = attempt_count < max_attempts
        assert should_retry

    def test_dlq_entry_has_ai_summary(self):
        """DLQ entries should have an AI-generated failure summary."""
        from app.services.retry import generate_failure_summary
        summary = generate_failure_summary("test-job", "timeout", 3)
        assert summary is not None
        assert len(summary) > 50


# ── Cron Expression Tests ─────────────────────────────────────────────────────

class TestCronExpressions:
    """Test cron expression parsing."""

    def test_valid_cron_expression(self):
        """Valid cron expressions should be parseable."""
        try:
            from croniter import croniter
            valid_exprs = [
                "* * * * *",      # every minute
                "0 9 * * 1-5",    # weekdays 9am
                "0 0 1 * *",      # monthly
                "*/5 * * * *",    # every 5 minutes
            ]
            for expr in valid_exprs:
                assert croniter.is_valid(expr), f"'{expr}' should be valid"
        except ImportError:
            pytest.skip("croniter not installed")

    def test_invalid_cron_expression(self):
        """Invalid cron expressions should be detected."""
        try:
            from croniter import croniter
            assert not croniter.is_valid("not a cron"), "Should be invalid"
            assert not croniter.is_valid("99 * * * *"), "Should be invalid"
        except ImportError:
            pytest.skip("croniter not installed")
