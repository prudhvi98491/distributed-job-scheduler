import asyncio
import datetime
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from backend.database import Base
from backend.models import User, Organization, Project, Queue, Job, RetryPolicy, JobExecution
from backend.worker import JobWorker

# Create an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(name="test_engine")
async def fixture_test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(name="db_session")
async def fixture_db_session(test_engine):
    session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    import backend.worker
    original_session = backend.worker.async_session
    backend.worker.async_session = session_maker
    try:
        async with session_maker() as session:
            yield session
    finally:
        backend.worker.async_session = original_session


@pytest.mark.asyncio
async def test_database_seeding_and_relations(db_session):
    # Create Organization
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.flush()

    # Create Project
    proj = Project(organization_id=org.id, name="Test Project")
    db_session.add(proj)
    await db_session.flush()

    # Create Retry Policy
    policy = RetryPolicy(
        name="Test Policy",
        strategy="fixed",
        base_delay=1,
        max_retries=2
    )
    db_session.add(policy)
    await db_session.flush()

    # Create Queue
    queue = Queue(
        project_id=proj.id,
        name="test-queue",
        priority=10,
        concurrency_limit=2,
        retry_policy_id=policy.id
    )
    db_session.add(queue)
    await db_session.commit()

    # Query relations
    result = await db_session.execute(select(Queue).filter(Queue.name == "test-queue"))
    saved_queue = result.scalars().first()
    assert saved_queue is not None
    assert saved_queue.priority == 10
    assert saved_queue.concurrency_limit == 2
    assert saved_queue.retry_policy_id == policy.id

@pytest.mark.asyncio
async def test_job_execution_lifecycle_and_retries(db_session):
    # Create required parent relations
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.flush()
    proj = Project(organization_id=org.id, name="Test Project")
    db_session.add(proj)
    await db_session.flush()
    policy = RetryPolicy(name="Fixed 1s", strategy="fixed", base_delay=1, max_retries=2)
    db_session.add(policy)
    await db_session.flush()
    queue = Queue(project_id=proj.id, name="default", priority=1, concurrency_limit=2, retry_policy_id=policy.id)
    db_session.add(queue)
    await db_session.flush()

    # 1. Enqueue job which will fail
    job_id = "test_job_1"
    job = Job(
        id=job_id,
        queue_id=queue.id,
        name="test_task",
        status="queued",
        payload='{"should_fail": true, "error_msg": "Intentional Failure", "duration": 0}',
        retry_count=0,
        max_retries=2,
        retry_policy_id=policy.id,
        scheduled_at=datetime.datetime.utcnow()
    )
    db_session.add(job)
    await db_session.commit()

    # Run a localized Worker cycle
    worker = JobWorker(concurrency=1)
    worker.worker_id = "test_worker"
    
    # We mock a small mock claim & execute cycle
    # Claim job
    claimed_job = await worker.claim_next_job()
    assert claimed_job is not None
    assert claimed_job.status == "claimed"
    
    # Execute job
    await worker.execute_job_flow(claimed_job)
    
    # Fetch job status from DB
    await db_session.refresh(job)
    # The job failed, and should be queued again for a retry (retry_count = 1 < max_retries = 2)
    assert job.status == "queued"
    assert job.retry_count == 1
    assert "Intentional Failure" in job.error_message

@pytest.mark.asyncio
async def test_workflow_dependencies_unblocking(db_session):
    # Setup base relations
    org = Organization(name="Test Org")
    db_session.add(org)
    await db_session.flush()
    proj = Project(organization_id=org.id, name="Test Project")
    db_session.add(proj)
    await db_session.flush()
    queue = Queue(project_id=proj.id, name="default", priority=1, concurrency_limit=2)
    db_session.add(queue)
    await db_session.flush()

    # Enqueue Parent job (A)
    parent_job = Job(
        id="parent_a",
        queue_id=queue.id,
        name="parent_task",
        status="queued",
        payload='{"duration": 0}',
        scheduled_at=datetime.datetime.utcnow()
    )
    
    # Enqueue Blocked Child job (B) dependent on Parent (A)
    child_job = Job(
        id="child_b",
        queue_id=queue.id,
        name="child_task",
        status="blocked",
        parent_job_id="parent_a",
        scheduled_at=datetime.datetime.utcnow()
    )
    
    db_session.add(parent_job)
    db_session.add(child_job)
    await db_session.commit()

    # Claim and execute parent
    worker = JobWorker(concurrency=1)
    worker.worker_id = "test_worker"
    
    claimed = await worker.claim_next_job()
    assert claimed.id == "parent_a"
    
    # Run parent
    await worker.execute_job_flow(claimed)
    
    # Check parent and child statuses
    await db_session.refresh(parent_job)
    await db_session.refresh(child_job)
    
    assert parent_job.status == "completed"
    # Child should be unblocked (status changed to queued)
    assert child_job.status == "queued"
