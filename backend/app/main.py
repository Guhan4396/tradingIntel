"""TradingIntel FastAPI application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("TradingIntel starting up...")

    # Create database tables
    try:
        await create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")

    # Seed default sources
    try:
        from app.database import AsyncSessionLocal
        from app.services.ingestion.registry import seed_default_sources
        async with AsyncSessionLocal() as db:
            await seed_default_sources(db)
        logger.info("Default sources seeded")
    except Exception as e:
        logger.error(f"Source seeding failed: {e}")

    # Start scheduler
    try:
        from app.services.scheduler import start_scheduler
        start_scheduler()
        logger.info("Background scheduler started")
    except Exception as e:
        logger.error(f"Scheduler start failed: {e}")

    logger.info("TradingIntel startup complete")
    yield

    # Shutdown
    logger.info("TradingIntel shutting down...")
    try:
        from app.services.scheduler import stop_scheduler
        stop_scheduler()
    except Exception as e:
        logger.error(f"Scheduler stop failed: {e}")


app = FastAPI(
    title="TradingIntel API",
    description="AI-Powered Trade Intelligence for Indian Exporters",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount routers
from app.routers import customers, shipments, intelligence, alerts, health_check, whatsapp

app.include_router(customers.router, prefix="/api/v1")
app.include_router(shipments.router, prefix="/api/v1")
app.include_router(intelligence.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(health_check.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "TradingIntel API",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "TradingIntel API",
        "docs": "/api/docs",
        "health": "/health",
    }
