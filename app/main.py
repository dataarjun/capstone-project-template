"""
FastAPI Application Entry Point

This is the main entry point for the Multi-Agent AML Investigation System.
It initializes the FastAPI app, mounts routes, and configures middleware.
"""

from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import agents, investigations, monitoring, health, prompts, transactions, chat
from app.core.config_simple import settings
from app.core.logger import get_logger

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Multi-Agent AML Investigation System",
    description="A FastAPI-based system for automated anti-money laundering investigations using multi-agent orchestration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS.split(",") if isinstance(settings.ALLOWED_HOSTS, str) else settings.ALLOWED_HOSTS
)

# Include API routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(investigations.router, prefix="/api/investigations", tags=["investigations"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])
app.include_router(prompts.router, prefix="/api", tags=["prompts"])
app.include_router(transactions.router, prefix="/api", tags=["transactions"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Multi-Agent AML Investigation System")
    # Add any initialization logic here

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down Multi-Agent AML Investigation System")
    # Add any cleanup logic here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
