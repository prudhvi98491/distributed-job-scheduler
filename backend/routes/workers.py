from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any
import datetime

from backend.database import get_db
from backend.models import Worker, Job, Queue, JobExecution
from backend.schemas import WorkerResponse

router = APIRouter(tags=["Workers & Metrics"])

@router.get("/api/workers", response_model=List[WorkerResponse])
async def list_workers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Worker).order_by(Worker.last_heartbeat_at.desc()))
    return result.scalars().all()

@router.get("/api/metrics")
async def get_system_metrics(db: AsyncSession = Depends(get_db)):
    # 1. Total queues and active workers
    queues_count = (await db.execute(select(func.count(Queue.id)))).scalar_one()
    
    # Active workers = heartbeated in the last 15 seconds
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
    workers_stmt = select(func.count(Worker.id)).filter(Worker.last_heartbeat_at >= cutoff)
    active_workers_count = (await db.execute(workers_stmt)).scalar_one()

    # 2. Jobs summary by status
    jobs_stmt = select(Job.status, func.count(Job.id)).group_by(Job.status)
    jobs_res = await db.execute(jobs_stmt)
    status_map = {status: count for status, count in jobs_res.all()}
    
    # 3. Average duration of executions
    duration_stmt = select(func.avg(JobExecution.duration_ms)).filter(JobExecution.status == "completed")
    avg_duration = (await db.execute(duration_stmt)).scalar() or 0.0

    # 4. Success and failure rates in the last 24 hours
    since_24h = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    daily_total_stmt = select(func.count(JobExecution.id)).filter(JobExecution.started_at >= since_24h)
    daily_total = (await db.execute(daily_total_stmt)).scalar_one() or 1
    
    daily_success_stmt = select(func.count(JobExecution.id)).filter(
        JobExecution.started_at >= since_24h,
        JobExecution.status == "completed"
    )
    daily_success = (await db.execute(daily_success_stmt)).scalar_one() or 0

    daily_failure_stmt = select(func.count(JobExecution.id)).filter(
        JobExecution.started_at >= since_24h,
        JobExecution.status == "failed"
    )
    daily_failure = (await db.execute(daily_failure_stmt)).scalar_one() or 0

    # 5. Throughput per queue
    queue_throughput_stmt = (
        select(Queue.name, func.count(Job.id))
        .join(Job)
        .filter(Job.status == "completed", Job.completed_at >= since_24h)
        .group_by(Queue.name)
    )
    queue_throughput_res = await db.execute(queue_throughput_stmt)
    queue_throughput = {qname: count for qname, count in queue_throughput_res.all()}

    return {
        "queues_count": queues_count,
        "active_workers_count": active_workers_count,
        "jobs_summary": {
            "queued": status_map.get("queued", 0) + status_map.get("scheduled", 0),
            "running": status_map.get("running", 0) + status_map.get("claimed", 0),
            "completed": status_map.get("completed", 0),
            "failed": status_map.get("failed", 0),
            "dlq": status_map.get("dlq", 0),
            "blocked": status_map.get("blocked", 0),
        },
        "performance": {
            "avg_duration_ms": round(avg_duration, 2),
            "daily_total_runs": daily_total,
            "daily_success_runs": daily_success,
            "daily_failure_runs": daily_failure,
            "success_rate_pct": round((daily_success / daily_total) * 100, 2) if daily_total > 0 else 100.0,
            "failure_rate_pct": round((daily_failure / daily_total) * 100, 2) if daily_total > 0 else 0.0,
        },
        "queue_throughput_24h": queue_throughput
    }
