from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import Job, Queue, JobStatus, JobLog, LogLevel, new_uuid, User
from app.schemas import JobEnqueue, BatchEnqueue, JobOut, LogOut
from app.auth import get_current_user
from app.services.websocket import broadcast

router = APIRouter(prefix="/api", tags=["jobs"])


@router.post("/queues/{queue_id}/jobs", response_model=JobOut, status_code=201)
async def enqueue_job(
    queue_id: str, body: JobEnqueue,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    queue = await _get_queue_or_404(queue_id, db)
    if queue.paused:
        raise HTTPException(status_code=409, detail="Queue is paused")

    # Idempotency check
    if body.idempotency_key:
        existing = await db.execute(select(Job).where(Job.idempotency_key == body.idempotency_key))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Duplicate idempotency key")

    # Determine initial status
    now = datetime.now(timezone.utc)
    if body.cron_expression or body.scheduled_at:
        initial_status = JobStatus.scheduled
    else:
        initial_status = JobStatus.queued

    # Get retry policy max attempts from queue's policy (if any)
    max_attempts = body.max_attempts
    if queue.retry_policy_id and queue.retry_policy:
        max_attempts = queue.retry_policy.max_attempts

    job = Job(
        id=new_uuid(),
        queue_id=queue_id,
        type=body.type,
        payload=body.payload,
        status=initial_status,
        priority=body.priority,
        scheduled_at=body.scheduled_at,
        cron_expression=body.cron_expression,
        is_recurring=body.is_recurring,
        max_attempts=max_attempts,
        idempotency_key=body.idempotency_key,
    )
    db.add(job)
    await db.flush()

    # Log creation
    db.add(JobLog(
        id=new_uuid(), job_id=job.id,
        level=LogLevel.info,
        message=f"Job enqueued with status={initial_status.value}",
    ))

    await broadcast({"event": "job_created", "job_id": job.id, "queue_id": queue_id, "status": initial_status.value})
    return job


@router.post("/queues/{queue_id}/jobs/batch", status_code=201)
async def batch_enqueue(
    queue_id: str, body: BatchEnqueue,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    queue = await _get_queue_or_404(queue_id, db)
    if queue.paused:
        raise HTTPException(status_code=409, detail="Queue is paused")

    created_ids = []
    for job_data in body.jobs:
        now = datetime.now(timezone.utc)
        initial_status = JobStatus.scheduled if (job_data.cron_expression or job_data.scheduled_at) else JobStatus.queued
        job = Job(
            id=new_uuid(), queue_id=queue_id, type=job_data.type,
            payload=job_data.payload, status=initial_status,
            priority=job_data.priority, scheduled_at=job_data.scheduled_at,
            cron_expression=job_data.cron_expression, is_recurring=job_data.is_recurring,
            max_attempts=job_data.max_attempts, idempotency_key=job_data.idempotency_key,
        )
        db.add(job)
        created_ids.append(job.id)

    await db.flush()
    await broadcast({"event": "batch_enqueued", "queue_id": queue_id, "count": len(created_ids)})
    return {"created": len(created_ids), "job_ids": created_ids}


@router.get("/queues/{queue_id}/jobs", response_model=List[JobOut])
async def list_jobs(
    queue_id: str,
    status: Optional[JobStatus] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    await _get_queue_or_404(queue_id, db)
    q = select(Job).where(Job.queue_id == queue_id)
    if status:
        q = q.where(Job.status == status)
    if type:
        q = q.where(Job.type == type)
    q = q.order_by(Job.priority.desc(), Job.created_at.asc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/jobs", response_model=List[JobOut])
async def list_all_jobs(
    status: Optional[JobStatus] = Query(None),
    type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    q = select(Job)
    if status:
        q = q.where(Job.status == status)
    if type:
        q = q.where(Job.type == type)
    q = q.order_by(Job.created_at.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _get_job_or_404(job_id, db)


@router.post("/jobs/{job_id}/cancel", response_model=JobOut)
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    job = await _get_job_or_404(job_id, db)
    if job.status in (JobStatus.completed, JobStatus.dead, JobStatus.cancelled):
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status={job.status.value}")
    job.status = JobStatus.cancelled
    db.add(JobLog(id=new_uuid(), job_id=job.id, level=LogLevel.info, message="Job cancelled by user"))
    await broadcast({"event": "job_cancelled", "job_id": job_id})
    return job


@router.post("/jobs/{job_id}/retry", response_model=JobOut)
async def retry_job(job_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    job = await _get_job_or_404(job_id, db)
    if job.status not in (JobStatus.failed, JobStatus.dead, JobStatus.cancelled):
        raise HTTPException(status_code=400, detail="Only failed/dead/cancelled jobs can be retried")
    job.status = JobStatus.queued
    job.attempt_count = 0
    job.next_retry_at = None
    job.claimed_at = None
    job.claimed_by = None
    db.add(JobLog(id=new_uuid(), job_id=job.id, level=LogLevel.info, message="Job manually re-queued for retry"))
    await broadcast({"event": "job_retried", "job_id": job_id})
    return job


@router.get("/jobs/{job_id}/logs", response_model=List[LogOut])
async def job_logs(
    job_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    await _get_job_or_404(job_id, db)
    result = await db.execute(
        select(JobLog).where(JobLog.job_id == job_id)
        .order_by(JobLog.logged_at.asc()).limit(limit)
    )
    return result.scalars().all()


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _get_queue_or_404(queue_id: str, db: AsyncSession) -> Queue:
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Queue not found")
    return q


async def _get_job_or_404(job_id: str, db: AsyncSession) -> Job:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
