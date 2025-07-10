"""
Main FastAPI application for AIRIES AI Backend
Entry point for the API server
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
import uvicorn

from .core.config import settings
from .core.database import init_db, close_db
from .core.logging import setup_logging, set_account_context, clear_account_context, get_logger, generate_request_id
from .api.v1.api import api_router


# Configure enhanced logging with account context
setup_logging(settings.LOG_LEVEL, structured=True)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting AIRIES AI Backend...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AIRIES AI Backend...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant SaaS platform for AI conversational agents",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.airies.ai"]
    )


@app.middleware("http")
async def account_context_middleware(request: Request, call_next):
    """Set account context for logging and tracking"""
    # Generate request ID
    request_id = generate_request_id()
    
    # Try to extract user/account info from token
    account_id = None
    user_id = None
    
    try:
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            # TODO: Implement token validation and user extraction
            # This will be implemented when we have the security functions ready
            # user = await get_current_user_from_token(token)
            # if user:
            #     account_id = user.account_id
            #     user_id = str(user.id)
    except Exception:
        # If token extraction fails, continue without context
        pass
    
    # Set account context for this request
    set_account_context(account_id, user_id, request_id)
    
    try:
        response = await call_next(request)
        return response
    finally:
        # Clear context after request
        clear_account_context()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for monitoring with account context"""
    start_time = time.time()
    
    # Log request with account context
    logger.log_api_call(
        method=request.method,
        endpoint=request.url.path,
        status_code=0,  # Will be updated in response
        response_time_ms=0,  # Will be updated in response
        extra_data={
            'client_host': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown')
        }
    )
    
    response = await call_next(request)
    
    # Log response with timing
    process_time = time.time() - start_time
    logger.log_api_call(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        response_time_ms=process_time * 1000,
        extra_data={
            'client_host': request.client.host if request.client else 'unknown'
        }
    )
    
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error for {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception for {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": time.time()
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AIRIES AI Backend API",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "redoc": f"{settings.API_V1_STR}/redoc"
    }


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        log_level=settings.LOG_LEVEL.lower()
    )