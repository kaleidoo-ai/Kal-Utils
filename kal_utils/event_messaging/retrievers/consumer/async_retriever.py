# Standard Library Imports
import os
import json
import asyncio

# Local Module imports
from kal_utils.event_messaging.retrievers.consumer.base_consumer_retriever import BaseConsumerRetriever

# load environment variables
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.logging import logger
# SYS_EVENT_MODE = settings.SYS_EVENT_MODE

class AsyncConsumerRetriever(BaseConsumerRetriever):
    def __init__(self) -> None:
        """initializes the correct consumer class

        Raises:
            ValueError: raises error if no valid SYS_EVENT_MODE str is available
        """
        logger.debug(f"starting __init__ of {self}")
        super().__init__()
        self.__mode = settings.SYS_EVENT_MODE
        if self.mode == "kafka":
            from kal_utils.event_messaging.consumers.kafka_async import KalSenseAioKafkaConsumer
            self.__consumer_cls = KalSenseAioKafkaConsumer
        elif self.mode == "rabbitmq":
            from kal_utils.event_messaging.consumers.rabbitmq_async import KalSenseAioRabbitMQConsumer
            self.__consumer_cls = KalSenseAioRabbitMQConsumer
        elif self.mode == "pubsub":
            from kal_utils.event_messaging.consumers.pubsub_async import KalSenseAioPubSubConsumer
            self.__consumer_cls = KalSenseAioPubSubConsumer
        else:
            self.__consumer_cls = None
            raise ValueError("[ERROR] ValueError: Must Contain a valid string representing an event messaging tool: (kafka, pubsub, rabbitmq)")
    
    @property
    def mode(self):
        return self.__mode
    
    @property
    def consumer_cls(self):
        raise ValueError("Cannot access self.consumer_cls attribute. to receive a consumer instance, call obj.get_consumer() instead")


    def get_consumer(self, topic:str) -> object:
        """return a child instance of KalSenseBaseConsumer with the connection details.

        Args:
            topic (str): topic to consume from.
            consumer_group (str): consumer group for tracing.

        Returns:
            KalSenseBaseConsumer: a child instance of KalSenseBaseConsumer with connection details already
        """
        
        logger.debug(f"returning {self.__consumer_cls} instance")    
        return self.__consumer_cls(topic=topic)