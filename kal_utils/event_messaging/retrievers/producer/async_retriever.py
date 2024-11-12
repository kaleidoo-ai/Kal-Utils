# Standard Library Imports
import os
import json

# For Unittest
# import unittest
# from unittest.mock import patch, MagicMock

# Local Module imports
from kal_utils.event_messaging.retrievers.producer.base_producer_retriever import BaseProducerRetriever

# load environment variables
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.logging import logger

# SYS_EVENT_MODE = settings.SYS_EVENT_MODE

class AsyncProducerRetriever(BaseProducerRetriever):
    def __init__(self) -> None:
        """initializes the correct producer class

        Raises:
            ValueError: raises error if no valid SYS_EVENT_MODE str is available
        """
        logger.debug("start init ProducerRetriever")
        super().__init__()
        self.__mode = settings.SYS_EVENT_MODE
        if self.mode == "kafka":
            from producers.kafka_async import KalSenseAioKafkaProducer
            logger.debug("start init kafka:ProducerRetriever")
            self.__producer_cls = KalSenseAioKafkaProducer
        elif self.mode == "rabbitmq":
            from producers.rabbitmq_async import KalSenseAioRabbitMQProducer
            self.__producer_cls = KalSenseAioRabbitMQProducer
        elif self.mode == "pubsub":
            from producers.pubsub_async import KalSenseAioPubSubProducer
            self.__producer_cls = KalSenseAioPubSubProducer
        else:
            self.__producer_cls = None
            raise ValueError("[ERROR] ValueError: Must Contain a valid string representing an event ")
    
    @property
    def mode(self):
        return self.__mode
    
    def get_producer(self, topic:str) -> object:
        """return a child instance of KalSenseBaseProducer with the connection details.

        Args:
            topic (str): topic to consume from.

        Returns:
            KalSenseBaseProducer: a child instance of KalSenseBaseProducer with connection details already
        """
        return self.__producer_cls(topic=topic)