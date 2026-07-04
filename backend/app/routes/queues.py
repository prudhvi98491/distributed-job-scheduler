from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.database import get_db
from app.models import Queue, Project, Job, JobStatus, new_uuid, User
from app.schemas import QueueCreate, QueueUpdate, QueueOut, QueueStats
from app.auth import get_current_user
from app.services.websocket import broadcast

router = APIRouter(prefix="/api", tags=["queues"])


@router.post("/projects/{project_id}/queues", response_model=QueueOut, status_code=201)
async def create_queue(
    project_id: str, body: QueueCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    project = await _get_project_or_404(project_id, db)
    queue = Queue(
        id=new_uuid(),
        project_id=project_id,
        name=body.name,
        description=body.description,
        concurrency_limit=body.concurrency_limit,
        priority=body.priority,
        retry_policy_id=body.retry_policy_id,
    )
    db.add(queue)
    await db.flush()
    await broadcast({"event": "queue_created", "queue_id": queue.id, "name": queue.name})
    return queue


@router.get("/projects/{project_id}/queues", response_model=List[QueueOut])
async def list_queues(
    project_id: str, db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    await _get_project_or_404(project_id, db)
    result = await db.execute(select(Queue).where(Queue.project_id == project_id))
    return result.scalars().all()


@router.get("/queues", response_model=List[QueueOut])
async def list_all_queues(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(select(Queue))
    return result.scalars().all()


@router.get("/queues/{queue_id}", response_model=QueueOut)
async def get_queue(queue_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await _get_queue_or_404(queue_id, db)


@router.put("/queues/{queue_id}", response_model=QueueOut)
async def update_queue(
    queue_id: str, body: QueueUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    queue = await _get_queue_or_404(queue_id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(queue, field, value)
    return queue


@router.post("/queues/{queue_id}/pause", response_model=QueueOut)
async def pause_queue(queue_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    queue = await _get_queue_or_404(queue_id, db)
    queue.paused = True
    await broadcast({"event": "queue_paused", "queue_id": queue_id})
    return queue


@router.post("/queues/{queue_id}/resume", response_model=QueueOut)
async def resume_queue(queue_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    queue = await _get_queue_or_404(queue_id, db)
    queue.paused = False
    await broadcast({"event": "queue_resumed", "queue_id": queue_id})
    return queue


@router.get("/queues/{queue_id}/stats", response_model=QueueStats)
async def queue_stats(queue_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    queue = await _get_queue_or_404(queue_id, db)

    counts = {}
    for s in JobStatus:
        result = await db.execute(
            select(func.count(Job.id)).where(Job.queue_id == queue_id, Job.status == s)
        )
        counts[s.value] = result.scalar() or 0

    total = sum(counts.values())
    return QueueStats(
        queue_id=queue_id,
        queue_name=queue.name,
        total=total,
        **counts,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────
async def _get_project_or_404(project_id: str, db: AsyncSession):
    result = await db.execute(select(Project).where(Project.id == project_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


async def _get_queue_or_404(queue_id: str, db: AsyncSession) -> Queue:
    result = await db.execute(select(Queue).where(Queue.id == queue_id))
    q = result.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Queue not found")
    return q
