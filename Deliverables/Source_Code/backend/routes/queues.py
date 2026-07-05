from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List, Dict, Any, Optional


from backend.database import get_db
from backend.models import Queue, Project, Job, RetryPolicy
from backend.schemas import QueueCreate, QueueUpdate, QueueResponse
from backend.auth import get_current_user, User

router = APIRouter(prefix="/api/queues", tags=["Queues"])

@router.post("", response_model=QueueResponse, status_code=status.HTTP_201_CREATED)
async def create_queue(
    queue_in: QueueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify project exists
    project = await db.get(Project, queue_in.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if queue name already exists
    stmt = select(Queue).filter(Queue.name == queue_in.name)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Queue name already exists")

    # Verify retry policy exists if specified
    if queue_in.retry_policy_id:
        policy = await db.get(RetryPolicy, queue_in.retry_policy_id)
        if not policy:
            raise HTTPException(status_code=404, detail="Retry policy not found")

    queue = Queue(
        project_id=queue_in.project_id,
        name=queue_in.name,
        priority=queue_in.priority,
        concurrency_limit=queue_in.concurrency_limit,
        retry_policy_id=queue_in.retry_policy_id
    )
    db.add(queue)
    await db.commit()
    await db.refresh(queue)
    return queue

@router.get("", response_model=List[QueueResponse])
async def list_queues(
    project_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Queue)
    if project_id:
        stmt = stmt.filter(Queue.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{queue_id}", response_model=QueueResponse)
async def get_queue(queue_id: int, db: AsyncSession = Depends(get_db)):
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    return queue

@router.patch("/{queue_id}", response_model=QueueResponse)
async def update_queue(
    queue_id: int,
    queue_in: QueueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    if queue_in.priority is not None:
        queue.priority = queue_in.priority
    if queue_in.concurrency_limit is not None:
        queue.concurrency_limit = queue_in.concurrency_limit
    if queue_in.is_paused is not None:
        queue.is_paused = queue_in.is_paused
    if queue_in.retry_policy_id is not None:
        if queue_in.retry_policy_id == 0:
            queue.retry_policy_id = None
        else:
            policy = await db.get(RetryPolicy, queue_in.retry_policy_id)
            if not policy:
                raise HTTPException(status_code=404, detail="Retry policy not found")
            queue.retry_policy_id = queue_in.retry_policy_id

    await db.commit()
    await db.refresh(queue)
    return queue

@router.delete("/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_queue(
    queue_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    await db.delete(queue)
    await db.commit()
    return None

@router.get("/{queue_id}/stats")
async def get_queue_stats(queue_id: int, db: AsyncSession = Depends(get_db)):
    queue = await db.get(Queue, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")

    # Aggregate counts of jobs by status
    stmt = (
        select(Job.status, func.count(Job.id))
        .filter(Job.queue_id == queue_id)
        .group_by(Job.status)
    )
    result = await db.execute(stmt)
    status_counts = {status: count for status, count in result.all()}

    # Initialize all standard statuses to 0
    stats = {
        "queued": status_counts.get("queued", 0) + status_counts.get("scheduled", 0), # Scheduled are future queued jobs
        "running": status_counts.get("running", 0) + status_counts.get("claimed", 0),
        "completed": status_counts.get("completed", 0),
        "failed": status_counts.get("failed", 0),
        "dlq": status_counts.get("dlq", 0),
        "total": sum(status_counts.values())
    }
    
    return {
        "queue_id": queue_id,
        "name": queue.name,
        "priority": queue.priority,
        "concurrency_limit": queue.concurrency_limit,
        "is_paused": queue.is_paused,
        "stats": stats
    }

