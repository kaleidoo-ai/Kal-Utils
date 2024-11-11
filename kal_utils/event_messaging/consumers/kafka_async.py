# Built-in imports
import os
import json
import asyncio
from typing import AsyncGenerator

# Third party imports
from aiokafka import AIOKafkaConsumer
# uncomment in standalone
# from loguru import logger

# KalSense imports
from .base import KalSenseBaseConsumer
from core.settings import settings
from core.logging import logger
from core.schema import Message




class KalSenseAioKafkaConsumer(KalSenseBaseConsumer):
    __consumer_cls = AIOKafkaConsumer
    __consumer_conn = settings.KAFKA_BOOTSTRAP_SERVERS
    REFRESH_THRESHOLD = 300  # 5 minutes

    def __init__(self, topic: str) -> None:
        consumer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic=topic, consumer_group=consumer_group)
        self.__consumer = None

    async def __aenter__(self):
        await self._create_consumer()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_consumer()

    async def _create_consumer(self):
        self.__consumer = KalSenseAioKafkaConsumer.__consumer_cls(
            self.topic,
            bootstrap_servers=[KalSenseAioKafkaConsumer.__consumer_conn],
            group_id=self.consumer_group,
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        await self.__consumer.start()
        self.__last_activity = asyncio.get_event_loop().time()

    async def _close_consumer(self):
        if self.__consumer:
            await self.__consumer.stop()

    async def _refresh_connection_if_needed(self):
        current_time = asyncio.get_event_loop().time()
        if current_time - self.__last_activity > self.REFRESH_THRESHOLD:
            await self._close_consumer()
            await self._create_consumer()

    async def consume(self) -> AsyncGenerator:
        if not self.__consumer:
            await self._create_consumer()

        try:
            async for message in self.__consumer:
                await self._refresh_connection_if_needed()
                self.__last_activity = asyncio.get_event_loop().time()
                yield Message.model_validate_json(message.value)
        except Exception as e:
            logger.error(f"Error consuming message: {e}")
    
    def __del__(self):
        """Closes the consumer.
        NOTE: Synchronous"""
        logger.info(f"Deleteing consumer")
        if self.__consumer:
            try:
                asyncio.get_event_loop().create_task(self._close_consumer())
                logger.info(f"Consumer closed")
            except Exception as e:
                logger.debug(f"No event loop running: {e}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._close_consumer())
                loop.close()
                logger.info(f"Consumer closed")