from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.crud.base import CRUDBase
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadResponse


class CRUDLead(CRUDBase[Lead, LeadCreate, LeadResponse]):
    def get_paginated(
        self, 
        db: Session, 
        page: int = 1, 
        page_size: int = 10
    ) -> Tuple[List[Lead], int]:
        """Get paginated leads with total count"""
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total = db.query(func.count(Lead.id)).scalar()
        
        # Get paginated results
        leads = (
            db.query(Lead)
            .order_by(Lead.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        
        return leads, total
    
    def get_by_email(self, db: Session, email: str) -> Optional[Lead]:
        """Get lead by email"""
        return db.query(self.model).filter(self.model.email == email).first()


lead = CRUDLead(Lead)
