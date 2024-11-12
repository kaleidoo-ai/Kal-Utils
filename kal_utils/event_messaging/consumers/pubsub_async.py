# Built-in imports
import asyncio
import json
from threading import Thread
from typing import AsyncGenerator
import os
import tracemalloc
from pydantic_core import ValidationError
import uuid

# Third Party imports
from google.cloud import pubsub_v1
from google.api_core.exceptions import NotFound
from google.oauth2 import service_account


# Local imports
from kal_utils.event_messaging.consumers.base import KalSenseBaseConsumer
from core.settings import settings
from core.schema import Message
# For System And API Testing In Containerized Environment
from core.logging import logger
# For Local Testing, single file execution, etc.
# from loguru import logger


# If credentials aren't loaded yet, load credentials
if not settings.PUBSUB_CREDENTIALS_JSON:
    try:
        with open(settings.PUBSUB_CREDENTIALS_PATH) as f:
            settings.PUBSUB_CREDENTIALS_JSON = json.load(f)
    except:
        os.environ['PUBSUB_CREDENTIALS_JSON'] = '{}'

# WARNING: comment in production, shows full traceback when used asynchronously
tracemalloc.start()

class KalSenseAioPubSubConsumer(KalSenseBaseConsumer):
    def __init__(self, topic: str) -> None:
        logger.debug("Initializing KalSenseAioPubSubConsumer")
        subscription_name = settings.SERVICES[settings.SERVICE_NAME]+str(uuid.uuid4())[:10]
        super().__init__(topic, subscription_name)
        credentials_json = settings.PUBSUB_CREDENTIALS_JSON
        self.__subscription_name = subscription_name
        self.__credentials = service_account.Credentials.from_service_account_info(credentials_json)
        self.__consumer = pubsub_v1.SubscriberClient(credentials=self.__credentials)
        self.__subscription_path = self.__consumer.subscription_path(self.__credentials.project_id, self.__subscription_name)
        self.__topic_path = self.__consumer.topic_path(self.__credentials.project_id, self.topic)
        self.logger = logger
        self.subscription = None
        self.__message_queue = asyncio.Queue()
        logger.debug("Finished pubsub consumer init")
        
    async def __aenter__(self):
        logger.debug("consumer __aenter__ called, ensuring connection is established")
        await self.__ensure_connection()
        logger.debug("Connection established, verifying topic and subscription")
        await self.verify_topic()
        logger.debug("Topic and subscription verified")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug(f"start aexit {self.__consumer}")
        if self.subscription:
            if not self.subscription.cancelled():
                logger.debug("Cancelling subscription")
                self.subscription.cancel()
                self.subscription.result()
                self.subscription = None
                logger.debug("Subscription cancelled")
        else:
            logger.debug("Subscription already Cancelled")
            
        if self.__consumer:
            self.__consumer.close()
            self.__consumer = None
            logger.debug("closed consumer")
        else:
            logger.debug("Consumer Already Closed")
        
    
    async def __ensure_connection(self):
        if not self.__consumer:
            self.__consumer = pubsub_v1.SubscriberClient(credentials=self.__credentials)
            self.__subscription_path = self.__consumer.subscription_path(self.__credentials.project_id, self.__subscription_name)
            self.__topic_path = self.__consumer.topic_path(self.__credentials.project_id, self.topic)

    async def verify_topic(self):
        logger.debug("Verifying topic")
        publisher = pubsub_v1.PublisherClient(credentials=self.__credentials)
        try:
            publisher.get_topic(request={"topic": self.__topic_path})
            logger.debug("Topic exists")
        except NotFound:
            logger.debug("Topic not found, creating topic")
            publisher.create_topic(request={"name": self.__topic_path})
        logger.debug("Topic verified, verifying subscription")
        try:
            self.__consumer.get_subscription(request={"subscription": self.__subscription_path})
            logger.debug("Subscription exists")
        except NotFound:
            logger.debug("Subscription not found, creating subscription")
            self.__consumer.create_subscription(
                request={"name": self.__subscription_path, "topic": self.__topic_path}
            )
        logger.debug("Subscription verified")

    def message_callback(self, message: pubsub_v1.subscriber.message.Message):
        data = json.loads(message.data.decode('utf-8'))
        logger.debug(f"Received message: {data}")
        try:
            if data.get("target", "") == settings.SERVICE_NAME:
                logger.debug(f"trying to get a new event loop")
                loop = asyncio.new_event_loop()
                logger.debug("Got New Loop, setting as event loop")
                asyncio.set_event_loop(loop)
                logger.debug(f"finished setting event loop, running self.__message_queue.put")
                loop.run_until_complete(self.__message_queue.put((data, message)))
                logger.debug("Done running the put in a new event loop")
                message.ack()
                loop.close()
                logger.debug(f"message acked and queued2")
            else:
                message.ack()
                logger.debug(f"message acked and NOT queued")
        except Exception as e:
            logger.error(f"Error in message_callback method: {str(e)}")
            
    def start_consumer(self):
        try:
            self.subscription = self.__consumer.subscribe(self.__subscription_path, callback=self.message_callback)
            logger.debug(f"consumer subscribe started")
        except Exception as e:
            if not self.subscription.cancelled():
                self.subscription.cancel()
                self.subscription.result()
            logger.error(f"Error in consume method: {str(e)}")
            raise e
    
    async def consume(self) -> AsyncGenerator:
            logger.debug("starting consumers.KalSenseAioKafkaConsumer")
            if not self.subscription:
                # await self.verify_topic()
                logger.debug(f"Starting Consumer")
                self.started_consumer = Thread(target=self.start_consumer)
                self.started_consumer.start()
                self.started_consumer.join()

            try:
                logger.debug(f"Waiting for message...")
                while not self.subscription.cancelled():
                    logger.debug(f"check queue size")
                    while self.__message_queue.qsize() == 0:
                        await asyncio.sleep(0.001)
                    logger.debug(f"queue is not empty ")
                    msg_data, message = await self.__message_queue.get()
                    logger.debug(f"Message received and processed: {msg_data}, yielding message")
                    yield Message.model_validate(msg_data)
                logger.debug(f"exit while loop not self.subscription.cancelled ")
            except asyncio.QueueEmpty:
                logger.info("No new messages")
                await self.consume().__anext__()
            except ValidationError as e:
                self.logger.error(f"Validation error while consuming message: {str(e)}")
            except Exception as e:
                if not self.subscription.cancelled():
                    self.subscription.cancel()
                    self.subscription.result()
                self.logger.error(f"Error while consuming message: {str(e)}")

    def __del__(self):
        try:
            if self.__consumer:
                self.__consumer.close()
                self.__consumer = None
            if self.subscription:    
                if not self.subscription.cancelled():
                    self.subscription.cancel()
                    self.subscription.result()
        except Exception as e:
            self.logger.error(f"Error while closing consumer: {str(e)}")