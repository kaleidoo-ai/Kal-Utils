import asyncio
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from typing import AsyncIterator, Optional
from contextlib import AsyncExitStack
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from circuitbreaker import circuit

from kal_utils.event_messaging.consumers.base import KalSenseBaseConsumer
from kal_utils.event_messaging.core.logging import logger
from kal_utils.event_messaging.core import settings
from kal_utils.event_messaging.core.schema import Message
from kal_utils.event_messaging.core.utils import RabbitMQConnectionManager, ConnectionConfig

class KalSenseAioRabbitMQConsumer(KalSenseBaseConsumer):
    def __init__(self, topic: str):
        super().__init__(topic, settings.core.service_name)
        
        self._connection_manager = RabbitMQConnectionManager(
            settings.rabbitmq.url,
            config=ConnectionConfig(
                pool_size=settings.rabbitmq.pool_size,
                connection_timeout=settings.rabbitmq.connection_timeout,
                idle_timeout=settings.rabbitmq.idle_timeout
            )
        )
        self._channel: Optional[aio_pika.Channel] = None
        self._queue: Optional[aio_pika.Queue] = None
        self._dlx_exchange: Optional[aio_pika.Exchange] = None

    async def __aenter__(self):
        await self._connection_manager.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @circuit(failure_threshold=3, recovery_timeout=60)
    async def _setup_channel(self, connection: aio_pika.Connection) -> None:
        self._channel = await connection.channel()
        await self._channel.set_qos(prefetch_count=100)
        
        exchange = await self._channel.declare_exchange(
            self.consumer_group,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        self._dlx_exchange = await self._channel.declare_exchange(
            f"{self.consumer_group}_dlx",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        self._queue = await self._channel.declare_queue(
            self.topic,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self._dlx_exchange.name,
                "x-max-priority": 10
            }
        )
        await self._queue.bind(exchange, routing_key=self.topic)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        retry=retry_if_exception_type(aio_pika.exceptions.AMQPError)
    )
    async def consume(self) -> AsyncIterator[Message]:
        async with AsyncExitStack() as stack:
            connection = await stack.enter_async_context(
                self._connection_manager.acquire()
            )
            
            if not self._channel or self._channel.is_closed:
                await self._setup_channel(connection)
            
            async with self._queue.iterator() as queue_iter:
                async for message in queue_iter:
                    msg_id = message.message_id or "unknown"
                    try:
                        parsed = Message.model_validate_json(message.body)
                        yield parsed
                        await message.ack()
                    except (json.JSONDecodeError, ValidationError) as e:
                        await message.reject(requeue=False)
                        logger.error(f"Invalid message {msg_id}: {str(e)}")
                    except Exception as e:
                        await message.nack(requeue=not message.redelivered)
                        if message.redelivered:
                            await self._move_to_dlx(message)

    async def _move_to_dlx(self, message: AbstractIncomingMessage) -> None:
        await self._dlx_exchange.publish(
            aio_pika.Message(
                body=message.body,
                headers=message.headers,
                message_id=message.message_id
            ),
            routing_key=self.topic
        )
        await message.ack()

    async def close(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        await self._connection_manager.stop()

    def __del__(self):
        if self._channel and not self._channel.is_closed:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except Exception as e:
                logger.warning(f"Consumer cleanup error: {str(e)}")


# import os
# import json
# import asyncio
# import aio_pika
# from aio_pika.abc import AbstractIncomingMessage
# import time
# from typing import Any, AsyncIterator, Optional
# from weakref import WeakKeyDictionary

# from kal_utils.event_messaging.consumers.base import KalSenseBaseConsumer
# from kal_utils.event_messaging.core.settings import settings
# from kal_utils.event_messaging.core.logging import logger
# from kal_utils.event_messaging.core.schema import Message
# from kal_utils.event_messaging.core.utils import RabbitMQConnectionManager, ConnectionConfig

# class KalSenseAioRabbitMQConsumer(KalSenseBaseConsumer):
#     """
#     Enhanced asynchronous RabbitMQ consumer with connection pooling and retry mechanism.
    
#     Features:
#     - Connection pooling via RabbitMQConnectionManager
#     - Automatic reconnection with exponential backoff
#     - Channel and queue management
#     - Error handling and logging
#     - Resource cleanup
#     """
    
#     # Class-level connection manager to be shared across instances
#     _connection_managers = WeakKeyDictionary()
#     _connection_manager_lock = asyncio.Lock()
    
#     def __init__(self, topic: str, stale_threshold: int = 300) -> None:
#         consumer_group = settings.SERVICES[settings.SERVICE_NAME]
#         super().__init__(topic, consumer_group)
        
#         self.__connection_string = settings.RABBITMQ_URL
#         self.__channel: Optional[aio_pika.Channel] = None
#         self.__queue: Optional[aio_pika.Queue] = None
#         # self.__last_activity = 0
#         # self.__stale_threshold = stale_threshold
#         self.__connection_manager = None
        
#     @classmethod
#     async def get_connection_manager(cls, connection_string: str) -> RabbitMQConnectionManager:
#         """Get or create a connection manager for the given connection string."""
#         async with cls._connection_manager_lock:
#             if connection_string not in cls._connection_managers:
#                 manager = RabbitMQConnectionManager(connection_string)
#                 await manager.start()
#                 cls._connection_managers[connection_string] = manager
#             return cls._connection_managers[connection_string]

#     async def __aenter__(self):
#         """Async context manager entry point."""
#         self.__connection_manager = await self.get_connection_manager(self.__connection_string)
#         return self

#     async def __aexit__(self, exc_type, exc_val, exc_tb):
#         """Async context manager exit point."""
#         await self.close()

#     async def _setup_channel(self, connection: aio_pika.Connection) -> None:
#         """Set up channel and queue with the given connection."""
#         self.__channel = await connection.channel()
        
#         # Declare exchange
#         exchange = await self.__channel.declare_exchange(
#             self.consumer_group,
#             aio_pika.ExchangeType.DIRECT
#         )
        
#         # Declare and bind queue
#         self.__queue = await self.__channel.declare_queue(
#             self.topic,
#             durable=True
#         )
#         await self.__queue.bind(exchange, routing_key=self.topic)
        
#         # self.__last_activity = time.time()

#     async def consume(self) -> AsyncIterator[Any]:
#         """
#         Consume messages from the queue with automatic reconnection.
        
#         Yields:
#             Any: Validated message objects
#         """
#         while True:
#             try:
#                 async with self.__connection_manager.acquire() as connection:
#                     if not self.__channel or self.__channel.is_closed:
#                         await self._setup_channel(connection)
                    
#                     async with self.__queue.iterator() as queue_iter:
#                         async for message in queue_iter:
#                             try:
#                                 async with message.process(requeue=False):
#                                     logger.debug(f"Received message: {message.body}")
#                                     # self.__last_activity = time.time()
#                                     yield Message.model_validate_json(message.body)
#                                     logger.debug(f"Successfully processed message: {message.body}")
#                             except Exception as e:
#                                 logger.error(f"Error processing message: {e}")
#                                 # Only requeue if it's not a validation error
#                                 if not isinstance(e, (json.JSONDecodeError, ValueError)):
#                                     message.nack(requeue=True)
#                                 continue
                            
#             except aio_pika.exceptions.ConnectionClosed:
#                 logger.warning("Connection closed, attempting to reconnect...")
#                 await asyncio.sleep(0.5)  # Wait before reconnection
#                 continue
                
#             except Exception as e:
#                 logger.error(f"Unexpected error in consume loop: {e}")
#                 # await asyncio.sleep(0)  # Uncomment If a delay between errors is desired
#                 continue

#     async def close(self) -> None:
#         """Close channel and cleanup resources."""
#         if self.__channel and not self.__channel.is_closed:
#             await self.__channel.close()
#         self.__channel = None
#         self.__queue = None

#     def __del__(self):
#         """Ensure resources are cleaned up."""
#         if self.__channel and not self.__channel.is_closed:
#             asyncio.create_task(self.close())




# from datetime import datetime
# import os
# import json
# import asyncio
# import uuid

# from pydantic import ValidationError
# import aio_pika
# from aio_pika.abc import AbstractIncomingMessage
# import time
# from typing import Any, AsyncIterator

# from kal_utils.event_messaging.consumers.base import KalSenseBaseConsumer
# from kal_utils.event_messaging.core.settings import settings
# # When deployed into a larger API uncomment the line below
# from kal_utils.event_messaging.core.logging import logger
# # When deployed into a larger API comment the line below
# #from loguru import logger
# from kal_utils.event_messaging.core.schema import Message
# from kal_utils.event_messaging.retrievers.consumer.async_retriever import AsyncConsumerRetriever
# from kal_utils.event_messaging.retrievers.producer.async_retriever import AsyncProducerRetriever
# from kal_utils.event_messaging.core.schema import Message, Metadata



# class KalSenseAioRabbitMQConsumer(KalSenseBaseConsumer):
#     """
#     An asynchronous RabbitMQ consumer for the KalSense system.

#     This class provides functionality to consume messages from a RabbitMQ queue
#     using the aio_pika library. It handles connection management, including
#     automatic reconnection for stale connections.

#     Attributes:
#         topic (str): The topic to consume messages from.
#         consumer_group (str): The consumer group name.

#     Args:
#         topic (str): The topic to consume messages from.
#         consumer_group (str): The consumer group name.
#         connection_string (str): The RabbitMQ connection string.
#         stale_threshold (int, optional): The time in seconds after which a connection
#             is considered stale. Defaults to 300 seconds (5 minutes).
#     """
    
#     def __init__(self, topic: str, stale_threshold: int = 300) -> None:
#         consumer_group = settings.SERVICES[settings.SERVICE_NAME]
#         super().__init__(topic, consumer_group)
#         self.__connection_string = settings.RABBITMQ_URL
#         self.__connection = None
#         self.__channel = None
#         self.__queue = None
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
#         # consumer_group is the queue and the topic is the exchange
#         # and it should be: consumer_group is exchange and topic is the queue & routing key
#         # (since it is direct queue type one routing key fits to a single queue (topic))
#         self.__connection = await aio_pika.connect_robust(self.__connection_string)
#         self.__channel = await self.__connection.channel()
#         exchange = await self.__channel.declare_exchange(self.consumer_group, aio_pika.ExchangeType.DIRECT)
#         self.__queue = await self.__channel.declare_queue(self.topic, durable=True)
#         await self.__queue.bind(exchange, routing_key=self.topic)
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

#     async def consume(self) -> AsyncIterator[Any]:
#         """
#         Consume messages from the queue.

#         Yields:
#             Any: The consumed message.
#         """
#         await self.__ensure_connection()
        
#         async with self.__queue.iterator() as queue_iter:
#             async for message in queue_iter:
#                 try:
#                     async with message.process(requeue=False):
#                         logger.debug(f"Received message: {message.body}")
#                         self.__last_activity = time.time()
#                         yield Message.model_validate_json(message.body)
#                         logger.debug(f"Successfully processed and acked message: {message.body}")
#                 except Exception as e:
#                     logger.error(f"Error processing message: {e}")
#                     message.nack(requeue=True)
#                     continue

#     async def close(self):
#         """Close the connection to RabbitMQ."""
#         if self.__connection and not self.__connection.is_closed:
#             await self.__connection.close()
#         self.__connection = None
#         self.__channel = None
#         self.__queue = None

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

#     async def generic_consumer(topic: str, handler_function: callable, request_type: type):    
#         try:
#             consumer = AsyncConsumerRetriever().get_consumer(topic)
#             async with consumer:
#                 async for msg in consumer.consume():                    
#                     try:
#                         request = request_type(**msg.data)
#                         await handler_function(request)
#                     except ValidationError as ve:
#                         logger.error(f"Validation error for message: {msg.data}. Error: {ve}")
#                     except Exception as e:
#                         logger.error(f"Error processing message: {msg.data}. Error: {e}")
#         except Exception as e:
#             logger.error(f"Error setting up consumer for topic '{topic}': {e}")

#     async def generic_producer(topic: str, body: dict):
#         try:
#             producer = AsyncProducerRetriever().get_producer(topic)
#             metadata = Metadata(
#                 service=os.getenv("SERVICE_NAME", "default_service"),
#                 system="On-Prem",
#                 timestamp=datetime.now().isoformat()
#             )
#             msg = Message(
#                 id=str(uuid.uuid4()),
#                 target=topic,
#                 source=os.getenv("SERVICE_NAME", "default_service"),
#                 data=body,
#                 metadata=metadata
#             )
#             async with producer:
#                 await producer.produce(msg.model_dump_json())
#                 logger.info(f"Message successfully produced to topic '{topic}': {msg}")
#         except Exception as e:
#             logger.error(f"Error producing message to topic '{topic}': {e}")