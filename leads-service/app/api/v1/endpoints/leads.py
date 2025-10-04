from fastapi import APIRouter, Depends, Form, File, UploadFile, Query, Body
from sqlalchemy.orm import Session
from app.core.postgres import get_postgres_db
from app.authentication.jwt import get_current_user, require_attorney
from app.schemas.lead import LeadResponse, LeadListResponse, LeadStatusUpdateRequest
from app.services.lead_service import LeadService
from app.models.lead import LeadStatus

router = APIRouter()
lead_service = LeadService()


@router.post("/leads", response_model=LeadResponse, status_code=201)
async def create_lead(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_postgres_db)
):
    """Create a new lead with resume upload"""
    return await lead_service.create_lead(first_name, last_name, email, resume, db)


@router.get("/leads", response_model=LeadListResponse)
async def get_leads(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (1-100)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_postgres_db)
):
    """Get paginated leads with resume download URLs (requires authentication)"""
    return lead_service.get_paginated_leads(db, page=page, page_size=page_size)


@router.patch("/leads/status", response_model=LeadResponse)
async def update_lead_status(
    request: LeadStatusUpdateRequest = Body(...),
    current_user: dict = Depends(require_attorney),  # Only attorneys can update status
    db: Session = Depends(get_postgres_db)
):
    """Update lead status by email (attorney only)"""
    return lead_service.update_lead_status(db, request.email, request.status)
