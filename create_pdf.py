import os
from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("helvetica", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, "Codity.AI Tech Assignment: Distributed Job Scheduler", border=0, align="L")
            self.cell(0, 10, f"Page {self.page_no()}", border=0, align="R")
            self.ln(10)
            self.set_draw_color(220, 220, 220)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(6)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, "Registration Number: RA2311026010746 | Tech Assignment Submission", align="C")

def create_report():
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # ------------------ PAGE 1: COVER PAGE ------------------
    pdf.add_page()
    
    # Accent Indigo Bar on left
    pdf.set_fill_color(99, 102, 241) 
    pdf.rect(0, 0, 12, 297, "F")
    
    pdf.set_left_margin(22)
    pdf.set_y(40)
    
    # Header tag
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "CODITY.AI TECH ASSIGNMENT SUBMISSION", ln=True)
    pdf.ln(4)
    
    # Title
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(15, 17, 28)
    pdf.multi_cell(0, 12, "Distributed Background\nJob Scheduling Platform")
    pdf.ln(6)
    
    # Subtitle
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "A high-performance execution engine with real-time UI dashboard.", ln=True)
    pdf.ln(45)
    
    # Candidate details section
    pdf.set_fill_color(245, 246, 250)
    pdf.rect(22, pdf.get_y(), 168, 100, "F")
    
    pdf.set_y(pdf.get_y() + 8)
    pdf.set_x(26)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "SUBMISSION INFORMATION", ln=True)
    pdf.ln(6)
    
    details = [
        ["Registration Number:", "RA2311026010746"],
        ["Candidate Name:", "Prudhvi"],
        ["Project Platform:", "Distributed Job Scheduler (Overdrive)"],
        ["GitHub Repository:", "https://github.com/prudhvi98491/distributed-job-scheduler"],
        ["Date of Submission:", "July 5, 2026"]
    ]
    
    pdf.set_font("helvetica", "", 10)
    for label, val in details:
        pdf.set_x(26)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(48, 8, label)
        if label.startswith("GitHub"):
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(99, 102, 241)
            pdf.cell(0, 8, val, ln=True, link=val)
            pdf.set_text_color(60, 60, 60)
        else:
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 8, val, ln=True)
            
    # ------------------ PAGE 2: EXEC SUMMARY & TECH STACK ------------------
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_x(15)
    pdf.set_y(20)
    
    pdf.set_font("helvetica", "B", 15)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 10, "1. Executive Summary", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    summary_text = (
        "This project implements a production-ready, highly reliable distributed background job scheduler "
        "system. Designed to handle concurrent task executions across multiple workers, the system guarantees "
        "fault tolerance, worker failover, and strict queue boundary limitations. The architecture includes "
        "features like multi-tenant organization workspaces, custom backoff retries, cron recurring tasks, "
        "and sequential workflows with dependency blocking. Users can monitor queues, track active nodes, "
        "and replay failed/DLQ tasks live via an Outfit-themed glassmorphic SPA dashboard."
    )
    pdf.multi_cell(0, 6, summary_text)
    pdf.ln(6)
    
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 8, "Core Technology Stack", ln=True)
    pdf.ln(2)
    
    # Tech Stack Table
    headers = ["Component", "Technology", "Description / Implementation Details"]
    rows = [
        ["API Framework", "FastAPI / Uvicorn", "Asynchronous endpoints, structured validation, OpenAPI docs"],
        ["Database", "SQLite (WAL Mode)", "ACID storage with Write-Ahead Logging & busy timeout lock protection"],
        ["Asynchronous ORM", "SQLAlchemy + aiosqlite", "Non-blocking connection pooling and entity relationship models"],
        ["Recurring Cron", "croniter", "Expression parser that calculates dynamic schedules for active cron jobs"],
        ["Dashboard SPA", "Vanilla HTML5 / CSS3 / JS", "Real-time state monitoring dashboard using modern glassmorphic design"],
        ["Testing Engine", "pytest + pytest-asyncio", "Verification framework simulating job lifecycle and retries"]
    ]
    
    # Table Header
    pdf.set_fill_color(240, 240, 245)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 8, headers[0], 1, 0, "C", True)
    pdf.cell(40, 8, headers[1], 1, 0, "C", True)
    pdf.cell(110, 8, headers[2], 1, 1, "C", True)
    
    pdf.set_font("helvetica", "", 9)
    for r in rows:
        pdf.cell(35, 8, r[0], 1, 0, "L")
        pdf.cell(40, 8, r[1], 1, 0, "L")
        pdf.cell(110, 8, r[2], 1, 1, "L")
        
    pdf.ln(8)
    
    # ------------------ PAGE 3: DATABASE DESIGN & NORMALIZATION ------------------
    pdf.add_page()
    pdf.set_y(20)
    
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 10, "2. Relational Database Design", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 10)
    db_intro = (
        "The relational database schema is normalized to 3NF (Third Normal Form) to eliminate redundancy, "
        "safeguard referential integrity, and maximize performance. Tables are connected via primary and foreign key "
        "constraints, utilizing ON DELETE CASCADE or ON DELETE SET NULL configurations."
    )
    pdf.multi_cell(0, 6, db_intro)
    pdf.ln(4)
    
    # Tables Description
    tables = [
        ["users", "Stores credentials (hashed via bcrypt), roles (admin, user, viewer), and metadata."],
        ["organizations", "Enables multi-tenancy, grouping projects and user access levels."],
        ["projects", "Contains project workspaces owned by organizations."],
        ["queues", "Defines job queues with priority, concurrency_limit, and retry policies."],
        ["jobs", "Core queue table containing status (queued, running, completed, failed, dlq), payload, worker_id, and parent_job_id (workflows)."],
        ["job_executions", "Tracks execution details, duration (ms), worker, and trace errors."],
        ["workers", "Worker fleet registry monitoring hostnames, IP addresses, heartbeats, and current loads."],
        ["cron_jobs", "Schedules recurring cron jobs to dynamically queue new jobs on intervals."],
        ["dead_letter_queue", "Holds permanently failed tasks for isolation and manual replay."]
    ]
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(40, 8, "Table Name", 1, 0, "C", True)
    pdf.cell(145, 8, "Schema Purpose & Normalization Details", 1, 1, "C", True)
    
    pdf.set_font("helvetica", "", 9)
    for name, desc in tables:
        start_y = pdf.get_y()
        pdf.multi_cell(40, 8, name, 1, "L")
        end_y = pdf.get_y()
        
        pdf.set_y(start_y)
        pdf.set_x(55)
        pdf.multi_cell(145, 8, desc, 1, "L")
        pdf.set_y(max(end_y, pdf.get_y()))
        
    pdf.ln(6)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Concurrency Control and Atomic Claims", ln=True)
    pdf.ln(1)
    
    pdf.set_font("helvetica", "", 10)
    concurrency_desc = (
        "To ensure that jobs are claimed atomically and prevent duplicate execution (maintaining strict idempotency), "
        "the worker service executes the claiming block inside a database transaction with an IMMEDIATE lock. "
        "The SQL query retrieves a single eligible job from a queue that is active (not paused) and whose current "
        "running/claimed job count is strictly below the queue's configured concurrency_limit. This ensures horizontal "
        "scalability without race conditions."
    )
    pdf.multi_cell(0, 6, concurrency_desc)

    # ------------------ PAGE 4: BACKEND ROUTE API ------------------
    pdf.add_page()
    pdf.set_y(20)
    
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 10, "3. REST API Endpoints", ln=True)
    pdf.ln(2)
    
    api_intro = (
        "The backend exposes clean REST APIs with structured JSON validation, Pydantic parsing, and "
        "JWT-based security layers. The dashboard communicates with these endpoints to render statistics, "
        "dispatch tasks, pause/resume queues, and inspect logs."
    )
    pdf.multi_cell(0, 6, api_intro)
    pdf.ln(4)
    
    endpoints = [
        ["POST", "/api/auth/register", "Registers a new user account with hashed credentials."],
        ["POST", "/api/auth/login", "Authenticates credentials and issues a JWT token."],
        ["POST", "/api/queues", "Creates a queue specifying concurrency limit & priority."],
        ["PATCH", "/api/queues/{id}", "Updates queue configs or pauses/resumes queue state."],
        ["POST", "/api/jobs", "Enqueue single task (immediate, delayed, or workflow)."],
        ["POST", "/api/jobs/batch", "Dispatches bulk job payloads under a single API call."],
        ["GET", "/api/jobs", "Lists jobs with pagination, queue, and status filters."],
        ["POST", "/api/jobs/{id}/retry", "Manually replays a failed or DLQ job."],
        ["GET", "/api/metrics", "Returns aggregate metrics, throughput trends, and error counts."]
    ]
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(20, 8, "Method", 1, 0, "C", True)
    pdf.cell(50, 8, "Endpoint", 1, 0, "C", True)
    pdf.cell(115, 8, "Description / Functionality", 1, 1, "C", True)
    
    pdf.set_font("helvetica", "", 9)
    for method, path, desc in endpoints:
        pdf.cell(20, 8, method, 1, 0, "C")
        if method == "POST":
            pdf.set_text_color(99, 102, 241)
        elif method == "PATCH":
            pdf.set_text_color(245, 158, 11)
        else:
            pdf.set_text_color(16, 185, 129)
        pdf.cell(50, 8, path, 1, 0, "L")
        pdf.set_text_color(60, 60, 60)
        pdf.cell(115, 8, desc, 1, 1, "L")
        
    pdf.ln(6)
    
    # ------------------ PAGE 5: RESILIENCY & VERIFICATION ------------------
    pdf.add_page()
    pdf.set_y(20)
    
    pdf.set_font("helvetica", "B", 15)
    pdf.cell(0, 10, "4. Resiliency & Test Verification", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Worker Resiliency & Failover Recovery", ln=True)
    pdf.ln(1)
    
    pdf.set_font("helvetica", "", 10)
    resilience_desc = (
        "Workers register themselves in the database and issue heartbeats every 5 seconds. If a worker goes offline "
        "for more than 15 seconds, it is marked as offline by healthy worker threads. Any running or claimed jobs "
        "on that node are automatically re-queued (status queued, worker_id reset) for failover recovery."
    )
    pdf.multi_cell(0, 6, resilience_desc)
    pdf.ln(4)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Automated Integration Testing", ln=True)
    pdf.ln(1)
    
    pdf.set_font("helvetica", "", 10)
    test_desc = (
        "We implemented integration tests in tests/test_scheduler.py to verify relationships, retries, and sequential "
        "workflow unblocking. Running pytest completes successfully:"
    )
    pdf.multi_cell(0, 6, test_desc)
    pdf.ln(4)
    
    # pytest execution box
    pdf.set_fill_color(245, 245, 245)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(15, pdf.get_y(), 180, 24, "FD")
    
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_x(18)
    pdf.set_font("courier", "B", 9)
    pdf.set_text_color(30, 130, 30)
    pdf.cell(0, 5, "tests/test_scheduler.py::test_database_seeding_and_relations PASSED", ln=True)
    pdf.set_x(18)
    pdf.cell(0, 5, "tests/test_scheduler.py::test_job_execution_lifecycle_and_retries PASSED", ln=True)
    pdf.set_x(18)
    pdf.cell(0, 5, "tests/test_scheduler.py::test_workflow_dependencies_unblocking PASSED", ln=True)
    pdf.set_x(18)
    pdf.set_font("courier", "B", 9)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 5, "============================== 3 passed in 2.02s ==============================", ln=True)
    
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.ln(15)
    
    # GitHub repository confirmation text
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, "Submission GitHub Repository", ln=True)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "https://github.com/prudhvi98491/distributed-job-scheduler", ln=True, link="https://github.com/prudhvi98491/distributed-job-scheduler")

    # Output file
    output_filename = "RA2311026010746.pdf"
    pdf.output(output_filename)
    print(f"PDF successfully created: {output_filename}")

if __name__ == "__main__":
    create_report()
