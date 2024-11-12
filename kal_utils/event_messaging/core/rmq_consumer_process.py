import asyncio
import multiprocessing
from event_messaging.retrievers.consumer.async_retriever import AsyncConsumerRetriever
from event_messaging.core.logging import logger

class RMQConsumerProcess(multiprocessing.Process):
    def __init__(
        self,
        topic: str,
        queue: multiprocessing.Queue,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.topic = topic
        self.queue = queue
        self.consumer = AsyncConsumerRetriever().get_consumer(self.topic)

    async def process_message(self, msg):
        # Callback Method for Future processing
        return msg

    async def consume_messages(self):
        # Connect to RabbitMQ
        logger.debug("Starting to consume messages")
        # async with self.consumer as consumer:
        async with self.consumer as consumer:
            async for msg in consumer.consume():
                self.queue.put(self.process_message(msg))
            

    def run(self):
        asyncio.run(self.consume_messages())