from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from typing import List
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models import Job, JobStatus, Worker, WorkerStatus, Queue, JobExecution, User
from app.schemas import SystemOverview, ThroughputPoint, LatencyStats
from app.auth import get_current_user

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/overview", response_model=SystemOverview)
async def overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)

    async def count(where_clause):
        r = await db.execute(select(func.count(Job.id)).where(where_clause))
        return r.scalar() or 0

    total_queues = (await db.execute(select(func.count(Queue.id)))).scalar() or 0
    total_jobs = (await db.execute(select(func.count(Job.id)))).scalar() or 0

    active_workers = (await db.execute(
        select(func.count(Worker.id)).where(Worker.status == WorkerStatus.active)
    )).scalar() or 0
    idle_workers = (await db.execute(
        select(func.count(Worker.id)).where(Worker.status == WorkerStatus.idle)
    )).scalar() or 0

    return SystemOverview(
        total_queues=total_queues,
        total_jobs=total_jobs,
        queued=await count(Job.status == JobStatus.queued),
        running=await count(Job.status == JobStatus.running),
        completed_24h=await count(and_(Job.status == JobStatus.completed, Job.completed_at >= since_24h)),
        failed_24h=await count(and_(Job.status == JobStatus.failed, Job.updated_at >= since_24h)),
        dead=await count(Job.status == JobStatus.dead),
        active_workers=active_workers,
        idle_workers=idle_workers,
    )


@router.get("/throughput", response_model=List[ThroughputPoint])
async def throughput(
    hours: int = 1,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Return per-minute job throughput for the last N hours."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    points = []

    # Build minute buckets
    minutes = hours * 60
    for i in range(min(minutes, 60)):  # cap at 60 data points
        bucket_start = since + timedelta(minutes=i * (minutes // 60))
        bucket_end = bucket_start + timedelta(minutes=(minutes // 60))

        completed_r = await db.execute(
            select(func.count(Job.id)).where(
                and_(
                    Job.status == JobStatus.completed,
                    Job.completed_at >= bucket_start,
                    Job.completed_at < bucket_end,
                )
            )
        )
        failed_r = await db.execute(
            select(func.count(Job.id)).where(
                and_(
                    Job.status.in_([JobStatus.failed, JobStatus.dead]),
                    Job.updated_at >= bucket_start,
                    Job.updated_at < bucket_end,
                )
            )
        )
        points.append(ThroughputPoint(
            timestamp=bucket_start.isoformat(),
            completed=completed_r.scalar() or 0,
            failed=failed_r.scalar() or 0,
        ))

    return points


@router.get("/latency", response_model=List[LatencyStats])
async def latency(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Average execution latency per queue."""
    queues_result = await db.execute(select(Queue))
    queues = queues_result.scalars().all()
    stats = []

    for queue in queues:
        execs_result = await db.execute(
            select(JobExecution).join(Job, Job.id == JobExecution.job_id)
            .where(and_(
                Job.queue_id == queue.id,
                JobExecution.status == "completed",
                JobExecution.duration_ms != None
            ))
        )
        execs = execs_result.scalars().all()
        durations = [e.duration_ms for e in execs if e.duration_ms]

        if durations:
            durations_sorted = sorted(durations)
            p95_idx = int(len(durations_sorted) * 0.95)
            stats.append(LatencyStats(
                queue_id=queue.id,
                queue_name=queue.name,
                avg_duration_ms=sum(durations) / len(durations),
                min_duration_ms=min(durations),
                max_duration_ms=max(durations),
                p95_duration_ms=float(durations_sorted[min(p95_idx, len(durations_sorted) - 1)]),
            ))
        else:
            stats.append(LatencyStats(
                queue_id=queue.id,
                queue_name=queue.name,
                avg_duration_ms=None,
                min_duration_ms=None,
                max_duration_ms=None,
                p95_duration_ms=None,
            ))

    return stats
