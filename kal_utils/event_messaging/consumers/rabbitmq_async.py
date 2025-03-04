import asyncio
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from pydantic import ValidationError
from typing import AsyncIterator, Optional
from contextlib import AsyncExitStack

from kal_utils.event_messaging.consumers.base import KalSenseBaseConsumer
from kal_utils.event_messaging.core.logging import logger
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.schema import Message
#from kal_utils.event_messaging.core.utils import RabbitMQConnectionManager, ConnectionConfig


class KalSenseAioRabbitMQConsumer(KalSenseBaseConsumer):
    """
    An asynchronous RabbitMQ consumer that can handle either a direct or fanout exchange.
    If `topic` is provided, a direct exchange is used.
    If `exchange_name` is provided (and topic=None), a fanout exchange is used.
    """

    def __init__(self, 
                 topic: Optional[str] = None, 
                 exchange_name: Optional[str] = None) -> None:
        # Decide exchange type based on which parameter is used
        if topic and not exchange_name:
            exchange_type = "direct"
            self._queue_name = topic
            self._exchange_name = topic  # or the same as group
        elif exchange_name and topic:
            exchange_type = "fanout"
            self._queue_name = topic  # For fanout, typically queue name can be unique or derived
            self._exchange_name = exchange_name
        else:
            raise ValueError(
                "Please provide exactly one of `topic` (for direct exchange) "
                "or `exchange_name` (for fanout exchange), but not both."
            )

        super().__init__(self._queue_name, settings.core.service_name, exchange_type=exchange_type)
        from kal_utils.event_messaging.core.utils.connection_manager import RabbitMQConnectionManager,ConnectionConfig
        # Create a RabbitMQ connection manager (pool)
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

    async def _setup_channel(self, connection: aio_pika.Connection) -> None:
        self._channel = await connection.channel()
        await self._channel.set_qos(prefetch_count=100)

        # Decide the exchange type at runtime
        if self.exchange_type == "direct":
            exchange_type = aio_pika.ExchangeType.DIRECT
        else:  # "fanout"
            exchange_type = aio_pika.ExchangeType.FANOUT

        # The "main" exchange
        exchange = await self._channel.declare_exchange(
            self._exchange_name,
            exchange_type,
            durable=True
        )

        # Also declare a DLX (dead-letter exchange) if needed
        self._dlx_exchange = await self._channel.declare_exchange(
            f"{self._queue_name}_dlx",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        # Declare queue with the same name as self.topic (or derived for fanout)
        self._queue = await self._channel.declare_queue(
            self._queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self._dlx_exchange.name,
                "x-max-priority": 10
            }
        )

        # For direct, we bind with a routing key = queue name
        # For fanout, the routing key is ignored, but you still can pass a key
        await self._queue.bind(exchange, routing_key=self._queue_name)

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
        """
        Manually move a poison message to the DLX (dead-letter exchange).
        """
        await self._dlx_exchange.publish(
            aio_pika.Message(
                body=message.body,
                headers=message.headers,
                message_id=message.message_id
            ),
            routing_key=self._queue_name
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
