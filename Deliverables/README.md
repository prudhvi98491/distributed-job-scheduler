# Overdrive | Distributed Job Scheduler

A production-grade, distributed asynchronous background job scheduler and monitoring dashboard built with FastAPI, SQLite (in high-concurrency WAL mode), SQLAlchemy, and a glassmorphic HTML/JS/CSS frontend.

---

## 🚀 Key Features

* **Tenant and Project Management**: Seamlessly isolate tasks and resources using multi-tenant Organization and Project boundaries.
* **Granular Queue Configurations**: Manage queue priority weights, concurrency limits, and custom retry policies with hot pause/resume controllers.
* **Sophisticated Job Lifecycle**:
  * **Immediate & Delayed Enqueueing**: Dispatch jobs instantly or schedule them with a future start delay.
  * **Batching**: Enqueue bulk job payloads in a single transaction.
  * **Workflow Pipeline Dependencies**: Chain executions sequentially (e.g., Job B starts `blocked` and automatically transitions to `queued` once parent Job A completes).
  * **Cron Recurring Schedules**: Register cron patterns (e.g., `*/10 * * * * *` for every 10 seconds) that trigger jobs automatically.
* **Resilient Worker Service**:
  * Atomically claims tasks using transactional queue boundaries to prevent duplicate execution.
  * Sends active heartbeats to database node register.
  * Re-queues running jobs automatically if a worker goes offline (misses heartbeats for >15 seconds).
  * Gracefully handles termination signals (`SIGINT`/`SIGTERM`) to finish running tasks and safely release claims on remaining jobs.
* **Custom Retry Policies**: Enforce Fixed delay, Linear backoff, or Exponential backoff on job failures, routing permanent failures into the Dead Letter Queue (DLQ) for review.
* **Glassmorphic Single Page Dashboard**: Real-time polling monitoring queue throughput, worker node status, detailed executions timeline, and one-click manual replays for failed/DLQ jobs.

---

## 🛠️ Technology Stack

* **Backend Framework**: Python 3.11, FastAPI, Uvicorn
* **Database & ORM**: SQLite (WAL Journal mode, Busy Timeout 5000ms), SQLAlchemy (Asynchronous database connections via `aiosqlite`)
* **Cron Calculations**: `croniter`
* **Testing Suite**: `pytest` & `pytest-asyncio`
* **Frontend**: Vanilla JS (ES6), CSS (Glassmorphism design tokens), HTML5 semantic layout.

---

## 📂 Project Architecture

```
├── backend/
│   ├── main.py           # FastAPI entrypoint, router configuration, DB seeds & lifespan hooks
│   ├── database.py       # Async engine, session maker & SQLite WAL pragma tuning
│   ├── models.py         # SQLAlchemy ORM models (Users, Orgs, Projects, Queues, Jobs, Executions)
│   ├── schemas.py        # Pydantic validation schemas
│   ├── auth.py           # JWT auth utils, password hashing, and role checks
│   ├── scheduler.py      # Cron scheduler polling daemon
│   ├── worker.py         # Job execution worker fleet manager
│   └── routes/
│       ├── auth.py       # Auth (register, login, orgs, projects) REST routes
│       ├── queues.py     # Queue management & configuration routes
│       ├── jobs.py       # Enqueueing, retries, and cron schedules routes
│       └── workers.py    # Worker Fleet status & metrics aggregation routes
├── frontend/
│   ├── index.html        # Glassmorphic single page dashboard
│   ├── styles.css        # Premium UI design tokens & responsive CSS
│   └── app.js            # Live updates, form actions & drawer controllers
└── tests/
    └── test_scheduler.py # Integration test suite (job lifecycle, retries, workflows)
```

---

## 💾 Quick Start & Execution

### 1. Run the Application
Start the FastAPI server. On startup, the database schema migration runs automatically, seeds a default administration account along with template queues/policies, and spawns the Worker and Scheduler daemons:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Access the Dashboard
Open your web browser and navigate to:
**[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

Use the Enqueue form tabs on the dashboard to trigger jobs, simulate artificial failures, pause/resume queues, and inspect execution timelines inside the detailed Job drawer.

---

## 🧪 Running Automated Tests
Run integration tests to verify database relationships, lifecycle schedules, retry backoff strategies, and dependent workflow unblocking:

```powershell
python -m pytest tests/test_scheduler.py
```
