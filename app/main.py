from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
import time
from loguru import logger
import os

from app.api.api import api_router
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware, LoggingMiddleware

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="""
    API for visually impaired people. Upload images to get detailed descriptions and assistance.
    This API uses vision-language models (VLMs) to analyze images and language models (LLMs) to provide
    context-aware descriptions and assistance based on the image content.
    """,
    version="1.0.0",
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    limit=settings.RATE_LIMIT_PER_MINUTE,
    window=60,
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Create storage directory if it doesn't exist
os.makedirs(settings.STORAGE_PATH, exist_ok=True)

# Mount static files for local storage
if settings.STORAGE_PROVIDER == "local":
    app.mount("/storage", StaticFiles(directory=settings.STORAGE_PATH), name="storage")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to track processing time for each request."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to provide clean error responses."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Our team has been notified."},
    )

@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Welcome to the Visually Impaired Assistant API",
        "documentation": f"{settings.API_V1_STR}/docs",
        "version": "1.0.0",
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "api_version": "1.0.0"} 