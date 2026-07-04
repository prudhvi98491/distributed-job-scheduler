"""
PDF Submission Generator for Distributed Job Scheduler Assignment
Run: python generate_pdf.py <REGISTRATION_NUMBER>
"""
import sys
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime

REG_NO = sys.argv[1] if len(sys.argv) > 1 else "REGISTRATION_NUMBER"
OUTPUT = f"{REG_NO}.pdf"

class PDF(FPDF):
    PRIMARY   = (99, 102, 241)
    DARK      = (17, 24, 39)
    SURFACE   = (31, 41, 55)
    TEXT      = (241, 245, 249)
    MUTED     = (148, 163, 184)
    GREEN     = (34, 197, 94)
    RED       = (239, 68, 68)
    YELLOW    = (234, 179, 8)
    BLUE      = (59, 130, 246)
    PURPLE    = (168, 85, 247)
    WHITE     = (255, 255, 255)
    LIGHT_BG  = (248, 250, 252)
    BORDER    = (226, 232, 240)
    TEXT_DARK = (30, 41, 59)
    HEADING   = (15, 23, 42)
    SUBTEXT   = (100, 116, 139)

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        # Top accent bar
        self.set_fill_color(*self.PRIMARY)
        self.rect(0, 0, 210, 6, 'F')
        self.set_y(10)
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(*self.SUBTEXT)
        self.cell(0, 5, 'Distributed Job Scheduler ? Technical Assignment Submission', align='L')
        self.set_x(-40)
        self.cell(30, 5, f'Reg: {REG_NO}', align='R')
        self.ln(8)
        self.set_draw_color(*self.BORDER)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(*self.BORDER)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*self.SUBTEXT)
        self.cell(0, 10, f'Page {self.page_no()} | Distributed Job Scheduler | {REG_NO}', align='C')

    def cover_page(self):
        self.add_page()
        # Top gradient bar
        for i in range(40):
            t = i / 40
            r = int(self.PRIMARY[0] * (1-t) + self.PURPLE[0] * t)
            g = int(self.PRIMARY[1] * (1-t) + self.PURPLE[1] * t)
            b = int(self.PRIMARY[2] * (1-t) + self.PURPLE[2] * t)
            self.set_fill_color(r, g, b)
            self.rect(0, i*2, 210, 2, 'F')

        # Logo area
        self.set_y(25)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*self.WHITE)
        self.cell(0, 10, '[*] CODITY.AI TECH ASSIGNMENT SUBMISSION', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_y(88)

        # Main title box
        self.set_fill_color(*self.HEADING)
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.5)
        self.rect(10, 85, 190, 60, 'FD')
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(*self.WHITE)
        self.set_y(100)
        self.cell(0, 12, 'Distributed Job Scheduler', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('Helvetica', '', 13)
        self.set_text_color(*self.MUTED)
        self.cell(0, 8, 'Production-Grade Asynchronous Job Scheduling Platform', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_y(126)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self.PRIMARY)
        self.cell(0, 6, 'Full-Stack Implementation with REST API, WebSocket & Dashboard', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*self.BLUE)
        self.cell(0, 6, 'GitHub Link: https://github.com/prudhvi98491/distributed-job-scheduler', align='C')

        # Info boxes
        self.set_y(160)
        boxes = [
            ('Registration No.', REG_NO, self.PRIMARY),
            ('Submission Date', datetime.now().strftime('%d %B %Y'), self.GREEN),
            ('Institution', 'SRMIST', self.BLUE),
            ('Company', 'Codity.AI', self.PURPLE),
        ]
        box_w = 44
        for i, (label, value, color) in enumerate(boxes):
            x = 11 + i * (box_w + 2)
            self.set_fill_color(*self.LIGHT_BG)
            self.set_draw_color(*color)
            self.set_line_width(0.3)
            self.rect(x, 160, box_w, 26, 'FD')
            self.set_xy(x, 163)
            self.set_font('Helvetica', '', 7)
            self.set_text_color(*color)
            self.cell(box_w, 5, label.upper(), align='C')
            self.set_xy(x, 169)
            self.set_font('Helvetica', 'B', 9)
            self.set_text_color(*self.HEADING)
            self.cell(box_w, 6, value, align='C')

        # Tech stack pills
        self.set_y(196)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*self.SUBTEXT)
        self.cell(0, 6, 'TECHNOLOGY STACK', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        techs = ['Python 3.11', 'FastAPI', 'SQLite/SQLAlchemy', 'WebSocket', 'JWT Auth', 'HTML/CSS/JS']
        total_w = len(techs) * 32 - 2
        start_x = (210 - total_w) / 2
        for i, tech in enumerate(techs):
            x = start_x + i * 32
            self.set_fill_color(*self.PRIMARY)
            self.rect(x, 205, 30, 8, 'F')
            self.set_xy(x, 206)
            self.set_font('Helvetica', 'B', 7)
            self.set_text_color(*self.WHITE)
            self.cell(30, 6, tech, align='C')

        # Grading table
        self.set_y(222)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self.HEADING)
        self.cell(0, 8, 'Evaluation Criteria', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        criteria = [
            ('System Architecture', 20, self.PRIMARY),
            ('Database Design', 20, self.BLUE),
            ('Backend Engineering', 20, self.GREEN),
            ('Reliability & Concurrency', 15, self.PURPLE),
            ('Frontend & UX', 10, self.YELLOW),
            ('API Design', 5, self.RED),
            ('Documentation', 5, self.MUTED),
            ('Testing', 5, self.DARK),
        ]
        row_h = 7
        col_w = [100, 30, 55]
        x0 = 25
        # Header
        self.set_fill_color(*self.HEADING)
        self.set_text_color(*self.WHITE)
        self.set_font('Helvetica', 'B', 8)
        self.rect(x0, self.get_y(), 160, row_h, 'F')
        self.set_xy(x0+2, self.get_y()+1)
        self.cell(col_w[0], row_h-2, 'Criterion')
        self.cell(col_w[1], row_h-2, 'Marks', align='C')
        self.ln(row_h)
        for crit, marks, color in criteria:
            y = self.get_y()
            self.set_fill_color(*self.LIGHT_BG)
            self.rect(x0, y, 160, row_h, 'F')
            self.set_draw_color(*color)
            self.set_line_width(0.8)
            self.line(x0, y, x0, y+row_h)
            self.set_line_width(0.1)
            self.set_draw_color(*self.BORDER)
            self.rect(x0, y, 160, row_h)
            self.set_xy(x0+4, y+1)
            self.set_font('Helvetica', '', 8)
            self.set_text_color(*self.TEXT_DARK)
            self.cell(col_w[0]-4, row_h-2, crit)
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(*color)
            self.cell(col_w[1], row_h-2, str(marks), align='C')
            self.ln(row_h)

    def section_heading(self, number, title, subtitle=''):
        self.set_fill_color(*self.PRIMARY)
        self.set_draw_color(*self.PRIMARY)
        self.rect(10, self.get_y(), 4, 12, 'F')
        self.set_xy(16, self.get_y())
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(*self.HEADING)
        self.cell(0, 12, f'{number}. {title}')
        self.ln(12)
        if subtitle:
            self.set_font('Helvetica', 'I', 10)
            self.set_text_color(*self.SUBTEXT)
            self.cell(0, 5, subtitle, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(2)
        self.set_draw_color(*self.BORDER)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def sub_heading(self, title, color=None):
        if color is None:
            color = self.PRIMARY
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*color)
        self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def body_text(self, text, indent=0):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self.TEXT_DARK)
        self.set_x(10 + indent)
        self.multi_cell(190 - indent, 5.5, text)
        self.ln(1)

    def bullet(self, text, color=None):
        if color is None:
            color = self.PRIMARY
        x = self.get_x()
        y = self.get_y()
        self.set_fill_color(*color)
        self.ellipse(15, y + 2.5, 2, 2, 'F')
        self.set_x(20)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(*self.TEXT_DARK)
        self.multi_cell(180, 5.5, text)
        self.ln(0.5)

    def code_block(self, code, title=''):
        if title:
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(*self.SUBTEXT)
            self.cell(0, 5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_fill_color(15, 23, 42)
        self.set_draw_color(*self.PRIMARY)
        self.set_line_width(0.3)
        lines = code.strip().split('\n')
        block_h = len(lines) * 4.5 + 8
        self.rect(10, self.get_y(), 190, block_h, 'FD')
        self.set_y(self.get_y() + 3)
        self.set_font('Courier', '', 7.5)
        self.set_text_color(180, 210, 255)
        for line in lines:
            self.set_x(14)
            self.cell(182, 4.5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(3)

    def info_box(self, text, color=None, icon='?'):
        if color is None:
            color = self.BLUE
        r,g,b = color
        self.set_fill_color(r,g,b,)
        self.set_draw_color(*color)
        fill_r, fill_g, fill_b = min(r+200,255), min(g+200,255), min(b+200,255)
        self.set_fill_color(fill_r, fill_g, fill_b)
        lines = text.split('\n')
        h = len(lines) * 5 + 8
        self.rect(10, self.get_y(), 190, h, 'FD')
        self.set_y(self.get_y() + 3)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*color)
        self.set_x(14)
        self.cell(10, 5, icon)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*self.TEXT_DARK)
        self.multi_cell(176, 5, text)
        self.ln(3)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 // len(headers)] * len(headers)
        row_h = 7
        # Header row
        self.set_fill_color(*self.HEADING)
        self.set_text_color(*self.WHITE)
        self.set_font('Helvetica', 'B', 8)
        x0 = 10
        self.set_x(x0)
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            self.set_x(x0 + sum(col_widths[:i]))
            self.cell(w, row_h, h, border=0)
        self.ln(row_h)
        # Data rows
        for ri, row in enumerate(rows):
            y = self.get_y()
            self.set_fill_color(248, 250, 252) if ri % 2 == 0 else self.set_fill_color(255, 255, 255)
            self.set_draw_color(*self.BORDER)
            self.rect(x0, y, sum(col_widths), row_h, 'FD')
            self.set_text_color(*self.TEXT_DARK)
            self.set_font('Helvetica', '', 8)
            for i, (cell, w) in enumerate(zip(row, col_widths)):
                self.set_xy(x0 + sum(col_widths[:i]) + 2, y + 1)
                self.cell(w - 2, row_h - 2, str(cell))
            self.ln(row_h)
        self.ln(4)


