from fastapi import UploadFile, HTTPException
from minio.error import S3Error
import os
import io
import logging
from app.core.s3 import get_s3_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileUploadService:
    def __init__(self):
        self.s3_client = get_s3_client()
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    async def upload_resume(self, file: UploadFile, email: str) -> str:
        """Upload resume to S3 and return the file path"""
        
        try:
            if not file.filename:
                raise HTTPException(status_code=400, detail="No file provided")
            
            resume_path = f"{email}/resume/{file.filename}"
            
            file_content = await file.read()
            if len(file_content) > self.max_file_size:
                raise HTTPException(status_code=400, detail="File too large (max 10MB)")
            
            file_data = io.BytesIO(file_content)
            self.s3_client.put_object(
                bucket_name=self.bucket_name,
                object_name=resume_path,
                data=file_data,
                length=len(file_content),
                content_type=file.content_type or "application/octet-stream"
            )
            
            return resume_path
            
        except HTTPException:
            raise
        except S3Error as e:
            logger.error(f"S3 error for {email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file")
        except Exception as e:
            logger.error(f"Upload error for {email}: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")
        finally:
            await file.seek(0)