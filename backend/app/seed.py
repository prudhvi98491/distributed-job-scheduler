"""
Seed demo data: one user, org, project, queues, retry policies, and sample jobs.
Only runs if the database is empty.
"""
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import (
    User, Organization, OrganizationMember, Project,
    RetryPolicy, Queue, Job, Worker,
    OrgRole, JobStatus, RetryStrategy, WorkerStatus, new_uuid
)
from app.auth import hash_password

logger = logging.getLogger(__name__)


async def seed_demo_data():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(select(User))
        if existing.scalars().first():
            return

        logger.info("Seeding demo data...")

        # ── User ──────────────────────────────────────────────────────────
        admin = User(
            id=new_uuid(), email="admin@demo.com", name="Admin User",
            password_hash=hash_password("password123"), role="admin"
        )
        db.add(admin)
        await db.flush()

        # ── Organization ──────────────────────────────────────────────────
        org = Organization(
            id=new_uuid(), name="Acme Corp", slug="acme-corp", created_by=admin.id
        )
        db.add(org)
        db.add(OrganizationMember(org_id=org.id, user_id=admin.id, role=OrgRole.owner))
        await db.flush()

        # ── Project ───────────────────────────────────────────────────────
        project = Project(
            id=new_uuid(), org_id=org.id, name="Data Pipeline",
            slug="data-pipeline", description="ETL and background processing",
            created_by=admin.id
        )
        db.add(project)
        await db.flush()

        # ── Retry Policies ────────────────────────────────────────────────
        policy_exp = RetryPolicy(
            id=new_uuid(), name="Exponential Backoff",
            max_attempts=5, strategy=RetryStrategy.exponential_backoff,
            base_delay_ms=2000, max_delay_ms=120000
        )
        policy_fixed = RetryPolicy(
            id=new_uuid(), name="Fixed 5s",
            max_attempts=3, strategy=RetryStrategy.fixed,
            base_delay_ms=5000, max_delay_ms=5000
        )
        db.add(policy_exp)
        db.add(policy_fixed)
        await db.flush()

        # ── Queues ────────────────────────────────────────────────────────
        q_email = Queue(
            id=new_uuid(), project_id=project.id, name="email-notifications",
            description="Transactional email delivery",
            concurrency_limit=10, priority=5, retry_policy_id=policy_exp.id
        )
        q_report = Queue(
            id=new_uuid(), project_id=project.id, name="report-generation",
            description="PDF and CSV report generation",
            concurrency_limit=3, priority=3, retry_policy_id=policy_fixed.id
        )
        q_sync = Queue(
            id=new_uuid(), project_id=project.id, name="data-sync",
            description="External API data synchronization",
            concurrency_limit=5, priority=2
        )
        q_cleanup = Queue(
            id=new_uuid(), project_id=project.id, name="cleanup-tasks",
            description="Database cleanup and archival",
            concurrency_limit=2, priority=1
        )
        db.add_all([q_email, q_report, q_sync, q_cleanup])
        await db.flush()

        # ── Workers ───────────────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        workers = []
        worker_configs = [
            ("worker-alpha", "prod-host-01", [q_email.id, q_report.id], WorkerStatus.active),
            ("worker-beta", "prod-host-02", [q_sync.id, q_cleanup.id], WorkerStatus.active),
            ("worker-gamma", "prod-host-03", [q_email.id, q_sync.id], WorkerStatus.idle),
            ("worker-delta", "prod-host-04", [q_report.id, q_cleanup.id], WorkerStatus.stopped),
        ]
        for name, host, qids, status in worker_configs:
            w = Worker(
                id=new_uuid(), name=name, hostname=host, pid=1000 + len(workers),
                queue_ids=qids, max_concurrency=5,
                status=status,
                last_heartbeat=now if status != WorkerStatus.stopped else now - timedelta(minutes=5)
            )
            db.add(w)
            workers.append(w)
        await db.flush()

        # ── Jobs ──────────────────────────────────────────────────────────
        job_specs = [
            # email queue - mix of statuses
            (q_email.id, "send-welcome-email", {"to": "alice@example.com", "template": "welcome"}, JobStatus.completed, 0),
            (q_email.id, "send-welcome-email", {"to": "bob@example.com", "template": "welcome"}, JobStatus.completed, 0),
            (q_email.id, "send-invoice", {"to": "carol@example.com", "invoice_id": "INV-001"}, JobStatus.running, 1),
            (q_email.id, "send-invoice", {"to": "dan@example.com", "invoice_id": "INV-002"}, JobStatus.queued, 0),
            (q_email.id, "send-newsletter", {"campaign_id": "CAMP-042", "batch": 1}, JobStatus.queued, 0),
            (q_email.id, "send-newsletter", {"campaign_id": "CAMP-042", "batch": 2}, JobStatus.queued, 0),
            (q_email.id, "send-password-reset", {"to": "eve@example.com"}, JobStatus.failed, 2),
            (q_email.id, "send-password-reset", {"to": "frank@example.com"}, JobStatus.dead, 3),
            # report queue
            (q_report.id, "generate-pdf-report", {"report_type": "monthly", "month": "2026-06"}, JobStatus.completed, 0),
            (q_report.id, "generate-csv-export", {"table": "orders", "date_range": "30d"}, JobStatus.running, 1),
            (q_report.id, "generate-pdf-report", {"report_type": "quarterly", "quarter": "Q2-2026"}, JobStatus.queued, 0),
            (q_report.id, "generate-analytics", {"dashboard_id": "dash-001"}, JobStatus.scheduled, 0),
            # sync queue
            (q_sync.id, "sync-crm-contacts", {"source": "salesforce", "page": 1}, JobStatus.completed, 0),
            (q_sync.id, "sync-crm-contacts", {"source": "salesforce", "page": 2}, JobStatus.completed, 0),
            (q_sync.id, "sync-inventory", {"warehouse_id": "WH-01"}, JobStatus.running, 1),
            (q_sync.id, "sync-payments", {"provider": "stripe", "since": "2026-07-01"}, JobStatus.queued, 0),
            (q_sync.id, "sync-payments", {"provider": "paypal", "since": "2026-07-01"}, JobStatus.failed, 1),
            # cleanup queue
            (q_cleanup.id, "purge-old-logs", {"days_threshold": 90}, JobStatus.completed, 0),
            (q_cleanup.id, "archive-completed-jobs", {"batch_size": 1000}, JobStatus.queued, 0),
            (q_cleanup.id, "vacuum-database", {}, JobStatus.scheduled, 0),
        ]

        from app.models import DeadLetterQueue, JobLog, LogLevel
        from app.services.retry import generate_failure_summary

        for queue_id, job_type, payload, status, attempts in job_specs:
            job = Job(
                id=new_uuid(), queue_id=queue_id, type=job_type,
                payload=payload, status=status,
                priority=2, attempt_count=attempts, max_attempts=3,
                scheduled_at=now + timedelta(hours=2) if status == JobStatus.scheduled else None,
                started_at=now - timedelta(minutes=5) if status in (JobStatus.running, JobStatus.completed) else None,
                completed_at=now - timedelta(minutes=2) if status == JobStatus.completed else None,
                claimed_by=workers[0].id if status in (JobStatus.running, JobStatus.claimed) else None,
            )
            db.add(job)
            await db.flush()

            # Add log entries
            db.add(JobLog(
                id=new_uuid(), job_id=job.id, level=LogLevel.info,
                message=f"Job enqueued: {job_type}"
            ))
            if status == JobStatus.completed:
                db.add(JobLog(
                    id=new_uuid(), job_id=job.id, level=LogLevel.info,
                    message="Job completed successfully"
                ))
            elif status in (JobStatus.failed, JobStatus.dead):
                db.add(JobLog(
                    id=new_uuid(), job_id=job.id, level=LogLevel.error,
                    message=f"Job failed: Connection timeout after 30s"
                ))

            # Create DLQ entry for dead jobs
            if status == JobStatus.dead:
                summary = generate_failure_summary(job_type, "Connection timeout after 30s", attempts)
                dlq = DeadLetterQueue(
                    id=new_uuid(), original_job_id=job.id, queue_id=queue_id,
                    payload=payload,
                    failure_reason=f"Exceeded max attempts (3)",
                    last_error="Connection timeout after 30s",
                    ai_summary=summary,
                    can_retry=True,
                )
                db.add(dlq)

        await db.commit()
        logger.info("Demo data seeded successfully")
        logger.info("Login: admin@demo.com / password123")
