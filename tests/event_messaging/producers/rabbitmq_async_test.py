
import os
import json
import asyncio
import aio_pika
from aio_pika import Message
from abc import ABC, abstractmethod
from dotenv import load_dotenv
import time
from typing import Any

from .base import KalSenseBaseProducer
# When deployed into a larger API uncomment the line below
# from core.logging import logger
# When deployed into a larger API comment the line below
from loguru import logger

load_dotenv()


class KalSenseAioRabbitMQProducer(KalSenseBaseProducer):

    def __init__(self, topic: str, producer_group: str, connection_string: str, stale_threshold: int = 300) -> None:
        super().__init__(topic, producer_group)
        self.__connection_string = connection_string
        self.__connection = None
        self.__channel = None
        self.__exchange = None
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
        self.__exchange = await self.__channel.declare_exchange(self.topic, aio_pika.ExchangeType.TOPIC)
        self.__last_activity = time.time()

    async def __ensure_connection(self):
        if not self.__connection or self.__connection.is_closed:
            await self.__connect()

    async def __check_and_renew_connection(self):
        current_time = time.time()
        if current_time - self.__last_activity > self.__stale_threshold:
            await self.close()
            await self.__connect()

    async def produce(self, message: Any, routing_key: str = ""):
        await self.__ensure_connection()
        
        aio_pika_message = Message(body=str(message).encode())
        await self.__exchange.publish(aio_pika_message, routing_key=routing_key)
        self.__last_activity = time.time()

    async def close(self):
        if self.__connection and not self.__connection.is_closed:
            await self.__connection.close()
        self.__connection = None
        self.__channel = None
        self.__exchange = None

    def __del__(self):
        if self.__connection and not self.__connection.is_closed:
            asyncio.get_event_loop().run_until_complete(self.close())


# class KalSenseRabbitMQAsyncProducer(KalSenseBaseProducer):
#     """
#     RabbitMQ implementation of KalSenseBaseProducer.
    
#     This class provides functionality to produce messages to a RabbitMQ queue.
#     """
#     __producer_conn = os.getenv("RABBITMQ_CONN_STR")
    
#     def __init__(self, topic: str, producer_group:str) -> None:
#         """
#         Initialize the RabbitMQ producer.
        
#         Args:
#             topic (str): The topic/queue to produce messages to.
#         """
#         super().__init__()
#         self.__topic = topic
#         self.__producer_group = producer_group
#         self.__connection = None
#         self.__channel = None
        
#         # Establish connection on initialization
#         # loop = asyncio.get_event_loop()
#         # loop.run_until_complete(self.__connect)
#         asyncio.create_task(self.__connect())

#     async def __connect(self) -> None:
#         """
#         Establish a connection to RabbitMQ and create a channel.
#         """
#         logger.info("Getting AIO_RabbitMQ connection")
#         self.__connection = await aio_pika.connect_robust(self.__producer_conn)
#         logger.info("got the connection, RUSH B")
#         self.__channel = await self.__connection.channel()
#         logger.info("Connected to RabbitMQ")

#     @property
#     def topic(self) -> str:
#         """
#         Get the topic/queue name.
        
#         Returns:
#             str: The topic/queue name.
#         """
#         return self.__topic

#     async def produce(self, message):
#         """
#         Produce a message to the RabbitMQ queue.
        
#         Args:
#             message: The message to be produced.
#         """
#         try:
#             await self.__channel.default_exchange.publish(
#                 aio_pika.Message(body=json.dumps(message).encode()),
#                 routing_key=self.__topic
#             )
#         except Exception as e:
#             logger.error(f"Error producing message: {e}")

#     def __del__(self):
#         """
#         Cleanup method to close the RabbitMQ connection when the object is deleted.
#         """
#         try:
#             if self.__connection and not self.__connection.is_closed:
#                 # loop = asyncio.get_event_loop()
#                 # loop.run_until_complete(self.__connection.close())
#                 self.__connection.close()
#             delattr(self, "__topic")
#             return True
#         except Exception as e:
#             logger.warning(f"An Error Occurred: {e}")
#             return False


# ------------------------------------------- UNIT TEST -------------------------------------------

import unittest
from unittest.mock import patch, MagicMock
import asyncio

class TestKalSenseRabbitMQProducer(unittest.TestCase):
    """
    Unit tests for the KalSenseRabbitMQProducer class.
    
    These tests cover the initialization, connection, message production,
    and cleanup processes of the RabbitMQ producer.
    """

    def setUp(self):
        """Set up the test environment before each test."""
        self.topic = "test_topic"
        self.test_message = {"key": "value"}

    @patch('your_module.aio_pika.connect_robust')
    def test_initialization(self, mock_connect):
        """Test the initialization of KalSenseRabbitMQProducer."""
        producer = KalSenseRabbitMQProducer(self.topic)
        self.assertEqual(producer.topic, self.topic)
        mock_connect.assert_called_once()

    @patch('your_module.aio_pika.connect_robust')
    @patch('your_module.aio_pika.Message')
    async def test_produce_message(self, mock_message, mock_connect):
        """Test the production of a message."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_exchange = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.default_exchange = mock_exchange

        producer = KalSenseRabbitMQProducer(self.topic)
        await producer.produce(self.test_message)

        mock_exchange.publish.assert_called_once()
        mock_message.assert_called_once_with(body=b'{"key": "value"}')

    @patch('your_module.aio_pika.connect_robust')
    async def test_connection_error(self, mock_connect):
        """Test error handling during connection."""
        mock_connect.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception):
            KalSenseRabbitMQProducer(self.topic)

    @patch('your_module.aio_pika.connect_robust')
    @patch('your_module.aio_pika.Message')
    async def test_produce_error(self, mock_message, mock_connect):
        """Test error handling during message production."""
        mock_connection = MagicMock()
        mock_channel = MagicMock()
        mock_exchange = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.default_exchange = mock_exchange
        mock_exchange.publish.side_effect = Exception("Publish failed")

        producer = KalSenseRabbitMQProducer(self.topic)
        
        with patch('builtins.print') as mock_print:
            await producer.produce(self.test_message)
            mock_print.assert_called_with("Error producing message: Publish failed")

    @patch('your_module.aio_pika.connect_robust')
    def test_cleanup(self, mock_connect):
        """Test the cleanup process when the producer is deleted."""
        mock_connection = MagicMock()
        mock_connect.return_value = mock_connection

        producer = KalSenseRabbitMQProducer(self.topic)
        del producer

        mock_connection.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()