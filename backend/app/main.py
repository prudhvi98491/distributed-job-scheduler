"""
Main FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os

from app.config import CORS_ORIGINS, APP_TITLE, APP_VERSION
from app.database import init_db
from app.services import websocket as ws_service
from app.services.scheduler import promote_scheduled_jobs, tick_cron_jobs, detect_stale_jobs
from app.routes import auth, organizations, projects, queues, jobs, workers, dlq, metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Distributed Job Scheduler API...")
    await init_db()
    logger.info("Database initialized")

    # Seed demo data
    from app.seed import seed_demo_data
    await seed_demo_data()

    # Start background scheduler
    scheduler.add_job(promote_scheduled_jobs, "interval", seconds=5, id="promote_jobs")
    scheduler.add_job(tick_cron_jobs, "interval", seconds=10, id="cron_tick")
    scheduler.add_job(detect_stale_jobs, "interval", seconds=15, id="stale_detection")
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Production-grade distributed job scheduling platform",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(organizations.router)
app.include_router(projects.router)
app.include_router(queues.router)
app.include_router(jobs.router)
app.include_router(workers.router)
app.include_router(dlq.router)
app.include_router(metrics.router)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_service.register(ws)
    try:
        while True:
            # Keep connection alive, receive pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        ws_service.unregister(ws)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "ws_connections": ws_service.connection_count(),
    }


# Serve frontend static files if built
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index = os.path.join(frontend_dist, "index.html")
        return FileResponse(index)