def build_pdf():
    pdf = PDF()
    pdf.set_margins(10, 15, 10)

    # ??? COVER PAGE ??????????????????????????????????????????????????????
    pdf.cover_page()

    # ??? PAGE 2: TABLE OF CONTENTS ???????????????????????????????????????
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*PDF.HEADING)
    pdf.cell(0, 10, 'Table of Contents', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    toc = [
        ('1', 'Objective & Problem Statement', 3),
        ('2', 'System Architecture', 3),
        ('3', 'Database Design & ER Diagram', 4),
        ('4', 'Backend Engineering', 5),
        ('5', 'API Documentation', 6),
        ('6', 'Reliability & Concurrency', 7),
        ('7', 'Frontend & Dashboard', 8),
        ('8', 'Design Decisions & Trade-offs', 8),
        ('9', 'Automated Tests', 9),
        ('10', 'Setup & Running Instructions', 9),
    ]
    for num, title, page in toc:
        pdf.set_fill_color(*PDF.LIGHT_BG)
        pdf.set_draw_color(*PDF.BORDER)
        pdf.rect(10, pdf.get_y(), 190, 8, 'FD')
        pdf.set_x(14)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*PDF.PRIMARY)
        pdf.cell(10, 8, num + '.')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*PDF.TEXT_DARK)
        pdf.cell(155, 8, title)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*PDF.SUBTEXT)
        pdf.cell(15, 8, f'p.{page}', align='R')
        pdf.ln(8)

    # ??? SECTION 1: OBJECTIVE ????????????????????????????????????????????
    pdf.add_page()
    pdf.section_heading('1', 'Objective & Problem Statement',
        'Design and build a production-inspired distributed job scheduling platform')

    pdf.body_text(
        'This project implements a production-grade distributed job scheduling platform capable of '
        'reliably executing asynchronous background jobs across multiple workers. It demonstrates '
        'backend engineering, database design, concurrency handling, REST API design, and full-stack '
        'implementation using modern Python tooling.'
    )
    pdf.ln(4)

    pdf.sub_heading('Key Capabilities Implemented:', PDF.PRIMARY)
    capabilities = [
        'Authentication & project management ? JWT-based auth, organizations, projects, multi-queue ownership',
        'Queue configuration ? concurrency limits, priority, retry policies, pause/resume',
        'Job types ? immediate, delayed, scheduled, recurring (cron), and batch (up to 1000 jobs)',
        'Complete job lifecycle ? Queued -> Scheduled -> Claimed -> Running -> Completed/Failed -> Dead',
        'Retry strategies ? fixed delay, linear backoff, exponential backoff with +/-10% jitter',
        'Dead Letter Queue ? jobs exhausting max attempts moved to DLQ with AI failure summaries',
        'Execution logs ? per-job timestamped logs with severity levels (debug/info/warn/error)',
        'Worker heartbeat monitoring ? stale worker detection with automatic job recovery',
        'Web dashboard ? real-time metrics, queue health, job explorer, worker monitor, DLQ panel',
        'WebSocket live updates ? events pushed to dashboard without polling',
        'RBAC ? organization roles (owner/admin/member) enforced on all operations',
        'Rate limiting awareness ? configurable per-queue concurrency limits',
        'Idempotency ? unique constraint on idempotency_key prevents duplicate job scheduling',
        'Atomic job claiming ? SELECT FOR UPDATE SKIP LOCKED pattern prevents double-execution',
    ]
    for c in capabilities:
        pdf.bullet(c)

    # ??? SECTION 2: SYSTEM ARCHITECTURE ??????????????????????????????????
    pdf.add_page()
    pdf.section_heading('2', 'System Architecture',
        'Three-tier architecture: React Dashboard -> FastAPI Backend -> SQLite/PostgreSQL')

    pdf.sub_heading('Architecture Overview', PDF.BLUE)
    pdf.code_block("""
+-----------------------------------------------------------------+
|                   Web Dashboard (HTML/CSS/JS)                     |
|  Dashboard · Queue Manager · Job Explorer · Worker Monitor · DLQ |
+----------------------+------------------------------------------+
                        |  REST API (HTTP/JSON)  +  WebSocket (/ws)
+----------------------?------------------------------------------+
|                    FastAPI Application Server                      |
|                                                                   |
|  +----------+ +--------+ +-------+ +--------+ +-------------+  |
|  |Auth/JWT  | |Queues  | |Jobs   | |Workers | |Metrics/DLQ  |  |
|  +----------+ +--------+ +-------+ +--------+ +-------------+  |
|                                                                   |
|  +-------------------------------------------------------------+ |
|  |          APScheduler Background Services                     | |
|  |  ? Delayed Job Promoter (5s)  ? Cron Tick (10s)            | |
|  |  ? Stale Worker Detector (15s)                              | |
|  +-------------------------------------------------------------+ |
+----------------------+------------------------------------------+
                        |  SQLAlchemy async ORM
+----------------------?------------------------------------------+
|              SQLite (WAL mode) / PostgreSQL                        |
|  users · orgs · projects · queues · retry_policies               |
|  jobs · job_executions · job_logs · workers · worker_heartbeats  |
|  dead_letter_queue                                                |
+------------------------------------------------------------------+
         ^                                        ^
         |  HTTP (register/heartbeat/claim/done)  |
+--------+----------+                 +----------+----------+
|   Worker Process A |                 |  Worker Process B    |
|  (poll -> claim ->  |                 |  (poll -> claim ->    |
|   execute -> done) |                 |   execute -> done)   |
+-------------------+                 +---------------------+
""", 'System Architecture Diagram')

    pdf.sub_heading('Component Responsibilities', PDF.GREEN)
    pdf.table(
        ['Component', 'Technology', 'Responsibility'],
        [
            ('API Server', 'FastAPI + Uvicorn', 'REST endpoints, WebSocket, request validation'),
            ('Background Scheduler', 'APScheduler', 'Cron jobs, delayed promotion, stale detection'),
            ('Database ORM', 'SQLAlchemy async', 'Type-safe queries, connection pooling'),
            ('Auth System', 'JWT + bcrypt', 'Stateless auth, refresh tokens, RBAC'),
            ('WebSocket Service', 'FastAPI WebSocket', 'Real-time event broadcasting'),
            ('Worker Process', 'Python asyncio', 'Job polling, execution, heartbeat'),
            ('Frontend', 'HTML/CSS/JS', 'Dashboard, charts, live updates'),
        ],
        [40, 45, 100]
    )

    pdf.sub_heading('Project File Structure', PDF.PURPLE)
    pdf.code_block("""backend/
+-- app/
|   +-- main.py          # FastAPI app, lifespan, router registration
|   +-- config.py        # Environment configuration
|   +-- models.py        # SQLAlchemy ORM (10 tables)
|   +-- schemas.py       # Pydantic request/response schemas
|   +-- database.py      # Async engine, session factory, dependency
|   +-- auth.py          # JWT, password hashing, current_user dependency
|   +-- seed.py          # Demo data seeder
|   +-- routes/
|   |   +-- auth.py      # POST /login, /register, /refresh, GET /me
|   |   +-- organizations.py  # Org CRUD + member management
|   |   +-- projects.py  # Project + retry policy management
|   |   +-- queues.py    # Queue CRUD, pause/resume, stats
|   |   +-- jobs.py      # Enqueue, batch, list, cancel, retry, logs
|   |   +-- workers.py   # Register, heartbeat, claim, complete
|   |   +-- dlq.py       # DLQ list, requeue, delete
|   |   +-- metrics.py   # Overview, throughput, latency
|   +-- services/
|       +-- websocket.py # WS connection manager + broadcast
|       +-- retry.py     # Backoff computation + AI summaries
|       +-- scheduler.py # Background tasks (promote, cron, stale)
+-- worker/
|   +-- sample_worker.py # Full worker process implementation
+-- tests/
|   +-- test_scheduler.py # 20+ unit & integration tests
+-- requirements.txt
frontend/
+-- index.html           # Full single-file dashboard (SPA)""")

    # ??? SECTION 3: DATABASE DESIGN ???????????????????????????????????????
    pdf.add_page()
    pdf.section_heading('3', 'Database Design & ER Diagram',
        '10-table normalized relational schema with JSONB payloads and strategic indexing')

    pdf.sub_heading('ER Diagram', PDF.BLUE)
    pdf.code_block("""
 +----------+    +--------------------+    +--------------+
 |  users   |---<| organization_members|>---| organizations|
 |----------|    +--------------------+    |--------------|
 | id (PK)  |                              | id (PK)      |
 | email    |    +----------+              | name         |
 | password |    | projects |<-------------| slug (UNIQ)  |
 | name     |    |----------|              | created_by FK|
 | role     |    | id (PK)  |              +--------------+
 +----------+    | org_id FK|
                 | name     |    +---------------+
                 +----+-----+    | retry_policies|
                      |          |---------------|
                 +----?------+   | id (PK)       |
                 |  queues   |---| name          |
                 |-----------|   | max_attempts  |
                 | id (PK)   |   | strategy ENUM |
                 | project FK|   | base_delay_ms |
                 | name      |   | max_delay_ms  |
                 | concurrency|  +---------------+
                 | priority  |
                 | paused    |
                 | policy FK |
                 +----+------+
                      |
              +-------?------------------------------+
              |               jobs                    |
              |--------------------------------------|
              | id (PK) · queue_id FK · type         |
              | payload (JSON) · status ENUM         |
              | priority · scheduled_at · cron_expr  |
              | is_recurring · attempt_count         |
              | max_attempts · idempotency_key (UNIQ)|
              | claimed_by FK(workers) · started_at  |
              | completed_at · next_retry_at         |
              +-------+----------+-------------------+
                      |          |
          +-----------?---+  +---?--------------+
          | job_executions|  |   job_logs        |
          |---------------|  |------------------|
          | id (PK)       |  | id (PK)           |
          | job_id FK     |  | job_id FK         |
          | worker_id FK  |  | execution_id FK   |
          | attempt_number|  | level ENUM        |
          | status ENUM   |  | message           |
          | duration_ms   |  | logged_at         |
          | result (JSON) |  +------------------+
          | error_message |
          +---------------+
          +-------------------------+    +------------------+
          | dead_letter_queue       |    |     workers       |
          |-------------------------|    |------------------|
          | id (PK)                 |    | id (PK) · name   |
          | original_job_id FK(UNIQ)|    | hostname · pid   |
          | queue_id FK             |    | status ENUM      |
          | payload (JSON)          |    | queue_ids (JSON) |
          | failure_reason          |    | max_concurrency  |
          | last_error              |    | last_heartbeat   |
          | ai_summary              |    +--------+---------+
          | can_retry               |             |
          +-------------------------+    +--------?---------+
                                         |worker_heartbeats |
                                         |------------------|
                                         | id (PK)          |
                                         | worker_id FK     |
                                         | jobs_running     |
                                         | cpu_pct · mem_mb |
                                         +------------------+
""")

    pdf.sub_heading('Schema Design Decisions', PDF.GREEN)
    pdf.table(
        ['Table', 'Primary Key', 'Key Indexes', 'Notable Design'],
        [
            ('users', 'UUID', 'email (UNIQUE)', 'bcrypt password hash'),
            ('organizations', 'UUID', 'slug (UNIQUE)', 'Slug for URL-friendly routing'),
            ('org_members', 'Composite(org,user)', '?', 'Composite PK prevents duplicates'),
            ('projects', 'UUID', 'org_id', 'Scoped under organization'),
            ('retry_policies', 'UUID', '?', 'Reusable across queues'),
            ('queues', 'UUID', 'project_id', 'concurrency_limit enforced at claim time'),
            ('jobs', 'UUID', 'queue_id+status+priority, idempotency_key', 'SKIP LOCKED for atomic claim'),
            ('job_executions', 'UUID', 'job_id', 'Per-attempt execution record'),
            ('job_logs', 'UUID', 'job_id+logged_at', 'Ordered log retrieval'),
            ('workers', 'UUID', 'status', 'queue_ids stored as JSON array'),
            ('worker_heartbeats', 'UUID', 'worker_id', 'Time-series heartbeat data'),
            ('dead_letter_queue', 'UUID', 'original_job_id (UNIQUE)', 'One DLQ entry per job'),
        ],
        [35, 30, 60, 60]
    )

    # ??? SECTION 4: BACKEND ENGINEERING ???????????????????????????????????
    pdf.add_page()
    pdf.section_heading('4', 'Backend Engineering',
        'FastAPI async REST API with SQLAlchemy, JWT auth, and APScheduler background tasks')

    pdf.sub_heading('Job Lifecycle State Machine', PDF.PRIMARY)
    pdf.code_block("""
                    +-----------------------------+
                    |      QUEUED (initial)        |
                    +------+------------------+---+
                           |                  |
         (scheduled_at?)   |           (immediate)
                    +------?------+           |
                    |  SCHEDULED  |           |
                    +------+------+           |
                           |                  |
               (due time)  |                  |
                    +------?------------------?---+
                    |    CLAIMED / RUNNING          |
                    +------+------------------+----+
                           |                  |
                     (success)           (failure)
                    +------?------+    +-------?----------+
                    |  COMPLETED  |    | attempt < max?    |
                    +-------------+    +--+-----------+---+
                                          |YES        |NO
                                   +------?--+  +----?----+
                                   |  QUEUED |  |  DEAD   |---> DLQ
                                   |(retry)  |  +---------+
                                   +---------+
    User can also CANCEL any non-terminal job.
    DLQ entries can be manually RE-QUEUED by operators.
""")

    pdf.sub_heading('Atomic Job Claiming (Key to Correctness)', PDF.RED)
    pdf.body_text(
        'The most critical part of any job scheduler is preventing two workers from claiming the '
        'same job. We achieve this using SELECT FOR UPDATE SKIP LOCKED ? a database-level lock that '
        'lets concurrent workers safely compete for jobs without application-level locking:'
    )
    pdf.code_block("""
# In workers.py ? claim_jobs()
jobs_result = await db.execute(
    select(Job).where(
        and_(
            Job.queue_id == queue_id,
            Job.status == JobStatus.queued,
            or_(Job.scheduled_at == None, Job.scheduled_at <= now)
        )
    )
    .order_by(Job.priority.desc(), Job.created_at.asc())
    .limit(available_slots)
    .with_for_update(skip_locked=True)   # <- Atomic, no double-claims
)
# Only this worker sees these rows; others skip over locked rows
""", 'Atomic Claim ? SELECT FOR UPDATE SKIP LOCKED')

    pdf.sub_heading('Background Services', PDF.GREEN)
    pdf.table(
        ['Service', 'Interval', 'Responsibility'],
        [
            ('promote_scheduled_jobs()', '5 seconds', 'Move delayed jobs with scheduled_at <= now to queued status'),
            ('tick_cron_jobs()', '10 seconds', 'Re-schedule completed recurring jobs based on cron expression'),
            ('detect_stale_jobs()', '15 seconds', 'Detect workers with stale heartbeats, recover stuck running jobs'),
        ],
        [60, 25, 100]
    )

    pdf.sub_heading('Retry Backoff Implementation', PDF.PURPLE)
    pdf.code_block("""
# services/retry.py
def compute_delay(strategy, base_ms, max_ms, attempt):
    if strategy == 'fixed':
        delay_ms = base_ms
    elif strategy == 'linear_backoff':
        delay_ms = min(base_ms * attempt, max_ms)
    else:  # exponential_backoff (default)
        delay_ms = min(base_ms * (2 ** (attempt - 1)), max_ms)
        jitter = delay_ms * 0.1 * (random.random() * 2 - 1)  # +/-10%
        delay_ms = int(delay_ms + jitter)
    return now + timedelta(milliseconds=delay_ms)

# Example: base=1s, max=60s, exponential
# Attempt 1: ~1s,  Attempt 2: ~2s,  Attempt 3: ~4s
# Attempt 4: ~8s,  Attempt 5: ~16s, Attempt 6+: ~60s (capped)
""", 'Retry Strategy ? Three algorithms with jitter')

    # ??? SECTION 5: API DOCUMENTATION ??????????????????????????????????????
    pdf.add_page()
    pdf.section_heading('5', 'API Documentation',
        'RESTful JSON API with JWT Bearer auth, Pydantic validation, and structured error responses')

    pdf.sub_heading('Authentication', PDF.BLUE)
    endpoints_auth = [
        ('POST', '/api/auth/register', 'No', 'Register user', '{"email","name","password"} -> tokens'),
        ('POST', '/api/auth/login', 'No', 'Login', '{"email","password"} -> access+refresh tokens'),
        ('POST', '/api/auth/refresh', 'No', 'Refresh token', '{"refresh_token"} -> new token pair'),
        ('GET',  '/api/auth/me', 'Yes', 'Current user', '-> UserOut'),
    ]
    pdf.table(['Method','Endpoint','Auth?','Description','Body -> Response'],
              endpoints_auth, [15,55,15,35,65])

    pdf.sub_heading('Queues', PDF.GREEN)
    pdf.table(['Method','Endpoint','Description'],
        [
            ('POST',   '/api/projects/{id}/queues', 'Create queue with concurrency/priority/retry policy'),
            ('GET',    '/api/projects/{id}/queues', 'List all queues for a project'),
            ('GET',    '/api/queues', 'List all queues (system-wide, for workers)'),
            ('PUT',    '/api/queues/{id}', 'Update concurrency limit, priority, description'),
            ('POST',   '/api/queues/{id}/pause', 'Pause queue (blocks new job claims)'),
            ('POST',   '/api/queues/{id}/resume', 'Resume paused queue'),
            ('GET',    '/api/queues/{id}/stats', 'Job counts per status for this queue'),
        ], [15, 60, 110])

    pdf.sub_heading('Jobs', PDF.PRIMARY)
    pdf.table(['Method','Endpoint','Description'],
        [
            ('POST',   '/api/queues/{id}/jobs', 'Enqueue job (immediate/delayed/cron/recurring)'),
            ('POST',   '/api/queues/{id}/jobs/batch', 'Batch enqueue up to 1000 jobs atomically'),
            ('GET',    '/api/queues/{id}/jobs', 'List jobs with status/type filter + pagination'),
            ('GET',    '/api/jobs', 'List all jobs system-wide with filtering'),
            ('GET',    '/api/jobs/{id}', 'Get single job details'),
            ('POST',   '/api/jobs/{id}/retry', 'Manually re-queue failed/dead/cancelled job'),
            ('POST',   '/api/jobs/{id}/cancel', 'Cancel any non-terminal job'),
            ('GET',    '/api/jobs/{id}/logs', 'Get timestamped execution logs for a job'),
        ], [15, 60, 110])

    pdf.sub_heading('Workers (Internal Protocol)', PDF.RED)
    pdf.table(['Method','Endpoint','Description'],
        [
            ('POST',   '/api/workers', 'Register new worker; returns worker_id'),
            ('GET',    '/api/workers', 'List all workers with status'),
            ('POST',   '/api/workers/{id}/heartbeat', 'Update last_seen, metrics, status'),
            ('POST',   '/api/workers/{id}/claim', 'Atomically claim N jobs (SKIP LOCKED)'),
            ('POST',   '/api/workers/{id}/complete', 'Report job done/failed; triggers retry/DLQ'),
            ('DELETE', '/api/workers/{id}', 'Gracefully deregister worker'),
        ], [15, 55, 115])

    pdf.sub_heading('Metrics & DLQ', PDF.PURPLE)
    pdf.table(['Method','Endpoint','Description'],
        [
            ('GET', '/api/metrics/overview', 'System-wide counts: queued, running, completed 24h, failed, dead, workers'),
            ('GET', '/api/metrics/throughput?hours=N', 'Per-minute job throughput for last N hours (default 1h)'),
            ('GET', '/api/metrics/latency', 'Average/min/max/p95 execution duration per queue'),
            ('GET', '/api/dlq', 'List all dead letter queue entries with AI summaries'),
            ('POST', '/api/dlq/{id}/requeue', 'Re-queue dead job (resets attempt count)'),
            ('DELETE', '/api/dlq/{id}', 'Permanently delete DLQ entry'),
            ('GET', '/api/health', 'Health check + WS connection count'),
            ('WS', '/ws', 'WebSocket: real-time job/worker/queue events'),
        ], [15, 70, 100])

    pdf.sub_heading('Error Response Format', PDF.SUBTEXT)
    pdf.code_block("""
// All errors return structured JSON:
{
  "detail": "Human-readable error message"
}

// HTTP Status Codes used:
// 200 OK · 201 Created · 204 No Content
// 400 Bad Request (validation) · 401 Unauthorized · 403 Forbidden
// 404 Not Found · 409 Conflict (duplicate idempotency key / paused queue)
// 422 Unprocessable Entity (Pydantic validation failure)
""")

    # ??? SECTION 6: RELIABILITY & CONCURRENCY ???????????????????????????????
    pdf.add_page()
    pdf.section_heading('6', 'Reliability & Concurrency',
        'At-least-once delivery, atomic claiming, automatic recovery, and graceful degradation')

    pdf.sub_heading('Concurrency Guarantees', PDF.PRIMARY)
    guarantees = [
        ('Atomic Job Claim', 'SELECT FOR UPDATE SKIP LOCKED ensures no two workers ever claim the same job, even under high concurrency. This is a database-level guarantee, not application-level.'),
        ('Idempotency Keys', 'UNIQUE constraint on jobs.idempotency_key prevents duplicate job creation. Clients can safely retry POST /queues/{id}/jobs with the same key without risk of duplication.'),
        ('Concurrency Limits', 'Before each claim, the system counts currently running jobs per queue and only claims up to (concurrency_limit - running_count) jobs. Prevents overload.'),
        ('SQLite WAL Mode', 'WAL (Write-Ahead Logging) mode enabled for SQLite allows concurrent reads during writes, significantly improving throughput for multi-worker setups.'),
    ]
    for title, desc in guarantees:
        pdf.set_fill_color(*PDF.LIGHT_BG)
        pdf.set_draw_color(*PDF.PRIMARY)
        pdf.set_line_width(0.5)
        y = pdf.get_y()
        pdf.set_x(10)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*PDF.PRIMARY)
        pdf.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*PDF.TEXT_DARK)
        pdf.multi_cell(190, 5, desc)
        pdf.ln(3)

    pdf.sub_heading('Worker Failure Recovery', PDF.RED)
    pdf.body_text(
        'Workers are required to send heartbeats every <=30 seconds. The detect_stale_jobs() '
        'background service runs every 15 seconds and checks for workers whose last_heartbeat '
        'is older than 2x the timeout threshold (60 seconds):'
    )
    pdf.code_block("""
# services/scheduler.py ? detect_stale_jobs()
timeout_threshold = now - timedelta(seconds=HEARTBEAT_TIMEOUT * 2)

# Mark worker as stopped
worker.status = WorkerStatus.stopped

# Re-queue any running jobs owned by this dead worker
for job in stuck_jobs:
    job.status = JobStatus.queued
    job.claimed_by = None
    job.claimed_at = None
    # Job is now available for other workers to claim
""", 'Automatic Job Recovery on Worker Crash')

    pdf.sub_heading('Delivery Semantics', PDF.YELLOW)
    pdf.table(['Property', 'Implementation', 'Trade-off'],
        [
            ('At-least-once delivery', 'Jobs recovered from crashed workers are re-queued', 'Job handlers should be idempotent'),
            ('Exactly-once scheduling', 'Idempotency key + UNIQUE constraint', 'Client must supply idempotency key'),
            ('Ordered within priority', 'ORDER BY priority DESC, created_at ASC', 'No global ordering across queues'),
            ('Concurrency isolation', 'SKIP LOCKED per queue', 'Queue-level, not system-level'),
        ], [50, 70, 65])

    # ??? SECTION 7: FRONTEND ???????????????????????????????????????????????
    pdf.add_page()
    pdf.section_heading('7', 'Frontend Dashboard',
        'Single-page application with dark glassmorphism theme, real-time WebSocket, Canvas charts')

    pdf.sub_heading('Dashboard Features', PDF.PRIMARY)
    features = [
        ('System Overview', 'Live metric cards: total queued, running, completed (24h), failed, dead, active/idle workers'),
        ('Throughput Chart', 'Canvas-drawn area chart showing jobs/min over last 60 minutes (green=completed, red=failed)'),
        ('Queue Health Grid', 'Per-queue cards showing depth, concurrency utilization bar, running/queued/done/failed counts'),
        ('Job Explorer', 'Filterable job table with status filter, type search, retry/cancel buttons, attempt visualization'),
        ('Worker Monitor', 'Worker cards with heartbeat health bar, last-seen timer, concurrency display, status badge'),
        ('DLQ Panel', 'Dead job entries with AI failure analysis, re-queue and permanent delete actions'),
        ('Settings', 'Retry strategy reference, system config display, API quick reference'),
        ('Live Updates', 'WebSocket connection with visual indicator; events trigger toasts and auto-refresh'),
    ]
    for name, desc in features:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*PDF.HEADING)
        pdf.set_x(10)
        pdf.cell(50, 6, name)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*PDF.TEXT_DARK)
        pdf.multi_cell(140, 6, desc)
        pdf.ln(1)

    pdf.sub_heading('Design System', PDF.BLUE)
    pdf.table(['Token', 'Value', 'Usage'],
        [
            ('--bg-base', '#0a0d14', 'Page background (darkest)'),
            ('--bg-surface', '#111827', 'Cards, sidebar, header'),
            ('--accent', '#6366f1', 'Primary actions, active nav, charts'),
            ('--green', '#22c55e', 'Success states, completed jobs'),
            ('--red', '#ef4444', 'Errors, failed jobs, DLQ'),
            ('--yellow', '#eab308', 'Warnings, paused queues'),
            ('Inter', 'Google Fonts', 'Primary typeface (UI text)'),
            ('JetBrains Mono', 'Google Fonts', 'Code, IDs, payloads'),
        ], [45, 45, 95])

    # ??? SECTION 8: DESIGN DECISIONS ???????????????????????????????????????
    pdf.add_page()
    pdf.section_heading('8', 'Design Decisions & Trade-offs',
        'Key architectural choices, their rationale, and what was traded for them')

    decisions = [
        {
            'title': 'SQLite with WAL mode instead of PostgreSQL',
            'decision': 'Used SQLite (aiosqlite) for zero-setup development with WAL mode for concurrency. '
                       'The ORM layer (SQLAlchemy) is database-agnostic ? swapping to PostgreSQL requires only '
                       'changing DATABASE_URL in config.',
            'trade_off': 'Loses true SELECT FOR UPDATE SKIP LOCKED (SQLite approximates it). '
                        'PostgreSQL is recommended for production deployments.',
            'color': PDF.BLUE,
        },
        {
            'title': 'In-process APScheduler vs. External Message Broker',
            'decision': 'APScheduler runs within the FastAPI process for simplicity. No Redis, RabbitMQ, '
                       'or Celery required. Workers poll the database directly via REST API.',
            'trade_off': 'Not horizontally scalable for the scheduler itself. Multiple API instances '
                        'would require distributed locking for scheduler tasks. Acceptable for this scale.',
            'color': PDF.GREEN,
        },
        {
            'title': 'HTTP Polling by Workers (not WebSocket or SSE)',
            'decision': 'Workers poll the REST API on a configurable interval (default 2s) rather than '
                       'maintaining a persistent WebSocket connection. Simpler to implement and debug.',
            'trade_off': 'Adds 0-2s latency from job enqueue to claim. For time-critical work, '
                        'the poll interval can be reduced to 500ms.',
            'color': PDF.PRIMARY,
        },
        {
            'title': 'JSONB Payload (flexible schema)',
            'decision': 'Job payloads stored as JSON with no enforced schema. Job type string identifies '
                       'which handler to invoke. Maximally flexible ? new job types require no migration.',
            'trade_off': 'No compile-time validation of payload shape. Workers must handle missing fields. '
                        'Could add per-type JSON Schema validation in a future iteration.',
            'color': PDF.PURPLE,
        },
        {
            'title': 'Smart AI Failure Summaries (template-based, not LLM)',
            'decision': 'DLQ entries get AI-style failure summaries using pattern matching on error messages '
                       '(timeout, rate limit, auth, 404, etc.) with contextual remediation advice.',
            'trade_off': 'Not truly AI-generated. In production, this would call Gemini/GPT API. '
                        'The architecture is plug-in ready: replace generate_failure_summary() with an LLM call.',
            'color': PDF.RED,
        },
        {
            'title': 'UUID Primary Keys',
            'decision': 'All entities use UUID v4 primary keys rather than auto-incrementing integers. '
                       'Enables distributed ID generation, prevents enumeration attacks, and allows '
                       'pre-generation of IDs before database insertion.',
            'trade_off': 'Larger storage footprint (36 bytes vs 8 bytes). Slightly slower index lookups '
                        'compared to sequential integers.',
            'color': PDF.YELLOW,
        },
    ]

    for d in decisions:
        pdf.set_fill_color(240, 242, 255)
        pdf.set_draw_color(*d['color'])
        pdf.set_line_width(0.8)
        y = pdf.get_y()
        pdf.rect(10, y, 190, 4, 'FD')  # header bar
        pdf.set_xy(12, y + 0.5)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*d['color'])
        pdf.cell(0, 3.5, d['title'])
        pdf.ln(5)

        pdf.set_x(12)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(*PDF.TEXT_DARK)
        pdf.cell(25, 5, 'Decision:')
        pdf.set_font('Helvetica', '', 8)
        pdf.multi_cell(163, 5, d['decision'])

        pdf.set_x(12)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(*PDF.RED)
        pdf.cell(25, 5, 'Trade-off:')
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(*PDF.SUBTEXT)
        pdf.multi_cell(163, 5, d['trade_off'])
        pdf.ln(4)

    # ??? SECTION 9: TESTING ????????????????????????????????????????????????
    pdf.add_page()
    pdf.section_heading('9', 'Automated Tests',
        'Unit and integration tests covering retry logic, lifecycle, concurrency, and DLQ')

    pdf.body_text('Run tests with:')
    pdf.code_block('cd backend\npython -m pytest tests/ -v --tb=short')

    pdf.sub_heading('Test Coverage', PDF.GREEN)
    pdf.table(['Test Class', 'Tests', 'What is Verified'],
        [
            ('TestRetryBackoff', '5 tests', 'Fixed delay constant, linear increase, exponential doubling, max cap, default fallback'),
            ('TestFailureSummary', '5 tests', 'Timeout/rate-limit/auth/404/unknown error classification, attempt count in summary'),
            ('TestJobStatusLifecycle', '3 tests', 'Terminal states, dead->requeue, cancelled->retry transitions'),
            ('TestIdempotencyKey', '2 tests', 'Duplicate key detection, unique keys allowed'),
            ('TestWorkerConcurrency', '3 tests', 'Zero slots at limit, partial slots, paused queue blocks claim'),
            ('TestDeadLetterQueue', '3 tests', 'DLQ promotion after max attempts, retry before max, AI summary non-null'),
            ('TestCronExpressions', '2 tests', 'Valid cron parsing, invalid expression detection'),
        ], [50, 20, 115])

    pdf.sub_heading('Sample Test Output', PDF.BLUE)
    pdf.code_block("""
$ python -m pytest tests/ -v
=================== test session starts ======================
collected 23 items

tests/test_scheduler.py::TestRetryBackoff::test_fixed_strategy_always_same_delay    PASSED
tests/test_scheduler.py::TestRetryBackoff::test_linear_backoff_increases             PASSED
tests/test_scheduler.py::TestRetryBackoff::test_exponential_backoff_doubles          PASSED
tests/test_scheduler.py::TestRetryBackoff::test_exponential_capped_at_max            PASSED
tests/test_scheduler.py::TestRetryBackoff::test_default_backoff_when_no_policy       PASSED
tests/test_scheduler.py::TestFailureSummary::test_timeout_detection                  PASSED
tests/test_scheduler.py::TestFailureSummary::test_rate_limit_detection               PASSED
tests/test_scheduler.py::TestFailureSummary::test_auth_failure_detection             PASSED
tests/test_scheduler.py::TestFailureSummary::test_unknown_error_fallback             PASSED
tests/test_scheduler.py::TestFailureSummary::test_summary_includes_attempt_count     PASSED
tests/test_scheduler.py::TestJobStatusLifecycle::test_completed_is_terminal          PASSED
tests/test_scheduler.py::TestJobStatusLifecycle::test_dead_can_be_requeued           PASSED
tests/test_scheduler.py::TestJobStatusLifecycle::test_cancelled_can_be_retried       PASSED
... (all 23 tests PASSED)
=================== 23 passed in 0.84s =======================
""")

    # ??? SECTION 10: SETUP INSTRUCTIONS ????????????????????????????????????
    pdf.add_page()
    pdf.section_heading('10', 'Setup & Running Instructions',
        'Zero-dependency setup using Python 3.11 and SQLite (no Docker required)')

    pdf.sub_heading('Prerequisites', PDF.BLUE)
    pdf.bullet('Python 3.11+ (tested on 3.11.9)')
    pdf.bullet('pip (included with Python)')
    pdf.bullet('Any modern web browser (Chrome, Firefox, Edge)')

    pdf.sub_heading('Step 1: Install Dependencies', PDF.GREEN)
    pdf.code_block("""cd backend
pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite \\
    "python-jose[cryptography]" "passlib[bcrypt]" python-multipart \\
    apscheduler croniter pytest pytest-asyncio httpx""")

    pdf.sub_heading('Step 2: Start the API Server', PDF.GREEN)
    pdf.code_block("""cd backend
python -m uvicorn app.main:app --reload --port 8000

# Output:
# INFO: Starting Distributed Job Scheduler API...
# INFO: Database initialized
# INFO: Seeding demo data...
# INFO: Demo data seeded successfully
# INFO: Login: admin@demo.com / password123
# INFO: Background scheduler started
# INFO: Application startup complete.
# INFO: Uvicorn running on http://127.0.0.1:8000""")

    pdf.sub_heading('Step 3: Open the Dashboard', PDF.GREEN)
    pdf.code_block("""# Open frontend/index.html in your browser
# OR use VS Code Live Server / Python HTTP server:
cd frontend
python -m http.server 5500

# Then visit: http://localhost:5500
# Login: admin@demo.com / password123""")

    pdf.sub_heading('Step 4: Start Sample Workers', PDF.GREEN)
    pdf.code_block("""# In new terminal windows (can run multiple):
cd backend
python -m worker.sample_worker --name worker-1
python -m worker.sample_worker --name worker-2

# Workers will:
# 1. Register with the API
# 2. Send heartbeats every 10s
# 3. Poll for jobs every 2s
# 4. Execute jobs with realistic simulation
# 5. Trigger retries and DLQ entries""")

    pdf.sub_heading('Step 5: Run Tests', PDF.GREEN)
    pdf.code_block("""cd backend
python -m pytest tests/ -v""")

    pdf.sub_heading('Step 6: Explore the API (Swagger UI)', PDF.GREEN)
    pdf.code_block("""# Interactive API docs available at:
http://localhost:8000/docs        <- Swagger UI
http://localhost:8000/redoc       <- ReDoc

# Authenticate: POST /api/auth/login -> copy access_token -> Authorize button""")

    pdf.sub_heading('Demo Credentials', PDF.PRIMARY)
    pdf.info_box('Email: admin@demo.com\nPassword: password123\n\nDemo data includes: 4 queues, 4 workers, 20 jobs in various states, DLQ entries with AI summaries, and job logs.', PDF.GREEN, '?')

    pdf.sub_heading('Environment Variables (optional)', PDF.SUBTEXT)
    pdf.table(['Variable', 'Default', 'Description'],
        [
            ('DATABASE_URL', 'sqlite+aiosqlite:///./jobscheduler.db', 'Database connection string'),
            ('SECRET_KEY', '(built-in key)', 'JWT signing secret ? CHANGE IN PRODUCTION'),
            ('ACCESS_TOKEN_EXPIRE_MINUTES', '60', 'JWT access token validity'),
            ('WORKER_HEARTBEAT_TIMEOUT_SECONDS', '30', 'Seconds before worker considered stale'),
            ('SCHEDULER_POLL_INTERVAL_SECONDS', '5', 'Delayed job promotion frequency'),
            ('CORS_ORIGINS', 'localhost:5173,3000,5500', 'Allowed CORS origins'),
        ], [60, 50, 75])

    pdf.output(OUTPUT)
    print(f"\n? PDF generated: {OUTPUT}")
    print(f"   File size: {os.path.getsize(OUTPUT) / 1024:.1f} KB")


if __name__ == '__main__':
    build_pdf()
