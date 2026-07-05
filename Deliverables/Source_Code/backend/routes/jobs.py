import datetime
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from typing import List, Optional, Dict, Any

from backend.database import get_db
from backend.models import Queue, Job, JobExecution, RetryPolicy, CronJob, DeadLetterQueue
from backend.schemas import (
    JobCreate, JobResponse, BatchJobCreate, JobDetailsResponse, CronJobCreate, CronJobResponse
)
from backend.auth import get_current_user, User
from croniter import croniter

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_in: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find queue
    stmt = select(Queue).filter(Queue.name == job_in.queue_name)
    queue = (await db.execute(stmt)).scalars().first()
    if not queue:
        raise HTTPException(status_code=404, detail=f"Queue '{job_in.queue_name}' not found")

    job_id = uuid.uuid4().hex
    scheduled_at = datetime.datetime.utcnow()
    if job_in.delay_seconds:
        scheduled_at += datetime.timedelta(seconds=job_in.delay_seconds)

    # Determine status if parent is specified
    status_str = "queued"
    if job_in.delay_seconds:
        status_str = "scheduled"
        
    root_job_id = job_id
    if job_in.parent_job_id:
        parent = await db.get(Job, job_in.parent_job_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent job not found")
        
        root_job_id = parent.root_job_id or parent.id
        if parent.status != "completed":
            status_str = "blocked" # Wait for parent to finish

    payload_json = json.dumps(job_in.payload) if job_in.payload else None
    
    # Retrieve default retry policy from queue if it has one
    retry_policy_id = queue.retry_policy_id
    max_retries = 3
    if queue.retry_policy_id:
        policy = await db.get(RetryPolicy, queue.retry_policy_id)
        if policy:
            max_retries = policy.max_retries

    job = Job(
        id=job_id,
        queue_id=queue.id,
        name=job_in.name,
        status=status_str,
        payload=payload_json,
        priority_override=job_in.priority_override or 0,
        retry_count=0,
        max_retries=max_retries,
        retry_policy_id=retry_policy_id,
        parent_job_id=job_in.parent_job_id,
        root_job_id=root_job_id,
        scheduled_at=scheduled_at
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job

@router.post("/batch", response_model=List[JobResponse], status_code=status.HTTP_201_CREATED)
async def create_batch_jobs(
    batch_in: BatchJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Queue).filter(Queue.name == batch_in.queue_name)
    queue = (await db.execute(stmt)).scalars().first()
    if not queue:
        raise HTTPException(status_code=404, detail=f"Queue '{batch_in.queue_name}' not found")

    retry_policy_id = queue.retry_policy_id
    max_retries = 3
    if queue.retry_policy_id:
        policy = await db.get(RetryPolicy, queue.retry_policy_id)
        if policy:
            max_retries = policy.max_retries

    created_jobs = []
    now = datetime.datetime.utcnow()

    for item_payload in batch_in.jobs:
        job_id = uuid.uuid4().hex
        job = Job(
            id=job_id,
            queue_id=queue.id,
            name=batch_in.name,
            status="queued",
            payload=json.dumps(item_payload) if item_payload else None,
            priority_override=batch_in.priority_override or 0,
            retry_count=0,
            max_retries=max_retries,
            retry_policy_id=retry_policy_id,
            scheduled_at=now
        )
        db.add(job)
        created_jobs.append(job)

    await db.commit()
    for job in created_jobs:
        await db.refresh(job)
    return created_jobs

@router.get("", response_model=Dict[str, Any])
async def list_jobs(
    queue_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit
    
    # Base query
    stmt = select(Job)
    count_stmt = select(func.count(Job.id))
    
    if queue_id:
        stmt = stmt.filter(Job.queue_id == queue_id)
        count_stmt = count_stmt.filter(Job.queue_id == queue_id)
        
    if status_filter:
        stmt = stmt.filter(Job.status == status_filter)
        count_stmt = count_stmt.filter(Job.status == status_filter)
        
    # Order by scheduled_at desc
    stmt = stmt.order_by(desc(Job.created_at)).offset(offset).limit(limit)
    
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "jobs": jobs
    }

@router.get("/{job_id}", response_model=JobDetailsResponse)
async def get_job_details(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        # Check DeadLetterQueue table as fallback or detailed log
        raise HTTPException(status_code=404, detail="Job not found")
        
    stmt = select(JobExecution).filter(JobExecution.job_id == job_id).order_by(desc(JobExecution.started_at))
    executions = (await db.execute(stmt)).scalars().all()
    
    return {
        "job": job,
        "executions": executions
    }

@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status not in ["failed", "dlq"]:
        raise HTTPException(status_code=400, detail="Only failed or DLQ jobs can be retried")
        
    # Reset job
    job.status = "queued"
    job.retry_count = 0
    job.error_message = None
    job.scheduled_at = datetime.datetime.utcnow()
    job.worker_id = None
    
    await db.commit()
    await db.refresh(job)
    return job

# Cron / Recurring Jobs API
@router.post("/cron", response_model=CronJobResponse, status_code=status.HTTP_201_CREATED)
async def create_cron_job(
    cron_in: CronJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find queue
    stmt = select(Queue).filter(Queue.name == cron_in.queue_name)
    queue = (await db.execute(stmt)).scalars().first()
    if not queue:
        raise HTTPException(status_code=404, detail=f"Queue '{cron_in.queue_name}' not found")

    # Validate cron expression
    if not croniter.is_valid(cron_in.cron_expression):
        raise HTTPException(status_code=400, detail="Invalid cron expression")

    # Calculate next execution time
    now = datetime.datetime.utcnow()
    iter = croniter(cron_in.cron_expression, now)
    next_run = iter.get_next(datetime.datetime)

    cron_job = CronJob(
        queue_id=queue.id,
        name=cron_in.name,
        cron_expression=cron_in.cron_expression,
        payload=json.dumps(cron_in.payload) if cron_in.payload else None,
        next_run_at=next_run,
        is_active=True
    )
    
    db.add(cron_job)
    await db.commit()
    await db.refresh(cron_job)
    return cron_job

@router.get("/cron/list", response_model=List[CronJobResponse])
async def list_cron_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CronJob))
    return result.scalars().all()

@router.post("/cron/{cron_id}/toggle", response_model=CronJobResponse)
async def toggle_cron_job(
    cron_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cron = await db.get(CronJob, cron_id)
    if not cron:
        raise HTTPException(status_code=404, detail="Cron job not found")
        
    cron.is_active = not cron.is_active
    if cron.is_active:
        now = datetime.datetime.utcnow()
        iter = croniter(cron.cron_expression, now)
        cron.next_run_at = iter.get_next(datetime.datetime)
    else:
        cron.next_run_at = None
        
    await db.commit()
    await db.refresh(cron)
    return cron
