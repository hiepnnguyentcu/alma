from aiokafka import AIOKafkaConsumer
import asyncio
import json
import logging
from app.core.config import settings
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

class KafkaConsumerService:
    def __init__(self):
        self.consumer = None
        self.started = False
        self._consuming_task = None
    
    async def start(self):
        """Start Kafka consumer"""
        if self.started:
            return
            
        try:
            self.consumer = AIOKafkaConsumer(
                settings.KAFKA_NEW_LEADS_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_CONSUMER_GROUP,
                auto_offset_reset='latest',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            
            await self.consumer.start()
            self.started = True
            
            self._consuming_task = asyncio.create_task(self._consume_messages())
            
            logger.info(f"Kafka consumer started for topic: {settings.KAFKA_NEW_LEADS_TOPIC}")
            
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self.started = False
    
    async def _consume_messages(self):
        """Background task to consume and process messages"""
        try:
            logger.info("📨 Starting to consume messages...")
            async for message in self.consumer:
                try:
                    # Log received message
                    logger.info(f"Received: {message.topic} - Offset: {message.offset}")
                    
                    # Send emails
                    if message.value.get("event_type") == "lead.created":
                        lead_data = message.value.get("lead_data", {})
                        await email_service.send_lead_email(lead_data)
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Kafka consumer error: {e}")

    async def stop(self):
        """Stop Kafka consumer"""
        if self._consuming_task:
            self._consuming_task.cancel()
            
        if self.consumer and self.started:
            await self.consumer.stop()
            self.started = False
            logger.info("Kafka consumer stopped")

kafka_consumer = KafkaConsumerService()