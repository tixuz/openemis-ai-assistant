"""
FastAPI Main Application

Production-ready backend with:
- JWT authentication
- Rate limiting
- CORS protection
- Safe command execution (no exec())
- Learning mechanism
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from backend.config import settings
from backend.api.routes import auth, automation, user, admin, variables


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Initialize FastAPI app
app = FastAPI(
    title="AI Automation System",
    description="Production-ready automation system with safe command execution",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS Middleware - Selective Origins
# Allows localhost with any port + specific OpenEMIS domains
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,  # localhost with any port
    allow_origins=[origin for origin in settings.CORS_ORIGINS if "openemis.org" in origin],  # OpenEMIS domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"{request.method} {request.url.path} - {request.client.host}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


# Include routers
app.include_router(auth.router)
app.include_router(automation.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(variables.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        System health status
    """
    from backend.core.llm_client import LLMClient

    # Check LLM connection
    llm_client = LLMClient(server_url=settings.LLM_SERVER_URL)
    llm_available = llm_client.test_connection()

    return {
        "status": "healthy",
        "version": "2.0.0",
        "llm_available": llm_available,
        "llm_server": settings.LLM_SERVER_URL
    }


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "AI Automation System",
        "version": "2.0.0",
        "description": "Production-ready automation with safe command execution",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "Safe command execution (no exec())",
            "JWT authentication",
            "Rate limiting",
            "Learning mechanism",
            "Few-shot prompting",
            "CORS protection"
        ]
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting AI Automation System v2.0.0")
    logger.info(f"LLM Server: {settings.LLM_SERVER_URL}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    logger.info(f"Rate Limit: {settings.RATE_LIMIT_PER_MINUTE}/minute")

    # Ensure directories exist
    import os
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(settings.LOGS_DIR, exist_ok=True)
    os.makedirs("logs/screenshots", exist_ok=True)

    logger.info("✅ System ready")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Automation System")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level=settings.LOG_LEVEL.lower()
    )
