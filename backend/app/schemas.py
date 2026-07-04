from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from app.models import (
    UserRole, OrgRole, JobStatus, RetryStrategy,
    WorkerStatus, LogLevel, ExecutionStatus
)


# ── Auth ──────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Organizations ─────────────────────────────────────────────────────────────
class OrgCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9\-]+$")


class OrgOut(BaseModel):
    id: str
    name: str
    slug: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberAdd(BaseModel):
    user_id: str
    role: OrgRole = OrgRole.member


# ── Projects ──────────────────────────────────────────────────────────────────
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9\-]+$")
    description: str = ""


class ProjectOut(BaseModel):
    id: str
    org_id: str
    name: str
    slug: str
    description: str
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Retry Policies ────────────────────────────────────────────────────────────
class RetryPolicyCreate(BaseModel):
    name: str
    max_attempts: int = Field(default=3, ge=1, le=20)
    strategy: RetryStrategy = RetryStrategy.exponential_backoff
    base_delay_ms: int = Field(default=1000, ge=100)
    max_delay_ms: int = Field(default=60000, ge=1000)


class RetryPolicyOut(BaseModel):
    id: str
    name: str
    max_attempts: int
    strategy: RetryStrategy
    base_delay_ms: int
    max_delay_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Queues ────────────────────────────────────────────────────────────────────
class QueueCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    concurrency_limit: int = Field(default=5, ge=1, le=100)
    priority: int = Field(default=0, ge=0, le=100)
    retry_policy_id: Optional[str] = None


class QueueUpdate(BaseModel):
    concurrency_limit: Optional[int] = Field(default=None, ge=1, le=100)
    priority: Optional[int] = Field(default=None, ge=0, le=100)
    retry_policy_id: Optional[str] = None
    description: Optional[str] = None


class QueueOut(BaseModel):
    id: str
    project_id: str
    name: str
    description: str
    concurrency_limit: int
    priority: int
    paused: bool
    retry_policy_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QueueStats(BaseModel):
    queue_id: str
    queue_name: str
    total: int
    queued: int
    scheduled: int
    running: int
    completed: int
    failed: int
    dead: int
    cancelled: int


# ── Jobs ──────────────────────────────────────────────────────────────────────
class JobEnqueue(BaseModel):
    type: str = "default"
    payload: Dict[str, Any] = {}
    priority: int = Field(default=0, ge=0, le=100)
    scheduled_at: Optional[datetime] = None
    cron_expression: Optional[str] = None
    is_recurring: bool = False
    max_attempts: int = Field(default=3, ge=1, le=20)
    idempotency_key: Optional[str] = None


class BatchEnqueue(BaseModel):
    jobs: List[JobEnqueue] = Field(min_length=1, max_length=1000)


class JobOut(BaseModel):
    id: str
    queue_id: str
    type: str
    payload: Dict[str, Any]
    status: JobStatus
    priority: int
    scheduled_at: Optional[datetime]
    cron_expression: Optional[str]
    is_recurring: bool
    claimed_at: Optional[datetime]
    claimed_by: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    attempt_count: int
    max_attempts: int
    idempotency_key: Optional[str]
    next_retry_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobFilter(BaseModel):
    status: Optional[JobStatus] = None
    type: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ── Workers ───────────────────────────────────────────────────────────────────
class WorkerRegister(BaseModel):
    name: str
    hostname: str = "localhost"
    pid: Optional[int] = None
    queue_ids: List[str] = []
    max_concurrency: int = Field(default=5, ge=1, le=50)
    metadata: Dict[str, Any] = {}


class WorkerHeartbeatIn(BaseModel):
    jobs_running: int = 0
    jobs_completed: int = 0
    jobs_failed: int = 0
    cpu_pct: float = 0.0
    mem_mb: float = 0.0
    status: WorkerStatus = WorkerStatus.active


class WorkerOut(BaseModel):
    id: str
    name: str
    hostname: str
    pid: Optional[int]
    status: WorkerStatus
    queue_ids: List[str]
    max_concurrency: int
    last_heartbeat: Optional[datetime]
    registered_at: datetime

    model_config = {"from_attributes": True}


class ClaimRequest(BaseModel):
    queue_ids: Optional[List[str]] = None
    max_jobs: int = Field(default=1, ge=1, le=10)


class CompleteJobRequest(BaseModel):
    execution_id: str
    status: ExecutionStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_stack: Optional[str] = None
    duration_ms: Optional[int] = None


# ── Executions ────────────────────────────────────────────────────────────────
class ExecutionOut(BaseModel):
    id: str
    job_id: str
    worker_id: Optional[str]
    attempt_number: int
    status: ExecutionStatus
    started_at: datetime
    finished_at: Optional[datetime]
    duration_ms: Optional[int]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]

    model_config = {"from_attributes": True}


# ── Logs ──────────────────────────────────────────────────────────────────────
class LogOut(BaseModel):
    id: str
    job_id: str
    execution_id: Optional[str]
    level: LogLevel
    message: str
    logged_at: datetime

    model_config = {"from_attributes": True}


# ── DLQ ───────────────────────────────────────────────────────────────────────
class DLQOut(BaseModel):
    id: str
    original_job_id: str
    queue_id: str
    payload: Dict[str, Any]
    failure_reason: Optional[str]
    last_error: Optional[str]
    ai_summary: Optional[str]
    final_attempt_at: datetime
    created_at: datetime
    can_retry: bool

    model_config = {"from_attributes": True}


# ── Metrics ───────────────────────────────────────────────────────────────────
class SystemOverview(BaseModel):
    total_queues: int
    total_jobs: int
    queued: int
    running: int
    completed_24h: int
    failed_24h: int
    dead: int
    active_workers: int
    idle_workers: int


class ThroughputPoint(BaseModel):
    timestamp: str
    completed: int
    failed: int


class LatencyStats(BaseModel):
    queue_id: str
    queue_name: str
    avg_duration_ms: Optional[float]
    min_duration_ms: Optional[int]
    max_duration_ms: Optional[int]
    p95_duration_ms: Optional[float]
