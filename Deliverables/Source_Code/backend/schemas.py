from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Org and Project Schemas
class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectCreate(BaseModel):
    organization_id: int
    name: str

class ProjectResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

# Retry Policy Schemas
class RetryPolicyCreate(BaseModel):
    name: str
    strategy: str = "fixed" # fixed, linear, exponential
    base_delay: int = 5 # seconds
    max_retries: int = 3
    backoff_factor: float = 2.0

class RetryPolicyResponse(BaseModel):
    id: int
    name: str
    strategy: str
    base_delay: int
    max_retries: int
    backoff_factor: float
    created_at: datetime

    class Config:
        from_attributes = True

# Queue Schemas
class QueueCreate(BaseModel):
    project_id: int
    name: str
    priority: Optional[int] = 1
    concurrency_limit: Optional[int] = 5
    retry_policy_id: Optional[int] = None

class QueueUpdate(BaseModel):
    priority: Optional[int] = None
    concurrency_limit: Optional[int] = None
    retry_policy_id: Optional[int] = None
    is_paused: Optional[bool] = None

class QueueResponse(BaseModel):
    id: int
    project_id: int
    name: str
    priority: int
    concurrency_limit: int
    retry_policy_id: Optional[int]
    is_paused: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Job Schemas
class JobCreate(BaseModel):
    queue_name: str
    name: str
    payload: Optional[Dict[str, Any]] = None
    priority_override: Optional[int] = 0
    delay_seconds: Optional[int] = None
    parent_job_id: Optional[str] = None

class BatchJobCreate(BaseModel):
    queue_name: str
    name: str
    jobs: List[Dict[str, Any]] # list of payloads
    priority_override: Optional[int] = 0

class JobResponse(BaseModel):
    id: str
    queue_id: int
    name: str
    status: str
    priority_override: int
    retry_count: int
    max_retries: int
    retry_policy_id: Optional[int]
    worker_id: Optional[str]
    parent_job_id: Optional[str]
    root_job_id: Optional[str]
    scheduled_at: datetime
    claimed_at: Optional[datetime]
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    created_at: datetime
    error_message: Optional[str]

    class Config:
        from_attributes = True

class JobExecutionResponse(BaseModel):
    id: int
    job_id: str
    worker_id: Optional[str]
    status: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    started_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True

class JobDetailsResponse(BaseModel):
    job: JobResponse
    executions: List[JobExecutionResponse]

    class Config:
        from_attributes = True

# Worker Schemas
class WorkerResponse(BaseModel):
    id: str
    hostname: str
    ip_address: Optional[str]
    status: str
    concurrency_limit: int
    active_jobs_count: int
    registered_at: datetime
    last_heartbeat_at: datetime

    class Config:
        from_attributes = True

# Cron Job Schemas
class CronJobCreate(BaseModel):
    queue_name: str
    name: str
    cron_expression: str
    payload: Optional[Dict[str, Any]] = None

class CronJobResponse(BaseModel):
    id: int
    queue_id: int
    name: str
    cron_expression: str
    payload: Optional[str]
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
