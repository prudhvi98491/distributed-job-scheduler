"""
Scheduler service: promotes delayed/scheduled jobs and handles cron recurrence.
Runs as an APScheduler background job within the FastAPI process.
"""
import logging
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import Job, JobStatus, new_uuid
from app.services.websocket import broadcast

logger = logging.getLogger(__name__)


async def promote_scheduled_jobs():
    """Move scheduled jobs that are due to 'queued' status."""
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(Job).where(
                    and_(
                        Job.status == JobStatus.scheduled,
                        Job.cron_expression == None,  # not a cron job
                        Job.scheduled_at <= now,
                    )
                )
            )
            jobs = result.scalars().all()
            for job in jobs:
                job.status = JobStatus.queued
                logger.info(f"Promoted delayed job {job.id} to queued")
                await broadcast({"event": "job_promoted", "job_id": job.id})

            if jobs:
                await db.commit()
        except Exception as e:
            logger.error(f"Error promoting scheduled jobs: {e}")
            await db.rollback()


async def tick_cron_jobs():
    """For recurring cron jobs that completed, compute next run time and re-queue."""
    try:
        from croniter import croniter
    except ImportError:
        return

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            # Find recurring jobs that are in 'scheduled' state (completed cycle re-scheduled them)
            result = await db.execute(
                select(Job).where(
                    and_(
                        Job.is_recurring == True,
                        Job.cron_expression != None,
                        Job.status == JobStatus.scheduled,
                        or_(Job.scheduled_at == None, Job.scheduled_at <= now),
                    )
                )
            )
            jobs = result.scalars().all()
            for job in jobs:
                # Compute next run from cron expression
                try:
                    cron = croniter(job.cron_expression, now)
                    next_run = cron.get_next(datetime)
                    job.status = JobStatus.queued
                    job.scheduled_at = next_run
                    logger.info(f"Cron job {job.id} promoted; next run at {next_run}")
                    await broadcast({"event": "cron_job_promoted", "job_id": job.id, "next_run": next_run.isoformat()})
                except Exception as e:
                    logger.warning(f"Invalid cron expression for job {job.id}: {e}")

            if jobs:
                await db.commit()
        except Exception as e:
            logger.error(f"Error ticking cron jobs: {e}")
            await db.rollback()


async def detect_stale_jobs():
    """Re-queue jobs stuck in 'running' state from dead workers."""
    from datetime import timedelta
    from app.config import WORKER_HEARTBEAT_TIMEOUT_SECONDS
    from app.models import Worker, WorkerStatus

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            timeout_threshold = now - timedelta(seconds=WORKER_HEARTBEAT_TIMEOUT_SECONDS * 2)

            # Find workers with stale heartbeats
            result = await db.execute(
                select(Worker).where(
                    and_(
                        Worker.status.in_([WorkerStatus.active, WorkerStatus.idle]),
                        Worker.last_heartbeat < timeout_threshold,
                    )
                )
            )
            stale_workers = result.scalars().all()

            for worker in stale_workers:
                logger.warning(f"Worker {worker.id} ({worker.name}) has stale heartbeat, marking stopped")
                worker.status = WorkerStatus.stopped

                # Re-queue any running jobs owned by this worker
                jobs_result = await db.execute(
                    select(Job).where(
                        and_(Job.claimed_by == worker.id, Job.status == JobStatus.running)
                    )
                )
                stuck_jobs = jobs_result.scalars().all()
                for job in stuck_jobs:
                    job.status = JobStatus.queued
                    job.claimed_by = None
                    job.claimed_at = None
                    logger.info(f"Re-queued stuck job {job.id} from dead worker {worker.id}")
                    await broadcast({"event": "job_requeued_stale_worker", "job_id": job.id, "worker_id": worker.id})

                await broadcast({"event": "worker_timed_out", "worker_id": worker.id})

            if stale_workers:
                await db.commit()
        except Exception as e:
            logger.error(f"Error detecting stale jobs: {e}")
            await db.rollback()
