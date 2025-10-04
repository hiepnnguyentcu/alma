import pytest
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.lead import LeadStatus
from app.schemas.lead import LeadResponse, LeadListResponse
import uuid
from datetime import datetime

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_file():
    file = Mock()
    file.filename = "resume.pdf"
    file.read = AsyncMock(return_value=b"fake_pdf")
    file.seek = AsyncMock()
    return file

@pytest.fixture
def sample_lead_response():
    return LeadResponse(
        id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        email="john@test.com",
        resume_path="path/resume.pdf",
        status=LeadStatus.PENDING,
        created_at=datetime.now()
    )
