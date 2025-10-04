from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import api_router
from app.core.config import settings
from app.core.postgres import check_postgres_health
from app.core.s3 import check_s3_health
from app.core.exceptions import configure_exception_handlers
from app.messaging.kafka_client import kafka_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure exception handling
configure_exception_handlers(app)

# Configure CORS middleware
allowed_origins = settings.ALLOWED_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Documentation available at: /docs")
    
    # Check PostgreSQL connectivity
    logger.info("Checking PostgreSQL connection...")
    postgres_healthy = await check_postgres_health()
    
    # Check S3/MinIO connectivity
    logger.info("Checking S3/MinIO connection...")
    s3_healthy = await check_s3_health()
    
    # Start Kafka on app startup
    logger.info("Starting Kafka connection...")
    await kafka_client.start()
    kafka_healthy = kafka_client.started
    
    if kafka_healthy:
        logger.info("Kafka connection established")
    else:
        logger.error("Kafka connection failed")
    
    # Summary
    if postgres_healthy and s3_healthy and kafka_healthy:
        logger.info("All services healthy! Application ready.")
    else:
        logger.warning("Some services are not healthy. Check logs above.")
    
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info(f"Shutting down {settings.PROJECT_NAME}")
    # Stop Kafka on app shutdown
    await kafka_client.stop()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if kafka_client.started else "degraded",
        "services": {
            "postgres": "connected",
            "s3": "connected", 
            "kafka": "connected" if kafka_client.started else "disconnected"
        },
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )