import asyncio
import aio_pika
from pydantic import ValidationError
from typing import Any, Optional
from contextlib import AsyncExitStack

from kal_utils.event_messaging.producers.base import KalSenseBaseProducer
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.logging import logger
from kal_utils.event_messaging.core.schema import Message



class KalSenseAioRabbitMQProducer(KalSenseBaseProducer):
    """
    An asynchronous RabbitMQ producer that can handle either a direct or fanout exchange.
    If `topic` is provided, a direct exchange is used.
    If `exchange_name` is provided (and topic=None), a fanout exchange is used.
    """

    def __init__(self, 
                 topic: Optional[str] = None, 
                 exchange_name: Optional[str] = None):
        # Decide exchange type
        if topic and not exchange_name:
            exchange_type = "direct"
            self._exchange_name = topic  # or some other naming
            self._routing_key = topic
        elif exchange_name and not topic:
            exchange_type = "fanout"
            self._exchange_name = exchange_name
            self._routing_key = ""  # routing key is typically ignored in fanout
        else:
            raise ValueError(
                "Please provide exactly one of `topic` (for direct exchange) "
                "or `exchange_name` (for fanout exchange), but not both."
            )

        super().__init__(topic or exchange_name, settings.core.service_name, exchange_type=exchange_type)
        from kal_utils.event_messaging.core.utils.connection_manager import RabbitMQConnectionManager, ConnectionConfig
        
        self._connection_manager = RabbitMQConnectionManager(
            settings.rabbitmq.url,
            config=ConnectionConfig(
                pool_size=settings.rabbitmq.pool_size,
                connection_timeout=settings.rabbitmq.connection_timeout,
                idle_timeout=settings.rabbitmq.idle_timeout
            )
        )
        self._channel: Optional[aio_pika.Channel] = None
        self._exchange: Optional[aio_pika.Exchange] = None

    async def __aenter__(self):
        await self._connection_manager.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _setup_channel(self, connection: aio_pika.Connection) -> None:
        self._channel = await connection.channel()

        # Decide exchange type
        if self.exchange_type == "direct":
            exchange_type = aio_pika.ExchangeType.DIRECT
        else:  # "fanout"
            exchange_type = aio_pika.ExchangeType.FANOUT

        # Declare the exchange (durable)
        self._exchange = await self._channel.declare_exchange(
            self._exchange_name,
            exchange_type,
            durable=True
        )

    async def produce(self, message: Any, **kwargs) -> None:
        async with AsyncExitStack() as stack:
            connection = await stack.enter_async_context(
                self._connection_manager.acquire()
            )
            if not self._channel or self._channel.is_closed:
                await self._setup_channel(connection)

            # If the user didn't pass a pydantic Message, parse/validate
            if not isinstance(message, Message):
                message = Message.model_validate(message)

            aio_message = aio_pika.Message(
                body=message.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=str(message.id),
                content_type='application/json'
            )

            # For direct, we use self._routing_key; for fanout, an empty key is typical
            await self._exchange.publish(
                aio_message,
                routing_key=self._routing_key,
                timeout=settings.rabbitmq.connection_timeout
            )

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
                logger.warning(f"Producer cleanup error: {str(e)}")
