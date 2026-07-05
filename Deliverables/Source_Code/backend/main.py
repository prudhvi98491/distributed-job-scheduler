import os
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from backend.database import engine, Base, async_session
from backend.models import User, Organization, Project, Queue, RetryPolicy, OrganizationUser
from backend.auth import hash_password
from backend.worker import JobWorker
from backend.scheduler import CronScheduler

# Import routers
from backend.routes.auth import router as auth_router
from backend.routes.queues import router as queues_router
from backend.routes.jobs import router as jobs_router
from backend.routes.workers import router as workers_router

async def seed_database():
    async with async_session() as db:
        async with db.begin():
            # 1. Create Default Admin User
            result = await db.execute(select(User).filter(User.username == "admin"))
            admin = result.scalars().first()
            if not admin:
                admin = User(
                    username="admin",
                    password_hash=hash_password("password"),
                    role="admin"
                )
                db.add(admin)
                await db.flush() # Flush to get ID

            # 2. Create Default Organization
            result = await db.execute(select(Organization).filter(Organization.name == "Acme Corporation"))
            org = result.scalars().first()
            if not org:
                org = Organization(name="Acme Corporation")
                db.add(org)
                await db.flush()

                # Add admin user to Organization
                org_user = OrganizationUser(
                    organization_id=org.id,
                    user_id=admin.id,
                    role="admin"
                )
                db.add(org_user)

            # 3. Create Default Project
            result = await db.execute(select(Project).filter(Project.name == "Production Services"))
            proj = result.scalars().first()
            if not proj:
                proj = Project(organization_id=org.id, name="Production Services")
                db.add(proj)
                await db.flush()

            # 4. Create Default Retry Policies
            policies_to_seed = [
                {"name": "Fixed 5s Retry", "strategy": "fixed", "base_delay": 5, "max_retries": 3, "backoff_factor": 1.0},
                {"name": "Linear Backoff", "strategy": "linear", "base_delay": 5, "max_retries": 4, "backoff_factor": 1.0},
                {"name": "Exponential Backoff", "strategy": "exponential", "base_delay": 2, "max_retries": 5, "backoff_factor": 2.0}
            ]
            
            created_policies = {}
            for p_data in policies_to_seed:
                result = await db.execute(select(RetryPolicy).filter(RetryPolicy.name == p_data["name"]))
                policy = result.scalars().first()
                if not policy:
                    policy = RetryPolicy(**p_data)
                    db.add(policy)
                    await db.flush()
                created_policies[p_data["strategy"]] = policy

            # 5. Create Default Queues
            queues_to_seed = [
                {"name": "default", "priority": 1, "concurrency_limit": 5, "retry_policy_id": created_policies["fixed"].id},
                {"name": "high-priority", "priority": 5, "concurrency_limit": 10, "retry_policy_id": created_policies["exponential"].id},
                {"name": "background-tasks", "priority": 1, "concurrency_limit": 2, "retry_policy_id": created_policies["linear"].id}
            ]

            for q_data in queues_to_seed:
                result = await db.execute(select(Queue).filter(Queue.name == q_data["name"]))
                queue = result.scalars().first()
                if not queue:
                    queue = Queue(
                        project_id=proj.id,
                        name=q_data["name"],
                        priority=q_data["priority"],
                        concurrency_limit=q_data["concurrency_limit"],
                        retry_policy_id=q_data["retry_policy_id"]
                    )
                    db.add(queue)

            await db.commit()

# Manage lifespan of background worker and scheduler
worker_instance = None
scheduler_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global worker_instance, scheduler_instance
    
    # 1. Setup DB Schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Seed DB
    await seed_database()
    
    # 3. Start worker & scheduler
    worker_instance = JobWorker(concurrency=5)
    scheduler_instance = CronScheduler()
    await worker_instance.start()
    await scheduler_instance.start()
    
    yield
    
    # 4. Stop worker & scheduler
    if scheduler_instance:
        await scheduler_instance.stop()
    if worker_instance:
        await worker_instance.stop()

app = FastAPI(
    title="Distributed Job Scheduler",
    description="A production-grade distributed background job scheduler dashboard and API.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(auth_router)
app.include_router(queues_router)
app.include_router(jobs_router)
app.include_router(workers_router)

# Serve Frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/")
async def get_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Frontend dashboard not found!</h1>")

@app.get("/styles.css")
async def get_css():
    css_path = os.path.join(FRONTEND_DIR, "styles.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return HTMLResponse("CSS not found", status_code=404)

@app.get("/app.js")
async def get_js():
    js_path = os.path.join(FRONTEND_DIR, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return HTMLResponse("JS not found", status_code=404)
