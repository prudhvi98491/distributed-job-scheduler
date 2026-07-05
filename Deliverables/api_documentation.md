# Overdrive API Documentation

Overdrive exposes a RESTful web API for organization isolation, queue configuration, task dispatching, cron job scheduling, and metrics aggregation.

## Security & Authentication
All request paths under `/api/queues`, `/api/jobs`, and `/api/metrics` require authentication.
* **Mechanism**: JWT Bearer Token.
* **Header Format**: `Authorization: Bearer <JWT_TOKEN>`

---

## Authentication Endpoints

### 1. Register User
Registers a new user and generates salted bcrypt credentials.
* **Method**: `POST`
* **Path**: `/api/auth/register`
* **Request Body**:
```json
{
  "username": "user123",
  "password": "securepassword",
  "role": "admin"
}
```
* **Response (200 OK)**:
```json
{
  "id": 1,
  "username": "user123",
  "role": "admin"
}
```

### 2. User Login
Validates credentials and issues an access token.
* **Method**: `POST`
* **Path**: `/api/auth/login`
* **Request Body**:
```json
{
  "username": "user123",
  "password": "securepassword"
}
```
* **Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer"
}
```

---

## Queue Configuration Endpoints

### 1. Create Queue
Configures a queue defining concurrent limits and priorities.
* **Method**: `POST`
* **Path**: `/api/queues`
* **Request Body**:
```json
{
  "project_id": 1,
  "name": "image-processing",
  "concurrency_limit": 5,
  "priority": 10,
  "retry_policy": "exponential"
}
```
* **Response (201 Created)**:
```json
{
  "id": 1,
  "project_id": 1,
  "name": "image-processing",
  "concurrency_limit": 5,
  "priority": 10,
  "retry_policy": "exponential"
}
```

### 2. Update Queue
* **Method**: `PATCH`
* **Path**: `/api/queues/{queue_id}`
* **Request Body**:
```json
{
  "concurrency_limit": 10,
  "priority": 20
}
```
* **Response (200 OK)**: Updated queue object.

---

## Job Management Endpoints

### 1. Enqueue Job
* **Method**: `POST`
* **Path**: `/api/jobs`
* **Request Body**:
```json
{
  "queue_id": 1,
  "payload": "{\"task\":\"resize\",\"filename\":\"avatar.png\"}",
  "run_at": "2026-07-05T12:00:00Z",
  "parent_job_id": null
}
```
* **Response (201 Created)**: Job object with state `"queued"` (or `"blocked"` if `parent_job_id` is active).

### 2. Batch Enqueue Jobs
* **Method**: `POST`
* **Path**: `/api/jobs/batch`
* **Request Body**:
```json
{
  "queue_id": 1,
  "payloads": [
    "{\"id\":1}",
    "{\"id\":2}"
  ]
}
```
* **Response (201 Created)**: List of successfully enqueued jobs.

### 3. Replay Failed Job (DLQ)
Manually requeues a failed job from the DLQ.
* **Method**: `POST`
* **Path**: `/api/jobs/{job_id}/retry`
* **Response (200 OK)**: Reset job object.

---

## Real-Time Metrics

### Get Queue and Worker Throughput
Aggregated counts of running, failed, and completed tasks alongside registered host worker health.
* **Method**: `GET`
* **Path**: `/api/metrics`
* **Response (200 OK)**:
```json
{
  "total_jobs": 150,
  "completed_jobs": 120,
  "failed_jobs": 5,
  "running_jobs": 3,
  "active_workers": 2,
  "queue_metrics": [
    {
      "queue_name": "default",
      "queued": 22,
      "running": 1
    }
  ]
}
```
