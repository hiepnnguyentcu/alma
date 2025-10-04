from aiokafka import AIOKafkaProducer
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class KafkaClient:
    def __init__(self):
        self.producer = None
        self.started = False
    
    async def start(self):
        """Start Kafka producer"""
        if self.started:
            return
            
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            await self.producer.start()
            self.started = True
            logger.info("Kafka producer started")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self.started = False
    
    async def stop(self):
        """Stop Kafka producer"""
        if self.producer and self.started:
            await self.producer.stop()
            self.started = False
            logger.info("Kafka producer stopped")
    
    async def send_message(self, topic: str, message: dict):
        """Send message to Kafka topic"""
        if not self.started:
            await self.start()
        
        if not self.started:
            logger.error("Kafka producer not available")
            return False
        
        try:
            await self.producer.send_and_wait(topic, value=message)
            logger.info(f"Message sent to {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

kafka_client = KafkaClient()