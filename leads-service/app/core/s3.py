from minio import Minio
from minio.error import S3Error
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_s3_client() -> Minio:
    """Create and return a MinIO/S3 client instance"""
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )


def ensure_s3_bucket_exists(client: Minio, bucket_name: str) -> None:
    """Ensure the specified S3 bucket exists, create if it doesn't"""
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Created S3 bucket: {bucket_name}")
        else:
            logger.info(f"S3 bucket already exists: {bucket_name}")
    except S3Error as e:
        logger.error(f"Error with S3 bucket: {e}")
        raise


async def check_s3_health() -> bool:
    """Check S3/MinIO connectivity and health"""
    try:
        client = create_s3_client()
        
        # Test connection by listing buckets
        buckets = client.list_buckets()
        logger.info(f"S3/MinIO health check passed - Found {len(buckets)} buckets")
        
        # Check if default bucket exists
        bucket_name = getattr(settings, 'MINIO_BUCKET_NAME', None)
        if bucket_name:
            bucket_exists = client.bucket_exists(bucket_name)
            if bucket_exists:
                logger.info(f"Default bucket '{bucket_name}' exists")
            else:
                logger.warning(f"Default bucket '{bucket_name}' does not exist")
        
        return True
    except S3Error as e:
        logger.error(f"S3/MinIO health check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"S3/MinIO health check error: {e}")
        return False


s3_client = create_s3_client()

if hasattr(settings, 'MINIO_BUCKET_NAME') and settings.MINIO_BUCKET_NAME:
    try:
        ensure_s3_bucket_exists(s3_client, settings.MINIO_BUCKET_NAME)
    except Exception as e:
        logger.warning(f"Could not ensure default bucket exists: {e}")


def get_s3_client() -> Minio:
    """Dependency function to get S3/MinIO client instance"""
    return s3_client
