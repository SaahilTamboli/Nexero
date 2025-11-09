"""
Nexero VR Backend - Main Application Entry Point

FastAPI backend service for VR real estate behavioral analytics platform.
Receives tracking data from Unreal Engine VR client and processes it for
AI-powered sales insights.

Architecture:
- FastAPI web framework
- Supabase PostgreSQL database
- Pydantic data validation
- Async operations for high performance

Workflow:
1. Sales person starts VR session from dashboard
2. Customer experiences property tour in VR
3. Unreal Engine collects behavioral data
4. After session ends, data sent to this backend via HTTP POST
5. Backend stores and processes for AI/ML analytics
6. Dashboard shows insights to sales team and builders

Endpoints:
- /api/v1/unreal/* - Unreal Engine integration endpoints
- /docs - Interactive API documentation (Swagger UI)
- /health - Health check for monitoring

Run:
    uvicorn app.main:app --reload
    or
    python app/main.py
"""

import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Callable

from app.api.v1.unreal import router as unreal_router
from app.config import get_settings
from app.core.database import SupabaseDB

# Configure logging with timest
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Handles initialization and cleanup tasks when the application
    starts and stops.
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Nexero VR Backend Started")
    logger.info("=" * 60)
    logger.info("📡 Ready to receive data from Unreal Engine")
    logger.info("📊 Processing pipeline: VR → API → Database → Analytics")
    logger.info("🌐 API Documentation: http://localhost:8000/docs")
    logger.info("💚 Health Check: http://localhost:8000/health")
    logger.info("=" * 60)
    
    # ASCII Art
    print("""
    ███╗   ██╗███████╗██╗  ██╗███████╗██████╗  ██████╗ 
    ████╗  ██║██╔════╝╚██╗██╔╝██╔════╝██╔══██╗██╔═══██╗
    ██╔██╗ ██║█████╗   ╚███╔╝ █████╗  ██████╔╝██║   ██║
    ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══╝  ██╔══██╗██║   ██║
    ██║ ╚████║███████╗██╔╝ ██╗███████╗██║  ██║╚██████╔╝
    ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ 
    
          VR Real Estate Analytics Platform
    """)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("👋 Nexero VR Backend shutting down")
    logger.info("=" * 60)


# Initialize FastAPI application
app = FastAPI(
    title="Nexero VR Backend",
    description="Backend API for VR real estate behavioral analytics. "
                "Receives tracking data from Unreal Engine VR tours and "
                "processes it for AI-powered sales insights.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Get application settings
settings = get_settings()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["*"] for development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Middleware: Log raw request body for debugging incoming Unreal payloads
@app.middleware("http")
async def log_raw_request_body(request: Request, call_next: Callable):
    try:
        # Only log API requests to reduce noise
        if request.url.path.startswith("/api/v1"):
            body_bytes = await request.body()
            # Try to decode as UTF-8 for readable logging
            try:
                body_text = body_bytes.decode("utf-8") if body_bytes else ""
            except Exception:
                body_text = str(body_bytes)

            logger.info("📥 [RAW REQUEST] %s %s -> %s", request.method, request.url.path, body_text)

            # Recreate receive function so downstream can read body again
            async def receive() -> dict:
                return {"type": "http.request", "body": body_bytes}

            request._receive = receive  # type: ignore[attr-defined]

    except Exception as e:
        logger.warning(f"Failed to log raw request body: {e}")

    response = await call_next(request)
    return response

# Include API routers
app.include_router(
    unreal_router,
    prefix="/api/v1"
)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    
    Provides basic information about the service and links to
    documentation and health check endpoints.
    
    Returns:
        dict: Service information and available endpoints
    """
    return {
        "service": "Nexero VR Backend",
        "version": "1.0.0",
        "status": "running",
        "description": "VR Real Estate Analytics Platform",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "api": "/api/v1/unreal"
        },
        "integrations": {
            "vr_client": "Unreal Engine",
            "database": "Supabase",
            "analytics": "AI/ML Pipeline"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Verifies the application is running and can connect to
    required services (database, etc.).
    
    Returns:
        dict: Health status information
    """
    try:
        # Test database connection
        db = SupabaseDB()
        db_status = "connected"
        
        # You could add a simple query here to verify database is responsive
        # For example: await db.client.table("vr_sessions").select("id").limit(1).execute()
        
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        db_status = "error"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "version": "1.0.0",
        "uptime": "running"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Catches all unhandled exceptions, logs them, and returns
    a user-friendly error response. Prevents internal errors
    from exposing sensitive information.
    
    Args:
        request: The incoming request that caused the error
        exc: The exception that was raised
    
    Returns:
        JSONResponse: Generic error message with 500 status
    """
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path
        }
    )


# Run application directly with Python
if __name__ == "__main__":
    import uvicorn
    import os
    
    logger.info("Starting Nexero VR Backend with Uvicorn...")
    
    # Get port from environment variable (Railway provides this)
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True,  # Enable auto-reload for development
        reload_dirs=["app"]  # Watch app directory for changes
    )
