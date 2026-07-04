import uuid
import enum
import json
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SAEnum, Float, JSON, event
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.dialects.sqlite import JSON as SAJSON


def utcnow():
    return datetime.now(timezone.utc)


def new_uuid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    admin = "admin"
    member = "member"


class OrgRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class JobStatus(str, enum.Enum):
    queued = "queued"
    scheduled = "scheduled"
    claimed = "claimed"
    running = "running"
    completed = "completed"
    failed = "failed"
    dead = "dead"
    cancelled = "cancelled"


class RetryStrategy(str, enum.Enum):
    fixed = "fixed"
    linear_backoff = "linear_backoff"
    exponential_backoff = "exponential_backoff"


class WorkerStatus(str, enum.Enum):
    active = "active"
    idle = "idle"
    stopped = "stopped"


class LogLevel(str, enum.Enum):
    debug = "debug"
    info = "info"
    warn = "warn"
    error = "error"


class ExecutionStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"


# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=new_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False, default="")
    role = Column(SAEnum(UserRole), default=UserRole.member, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    org_memberships = relationship("OrganizationMember", back_populates="user")
    organizations = relationship("Organization", back_populates="creator")


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    creator = relationship("User", back_populates="organizations")
    members = relationship("OrganizationMember", back_populates="organization")
    projects = relationship("Project", back_populates="organization")


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    org_id = Column(String, ForeignKey("organizations.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    role = Column(SAEnum(OrgRole), default=OrgRole.member, nullable=False)
    joined_at = Column(DateTime(timezone=True), default=utcnow)

    organization = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="org_memberships")


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=new_uuid)
    org_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False)
    description = Column(Text, default="")
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organization = relationship("Organization", back_populates="projects")
    queues = relationship("Queue", back_populates="project")


class RetryPolicy(Base):
    __tablename__ = "retry_policies"
    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    max_attempts = Column(Integer, default=3)
    strategy = Column(SAEnum(RetryStrategy), default=RetryStrategy.exponential_backoff)
    base_delay_ms = Column(Integer, default=1000)
    max_delay_ms = Column(Integer, default=60000)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    queues = relationship("Queue", back_populates="retry_policy")


class Queue(Base):
    __tablename__ = "queues"
    id = Column(String, primary_key=True, default=new_uuid)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    concurrency_limit = Column(Integer, default=5)
    priority = Column(Integer, default=0)
    paused = Column(Boolean, default=False)
    retry_policy_id = Column(String, ForeignKey("retry_policies.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="queues")
    retry_policy = relationship("RetryPolicy", back_populates="queues")
    jobs = relationship("Job", back_populates="queue")


class Worker(Base):
    __tablename__ = "workers"
    id = Column(String, primary_key=True, default=new_uuid)
    name = Column(String, nullable=False)
    hostname = Column(String, nullable=False, default="localhost")
    pid = Column(Integer, nullable=True)
    status = Column(SAEnum(WorkerStatus), default=WorkerStatus.idle)
    queue_ids = Column(JSON, default=list)   # list of queue UUIDs
    max_concurrency = Column(Integer, default=5)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), default=utcnow)
    metadata_ = Column("metadata", JSON, default=dict)

    heartbeats = relationship("WorkerHeartbeat", back_populates="worker")
    jobs = relationship("Job", back_populates="claimed_by_worker")
    executions = relationship("JobExecution", back_populates="worker")


class WorkerHeartbeat(Base):
    __tablename__ = "worker_heartbeats"
    id = Column(String, primary_key=True, default=new_uuid)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=False, index=True)
    heartbeat_at = Column(DateTime(timezone=True), default=utcnow)
    jobs_running = Column(Integer, default=0)
    jobs_completed = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)
    cpu_pct = Column(Float, default=0.0)
    mem_mb = Column(Float, default=0.0)

    worker = relationship("Worker", back_populates="heartbeats")


class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=new_uuid)
    queue_id = Column(String, ForeignKey("queues.id"), nullable=False, index=True)
    type = Column(String, nullable=False, default="default")
    payload = Column(JSON, default=dict)
    status = Column(SAEnum(JobStatus), default=JobStatus.queued, nullable=False, index=True)
    priority = Column(Integer, default=0, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    cron_expression = Column(String, nullable=True)
    is_recurring = Column(Boolean, default=False)
    claimed_at = Column(DateTime(timezone=True), nullable=True)
    claimed_by = Column(String, ForeignKey("workers.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    idempotency_key = Column(String, nullable=True, unique=True, index=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    queue = relationship("Queue", back_populates="jobs")
    claimed_by_worker = relationship("Worker", back_populates="jobs")
    executions = relationship("JobExecution", back_populates="job")
    logs = relationship("JobLog", back_populates="job")
    dlq_entry = relationship("DeadLetterQueue", back_populates="original_job", uselist=False)


class JobExecution(Base):
    __tablename__ = "job_executions"
    id = Column(String, primary_key=True, default=new_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    worker_id = Column(String, ForeignKey("workers.id"), nullable=True)
    attempt_number = Column(Integer, default=1)
    status = Column(SAEnum(ExecutionStatus), default=ExecutionStatus.running)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_stack = Column(Text, nullable=True)

    job = relationship("Job", back_populates="executions")
    worker = relationship("Worker", back_populates="executions")
    logs = relationship("JobLog", back_populates="execution")


class JobLog(Base):
    __tablename__ = "job_logs"
    id = Column(String, primary_key=True, default=new_uuid)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False, index=True)
    execution_id = Column(String, ForeignKey("job_executions.id"), nullable=True)
    level = Column(SAEnum(LogLevel), default=LogLevel.info)
    message = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    logged_at = Column(DateTime(timezone=True), default=utcnow)

    job = relationship("Job", back_populates="logs")
    execution = relationship("JobExecution", back_populates="logs")


class DeadLetterQueue(Base):
    __tablename__ = "dead_letter_queue"
    id = Column(String, primary_key=True, default=new_uuid)
    original_job_id = Column(String, ForeignKey("jobs.id"), nullable=False, unique=True, index=True)
    queue_id = Column(String, ForeignKey("queues.id"), nullable=False)
    payload = Column(JSON, default=dict)
    failure_reason = Column(Text, nullable=True)
    last_error = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    final_attempt_at = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    can_retry = Column(Boolean, default=True)

    original_job = relationship("Job", back_populates="dlq_entry")
