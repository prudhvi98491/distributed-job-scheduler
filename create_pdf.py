import os
from fpdf import FPDF

class AcademicPDFReport(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("helvetica", "I", 8)
            self.set_text_color(110, 110, 110)
            self.cell(0, 10, "Technical Thesis & Implementation: Distributed Job Scheduler", border=0, align="L")
            self.cell(0, 10, f"Page {self.page_no()}", border=0, align="R")
            self.ln(10)
            self.set_draw_color(220, 220, 220)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.set_text_color(140, 140, 140)
            self.cell(0, 10, "Registration Number: RA2311026010746 | Tech Assignment Submission", align="C")

def create_report():
    pdf = AcademicPDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # ------------------ PAGE 1: COVER PAGE ------------------
    pdf.add_page()
    
    # Left margin accent bar
    pdf.set_fill_color(99, 102, 241) 
    pdf.rect(0, 0, 12, 297, "F")
    
    pdf.set_left_margin(22)
    pdf.set_y(35)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "CODITY.AI TECH ASSIGNMENT SUBMISSION", ln=True)
    pdf.ln(4)
    
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(15, 17, 28)
    pdf.multi_cell(0, 11, "Distributed Asynchronous\nJob Scheduler (Overdrive)")
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "Full-Stack Design Thesis, Relational Schema Normalization, and Resiliency Verification.", ln=True)
    pdf.ln(35)
    
    pdf.set_fill_color(245, 246, 250)
    pdf.rect(22, pdf.get_y(), 168, 110, "F")
    
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
        ["Date of Submission:", "July 5, 2026"],
        ["Academic Institution:", "SRM Institute of Science and Technology"]
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
            
    # ------------------ PAGE 2: CONTINUOUS FLOW CONTENT ------------------
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_x(15)
    pdf.set_y(15)
    
    # 1. System Architecture
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 8, "1. System Architecture (20 Marks)", ln=True)
    pdf.set_draw_color(99, 102, 241)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 9.5)
    pdf.set_text_color(60, 60, 60)
    arch_desc = (
        "The scheduler platform is built on an event-driven distributed architecture designed to coordinate "
        "background job execution across multiple worker nodes. The system consists of three main blocks:\n"
        " - The Web API Gateway (FastAPI): Handles user registration, queue updates, job enqueueing, and dashboard metrics.\n"
        " - The Cron Scheduler Daemon (croniter): Scans the recurring cron database records to dynamically trigger jobs.\n"
        " - The Worker Fleet: Multiple isolated workers that register with host IP addresses and continuously claim and "
        "execute jobs, maintaining horizontal scalability."
    )
    pdf.multi_cell(0, 5, arch_desc)
    pdf.ln(4)
    
    # Embed Architecture Diagram Image
    if os.path.exists("architecture_diagram.png"):
        pdf.image("architecture_diagram.png", x=20, w=170)
        pdf.ln(6)
    
    # 2. Database Design
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 8, "2. Database Design & Normalization (20 Marks)", ln=True)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 9.5)
    db_desc = (
        "The relational schema is normalized to Third Normal Form (3NF) to maintain referential integrity. "
        "Primary keys utilize single-attribute IDs (UUIDs for jobs to prevent enumeration, integers for others). "
        "Foreign keys employ CASCADE constraints to clean up related records automatically."
    )
    pdf.multi_cell(0, 5, db_desc)
    pdf.ln(4)
    
    # Tables Description Table using FPDF table()
    tables_data = [
        ["Table Name", "Schema Purpose & Normalization Details"],
        ["users", "Credentials (hashed via bcrypt), roles (admin, user), metadata."],
        ["organizations", "Enables multi-tenancy workspace isolation."],
        ["projects", "Contains project workspaces owned by organizations."],
        ["queues", "Defines concurrency, priorities, and retry policies."],
        ["jobs", "Core queue table containing payload, status, and parent_job_id."],
        ["job_executions", "Tracks execution details, duration (ms), and trace errors."],
        ["workers", "Worker fleet registry monitoring hostnames, IP, and heartbeats."],
        ["cron_jobs", "Schedules recurring cron jobs to dynamically queue jobs."],
        ["dead_letter_queue", "Holds permanently failed tasks for manual replay."]
    ]
    
    pdf.set_font("helvetica", "", 8.5)
    with pdf.table(col_widths=(40, 140), text_align="LEFT") as table:
        for index, row in enumerate(tables_data):
            row_cells = table.row()
            if index == 0:
                pdf.set_font("helvetica", "B", 8.5)
            else:
                pdf.set_font("helvetica", "", 8.5)
            for cell_text in row:
                row_cells.cell(cell_text)
    pdf.ln(6)
    
    # 3. Backend Engineering & API Design
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 8, "3. Backend Engineering & API Design (25 Marks)", ln=True)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 9.5)
    backend_desc = (
        "The REST APIs utilize Pydantic schemas for request validation. A JWT security layer manages authentication "
        "and role-based permissions (RBAC). The endpoints aggregate system-wide performance and queue throughput data."
    )
    pdf.multi_cell(0, 5, backend_desc)
    pdf.ln(4)
    
    endpoints_data = [
        ["Method", "Endpoint Path", "Description & Functionality"],
        ["POST", "/api/auth/register", "Registers a user account with hashed credentials."],
        ["POST", "/api/auth/login", "Authenticates credentials and issues a JWT token."],
        ["POST", "/api/queues", "Creates a queue specifying concurrency limit & priority."],
        ["PATCH", "/api/queues/{id}", "Updates queue configs or pauses/resumes queue state."],
        ["POST", "/api/jobs", "Enqueue single task (immediate, delayed, or workflow)."],
        ["POST", "/api/jobs/batch", "Dispatches bulk job payloads under a single API call."],
        ["GET", "/api/jobs", "Lists jobs with pagination, queue, and status filters."],
        ["POST", "/api/jobs/{id}/retry", "Manually replays a failed or DLQ job."],
        ["GET", "/api/metrics", "Returns aggregate metrics, throughput trends, and error counts."]
    ]
    
    with pdf.table(col_widths=(20, 50, 110), text_align="LEFT") as table:
        for index, row in enumerate(endpoints_data):
            row_cells = table.row()
            if index == 0:
                pdf.set_font("helvetica", "B", 8.5)
            else:
                pdf.set_font("helvetica", "", 8.5)
            for cell_text in row:
                row_cells.cell(cell_text)
    pdf.ln(6)
    
    # 4. Reliability & Concurrency
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 8, "4. Reliability & Concurrency (15 Marks)", ln=True)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 9.5)
    concurrency_desc = (
        "To guarantee atomic task claims and prevent duplicate job execution, we execute claim operations inside "
        "a SQLite transaction with an IMMEDIATE lock. Candidate jobs are filtered dynamically to only select from "
        "active queues whose current active job count is below their concurrency_limit.\n"
        "Workers register themselves in the database and issue heartbeats every 5 seconds. If a worker goes offline "
        "for more than 15 seconds, it is marked as offline, and its active jobs are automatically re-queued for failover."
    )
    pdf.multi_cell(0, 5, concurrency_desc)
    pdf.ln(6)
    
    # 5. Frontend & UX
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 8, "5. Frontend & UX (10 Marks)", ln=True)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 9.5)
    frontend_desc = (
        "A premium Outfit-themed glassmorphic SPA dashboard provides real-time monitoring and control. "
        "The interface updates live every 2 seconds, displaying active worker statuses, queue configs, "
        "job execution metrics, and a detailed drawer containing trace logs and manual retry controls."
    )
    pdf.multi_cell(0, 5, frontend_desc)
    pdf.ln(4)

    # Embed Live Dashboard Screenshot Image
    if os.path.exists("dashboard_screenshot.png"):
        pdf.image("dashboard_screenshot.png", x=15, w=180)
        pdf.ln(6)
    
    # 6. Testing & Documentation
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 8, "6. Testing & Documentation (10 Marks)", ln=True)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("helvetica", "", 9.5)
    testing_desc = (
        "We implemented automated integration tests in tests/test_scheduler.py to verify system correctness. "
        "The tests cover database relationships, retry policies, backoffs, and sequential workflows. "
        "Running pytest completes successfully:"
    )
    pdf.multi_cell(0, 5, testing_desc)
    pdf.ln(4)
    
    # Pytest execution box
    pdf.set_fill_color(245, 245, 245)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(15, pdf.get_y(), 180, 22, "FD")
    
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_x(18)
    pdf.set_font("courier", "B", 8.5)
    pdf.set_text_color(30, 130, 30)
    pdf.cell(0, 4.5, "tests/test_scheduler.py::test_database_seeding_and_relations PASSED", ln=True)
    pdf.set_x(18)
    pdf.cell(0, 4.5, "tests/test_scheduler.py::test_job_execution_lifecycle_and_retries PASSED", ln=True)
    pdf.set_x(18)
    pdf.cell(0, 4.5, "tests/test_scheduler.py::test_workflow_dependencies_unblocking PASSED", ln=True)
    pdf.set_x(18)
    pdf.set_text_color(15, 17, 28)
    pdf.cell(0, 4.5, "============================== 3 passed in 2.02s ==============================", ln=True)
    pdf.ln(12)
    
    pdf.set_font("helvetica", "B", 10.5)
    pdf.cell(0, 8, "Verification GitHub Repository Link", ln=True)
    pdf.set_font("helvetica", "B", 9.5)
    pdf.set_text_color(99, 102, 241)
    pdf.cell(0, 8, "https://github.com/prudhvi98491/distributed-job-scheduler", ln=True, link="https://github.com/prudhvi98491/distributed-job-scheduler")

    # Output file
    output_filename = "RA2311026010746.pdf"
    pdf.output(output_filename)
    print(f"PDF successfully created: {output_filename}")

if __name__ == "__main__":
    create_report()
