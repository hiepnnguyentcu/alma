import pytest
from unittest.mock import patch, AsyncMock, Mock
from app.services.lead_service import LeadService
from fastapi import HTTPException
from app.schemas.lead import LeadResponse
from app.models.lead import LeadStatus
import uuid
from datetime import datetime
import logging

class TestLeadService:
    
    def setup_method(self):
        self.service = LeadService()

    @patch('app.services.lead_service.lead_crud')
    @patch('app.services.lead_service.FileUploadService')
    @pytest.mark.asyncio
    async def test_create_lead_success(self, mock_file_service_class, mock_crud, mock_db, mock_file):
        """Test service creates lead successfully"""
        mock_file_service = Mock()
        mock_file_service.upload_resume = AsyncMock(return_value="path/resume.pdf")
        mock_file_service_class.return_value = mock_file_service
        
        # Mock get_by_email to return None (no existing lead)
        mock_crud.get_by_email.return_value = None
        
        mock_lead_response = LeadResponse(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            resume_path="path/resume.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now()
        )
        mock_crud.create.return_value = mock_lead_response
        
        with patch.object(LeadResponse, 'from_orm', return_value=mock_lead_response):
            with patch.object(self.service, '_generate_resume_url', return_value="http://test-url"):
                with patch.object(self.service, '_publish_lead_created_event', new_callable=AsyncMock):
                    service = LeadService()
                    result = await service.create_lead("John", "Doe", "john@test.com", mock_file, mock_db)
        
        assert result.first_name == "John"
        mock_crud.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_lead_invalid_email(self, mock_db, mock_file):
        """Test service validates email"""
        with pytest.raises(HTTPException) as exc:
            await self.service.create_lead("John", "Doe", "invalid-email", mock_file, mock_db)
        
        assert exc.value.status_code == 400

    @patch('app.services.lead_service.lead_crud')
    @patch('app.services.lead_service.FileUploadService')
    def test_get_paginated_leads_success(self, mock_file_service_class, mock_crud, mock_db):
        """Test service returns paginated leads"""
        mock_file_service = Mock()
        mock_file_service_class.return_value = mock_file_service
        
        mock_lead_response = LeadResponse(
            id=uuid.uuid4(),
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            resume_path="path/resume.pdf",
            status=LeadStatus.PENDING,
            created_at=datetime.now()
        )
        mock_crud.get_paginated.return_value = ([mock_lead_response], 1)
        
        with patch.object(LeadResponse, 'from_orm', return_value=mock_lead_response):
            service = LeadService()
            result = service.get_paginated_leads(mock_db, page=1, page_size=10)
        
        assert result.total == 1
        assert result.page == 1
        assert len(result.leads) == 1

    @patch('app.services.lead_service.lead_crud')
    @patch('app.services.lead_service.FileUploadService')
    def test_update_lead_status_success(self, mock_file_service_class, mock_crud, mock_db):
        """Test service updates lead status successfully"""
        mock_file_service = Mock()
        mock_file_service_class.return_value = mock_file_service
        
        mock_existing_lead = Mock()
        mock_existing_lead.email = "john@test.com"
        mock_existing_lead.status = LeadStatus.PENDING
        mock_existing_lead.resume_path = "path/resume.pdf"
        mock_crud.get_by_email.return_value = mock_existing_lead
        
        mock_updated_lead = LeadResponse(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            resume_path="path/resume.pdf",
            status=LeadStatus.REACHED_OUT,
            created_at=datetime.now()
        )
        mock_crud.update.return_value = mock_updated_lead
        
        with patch.object(LeadResponse, 'from_orm', return_value=mock_updated_lead):
            service = LeadService()
            result = service.update_lead_status(mock_db, "john@test.com", LeadStatus.REACHED_OUT)
        
        assert result.email == "john@test.com"
        assert result.status == LeadStatus.REACHED_OUT
        mock_crud.get_by_email.assert_called_once_with(mock_db, "john@test.com")
        mock_crud.update.assert_called_once()

    @patch('app.services.lead_service.lead_crud')
    def test_update_lead_status_lead_not_found(self, mock_crud, mock_db):
        """Test service handles lead not found"""
        mock_crud.get_by_email.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            self.service.update_lead_status(mock_db, "nonexistent@test.com", LeadStatus.REACHED_OUT)
        
        assert exc.value.status_code == 404
        assert "not found" in str(exc.value.detail)

    @patch('app.services.lead_service.lead_crud')
    def test_update_lead_status_update_fails(self, mock_crud, mock_db):
        """Test service handles update failure"""
        mock_existing_lead = Mock()
        mock_crud.get_by_email.return_value = mock_existing_lead
        
        mock_crud.update.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            self.service.update_lead_status(mock_db, "john@test.com", LeadStatus.REACHED_OUT)
        
        assert exc.value.status_code == 500
        assert "Failed to update" in str(exc.value.detail)

    @patch('app.services.lead_service.lead_crud')
    def test_update_lead_status_database_error(self, mock_crud, mock_db):
        """Test service handles database errors"""
        mock_existing_lead = Mock()
        mock_crud.get_by_email.return_value = mock_existing_lead
        
        mock_crud.update.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc:
            self.service.update_lead_status(mock_db, "john@test.com", LeadStatus.REACHED_OUT)
        
        assert exc.value.status_code == 500
