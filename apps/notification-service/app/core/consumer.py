import asyncio
import json
import uuid
import aio_pika
import structlog
from showbook_common.database import db_manager
from app.core.config import settings
from app.services.notification_service import NotificationService

logger = structlog.get_logger(__name__)

class EventConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
        self.running = False
        self.task = None

    async def start(self):
        self.running = True
        self.task = asyncio.create_task(self.consume_loop())
        logger.info("consumer_background_task_started")

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("consumer_stopped")

    async def consume_loop(self):
        while self.running:
            try:
                self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self.channel = await self.connection.channel()
                
                # Declare main exchange
                exchange = await self.channel.declare_exchange(
                    "showbook.events", 
                    aio_pika.ExchangeType.TOPIC, 
                    durable=True
                )
                
                # Declare queue
                self.queue = await self.channel.declare_queue(
                    "notification_service_queue", 
                    durable=True
                )
                
                # Bind events
                await self.queue.bind(exchange, routing_key="booking.*")
                await self.queue.bind(exchange, routing_key="payment.*")
                
                logger.info("rabbitmq_consumer_connected")
                
                async with self.queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process(requeue=True):
                            raw_body = json.loads(message.body.decode())
                            
                            # Normalize event envelope format
                            if isinstance(raw_body, dict) and "event_id" in raw_body:
                                event = raw_body
                            else:
                                event = {
                                    "event_id": message.message_id or str(uuid.uuid4()),
                                    "event_type": message.routing_key or "unknown",
                                    "payload": raw_body
                                }
                            
                            logger.info(
                                "event_received", 
                                event_type=event.get("event_type"), 
                                event_id=event.get("event_id")
                            )
                            
                            async with db_manager.get_db_context() as db:
                                await NotificationService.process_event(event, db)
                                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("consumer_loop_error", error=str(e))
                # Wait 5 seconds before reconnecting
                await asyncio.sleep(5)

consumer = EventConsumer()
