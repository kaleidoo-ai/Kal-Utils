import asyncio
import aio_pika
import time
from typing import Any, Optional
import json
from weakref import WeakKeyDictionary

from kal_utils.event_messaging.producers.base import KalSenseBaseProducer
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.logging import logger
from kal_utils.event_messaging.core.utils import RabbitMQConnectionManager

class KalSenseAioRabbitMQProducer(KalSenseBaseProducer):
    """
    Enhanced asynchronous RabbitMQ producer with connection pooling and retry mechanism.
    
    Features:
    - Connection pooling via RabbitMQConnectionManager
    - Automatic reconnection with exponential backoff
    - Channel and exchange management
    - Message delivery confirmation
    - Error handling and logging
    - Resource cleanup
    """
    
    # Class-level connection manager to be shared across instances
    _connection_managers = WeakKeyDictionary()
    _connection_manager_lock = asyncio.Lock()
    
    def __init__(self, topic: str, stale_threshold: int = 300) -> None:
        producer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic, producer_group)
        
        self.__connection_string = settings.RABBITMQ_URL
        self.__channel: Optional[aio_pika.Channel] = None
        self.__exchange: Optional[aio_pika.Exchange] = None
        self.__last_activity = 0
        self.__stale_threshold = stale_threshold
        self.__connection_manager = None

    @classmethod
    async def get_connection_manager(cls, connection_string: str) -> RabbitMQConnectionManager:
        """Get or create a connection manager for the given connection string."""
        async with cls._connection_manager_lock:
            if connection_string not in cls._connection_managers:
                manager = RabbitMQConnectionManager(connection_string)
                await manager.start()
                cls._connection_managers[connection_string] = manager
            return cls._connection_managers[connection_string]

    async def __aenter__(self):
        """Async context manager entry point."""
        self.__connection_manager = await self.get_connection_manager(self.__connection_string)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point."""
        await self.close()

    async def _setup_channel(self, connection: aio_pika.Connection) -> None:
        """Set up channel and exchange with the given connection."""
        self.__channel = await connection.channel()
        await self.__channel.set_qos(prefetch_count=1)
        
        # Declare exchange
        self.__exchange = await self.__channel.declare_exchange(
            self.producer_group,
            aio_pika.ExchangeType.DIRECT
        )
        
        # Declare queue and bind it to the exchange
        queue = await self.__channel.declare_queue(
            self.topic,
            durable=True
        )
        await queue.bind(self.__exchange, routing_key=self.topic)
        
        self.__last_activity = time.time()

    async def produce(self, message: Any, max_retries:int = 5, initial_delay:float=1.0) -> None:
        """
        Produce a message to the exchange with automatic reconnection and retry logic.
        
        Args:
            message: The message to publish. Will be converted to JSON if not already a string.
            max_retries: Amount of retries for sending the message
        
        Raises:
            aio_pika.exceptions.PublishError: If message cannot be published after retries
            ValueError: If message cannot be serialized to JSON
        """
        if not isinstance(message, str):
            try:
                message = json.dumps(message)
            except Exception as e:
                logger.error(f"Failed to serialize message to JSON: {e}")
                raise ValueError(f"Message serialization failed: {e}")

        for attempt in range(max_retries):
            try:
                async with self.__connection_manager.acquire() as connection:
                    if not self.__channel or self.__channel.is_closed:
                        await self._setup_channel(connection)

                    # Create message with persistence and timestamp
                    message_body = message.encode()
                    aio_pika_message = aio_pika.Message(
                        body=message_body,
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        timestamp=time.time(),
                        content_type='application/json'
                    )

                    # Publish with confirmation
                    await self.__exchange.publish(
                        aio_pika_message,
                        routing_key=self.topic,
                        timeout=30  # 30 seconds timeout for publish confirmation
                    )
                    
                    self.__last_activity = time.time()
                    logger.debug(f"Successfully published message to {self.topic}")
                    return

            except aio_pika.exceptions.ConnectionClosed:
                logger.warning("Connection closed during publish attempt")
                if attempt < max_retries:
                    await asyncio.sleep(initial_delay)
                    initial_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise aio_pika.exceptions.ConnectionClosed(f"Failed to publish message after {max_retries} attempts: {e}")

            except Exception as e:
                logger.error(f"Error publishing message (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(initial_delay)
                    initial_delay *= 2  # Exponential backoff
                else:
                    raise aio_pika.exceptions.PublishError(f"Failed to publish message after {max_retries} attempts: {e}")

    async def close(self) -> None:
        """Close channel and cleanup resources."""
        if self.__channel and not self.__channel.is_closed:
            await self.__channel.close()
        self.__channel = None
        self.__exchange = None

    def __del__(self):
        """Ensure resources are cleaned up."""
        if self.__channel and not self.__channel.is_closed:
            asyncio.create_task(self.close())



# import asyncio
# import aio_pika
# import time
# from typing import Any
# import json

# from kal_utils.event_messaging.producers.base import KalSenseBaseProducer
# from kal_utils.event_messaging.core.settings import settings
# # When deployed into a larger API uncomment the line below
# from kal_utils.event_messaging.core.logging import logger
# # When deployed into a larger API comment the line below
# # from loguru import logger

# class KalSenseAioRabbitMQProducer(KalSenseBaseProducer):
#     """
#     An asynchronous RabbitMQ producer for the KalSense system.

