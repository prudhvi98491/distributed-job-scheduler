import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
)
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False) # admin, user, viewer
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organizations = relationship("OrganizationUser", back_populates="user")

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")

class OrganizationUser(Base):
    __tablename__ = "organization_users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, default="member") # admin, member

    # Relationships
    organization = relationship("Organization", back_populates="users")
    user = relationship("User", back_populates="organizations")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    queues = relationship("Queue", back_populates="project", cascade="all, delete-orphan")

class RetryPolicy(Base):
    __tablename__ = "retry_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    strategy = Column(String, default="fixed") # fixed, linear, exponential
    base_delay = Column(Integer, default=5) # in seconds
    max_retries = Column(Integer, default=3)
    backoff_factor = Column(Float, default=2.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    queues = relationship("Queue", back_populates="retry_policy")

class Queue(Base):
    __tablename__ = "queues"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, unique=True, index=True, nullable=False)
    priority = Column(Integer, default=1) # Higher number = higher priority
    concurrency_limit = Column(Integer, default=5)
    retry_policy_id = Column(Integer, ForeignKey("retry_policies.id", ondelete="SET NULL"), nullable=True)
    is_paused = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="queues")
    retry_policy = relationship("RetryPolicy", back_populates="queues")
    jobs = relationship("Job", back_populates="queue", cascade="all, delete-orphan")
    cron_jobs = relationship("CronJob", back_populates="queue", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True) # UUID
    queue_id = Column(Integer, ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, default="queued") # queued, scheduled, claimed, running, completed, failed, dlq
    payload = Column(Text, nullable=True) # JSON payload
    priority_override = Column(Integer, default=0) # Added to queue priority
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    retry_policy_id = Column(Integer, ForeignKey("retry_policies.id", ondelete="SET NULL"), nullable=True)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)

    parent_job_id = Column(String, ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    root_job_id = Column(String, nullable=True)

    scheduled_at = Column(DateTime, default=datetime.datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    error_message = Column(Text, nullable=True)

    # Relationships
    queue = relationship("Queue", back_populates="jobs")
    executions = relationship("JobExecution", back_populates="job", cascade="all, delete-orphan")
    worker = relationship("Worker", back_populates="jobs")

class JobExecution(Base):
    __tablename__ = "job_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(String, ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False) # running, completed, failed
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="executions")
    worker = relationship("Worker")

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True, index=True) # hostname or UUID
    hostname = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    status = Column(String, default="active") # active, idle, offline
    concurrency_limit = Column(Integer, default=10)
    active_jobs_count = Column(Integer, default=0)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_heartbeat_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    jobs = relationship("Job", back_populates="worker")

class CronJob(Base):
    __tablename__ = "cron_jobs"

    id = Column(Integer, primary_key=True, index=True)
    queue_id = Column(Integer, ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)
    payload = Column(Text, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    queue = relationship("Queue", back_populates="cron_jobs")

class DeadLetterQueue(Base):
    __tablename__ = "dead_letter_queue"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, nullable=False)
    queue_id = Column(Integer, ForeignKey("queues.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    payload = Column(Text, nullable=True)
    failed_at = Column(DateTime, default=datetime.datetime.utcnow)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
