from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from pydantic import ValidationError
import uuid
import logging
import math
import urllib.parse
from app.models.lead import LeadStatus
from app.schemas.lead import LeadResponse, LeadCreate, LeadListResponse
from app.services.file_service import FileUploadService
from app.crud.lead import lead as lead_crud
from app.messaging.publisher import event_publisher
from app.core.config import settings
import uuid
import logging
import math

logger = logging.getLogger(__name__)


class LeadService:
    def __init__(self):
        self.file_service = FileUploadService()

    async def create_lead(
        self,
        first_name: str,
        last_name: str,
        email: str,
        resume_file: UploadFile,
        db: Session
    ) -> LeadResponse:
        """Create a new lead with resume upload"""
        
        try:
            lead_data = LeadCreate(
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                email=email.strip()
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Validation error: {e.errors()[0]['msg']}")
        
        existing_lead = lead_crud.get_by_email(db, lead_data.email)
        if existing_lead:
            raise HTTPException(
                status_code=409, 
                detail=f"A lead with email {lead_data.email} already exists"
            )
        
        try:
            resume_path = await self.file_service.upload_resume(resume_file, lead_data.email)
            
            lead_data.id = uuid.uuid4()
            lead_data.resume_path = resume_path
            lead_data.status = LeadStatus.PENDING
            
            db_lead = lead_crud.create(db, obj_in=lead_data)
            
            lead_response = LeadResponse.from_orm(db_lead)
            lead_response.resume_url = self._generate_resume_url(db_lead.resume_path)
            
            await self._publish_lead_created_event(lead_response)
            return lead_response
            
        except HTTPException:
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error for {email}: {e}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred")

    async def _publish_lead_created_event(self, lead_response: LeadResponse):
        """Publish lead created event - internal business logic"""
        try:
            await event_publisher.publish_lead_created(
                lead_response=lead_response,
                metadata={
                    "source": "lead_service",
                    "event_version": "1.0"
                }
            )
            logger.info(f"Lead created event published for {lead_response.email}")
            
        except Exception as e:
            logger.error(f"Failed to publish lead created event: {e}")
            
    def get_paginated_leads(
        self, 
        db: Session, 
        page: int = 1, 
        page_size: int = 10
    ) -> LeadListResponse:
        """Get paginated leads with resume URLs"""
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
        
        try:
            leads, total = lead_crud.get_paginated(db, page=page, page_size=page_size)
            
            lead_responses = []
            for lead in leads:
                lead_response = LeadResponse.from_orm(lead)
                lead_response.resume_url = self._generate_resume_url(lead.resume_path)
                lead_responses.append(lead_response)
            
            total_pages = math.ceil(total / page_size) if total > 0 else 1
            
            return LeadListResponse(
                leads=lead_responses,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error fetching paginated leads: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch leads")
        
    def _generate_resume_url(self, resume_path: str) -> str:
        """Generate MinIO URL from resume path"""
        if not resume_path:
            return None
            
        # URL encode the path
        encoded_path = urllib.parse.quote(resume_path, safe='')
        
        # Generate MinIO browser URL
        minio_url = f"{settings.MINIO_URL}/browser/leads/{encoded_path}"
        
        return minio_url

    def update_lead_status(self, db: Session, email: str, new_status: LeadStatus) -> LeadResponse:
        """Update lead status via their email (attorney only)"""
        try:
            existing_lead = lead_crud.get_by_email(db, email)
            if not existing_lead:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Lead with email {email} not found"
                )
            
            update_data = {"status": new_status}
            updated_lead = lead_crud.update(db, db_obj=existing_lead, obj_in=update_data)
            
            if not updated_lead:
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to update lead status"
                )
            
            lead_response = LeadResponse.from_orm(updated_lead)
            
            logger.info(f"Lead status updated: {email} -> {new_status}")
            return lead_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating lead status for {email}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update lead status")