#     This class provides functionality to produce messages to a RabbitMQ exchange
#     using the aio_pika library. It handles connection management, including
#     automatic reconnection for stale connections.

#     Attributes:
#         topic (str): The topic to produce messages to.
#         producer_group (str): The producer group name.

#     Args:
#         topic (str): The topic to produce messages to.
#         producer_group (str): The producer group name.
#         connection_string (str): The RabbitMQ connection string.
#         stale_threshold (int, optional): The time in seconds after which a connection
#             is considered stale. Defaults to 300 seconds (5 minutes).
#     """

#     def __init__(self, topic: str, stale_threshold: int = 300) -> None:
#         # producer_group is the queue and the topic is the exchange
#         # and it should be: producer_group is exchange and topic is the queue & routing key 
#         producer_group = settings.SERVICES[settings.SERVICE_NAME]
#         super().__init__(topic, producer_group)
#         self.__connection_string = settings.RABBITMQ_URL
#         self.__connection = None
#         self.__channel = None
#         self.__exchange = None
#         self.__last_activity = 0
#         self.__stale_threshold = stale_threshold

#     async def __aenter__(self):
#         """Async context manager entry point."""
#         await self.__ensure_connection()
#         return self

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         """Async context manager exit point."""
#         await self.close()

#     async def __connect(self):
#         """Establish a connection to RabbitMQ."""
#         self.__connection = await aio_pika.connect_robust(self.__connection_string)
#         self.__channel = await self.__connection.channel()
#         self.__exchange = await self.__channel.declare_exchange(self.producer_group, aio_pika.ExchangeType.DIRECT)
#         queue = await self.__channel.declare_queue(self.topic, durable=True)
#         await queue.bind(self.__exchange, routing_key=self.topic)
#         self.__last_activity = time.time()

#     async def __ensure_connection(self):
#         """Ensure that a connection exists, creating one if necessary."""
#         if not self.__connection or self.__connection.is_closed:
#             await self.__connect()

#     async def __check_and_renew_connection(self):
#         """Check if the connection is stale and renew it if necessary."""
#         current_time = time.time()
#         if current_time - self.__last_activity > self.__stale_threshold:
#             await self.close()
#             await self.__connect()

#     async def produce(self, message: Any):
#         """
#         Produce a message to the exchange.

