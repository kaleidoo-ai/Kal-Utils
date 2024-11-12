import os
import json
import asyncio
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import time

from .base import KalSenseBaseConsumer
# When deployed into a larger API uncomment the line below
# from core.logging import logger
# When deployed into a larger API comment the line below
from loguru import logger

load_dotenv()


class KalSenseAioRabbitMQConsumer(KalSenseBaseConsumer):
    def __init__(self, topic: str, consumer_group: str, connection_string: str, stale_threshold: int = 300) -> None:
        super().__init__(topic, consumer_group)
        self.__connection_string = connection_string
        self.__connection = None
        self.__channel = None
        self.__queue = None
        self.__last_activity = 0
        self.__stale_threshold = stale_threshold  # 5 minutes by default

    async def __aenter__(self):
        await self.__ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def __connect(self):
        self.__connection = await aio_pika.connect_robust(self.__connection_string)
        self.__channel = await self.__connection.channel()
        exchange = await self.__channel.declare_exchange(self.topic, aio_pika.ExchangeType.TOPIC)
        self.__queue = await self.__channel.declare_queue(self.consumer_group, durable=True)
        await self.__queue.bind(exchange, routing_key="#")
        self.__last_activity = time.time()

    async def __ensure_connection(self):
        if not self.__connection or self.__connection.is_closed:
            await self.__connect()

    async def __check_and_renew_connection(self):
        current_time = time.time()
        if current_time - self.__last_activity > self.__stale_threshold:
            await self.close()
            await self.__connect()

    async def consume(self):
        await self.__ensure_connection()
        
        async with self.__queue.iterator() as queue_iter:
            async for message in queue_iter:
                self.__last_activity = time.time()
                yield message

    async def close(self):
        if self.__connection and not self.__connection.is_closed:
            await self.__connection.close()
        self.__connection = None
        self.__channel = None
        self.__queue = None

    def __del__(self):
        if self.__connection and not self.__connection.is_closed:
            asyncio.get_event_loop().run_until_complete(self.close())


# class KalSenseRabbitMQAsyncConsumer(KalSenseBaseConsumer):
#     __consumer_conn = os.getenv("RABBITMQ_CONN_STR")
    
#     def __init__(self, topic: str, consumer_group: str) -> None:
#         super().__init__()
#         self.__topic = topic
#         self.__consumer_group = consumer_group
#         self.__connection = None
#         self.__channel = None
#         self.__queue = None
        
#         # Establish connection on initialization
#         # loop = asyncio.get_event_loop()
#         # loop.run_until_complete(self.__connect())
#         asyncio.create_task(self.__connect())

#     async def __connect(self):
#         self.__connection = await aio_pika.connect_robust(self.__consumer_conn)
#         async with self.__connection:
#             self.__channel = await self.__connection.channel()
#             await self.__channel.set_qos(prefetch_count=10)
#             self.__queue = await self.__channel.declare_queue(self.__topic, durable=True, auto_delete=False, exclusive=False)

#     @property
#     def topic(self) -> str:
#         return self.__topic

#     @property
#     def consumer_group(self) -> str:
#         return self.__consumer_group

#     @property
#     def consumer(self):
#         raise AttributeError("Cannot access self.consumer attribute. To consume from topic, call obj.consume() instead")

#     async def consume(self):
#         async with self.__queue.iterator() as queue_iter:
#             async for message in queue_iter:
#                 try:
#                     async with message.process():
#                         decoded_message = json.loads(message.body.decode('utf-8'))
#                         yield decoded_message
#                 except Exception as e:
#                     logger.error(f"Error processing message from rabbitmq using async consumer:\n{e}")
#                     continue

#     def __del__(self):
#         try:
#             if self.__connection and not self.__connection.is_closed:
#                 # loop = asyncio.get_event_loop()
#                 # loop.run_until_complete(self.__connection.close())
#                 self.__connection.close()
#             delattr(self, "__topic")
#             delattr(self, "__consumer_group")
            
#             return True
#         except Exception as e:
#             logger.error(f"An Error Occurred in RabbitMQAsyncConsumer: {e}")
#             return False