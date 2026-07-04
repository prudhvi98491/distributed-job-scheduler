"""
Sample Worker Process
---------------------
Demonstrates the full worker lifecycle:
  - Register with the scheduler
  - Send heartbeats every 10s
  - Poll for jobs, claim atomically, execute with realistic simulation
  - Report completion or failure (to trigger retry/DLQ)
  - Handle graceful shutdown

Usage:
    cd backend
    python -m worker.sample_worker --queue email-notifications --queue data-sync
"""
import asyncio
import argparse
import logging
import random
import signal
import sys
import os
import time
from datetime import datetime, timezone

import httpx

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("worker")

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2"))
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "10"))


# ── Job Handlers ──────────────────────────────────────────────────────────────

async def handle_send_email(payload: dict) -> dict:
    """Simulate sending an email."""
    to = payload.get("to", "unknown")
    template = payload.get("template", "default")
    logger.info(f"  📧 Sending {template} email to {to}...")
    await asyncio.sleep(random.uniform(0.5, 2.0))
    if random.random() < 0.05:  # 5% failure rate
        raise Exception(f"SMTP connection refused: could not connect to mail.example.com:587")
    return {"delivered": True, "recipient": to, "template": template}


async def handle_generate_report(payload: dict) -> dict:
    """Simulate generating a PDF/CSV report."""
    report_type = payload.get("report_type", "default")
    logger.info(f"  📊 Generating {report_type} report...")
    await asyncio.sleep(random.uniform(2.0, 5.0))
    if random.random() < 0.08:  # 8% failure
        raise Exception("Timeout: report generation exceeded 5s limit")
    file_size = random.randint(50, 500)
    return {"file": f"report_{report_type}_{int(time.time())}.pdf", "size_kb": file_size}


async def handle_sync_data(payload: dict) -> dict:
    """Simulate syncing data from an external API."""
    source = payload.get("source", payload.get("provider", "unknown"))
    logger.info(f"  🔄 Syncing from {source}...")
    await asyncio.sleep(random.uniform(1.0, 4.0))
    if random.random() < 0.1:  # 10% failure
        raise Exception(f"Rate limit exceeded: {source} API returned 429 Too Many Requests")
    records = random.randint(10, 500)
    return {"records_synced": records, "source": source}


async def handle_cleanup(payload: dict) -> dict:
    """Simulate database cleanup."""
    logger.info(f"  🧹 Running cleanup task...")
    await asyncio.sleep(random.uniform(0.5, 3.0))
    deleted = random.randint(100, 5000)
    return {"records_deleted": deleted}


async def handle_default(payload: dict) -> dict:
    """Default handler for unknown job types."""
    logger.info(f"  ⚙️  Processing generic job...")
    await asyncio.sleep(random.uniform(0.2, 1.5))
    return {"processed": True}


JOB_HANDLERS = {
    "send-welcome-email": handle_send_email,
    "send-invoice": handle_send_email,
    "send-newsletter": handle_send_email,
    "send-password-reset": handle_send_email,
    "generate-pdf-report": handle_generate_report,
    "generate-csv-export": handle_generate_report,
    "generate-analytics": handle_generate_report,
    "sync-crm-contacts": handle_sync_data,
    "sync-inventory": handle_sync_data,
    "sync-payments": handle_sync_data,
    "purge-old-logs": handle_cleanup,
    "archive-completed-jobs": handle_cleanup,
    "vacuum-database": handle_cleanup,
}


# ── Worker Class ──────────────────────────────────────────────────────────────

