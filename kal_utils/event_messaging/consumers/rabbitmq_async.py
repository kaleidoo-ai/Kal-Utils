import os
import json
import asyncio
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
import time
from typing import Any, AsyncIterator

from .base import KalSenseBaseConsumer
from core.settings import settings
# When deployed into a larger API uncomment the line below
from core.logging import logger
# When deployed into a larger API comment the line below
#from loguru import logger
from core.schema import Message


class KalSenseAioRabbitMQConsumer(KalSenseBaseConsumer):
    """
    An asynchronous RabbitMQ consumer for the KalSense system.

    This class provides functionality to consume messages from a RabbitMQ queue
    using the aio_pika library. It handles connection management, including
    automatic reconnection for stale connections.

    Attributes:
        topic (str): The topic to consume messages from.
        consumer_group (str): The consumer group name.

    Args:
        topic (str): The topic to consume messages from.
        consumer_group (str): The consumer group name.
        connection_string (str): The RabbitMQ connection string.
        stale_threshold (int, optional): The time in seconds after which a connection
            is considered stale. Defaults to 300 seconds (5 minutes).
    """
    
    def __init__(self, topic: str, stale_threshold: int = 300) -> None:
        consumer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic, consumer_group)
        self.__connection_string = settings.RABBITMQ_URL
        self.__connection = None
        self.__channel = None
        self.__queue = None
        self.__last_activity = 0
        self.__stale_threshold = stale_threshold

    async def __aenter__(self):
        """Async context manager entry point."""
        await self.__ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.close()

    async def __connect(self):
        """Establish a connection to RabbitMQ."""
        # consumer_group is the queue and the topic is the exchange
        # and it should be: consumer_group is exchange and topic is the queue & routing key
        # (since it is direct queue type one routing key fits to a single queue (topic))
        self.__connection = await aio_pika.connect_robust(self.__connection_string)
        self.__channel = await self.__connection.channel()
        exchange = await self.__channel.declare_exchange(self.consumer_group, aio_pika.ExchangeType.DIRECT)
        self.__queue = await self.__channel.declare_queue(self.topic, durable=True)
        await self.__queue.bind(exchange, routing_key=self.topic)
        self.__last_activity = time.time()

    async def __ensure_connection(self):
        """Ensure that a connection exists, creating one if necessary."""
        if not self.__connection or self.__connection.is_closed:
            await self.__connect()

    async def __check_and_renew_connection(self):
        """Check if the connection is stale and renew it if necessary."""
        current_time = time.time()
        if current_time - self.__last_activity > self.__stale_threshold:
            await self.close()
            await self.__connect()

    async def consume(self) -> AsyncIterator[Any]:
        """
        Consume messages from the queue.

        Yields:
            Any: The consumed message.
        """
        await self.__ensure_connection()
        
        async with self.__queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    async with message.process(requeue=False):
                        logger.debug(f"Received message: {message.body}")
                        self.__last_activity = time.time()
                        yield Message.model_validate_json(message.body)
                        logger.debug(f"Successfully processed and acked message: {message.body}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    message.nack(requeue=True)
                    continue

    async def close(self):
        """Close the connection to RabbitMQ."""
        if self.__connection and not self.__connection.is_closed:
            await self.__connection.close()
        self.__connection = None
        self.__channel = None
        self.__queue = None

    def __del__(self):
        """Destructor to ensure resources are cleaned up."""
        if self.__connection and not self.__connection.is_closed:
            self._sync_close()

    def _sync_close(self):
        """Synchronously close the asynchronous connection."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.close())
        finally:
            loop.close()