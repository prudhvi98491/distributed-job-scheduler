"""Retry backoff computation and AI failure summary generation."""
import math
import random
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Job, Queue, RetryPolicy, RetryStrategy


async def compute_next_retry_at(
    job: Job,
    queue: Optional[Queue],
    db: AsyncSession
) -> datetime:
    """
    Compute the next retry time based on retry policy strategy.
    Falls back to exponential backoff if no policy configured.
    """
    now = datetime.now(timezone.utc)
    attempt = job.attempt_count  # already incremented

    policy: Optional[RetryPolicy] = None
    if queue and queue.retry_policy_id:
        result = await db.execute(select(RetryPolicy).where(RetryPolicy.id == queue.retry_policy_id))
        policy = result.scalar_one_or_none()

    if policy:
        strategy = policy.strategy
        base_ms = policy.base_delay_ms
        max_ms = policy.max_delay_ms
    else:
        # Default: exponential backoff 1s base, 60s max
        strategy = RetryStrategy.exponential_backoff
        base_ms = 1000
        max_ms = 60000

    if strategy == RetryStrategy.fixed:
        delay_ms = base_ms
    elif strategy == RetryStrategy.linear_backoff:
        delay_ms = min(base_ms * attempt, max_ms)
    else:  # exponential_backoff
        delay_ms = min(base_ms * (2 ** (attempt - 1)), max_ms)
        # Add jitter (±10%)
        jitter = delay_ms * 0.1 * (random.random() * 2 - 1)
        delay_ms = int(delay_ms + jitter)

    return now + timedelta(milliseconds=delay_ms)


def generate_failure_summary(job_type: str, error_message: str, attempts: int) -> str:
    """
    Generate an AI-style failure summary for DLQ entries.
    In production this would call an LLM API; here we use a smart template.
    """
    error_lower = error_message.lower() if error_message else ""

    if "timeout" in error_lower or "timed out" in error_lower:
        category = "Timeout Failure"
        insight = "The job exceeded the allowed execution time. Consider increasing timeout limits or optimizing the job payload processing."
    elif "connection" in error_lower or "connect" in error_lower:
        category = "Connectivity Failure"
        insight = "The job could not establish a required network connection. Check network routes, firewall rules, and service availability."
    elif "memory" in error_lower or "oom" in error_lower:
        category = "Resource Exhaustion"
        insight = "The job ran out of memory. Consider reducing payload size, adding pagination, or increasing worker memory limits."
    elif "permission" in error_lower or "unauthorized" in error_lower or "403" in error_lower:
        category = "Authorization Failure"
        insight = "The job lacked required permissions. Verify API keys, IAM roles, and access control policies."
    elif "not found" in error_lower or "404" in error_lower:
        category = "Resource Not Found"
        insight = "A required resource was not found. The target may have been deleted or the identifier may be stale."
    elif "validation" in error_lower or "invalid" in error_lower:
        category = "Validation Failure"
        insight = "The job payload failed validation. Review the schema requirements for this job type."
    elif "rate" in error_lower or "throttl" in error_lower or "429" in error_lower:
        category = "Rate Limit Exceeded"
        insight = "External API rate limits were hit. Implement exponential backoff and reduce request frequency."
    else:
        category = "Unclassified Failure"
        insight = "The job failed with an unclassified error. Review the execution logs for root cause analysis."

    return (
        f"[{category}] Job '{job_type}' permanently failed after {attempts} attempt(s). "
        f"{insight} "
        f"Last error: {error_message[:200] if error_message else 'No error message recorded.'}"
    )
