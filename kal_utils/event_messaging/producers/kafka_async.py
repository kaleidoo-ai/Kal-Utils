import asyncio
import time
from typing import Any
import json

from aiokafka import AIOKafkaProducer

from .base import KalSenseBaseProducer
from core.settings import settings
from core.logging import logger

class KalSenseAioKafkaProducer(KalSenseBaseProducer):
    __producer_cls = AIOKafkaProducer
    __consumer_conn = settings.KAFKA_BOOTSTRAP_SERVERS
    __default_stale_threshold = 300
    
    def __init__(self, topic: str, stale_threshold: int = None) -> None:
        producer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic=topic, producer_group=producer_group)
        self.__bootstrap_servers = self.__consumer_conn
        self.__producer = None
        self.__last_activity = 0
        self.__stale_threshold = stale_threshold if stale_threshold else self.__default_stale_threshold

    async def __aenter__(self):
        await self.__ensure_connection()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def __connect(self):
        self.__producer = self.__producer_cls(bootstrap_servers=self.__bootstrap_servers)
        await self.__producer.start()
        self.__last_activity = time.time()

    async def __ensure_connection(self):
        if not self.__producer:
            await self.__connect()

    async def __check_and_renew_connection(self):
        current_time = time.time()
        if current_time - self.__last_activity > self.__stale_threshold:
            await self.close()
            await self.__connect()

    async def produce(self, message: Any, key: bytes = None):
        if not isinstance(message, str):
            message = json.dumps(message)
        await self.__ensure_connection()
        await self.__check_and_renew_connection()
        await self.__producer.send_and_wait(self.topic, json.dumps(message).encode(), key=key)
        self.__last_activity = time.time()

    async def close(self):
        if self.__producer:
            await self.__producer.stop()
            self.__producer = None

    def __del__(self):
        if self.__producer:
            self._sync_close()

    def _sync_close(self):
        logger.info(f"Deleting producer")
        try:
            asyncio.get_event_loop_policy().get_event_loop().create_task(self.close)
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.close())
            finally:
                loop.close()