class SampleWorker:
    def __init__(self, name: str, queue_ids: list, token: str):
        self.name = name
        self.queue_ids = queue_ids
        self.token = token
        self.worker_id: str = None
        self.running = True
        self.jobs_completed = 0
        self.jobs_failed = 0
        self.active_jobs = 0

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    async def register(self, client: httpx.AsyncClient):
        import socket
        resp = await client.post(
            f"{API_BASE}/api/workers",
            json={
                "name": self.name,
                "hostname": socket.gethostname(),
                "pid": os.getpid(),
                "queue_ids": self.queue_ids,
                "max_concurrency": 5,
                "metadata": {"version": "1.0.0", "language": "python"},
            },
            headers=self.headers(),
        )
        resp.raise_for_status()
        data = resp.json()
        self.worker_id = data["id"]
        logger.info(f"✅ Registered as worker {self.worker_id} ({self.name})")

    async def send_heartbeat(self, client: httpx.AsyncClient):
        try:
            await client.post(
                f"{API_BASE}/api/workers/{self.worker_id}/heartbeat",
                json={
                    "jobs_running": self.active_jobs,
                    "jobs_completed": self.jobs_completed,
                    "jobs_failed": self.jobs_failed,
                    "cpu_pct": random.uniform(10, 60),
                    "mem_mb": random.uniform(100, 400),
                    "status": "active" if self.active_jobs > 0 else "idle",
                },
                headers=self.headers(),
            )
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    async def execute_job(self, job: dict, execution_id: str, client: httpx.AsyncClient):
        """Execute a single job and report completion."""
        job_id = job["job_id"]
        job_type = job.get("type", "default")
        payload = job.get("payload", {})

        logger.info(f"🚀 Executing job {job_id} (type={job_type})")
        self.active_jobs += 1
        start_ms = int(time.time() * 1000)

        try:
            handler = JOB_HANDLERS.get(job_type, handle_default)
            result = await handler(payload)
            duration_ms = int(time.time() * 1000) - start_ms
            self.jobs_completed += 1
            logger.info(f"✅ Job {job_id} completed in {duration_ms}ms")

            await client.post(
                f"{API_BASE}/api/workers/{self.worker_id}/complete",
                json={
                    "execution_id": execution_id,
                    "status": "completed",
                    "result": result,
                    "duration_ms": duration_ms,
                },
                headers=self.headers(),
            )
        except Exception as e:
            duration_ms = int(time.time() * 1000) - start_ms
            self.jobs_failed += 1
            logger.error(f"❌ Job {job_id} failed: {e}")

            await client.post(
                f"{API_BASE}/api/workers/{self.worker_id}/complete",
                json={
                    "execution_id": execution_id,
                    "status": "failed",
                    "error_message": str(e),
                    "error_stack": f"Traceback in {job_type} handler",
                    "duration_ms": duration_ms,
                },
                headers=self.headers(),
            )
        finally:
            self.active_jobs -= 1

    async def poll_and_execute(self, client: httpx.AsyncClient):
        """Poll for jobs and execute them concurrently."""
        try:
            resp = await client.post(
                f"{API_BASE}/api/workers/{self.worker_id}/claim",
                json={"queue_ids": self.queue_ids, "max_jobs": 3},
                headers=self.headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            jobs = data.get("jobs", [])

            if jobs:
                tasks = [
                    self.execute_job(j, j["execution_id"], client)
                    for j in jobs
                ]
                await asyncio.gather(*tasks)
        except Exception as e:
            logger.warning(f"Poll error: {e}")

    async def run(self):
        """Main worker loop."""
        logger.info(f"🔧 Starting worker: {self.name}")
        last_heartbeat = 0

        async with httpx.AsyncClient(timeout=30.0) as client:
            await self.register(client)

            while self.running:
                now = time.time()

                # Send heartbeat
                if now - last_heartbeat > HEARTBEAT_INTERVAL:
                    await self.send_heartbeat(client)
                    last_heartbeat = now

                # Poll for jobs
                await self.poll_and_execute(client)
                await asyncio.sleep(POLL_INTERVAL)

            # Final heartbeat on shutdown
            await client.post(
                f"{API_BASE}/api/workers/{self.worker_id}/heartbeat",
                json={"status": "stopped", "jobs_running": 0,
                      "jobs_completed": self.jobs_completed, "jobs_failed": self.jobs_failed,
                      "cpu_pct": 0, "mem_mb": 0},
                headers=self.headers(),
            )
            logger.info(f"👋 Worker {self.name} shut down gracefully. "
                        f"Completed: {self.jobs_completed}, Failed: {self.jobs_failed}")

    def stop(self):
        self.running = False


async def main():
    parser = argparse.ArgumentParser(description="Sample Distributed Job Worker")
    parser.add_argument("--name", default=f"worker-{os.getpid()}", help="Worker name")
    parser.add_argument("--email", default="admin@demo.com", help="API user email")
    parser.add_argument("--password", default="password123", help="API user password")
    parser.add_argument("--queues", nargs="*", default=[], help="Queue IDs to subscribe to")
    args = parser.parse_args()

    # Login to get token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{API_BASE}/api/auth/login",
            json={"email": args.email, "password": args.password}
        )
        if resp.status_code != 200:
            logger.error(f"Login failed: {resp.text}")
            sys.exit(1)
        token = resp.json()["access_token"]
        logger.info("🔑 Authenticated successfully")

        # If no queue IDs specified, fetch all queues
        queue_ids = args.queues
        if not queue_ids:
            q_resp = await client.get(
                f"{API_BASE}/api/queues",
                headers={"Authorization": f"Bearer {token}"}
            )
            if q_resp.status_code == 200:
                queue_ids = [q["id"] for q in q_resp.json()]
                logger.info(f"📋 Subscribed to {len(queue_ids)} queues")

    worker = SampleWorker(name=args.name, queue_ids=queue_ids, token=token)

    # Graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, worker.stop)
        except NotImplementedError:
            pass  # Windows

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
