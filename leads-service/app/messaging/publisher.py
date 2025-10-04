from app.messaging.kafka_client import kafka_client
from app.core.config import settings
from app.schemas.events import LeadCreatedEvent, KafkaMessage
from app.schemas.lead import LeadResponse
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EventPublisher:
    """Service for publishing domain events"""
    
    @staticmethod
    async def publish_lead_created(lead_response: LeadResponse, metadata: Optional[dict] = None) -> bool:
        """Publish lead created event with proper DTOs"""
        try:
            event = LeadCreatedEvent.from_lead_response(lead_response)
            
            kafka_message = event.to_kafka_message(topic=settings.KAFKA_NEW_LEADS_TOPIC)
            
            success = await kafka_client.send_message(
                kafka_message.topic,
                kafka_message.value
            )
            
            if success:
                logger.info(f"Lead created event published: {event.event_id} for {lead_response.email}")
            else:
                logger.error(f"Failed to publish lead created event for {lead_response.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error publishing lead created event: {e}")
            return False
        
event_publisher = EventPublisher()