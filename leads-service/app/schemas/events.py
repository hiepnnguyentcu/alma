"""Event schemas for Kafka message publishing."""
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from app.schemas.lead import LeadResponse
from app.utils import make_json_safe


class KafkaMessage(BaseModel):
    """Wrapper for Kafka messages with metadata."""
    topic: str
    key: Optional[str] = None
    value: Dict[str, Any]
    headers: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LeadCreatedEvent(BaseModel):
    """Event data for when a lead is created."""
    event_type: str = "lead.created"
    event_id: str = Field(description="Unique identifier for this event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lead_id: UUID
    lead_data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_lead_response(
        cls, 
        lead_response: LeadResponse, 
        event_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "LeadCreatedEvent":
        """Create event from lead response."""
        return cls(
            event_id=event_id or str(uuid4()),
            lead_id=lead_response.id,
            lead_data=lead_response.model_dump(),
            metadata=metadata or {}
        )

    def to_kafka_message(self, topic: str = "lead-events") -> KafkaMessage:
        """Convert to Kafka message format with JSON-safe values."""
        # Convert all data to JSON-safe format
        json_safe_value = make_json_safe(self.model_dump())
        
        return KafkaMessage(
            topic=topic,
            key=str(self.lead_id),
            value=json_safe_value,
            headers={
                "event_type": self.event_type,
                "event_id": self.event_id,
                "content_type": "application/json"
            }
        )