from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from typing import List, Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models import (
    Worker, WorkerHeartbeat, Job, JobExecution, JobLog,
    JobStatus, WorkerStatus, ExecutionStatus, LogLevel,
    new_uuid, User, Queue, DeadLetterQueue
)
from app.schemas import (
    WorkerRegister, WorkerHeartbeatIn, WorkerOut,
    ClaimRequest, CompleteJobRequest, ExecutionOut
)
from app.auth import get_current_user
from app.services.websocket import broadcast
from app.services.retry import compute_next_retry_at, generate_failure_summary

router = APIRouter(prefix="/api/workers", tags=["workers"])


@router.post("", response_model=WorkerOut, status_code=201)
async def register_worker(
    body: WorkerRegister,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    worker = Worker(
        id=new_uuid(),
        name=body.name,
        hostname=body.hostname,
        pid=body.pid,
        queue_ids=body.queue_ids,
        max_concurrency=body.max_concurrency,
        status=WorkerStatus.idle,
        last_heartbeat=datetime.now(timezone.utc),
        metadata_=body.metadata,
    )
    db.add(worker)
    await db.flush()
    await broadcast({"event": "worker_registered", "worker_id": worker.id, "name": worker.name})
    return worker


@router.get("", response_model=List[WorkerOut])
async def list_workers(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Worker).order_by(Worker.registered_at.desc()))
    return result.scalars().all()


