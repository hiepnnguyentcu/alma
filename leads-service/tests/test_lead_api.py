import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException
from app.schemas.lead import LeadListResponse
from app.models.lead import LeadStatus

class TestLeadAPI:
    
    @patch('app.api.v1.endpoints.leads.lead_service.create_lead')
    @patch('app.core.postgres.get_postgres_db')
    def test_create_lead_success(self, mock_get_db, mock_create_lead, client, sample_lead_response):
        """Test POST /leads works"""
        mock_get_db.return_value = Mock()
        mock_create_lead.return_value = sample_lead_response
        
        files = {"resume": ("resume.pdf", b"fake", "application/pdf")}
        data = {"first_name": "John", "last_name": "Doe", "email": "john@test.com"}
        
        response = client.post("/api/v1/leads", files=files, data=data)
        
        assert response.status_code == 201
        assert response.json()["first_name"] == "John"

    @patch('app.core.postgres.get_postgres_db')
    def test_create_lead_validation_error(self, mock_get_db, client):
        """Test POST /leads fails with invalid data"""
        mock_get_db.return_value = Mock()
        
        files = {"resume": ("resume.pdf", b"fake", "application/pdf")}
        data = {"first_name": "John"}
        
        response = client.post("/api/v1/leads", files=files, data=data)
        assert response.status_code == 422

    def test_get_leads_requires_auth(self, client):
        """Test GET /leads fails without auth"""
        response = client.get("/api/v1/leads")
        assert response.status_code in [401, 403]
        
    def test_get_leads_invalid_token(self, client):
        """Test GET /leads fails with invalid token"""
        response = client.get("/api/v1/leads", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401

    @patch('app.api.v1.endpoints.leads.lead_service.update_lead_status')
    @patch('app.core.postgres.get_postgres_db')
    def test_update_lead_status_success(self, mock_get_db, mock_update_status, client, sample_lead_response):
        """Test PATCH /leads/status works for attorney"""
        from app.authentication.jwt import require_attorney
        
        def mock_require_attorney():
            return {"username": "attorney1", "role": "ATTORNEY"}
        
        client.app.dependency_overrides[require_attorney] = mock_require_attorney
        
        try:
            mock_get_db.return_value = Mock()
            
            updated_lead = sample_lead_response.model_copy()
            updated_lead.status = LeadStatus.REACHED_OUT
            mock_update_status.return_value = updated_lead
            
            response = client.patch("/api/v1/leads/status", 
                headers={"Authorization": "Bearer attorney_token"},
                json={"email": "john@test.com", "status": "REACHED_OUT"}
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "REACHED_OUT"
            mock_update_status.assert_called_once()
        finally:
            client.app.dependency_overrides.clear()

    @patch('app.core.postgres.get_postgres_db')
    def test_update_lead_status_requires_attorney_role(self, mock_get_db, client):
        """Test PATCH /leads/status fails for non-attorney"""
        from app.authentication.jwt import require_attorney
        from fastapi import HTTPException
        
        def mock_require_attorney_fail():
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        client.app.dependency_overrides[require_attorney] = mock_require_attorney_fail
        
        try:
            mock_get_db.return_value = Mock()
            
            response = client.patch("/api/v1/leads/status",
                headers={"Authorization": "Bearer client_token"},
                json={"email": "john@test.com", "status": "REACHED_OUT"}
            )
            
            assert response.status_code == 403
        finally:
            client.app.dependency_overrides.clear()

    @patch('app.api.v1.endpoints.leads.lead_service.update_lead_status')
    @patch('app.core.postgres.get_postgres_db')
    def test_update_lead_status_lead_not_found(self, mock_get_db, mock_update_status, client):
        """Test PATCH /leads/status fails when lead doesn't exist"""
        from app.authentication.jwt import require_attorney
        
        def mock_require_attorney():
            return {"username": "attorney1", "role": "ATTORNEY"}
        
        client.app.dependency_overrides[require_attorney] = mock_require_attorney
        
        try:
            mock_get_db.return_value = Mock()
            mock_update_status.side_effect = HTTPException(status_code=404, detail="Lead not found")
            
            response = client.patch("/api/v1/leads/status",
                headers={"Authorization": "Bearer attorney_token"},
                json={"email": "nonexistent@test.com", "status": "REACHED_OUT"}
            )
            
            assert response.status_code == 404
        finally:
            client.app.dependency_overrides.clear()

    @patch('app.core.postgres.get_postgres_db')
    def test_update_lead_status_invalid_request_data(self, mock_get_db, client):
        """Test PATCH /leads/status fails with invalid data"""
        from app.authentication.jwt import require_attorney
        
        def mock_require_attorney():
            return {"username": "attorney1", "role": "ATTORNEY"}
        
        client.app.dependency_overrides[require_attorney] = mock_require_attorney
        
        try:
            mock_get_db.return_value = Mock()
            
            response = client.patch("/api/v1/leads/status",
                headers={"Authorization": "Bearer attorney_token"},
                json={"email": "invalid-email", "status": "INVALID_STATUS"}
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            client.app.dependency_overrides.clear()
    
    @patch('app.core.postgres.get_postgres_db')
    def test_update_lead_status_missing_fields(self, mock_get_db, client):
        """Test PATCH /leads/status fails with missing required fields"""
        from app.authentication.jwt import require_attorney
        
        def mock_require_attorney():
            return {"username": "attorney1", "role": "ATTORNEY"}
        
        client.app.dependency_overrides[require_attorney] = mock_require_attorney
        
        try:
            mock_get_db.return_value = Mock()
            
            response = client.patch("/api/v1/leads/status",
                headers={"Authorization": "Bearer attorney_token"},
                json={"email": "john@test.com"}  # Missing status
            )
            
            assert response.status_code == 422  # Validation error
        finally:
            client.app.dependency_overrides.clear()
