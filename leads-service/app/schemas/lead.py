from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.lead import LeadStatus


class LeadCreate(BaseModel):
    id: Optional[UUID] = None
    first_name: str = Field(..., min_length=1, max_length=50, description="First name is required")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name is required") 
    email: EmailStr = Field(..., description="Valid email address is required")
    resume_path: Optional[str] = None
    status: Optional[LeadStatus] = LeadStatus.PENDING


class LeadStatusUpdateRequest(BaseModel):
    email: EmailStr = Field(..., description="Email of the lead to update")
    status: LeadStatus = Field(..., description="New status for the lead")


class LeadResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    resume_path: str
    resume_url: Optional[str] = None
    status: LeadStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