#         Args:
#             message (Any): The message to produce.
#             routing_key (str, optional): The routing key for the message. Defaults to "#".
#         """
#         await self.__ensure_connection()
#         await self.__check_and_renew_connection()
#         if not isinstance(message, str):
#             message = json.dumps(message)
#         await self.__exchange.publish(
#             aio_pika.Message(body=message.encode()),
#             routing_key=self.topic
#         )
#         self.__last_activity = time.time()

#     async def close(self):
#         """Close the connection to RabbitMQ."""
#         if self.__connection and not self.__connection.is_closed:
#             await self.__connection.close()
#         self.__connection = None
#         self.__channel = None
#         self.__exchange = None

#     def __del__(self):
#         """Destructor to ensure resources are cleaned up."""
#         if self.__connection and not self.__connection.is_closed:
#             self._sync_close()

#     def _sync_close(self):
#         """Synchronously close the asynchronous connection."""
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             loop.run_until_complete(self.close())
#         finally:
#             loop.close()


# # ------------------------------------------- UNIT TEST -------------------------------------------

# import unittest
# from unittest.mock import patch, MagicMock
# import asyncio

# class TestKalSenseRabbitMQProducer(unittest.TestCase):
#     """
#     Unit tests for the KalSenseRabbitMQProducer class.
    
#     These tests cover the initialization, connection, message production,
#     and cleanup processes of the RabbitMQ producer.
#     """

#     def setUp(self):
#         """Set up the test environment before each test."""
#         self.topic = "test_topic"
#         self.test_message = {"key": "value"}

#     @patch('your_module.aio_pika.connect_robust')
#     def test_initialization(self, mock_connect):
#         """Test the initialization of KalSenseRabbitMQProducer."""
#         producer = KalSenseAioRabbitMQProducer(self.topic)
#         self.assertEqual(producer.topic, self.topic)
#         mock_connect.assert_called_once()

#     @patch('your_module.aio_pika.connect_robust')
#     @patch('your_module.aio_pika.Message')
#     async def test_produce_message(self, mock_message, mock_connect):
#         """Test the production of a message."""
#         mock_connection = MagicMock()
#         mock_channel = MagicMock()
#         mock_exchange = MagicMock()
#         mock_connect.return_value = mock_connection
#         mock_connection.channel.return_value = mock_channel
#         mock_channel.default_exchange = mock_exchange

#         producer = KalSenseAioRabbitMQProducer(self.topic)
#         await producer.produce(self.test_message)

#         mock_exchange.publish.assert_called_once()
#         mock_message.assert_called_once_with(body=b'{"key": "value"}')

#     @patch('your_module.aio_pika.connect_robust')
#     async def test_connection_error(self, mock_connect):
#         """Test error handling during connection."""
#         mock_connect.side_effect = Exception("Connection failed")

#         with self.assertRaises(Exception):
#             KalSenseAioRabbitMQProducer(self.topic)

#     @patch('your_module.aio_pika.connect_robust')
#     @patch('your_module.aio_pika.Message')
#     async def test_produce_error(self, mock_message, mock_connect):
#         """Test error handling during message production."""
#         mock_connection = MagicMock()
#         mock_channel = MagicMock()
#         mock_exchange = MagicMock()
#         mock_connect.return_value = mock_connection
#         mock_connection.channel.return_value = mock_channel
#         mock_channel.default_exchange = mock_exchange
#         mock_exchange.publish.side_effect = Exception("Publish failed")

#         producer = KalSenseAioRabbitMQProducer(self.topic)
        
#         with patch('builtins.print') as mock_print:
#             await producer.produce(self.test_message)
#             mock_print.assert_called_with("Error producing message: Publish failed")

#     @patch('your_module.aio_pika.connect_robust')
#     def test_cleanup(self, mock_connect):
#         """Test the cleanup process when the producer is deleted."""
#         mock_connection = MagicMock()
#         mock_connect.return_value = mock_connection

#         producer = KalSenseAioRabbitMQProducer(self.topic)
#         del producer

#         mock_connection.close.assert_called_once()

# if __name__ == '__main__':
#     unittest.main()