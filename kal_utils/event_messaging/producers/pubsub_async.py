import asyncio
import time
from typing import Any
import json
from concurrent import futures

from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.api_core.exceptions import NotFound


from kal_utils.event_messaging.producers.base import KalSenseBaseProducer
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.schema import Message

from kal_utils.event_messaging.core.logging import logger
# NOTE: Uncomment the next line and comment the previous line for single file testing
# from loguru import logger


class KalSenseAioPubSubProducer(KalSenseBaseProducer):
    def __init__(self, topic: str) -> None:
        producer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic, producer_group)
        self.__project_id = settings.PUBSUB_CREDENTIALS_JSON['project_id']
        self.__credentials = service_account.Credentials.from_service_account_info(settings.PUBSUB_CREDENTIALS_JSON)
        self.__producer = None
        self.__topic_path = None

    async def __aenter__(self):
        logger.debug("Entered __aenter__")
        await self.__ensure_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Entered __aexit__")
        await self.close()

    async def __ensure_connection(self):
        if not self.__producer:
            logger.debug("Creating PubSub client")
            self.__producer = pubsub_v1.PublisherClient(credentials=self.__credentials)
            logger.debug("Created PubSub client, getting topic path")
            self.__topic_path = self.__producer.topic_path(self.__project_id, self.topic)
            logger.debug("Created topic path, verifying topic")
            await self.verify_topic()
            logger.debug("Topic verified")

    async def verify_topic(self):
        try:
            self.__producer.get_topic(request={"topic": self.__topic_path})
        except NotFound:
            self.__producer.create_topic(request={"name": self.__topic_path})

    async def produce(self, message: Message):
        await self.__ensure_connection()
        
        # Convert message to JSON string if it's not already a string
        if not isinstance(message, str):
            message = json.dumps(message)

        # Publish the message
        future = self.__producer.publish(self.__topic_path, message.encode('utf-8'))
        
        # Wait for the publish to complete
        try:
            futures.wait([future], return_when=futures.ALL_COMPLETED)
            # await asyncio.wrap_future(future)
            logger.info(f"Published message {message}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    async def close(self):
        if self.__producer and self.__producer.transport:
            self.__producer.transport.close()
        self.__producer = None

    def __del__(self):
        if hasattr(self, '_KalSenseAioPubSubPublisher__consumer'):
            self._sync_close()

    def _sync_close(self):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.close())
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.close())
                loop.close()
        except Exception as e:
            logger.warning(f"error occurred while closing {e}")