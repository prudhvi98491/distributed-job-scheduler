import asyncio
import datetime
import logging
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from croniter import croniter

from backend.database import async_session
from backend.models import CronJob, Job, Queue, RetryPolicy

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Scheduler")

class CronScheduler:
    def __init__(self):
        self.running = False

    async def start(self):
        self.running = True
        logger.info("Starting Cron Scheduler...")
        self.scheduler_task = asyncio.create_task(self.scheduler_loop())

    async def stop(self):
        logger.info("Stopping Cron Scheduler...")
        self.running = False
        self.scheduler_task.cancel()
        logger.info("Cron Scheduler stopped.")

    async def scheduler_loop(self):
        while self.running:
            try:
                await self.tick()
            except Exception as e:
                logger.error(f"Scheduler tick failed: {e}")
            await asyncio.sleep(2) # Tick every 2 seconds

    async def tick(self):
        now = datetime.datetime.utcnow()
        async with async_session() as db:
            async with db.begin():
                # Find active cron jobs that are due
                stmt = select(CronJob).filter(
                    CronJob.is_active == True,
                    CronJob.next_run_at <= now
                )
                due_cron_jobs = (await db.execute(stmt)).scalars().all()
                
                for cron in due_cron_jobs:
                    logger.info(f"Triggering recurring cron job: {cron.name} ({cron.cron_expression})")
                    
                    # 1. Load queue
                    queue = await db.get(Queue, cron.queue_id)
                    if not queue:
                        logger.error(f"Queue {cron.queue_id} not found for cron {cron.id}. Skipping.")
                        continue
                        
                    # 2. Setup job parameters
                    job_id = uuid.uuid4().hex
                    retry_policy_id = queue.retry_policy_id
                    max_retries = 3
                    if queue.retry_policy_id:
                        policy = await db.get(RetryPolicy, queue.retry_policy_id)
                        if policy:
                            max_retries = policy.max_retries
                            
                    # 3. Create job
                    job = Job(
                        id=job_id,
                        queue_id=cron.queue_id,
                        name=cron.name,
                        status="queued",
                        payload=cron.payload,
                        retry_count=0,
                        max_retries=max_retries,
                        retry_policy_id=retry_policy_id,
                        scheduled_at=now
                    )
                    db.add(job)
                    
                    # 4. Update cron job last run and next run
                    cron.last_run_at = now
                    iter = croniter(cron.cron_expression, now)
                    cron.next_run_at = iter.get_next(datetime.datetime)
                    
                await db.commit()
