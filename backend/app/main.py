"""
Month-End Close Orchestrator - Main FastAPI Application
Production-grade autonomous agentic AI platform for PE fund financial close operations.
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.config import settings
from app.database import init_db, SessionLocal
from app.api.companies import router as companies_router
from app.api.agents import router as agents_router
from app.api.reports import router as reports_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Socket.IO setup for real-time WebSocket updates
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.WS_CORS_ORIGINS.split(","),
    logger=False,
)

# Background scheduler reference
scheduler_task = None


async def broadcast_to_clients(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    await sio.emit("agent_update", message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialized")

    # Start autonomous scheduler
    global scheduler_task
    scheduler_task = asyncio.create_task(autonomous_scheduler())
    logger.info("Autonomous scheduler started")

    yield

    # Shutdown
    if scheduler_task:
        scheduler_task.cancel()
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Autonomous AI-powered month-end close orchestration for PE portfolio companies",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(companies_router)
app.include_router(agents_router)
app.include_router(reports_router)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)


# ---- Socket.IO Events ----

@sio.event
async def connect(sid, environ):
    logger.info(f"WebSocket client connected: {sid}")
    await sio.emit("connection_established", {
        "message": "Connected to Month-End Close Orchestrator",
        "timestamp": datetime.utcnow().isoformat(),
    }, room=sid)


@sio.event
async def disconnect(sid):
    logger.info(f"WebSocket client disconnected: {sid}")


@sio.event
async def trigger_agent(sid, data):
    """Handle agent trigger requests from WebSocket clients."""
    agent_type = data.get("agent_type")
    company_id = data.get("company_id")
    period = data.get("period", "2026-01")

    logger.info(f"Agent trigger received: {agent_type} for {company_id}")

    db = SessionLocal()
    try:
        from app.services.scheduler import run_single_agent
        result = await run_single_agent(agent_type, company_id, period, db)
        await sio.emit("agent_result", {
            "agent_type": agent_type,
            "company_id": company_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }, room=sid)
    except Exception as e:
        await sio.emit("agent_error", {
            "agent_type": agent_type,
            "error": str(e),
        }, room=sid)
    finally:
        db.close()


# ---- Health & Info Endpoints ----

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/seed")
async def seed_database():
    """Seed the database with sample data."""
    from app.services.data_loader import DataLoader
    db = SessionLocal()
    try:
        loader = DataLoader(db)
        loader.clear_all()
        stats = loader.load_all()
        return {"message": "Database seeded successfully", "stats": stats}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@app.get("/api/settings")
def get_settings():
    """Get current application settings (non-sensitive)."""
    return {
        "variance_threshold_pct": settings.VARIANCE_THRESHOLD_PCT,
        "variance_threshold_amt": settings.VARIANCE_THRESHOLD_AMT,
        "daily_close_hour": settings.DAILY_CLOSE_HOUR,
        "monitoring_interval_minutes": settings.MONITORING_INTERVAL_MINUTES,
        "email_enabled": settings.EMAIL_ENABLED,
        "llm_model": settings.CLAUDE_MODEL,
        "max_agent_retries": settings.MAX_AGENT_RETRIES,
    }


# ---- Autonomous Scheduler ----

async def autonomous_scheduler():
    """Background task that runs autonomous agent operations on schedule."""
    logger.info("Autonomous scheduler initialized")
    last_daily_run = None
    last_monitor_run = None

    while True:
        try:
            now = datetime.utcnow()

            # Daily close check (9 AM)
            if (last_daily_run is None or
                (now - last_daily_run).total_seconds() > 86400):
                if now.hour == settings.DAILY_CLOSE_HOUR:
                    logger.info("Running scheduled daily check...")
                    from app.services.scheduler import run_daily_check
                    await run_daily_check()
                    last_daily_run = now

            # Monitoring every 5 minutes
            if (last_monitor_run is None or
                (now - last_monitor_run).total_seconds() > settings.MONITORING_INTERVAL_MINUTES * 60):
                from app.services.scheduler import run_monitoring
                await run_monitoring()
                last_monitor_run = now

            # Process any pending workflow tasks
            from app.services.scheduler import process_workflow_tasks
            await process_workflow_tasks()

            await asyncio.sleep(30)  # Check every 30 seconds

        except asyncio.CancelledError:
            logger.info("Scheduler cancelled")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            await asyncio.sleep(60)
