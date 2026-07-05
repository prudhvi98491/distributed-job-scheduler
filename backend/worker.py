import asyncio
import datetime
import socket
import sys
from typing import Optional, Dict

import uuid
import json
import logging
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func, or_

from backend.database import async_session
from backend.models import Worker, Job, Queue, RetryPolicy, JobExecution, DeadLetterQueue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Worker")

class JobWorker:
    def __init__(self, concurrency: int = 5):
        self.worker_id = f"worker_{socket.gethostname()}_{uuid.uuid4().hex[:6]}"
        self.concurrency = concurrency
        self.active_tasks = {}
        self.running = False

    async def start(self):
        self.running = True
        logger.info(f"Starting worker {self.worker_id} with concurrency limit {self.concurrency}")
        
        # Register worker in DB
        async with async_session() as db:
            worker = Worker(
                id=self.worker_id,
                hostname=socket.gethostname(),
                ip_address=socket.gethostbyname(socket.gethostname()) if hasattr(socket, 'gethostbyname') else '127.0.0.1',
                status="active",
                concurrency_limit=self.concurrency,
                active_jobs_count=0
            )
            db.add(worker)
            await db.commit()

        # Start loops
        self.heartbeat_task = asyncio.create_task(self.heartbeat_loop())
        self.cleanup_task = asyncio.create_task(self.cleanup_loop())
        self.polling_task = asyncio.create_task(self.polling_loop())

    async def stop(self):
        logger.info("Stopping worker gracefully...")
        self.running = False
        
        # Cancel daemon loops
        self.heartbeat_task.cancel()
        self.cleanup_task.cancel()
        self.polling_task.cancel()
        
        # Wait for active tasks to complete with a timeout
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to finish...")
            try:
                await asyncio.wait(self.active_tasks.values(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for tasks to finish. Re-queueing outstanding jobs.")
        
        # Re-queue any unfinished claimed/running jobs
        async with async_session() as db:
            stmt = select(Job).filter(Job.worker_id == self.worker_id, Job.status.in_(["claimed", "running"]))
            unfinished_jobs = (await db.execute(stmt)).scalars().all()
            for job in unfinished_jobs:
                job.status = "queued"
                job.worker_id = None
                job.error_message = "Worker shutdown during execution"
            
            # Set worker offline
            worker = await db.get(Worker, self.worker_id)
            if worker:
                worker.status = "offline"
                worker.active_jobs_count = 0
            
            await db.commit()
        logger.info("Worker stopped.")

    async def heartbeat_loop(self):
        while self.running:
            try:
                async with async_session() as db:
                    worker = await db.get(Worker, self.worker_id)
                    if worker:
                        worker.last_heartbeat_at = datetime.datetime.utcnow()
                        worker.active_jobs_count = len(self.active_tasks)
                        worker.status = "idle" if len(self.active_tasks) == 0 else "active"
                        await db.commit()
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
            await asyncio.sleep(5)

    async def cleanup_loop(self):
        """Periodically cleans up dead workers (no heartbeat > 15s) and re-queues their jobs."""
        while self.running:
            try:
                async with async_session() as db:
                    cutoff = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
                    # Find offline workers
                    stmt = select(Worker).filter(Worker.last_heartbeat_at < cutoff, Worker.status != "offline")
                    dead_workers = (await db.execute(stmt)).scalars().all()
                    
                    for w in dead_workers:
                        logger.warning(f"Worker {w.id} missed heartbeats. Marking offline and recovering jobs.")
                        w.status = "offline"
                        
                        # Find jobs claimed by this worker
                        job_stmt = select(Job).filter(Job.worker_id == w.id, Job.status.in_(["claimed", "running"]))
                        dead_jobs = (await db.execute(job_stmt)).scalars().all()
                        for job in dead_jobs:
                            logger.info(f"Recovering job {job.id} from dead worker {w.id}")
                            job.status = "queued"
                            job.worker_id = None
                            job.error_message = f"Recovered from offline worker {w.id}"
                            
                    await db.commit()
            except Exception as e:
                logger.error(f"Cleanup offline workers failed: {e}")
            await asyncio.sleep(10)

    async def polling_loop(self):
        while self.running:
            # Enforce local concurrency
            if len(self.active_tasks) >= self.concurrency:
                await asyncio.sleep(0.5)
                continue

            try:
                job = await self.claim_next_job()
                if job:
                    # Start execution asynchronously
                    task = asyncio.create_task(self.execute_job_flow(job))
                    self.active_tasks[job.id] = task
                    task.add_done_callback(lambda t, j_id=job.id: self.active_tasks.pop(j_id, None))
                else:
                    await asyncio.sleep(1) # Back off if no jobs are available
            except Exception as e:
                logger.error(f"Polling failed: {e}")
                await asyncio.sleep(2)

    async def claim_next_job(self) -> Optional[Job]:
        """Claim a job atomically taking queue concurrency limits and priorities into account."""
        async with async_session() as db:
            async with db.begin():
                now = datetime.datetime.utcnow()
                
                # Subquery to list active queue IDs and count their current active jobs
                # A queue is eligible if it is not paused AND its active jobs are less than its concurrency limit
                eligible_queues_stmt = select(Queue).filter(Queue.is_paused == False)
                queues = (await db.execute(eligible_queues_stmt)).scalars().all()
                
                eligible_queue_ids = []
                for q in queues:
                    # Count active jobs in this queue
                    cnt_stmt = select(func.count(Job.id)).filter(
                        Job.queue_id == q.id,
                        Job.status.in_(["running", "claimed"])
                    )
                    active_count = (await db.execute(cnt_stmt)).scalar_one()
                    if active_count < q.concurrency_limit:
                        eligible_queue_ids.append(q.id)

                if not eligible_queue_ids:
                    return None

                # Find candidate jobs
                # Order by combined priority (queue.priority + priority_override) desc, then created_at asc
                job_stmt = (
                    select(Job)
                    .join(Queue, Job.queue_id == Queue.id)
                    .filter(
                        Job.status == "queued",
                        Job.scheduled_at <= now,
                        Job.queue_id.in_(eligible_queue_ids)
                    )
                    .order_by((Queue.priority + Job.priority_override).desc(), Job.created_at.asc())
                    .limit(1)
                )
                
                job = (await db.execute(job_stmt)).scalars().first()
                if job:
                    # Atomically mark claimed
                    job.status = "claimed"
                    job.claimed_at = now
                    job.worker_id = self.worker_id
                    # Need to return an object bound to a session that won't be closed immediately,
                    # or we can refresh/detach it. We'll extract its fields.
                    job_data = {
                        "id": job.id,
                        "name": job.name,
                        "payload": job.payload,
                        "retry_count": job.retry_count,
                        "max_retries": job.max_retries,
                        "retry_policy_id": job.retry_policy_id
                    }
                    return job
                return None

    async def execute_job_flow(self, job: Job):
        job_id = job.id
        logger.info(f"Executing job {job_id} ({job.name})")
        
        # 1. Update job to running, and create execution entry
        start_time = datetime.datetime.utcnow()
        async with async_session() as db:
            db_job = await db.get(Job, job_id)
            if not db_job:
                return
            db_job.status = "running"
            
            execution = JobExecution(
                job_id=job_id,
                worker_id=self.worker_id,
                status="running",
                started_at=start_time
            )
            db.add(execution)
            await db.commit()
            execution_id = execution.id

        # 2. Execute simulated work
        payload_data = {}
        if job.payload:
            try:
                payload_data = json.loads(job.payload)
            except Exception:
                pass

        error_message = None
        status_res = "completed"
        
        try:
            await self.run_task_payload(job.name, payload_data)
        except Exception as e:
            status_res = "failed"
            error_message = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"Job {job_id} failed: {e}")

        # 3. Finalize execution and apply retry/dependency policies
        end_time = datetime.datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        async with async_session() as db:
            db_job = await db.get(Job, job_id)
            db_exec = await db.get(JobExecution, execution_id)
            
            db_exec.status = status_res
            db_exec.ended_at = end_time
            db_exec.duration_ms = duration_ms
            db_exec.error_message = error_message

            if status_res == "completed":
                db_job.status = "completed"
                db_job.completed_at = end_time
                db_job.error_message = None
                
                # UNBLOCK CHILD JOBS (Workflows Dependency Management)
                children_stmt = select(Job).filter(Job.parent_job_id == job_id, Job.status == "blocked")
                children = (await db.execute(children_stmt)).scalars().all()
                for child in children:
                    logger.info(f"Unblocking dependent child job {child.id} since parent {job_id} completed.")
                    child.status = "queued"
                    child.scheduled_at = datetime.datetime.utcnow()

            else:
                # Calculate retry policy
                db_job.retry_count += 1
                db_job.failed_at = end_time
                db_job.error_message = error_message

                if db_job.retry_count < db_job.max_retries:
                    # Get retry policy
                    delay = 5 # Default
                    if db_job.retry_policy_id:
                        policy = await db.get(RetryPolicy, db_job.retry_policy_id)
                        if policy:
                            delay = self.calculate_backoff(policy, db_job.retry_count)
                    
                    db_job.status = "queued"
                    db_job.scheduled_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=delay)
                    logger.info(f"Scheduling retry #{db_job.retry_count} for job {job_id} in {delay}s")
                else:
                    # Move to Dead Letter Queue (DLQ)
                    db_job.status = "dlq"
                    logger.warning(f"Job {job_id} exceeded max retries. Moving to DLQ.")
                    
                    dlq_entry = DeadLetterQueue(
                        job_id=db_job.id,
                        queue_id=db_job.queue_id,
                        name=db_job.name,
                        payload=db_job.payload,
                        error_message=error_message,
                        retry_count=db_job.retry_count
                    )
                    db.add(dlq_entry)

            await db.commit()

    def calculate_backoff(self, policy: RetryPolicy, attempt: int) -> int:
        if policy.strategy == "linear":
            return policy.base_delay * attempt
        elif policy.strategy == "exponential":
            return int(policy.base_delay * (policy.backoff_factor ** (attempt - 1)))
        else: # fixed
            return policy.base_delay

    async def run_task_payload(self, name: str, payload: dict):
        """Simulates execution of tasks based on the job name."""
        duration = payload.get("duration", 2)
        
        # Support artificial failure
        if payload.get("should_fail", False):
            # If fail_on_attempts is listed, fail only on those attempts
            # But here we just fail
            await asyncio.sleep(1)
            raise ValueError(payload.get("error_msg", "Simulated job failure"))

        if name == "http_request":
            url = payload.get("url", "https://httpbin.org/delay/1")
            method = payload.get("method", "GET")
            logger.info(f"Simulating API call: {method} {url}")
            await asyncio.sleep(duration)
            
        elif name == "calculation":
            logger.info("Running CPU-bound mathematical simulation...")
            await asyncio.sleep(duration)
            
        elif name == "send_email":
            logger.info(f"Sending simulated email to {payload.get('to', 'user@example.com')}")
            await asyncio.sleep(duration)
            
        else:
            # Default task execution sleep
            logger.info(f"Executing standard simulation task: {name}")
            await asyncio.sleep(duration)
