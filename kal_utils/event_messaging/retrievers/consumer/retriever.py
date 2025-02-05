# Standard Library Imports
import os
import json
import asyncio

# Local Module imports
from kal_utils.event_messaging.retrievers.consumer.base_consumer_retriever import BaseConsumerRetriever

# load environment variables
from kal_utils.event_messaging.core.settings import settings

SYS_EVENT_MODE = settings.rabbitmq.event_mode

class ConsumerRetriever(BaseConsumerRetriever):
    def __init__(self) -> None:
        """initializes the correct consumer class

        Raises:
            ValueError: raises error if no valid SYS_EVENT_MODE str is available
        """
        super().__init__()
        self.__mode = SYS_EVENT_MODE
        if self.mode == "kafka":
            from kal_utils.event_messaging.consumers.kafka import KalSenseKafkaConsumer
            self.__consumer_cls = KalSenseKafkaConsumer
        elif self.mode == "rabbitmq":
            from kal_utils.event_messaging.consumers.rabbitmq import KalSenseRabbitMQConsumer
            self.__consumer_cls = KalSenseRabbitMQConsumer
        elif self.mode == "pubsub":
            from kal_utils.event_messaging.consumers.pubsub import KalSensePubSubConsumer
            self.__consumer_cls = KalSensePubSubConsumer
        else:
            self.__consumer_cls = None
            raise ValueError("[ERROR] ValueError: Must Contain a valid string representing an event ")
    
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
        
                
        return self.__consumer_cls(topic=topic) #, consumer_group=consumer_group)


# ------------------------------------------- UNIT TEST -------------------------------------------

# Unittest
import unittest
from unittest.mock import patch, MagicMock
class TestConsumerRetriever(unittest.TestCase):
    @patch('builtins.SYS_MESSAGING_QUEUE_MODE', 'kafka')
    def test_init_kafka(self):
        with patch('__main__.KalSenseKafkaConsumer') as mock_kafka:
            retriever = ConsumerRetriever()
            self.assertEqual(retriever.mode, 'kafka')
            self.assertEqual(retriever._ConsumerRetriever__consumer, mock_kafka)

    @patch('builtins.SYS_MESSAGING_QUEUE_MODE', 'rabbitmq')
    def test_init_rabbitmq(self):
        with patch('__main__.KalSenseRabbitMQConsumer') as mock_rabbitmq:
            retriever = ConsumerRetriever()
            self.assertEqual(retriever.mode, 'rabbitmq')
            self.assertEqual(retriever._ConsumerRetriever__consumer, mock_rabbitmq)

    @patch('builtins.SYS_MESSAGING_QUEUE_MODE', 'pubsub')
    def test_init_pubsub(self):
        with patch('__main__.KalSensePubSubConsumer') as mock_pubsub:
            retriever = ConsumerRetriever()
            self.assertEqual(retriever.mode, 'pubsub')
            self.assertEqual(retriever._ConsumerRetriever__consumer, mock_pubsub)

    @patch('builtins.SYS_MESSAGING_QUEUE_MODE', 'invalid')
    def test_init_invalid(self):
        with self.assertRaises(ValueError):
            ConsumerRetriever()

    @patch('builtins.SYS_MESSAGING_QUEUE_MODE', 'kafka')
    def test_get_consumer(self):
        with patch('__main__.KalSenseKafkaConsumer') as mock_kafka:
            mock_kafka.return_value = MagicMock()
            retriever = ConsumerRetriever()
            consumer = retriever.get_consumer("test-topic", "test-group")
            mock_kafka.assert_called_once_with(topic="test-topic", consumer_group="test-group")
            self.assertIsInstance(consumer, MagicMock)

if __name__ == '__main__':
    unittest.main()