@router.get("/{worker_id}", response_model=WorkerOut)
async def get_worker(worker_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _get_worker_or_404(worker_id, db)


@router.post("/{worker_id}/heartbeat")
async def heartbeat(
    worker_id: str, body: WorkerHeartbeatIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    worker = await _get_worker_or_404(worker_id, db)
    now = datetime.now(timezone.utc)
    worker.last_heartbeat = now
    worker.status = body.status

    hb = WorkerHeartbeat(
        id=new_uuid(), worker_id=worker_id,
        heartbeat_at=now,
        jobs_running=body.jobs_running,
        jobs_completed=body.jobs_completed,
        jobs_failed=body.jobs_failed,
        cpu_pct=body.cpu_pct,
        mem_mb=body.mem_mb,
    )
    db.add(hb)
    await broadcast({
        "event": "worker_heartbeat",
        "worker_id": worker_id,
        "jobs_running": body.jobs_running,
        "status": body.status.value
    })
    return {"ok": True, "timestamp": now.isoformat()}


@router.post("/{worker_id}/claim")
async def claim_jobs(
    worker_id: str, body: ClaimRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Atomically claim available jobs for this worker."""
    worker = await _get_worker_or_404(worker_id, db)

    queue_ids = body.queue_ids or worker.queue_ids or []
    now = datetime.now(timezone.utc)

    # For each queue, check concurrency limits then claim jobs
    claimed_jobs = []

    for queue_id in queue_ids:
        # Check queue is not paused
        q_result = await db.execute(select(Queue).where(Queue.id == queue_id))
        queue = q_result.scalar_one_or_none()
        if not queue or queue.paused:
            continue

        # Count currently running jobs in this queue
        running_result = await db.execute(
            select(Job).where(
                and_(Job.queue_id == queue_id, Job.status == JobStatus.running)
            )
        )
        running_count = len(running_result.scalars().all())
        available_slots = queue.concurrency_limit - running_count
        if available_slots <= 0:
            continue

        # Find claimable jobs: queued, not paused, scheduled_at <= now or null
        jobs_result = await db.execute(
            select(Job).where(
                and_(
                    Job.queue_id == queue_id,
                    Job.status == JobStatus.queued,
                    or_(Job.scheduled_at == None, Job.scheduled_at <= now)
                )
            )
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .limit(min(available_slots, body.max_jobs - len(claimed_jobs)))
            .with_for_update(skip_locked=True)
        )
        jobs = jobs_result.scalars().all()

        for job in jobs:
            job.status = JobStatus.running
            job.claimed_at = now
            job.claimed_by = worker_id
            job.started_at = now
            job.attempt_count += 1

            # Create execution record
            execution = JobExecution(
                id=new_uuid(),
                job_id=job.id,
                worker_id=worker_id,
                attempt_number=job.attempt_count,
                status=ExecutionStatus.running,
                started_at=now,
            )
            db.add(execution)
            db.add(JobLog(
                id=new_uuid(), job_id=job.id, execution_id=execution.id,
                level=LogLevel.info,
                message=f"Job claimed by worker {worker.name} (attempt {job.attempt_count})"
            ))
            claimed_jobs.append({"job_id": job.id, "execution_id": execution.id, "payload": job.payload, "type": job.type})
            await broadcast({"event": "job_claimed", "job_id": job.id, "worker_id": worker_id})

        if len(claimed_jobs) >= body.max_jobs:
            break

    if claimed_jobs:
        worker.status = WorkerStatus.active

    return {"claimed": len(claimed_jobs), "jobs": claimed_jobs}


@router.post("/{worker_id}/complete")
async def complete_job(
    worker_id: str, body: CompleteJobRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Mark a job execution as completed or failed."""
    worker = await _get_worker_or_404(worker_id, db)

    # Get execution
    exec_result = await db.execute(
        select(JobExecution).where(JobExecution.id == body.execution_id)
    )
    execution = exec_result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    job_result = await db.execute(select(Job).where(Job.id == execution.job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    now = datetime.now(timezone.utc)
    execution.status = body.status
    execution.finished_at = now
    execution.duration_ms = body.duration_ms
    execution.result = body.result
    execution.error_message = body.error_message
    execution.error_stack = body.error_stack

    if body.status == ExecutionStatus.completed:
        job.status = JobStatus.completed
        job.completed_at = now

        # If recurring, re-queue for next cron cycle (handled by scheduler service)
        if job.is_recurring and job.cron_expression:
            job.status = JobStatus.scheduled

        db.add(JobLog(
            id=new_uuid(), job_id=job.id, execution_id=execution.id,
            level=LogLevel.info,
            message=f"Job completed in {body.duration_ms}ms"
        ))
        await broadcast({"event": "job_completed", "job_id": job.id, "duration_ms": body.duration_ms})

    elif body.status == ExecutionStatus.failed:
        # Check if we should retry
        queue_result = await db.execute(select(Queue).where(Queue.id == job.queue_id))
        queue = queue_result.scalar_one_or_none()

        if job.attempt_count < job.max_attempts:
            # Schedule retry
            next_retry = await compute_next_retry_at(job, queue, db)
            job.status = JobStatus.queued
            job.next_retry_at = next_retry
            job.scheduled_at = next_retry

            db.add(JobLog(
                id=new_uuid(), job_id=job.id, execution_id=execution.id,
                level=LogLevel.warn,
                message=f"Job failed (attempt {job.attempt_count}/{job.max_attempts}): {body.error_message}. Retrying at {next_retry}"
            ))
            await broadcast({"event": "job_failed_retrying", "job_id": job.id, "attempt": job.attempt_count})
        else:
            # Move to DLQ
            job.status = JobStatus.dead
            ai_summary = generate_failure_summary(job.type, body.error_message or "", job.attempt_count)
            dlq_entry = DeadLetterQueue(
                id=new_uuid(),
                original_job_id=job.id,
                queue_id=job.queue_id,
                payload=job.payload,
                failure_reason=f"Exceeded max attempts ({job.max_attempts})",
                last_error=body.error_message,
                ai_summary=ai_summary,
                can_retry=True,
            )
            db.add(dlq_entry)
            db.add(JobLog(
                id=new_uuid(), job_id=job.id, execution_id=execution.id,
                level=LogLevel.error,
                message=f"Job permanently failed after {job.max_attempts} attempts. Moved to DLQ."
            ))
            await broadcast({"event": "job_dead", "job_id": job.id, "queue_id": job.queue_id})

    # Update worker status
    running_result = await db.execute(
        select(Job).where(and_(Job.claimed_by == worker_id, Job.status == JobStatus.running))
    )
    still_running = running_result.scalars().all()
    worker.status = WorkerStatus.active if still_running else WorkerStatus.idle

    return {"ok": True}


@router.delete("/{worker_id}")
async def deregister_worker(worker_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    worker = await _get_worker_or_404(worker_id, db)
    worker.status = WorkerStatus.stopped
    await broadcast({"event": "worker_stopped", "worker_id": worker_id})
    return {"ok": True}


@router.get("/{worker_id}/executions", response_model=List[ExecutionOut])
async def worker_executions(
    worker_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(JobExecution).where(JobExecution.worker_id == worker_id)
        .order_by(JobExecution.started_at.desc()).limit(limit)
    )
    return result.scalars().all()


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _get_worker_or_404(worker_id: str, db: AsyncSession) -> Worker:
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Worker not found")
    return w
