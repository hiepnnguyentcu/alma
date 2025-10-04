from fastapi import FastAPI
import logging

from app.core.config import settings
from app.core.postgres import check_postgres_health
from app.messaging.kafka_consumer import kafka_consumer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    
    # Check PostgreSQL connectivity
    logger.info("Checking PostgreSQL connection...")
    postgres_healthy = await check_postgres_health()
    
    # Start Kafka Consumer on app startup
    logger.info("Starting Kafka consumer...")
    await kafka_consumer.start()
    kafka_healthy = kafka_consumer.started
    
    if kafka_healthy:
        logger.info("Kafka consumer started successfully")
    else:
        logger.error("Kafka consumer failed to start")
    
    # Summary
    if postgres_healthy and kafka_healthy:
        logger.info("All services healthy! Notification service ready.")
    else:
        logger.warning("⚠️ Some services are not healthy. Check logs above.")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info(f"Shutting down {settings.PROJECT_NAME}")
    # Stop Kafka Consumer on app shutdown
    await kafka_consumer.stop()

@app.get("/")
async def root():
    """Root endpoint for service identification"""
    return {
        "service": settings.PROJECT_NAME,
        "type": "kafka_consumer",
        "status": "running",
        "version": settings.VERSION
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if kafka_consumer.started else "degraded",
        "services": {
            "postgres": "connected",
            "kafka_consumer": "running" if kafka_consumer.started else "stopped"
        },
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )