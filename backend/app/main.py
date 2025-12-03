"""Main FastAPI application for 911 Operator Training Simulator"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models import schemas
from app.api.routes import calls, websocket
from app.db import init_db, engine
from app.services.dialogue_manager import dialogue_manager
from app.services.storage_service import storage_service
from app.services.tts_service import tts_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting 911 Operator Training Simulator Backend...")

    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()

        # Initialize dialogue manager (Redis)
        logger.info("Initializing dialogue manager...")
        await dialogue_manager.initialize()

        logger.info("Application startup complete!")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")

    try:
        # Close dialogue manager (Redis)
        await dialogue_manager.close()

        # Close database connections
        await engine.dispose()

        logger.info("Application shutdown complete")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title="911 Operator Training Simulator API",
    description="Backend API for AI-powered 911 operator training simulation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(calls.router)
app.include_router(websocket.router)


# Health check endpoints
@app.get("/health", response_model=schemas.HealthCheckResponse, tags=["health"])
async def health_check():
    """
    Basic health check endpoint.

    Returns application status and version.
    """
    return schemas.HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0"
    )


@app.get("/ready", response_model=schemas.ReadinessCheckResponse, tags=["health"])
async def readiness_check():
    """
    Readiness check endpoint.

    Verifies all external dependencies are available.
    """
    # Check database
    database_ready = True
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_ready = False

    # Check Redis
    redis_ready = True
    try:
        if dialogue_manager.redis_client:
            await dialogue_manager.redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_ready = False

    # Check S3
    s3_ready = await storage_service.health_check()

    # Check TTS
    tts_ready = await tts_service.health_check()

    # Overall status
    all_ready = database_ready and redis_ready and s3_ready and tts_ready
    overall_status = "ready" if all_ready else "not_ready"

    return schemas.ReadinessCheckResponse(
        status=overall_status,
        database=database_ready,
        redis=redis_ready,
        s3=s3_ready,
        tts=tts_ready,
        timestamp=datetime.utcnow()
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "911 Operator Training Simulator API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "readiness": "/ready"
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
