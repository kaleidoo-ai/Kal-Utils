import asyncio
import multiprocessing
from retrievers.consumer.async_retriever import ConsumerRetriever
from core.logging import logger

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
        self.consumer = ConsumerRetriever().get_consumer(self.topic)

    async def process_message(self, msg):
        pass

    async def consume_messages(self):
        # Connect to RabbitMQ
        logger.debug("Starting to consume messages")
        # async with self.consumer as consumer:
        async with self.consumer as consumer:
            async for msg in consumer.consume():
                self.queue.put(self.process_message(msg))
            

    def run(self):
        asyncio.run(self.consume_messages())