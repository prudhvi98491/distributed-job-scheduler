from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.database import get_db
from app.models import DeadLetterQueue, Job, JobStatus, JobLog, LogLevel, new_uuid, User
from app.schemas import DLQOut
from app.auth import get_current_user
from app.services.websocket import broadcast

router = APIRouter(prefix="/api/dlq", tags=["dead-letter-queue"])


@router.get("", response_model=List[DLQOut])
async def list_dlq(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(DeadLetterQueue).order_by(DeadLetterQueue.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{dlq_id}/requeue")
async def requeue_dlq_entry(
    dlq_id: str, db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    entry = await _get_dlq_or_404(dlq_id, db)
    if not entry.can_retry:
        raise HTTPException(status_code=400, detail="This DLQ entry is not retryable")

    # Re-queue the original job
    job_result = await db.execute(select(Job).where(Job.id == entry.original_job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Original job not found")

    job.status = JobStatus.queued
    job.attempt_count = 0
    job.claimed_at = None
    job.claimed_by = None
    job.next_retry_at = None

    db.add(JobLog(
        id=new_uuid(), job_id=job.id,
        level=LogLevel.info,
        message="Job re-queued from Dead Letter Queue"
    ))
    await broadcast({"event": "dlq_requeued", "dlq_id": dlq_id, "job_id": job.id})
    return {"ok": True, "job_id": job.id}


@router.delete("/{dlq_id}")
async def delete_dlq_entry(
    dlq_id: str, db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    entry = await _get_dlq_or_404(dlq_id, db)
    await db.delete(entry)
    return {"ok": True}


async def _get_dlq_or_404(dlq_id: str, db: AsyncSession) -> DeadLetterQueue:
    result = await db.execute(select(DeadLetterQueue).where(DeadLetterQueue.id == dlq_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="DLQ entry not found")
    return entry
