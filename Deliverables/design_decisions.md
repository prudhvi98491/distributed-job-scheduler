# Technical Design Decisions & Trade-Offs

This document outlines the major architectural trade-offs, database locks, and failover design patterns incorporated into the Overdrive Distributed Job Scheduler.

---

## 1. Database Choice: SQLite (WAL Mode) vs. PostgreSQL
### Decision
The system utilizes SQLite running in **Write-Ahead Logging (WAL)** mode instead of PostgreSQL for the relational engine.
### Trade-Offs
* **Pros (SQLite WAL)**:
  * Zero configuration or runtime infrastructure dependency (no separate PostgreSQL daemon/Docker needed for local or academic setup).
  * In WAL mode, writers do not block readers, enabling high read performance for dashboard polling and concurrent job lookups.
  * Native file-locking scales smoothly for local and medium-scale multi-process loads.
* **Cons**:
  * SQLite does not scale horizontally across multiple separate host nodes (requires a shared filesystem or replication tool like LiteFS). If multi-host node distribution is needed, migrating database connection strings to PostgreSQL is recommended.

---

## 2. Concurrency Control: Atomic Claims vs. Row-Level Locks
### Decision
To prevent multiple workers from claiming and executing the same job concurrently, claiming transactions use **`BEGIN IMMEDIATE`** locks.
### Trade-Offs
* **Pros**:
  * SQLite’s `BEGIN IMMEDIATE` locks the database for write transactions immediately when the transaction begins. This guarantees that no other connection can acquire a write lock during selection, completely eliminating double-claiming race conditions.
  * Queue-level concurrency limits are calculated inside the transaction before claiming, ensuring we never exceed limits during high-frequency polls.
* **Cons**:
  * Locking the entire database for the duration of the claim query limits write throughput compared to row-level locks (`SELECT FOR UPDATE` in PostgreSQL). However, because the claim transaction takes <5ms, the latency is negligible for standard workloads.

---

## 3. Cron Daemon Strategy: In-App croniter vs. Celery Beat
### Decision
A lightweight, loop-based daemon parses cron expressions using the python `croniter` library instead of integrating a heavy broker framework like Celery Beat.
### Trade-Offs
* **Pros**:
  * Keeps the codebase compact and transparent.
  * Allows direct inspection and management of the cron queue from the database, rendering it observable via the API metrics endpoints.
* **Cons**:
  * High-precision cron schedules (e.g. sub-second resolution) are not supported. Precision is limited to the loop check frequency (1 second), which is standard for crontabs.

---

## 4. Worker Failover: Decentralized Poll vs. Central Orchestrator
### Decision
Instead of a single coordinator node tracking worker health, a **decentralized failover check** is run during normal worker heartbeats.
### Trade-Offs
* **Pros**:
  * No single point of failure (SPOF) for orchestration. If a manager node dies, workers still operate.
  * Worker heartbeats are stored in the shared database. Any active worker node running the heartbeat daemon can identify and failover dead worker nodes.
* **Cons**:
  * Adds minor SQL query overhead during heartbeat cycles to check for expired worker nodes.
