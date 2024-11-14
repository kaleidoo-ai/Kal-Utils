# Standard Library Imports
import os
import json

# For Unittest
import unittest
from unittest.mock import patch, MagicMock

# Local Module imports
from kal_utils.event_messaging.retrievers.producer.base_producer_retriever import BaseProducerRetriever

# load environment variables
from kal_utils.event_messaging.core.settings import settings

SYS_EVENT_MODE = settings.SYS_EVENT_MODE

class ProducerRetriever(BaseProducerRetriever):
    def __init__(self) -> None:
        """initializes the correct producer class

        Raises:
            ValueError: raises error if no valid SYS_EVENT_MODE str is available
        """
        super().__init__()
        self.__mode = SYS_EVENT_MODE
        if self.mode == "kafka":
            from kal_utils.event_messaging.producers.kafka import KalSenseKafkaProducer
            self.__producer_cls = KalSenseKafkaProducer
        elif self.mode == "rabbitmq":
            from kal_utils.event_messaging.producers.rabbitmq import KalSenseRabbitMQProducer
            self.__producer_cls = KalSenseRabbitMQProducer
        elif self.mode == "pubsub":
            from kal_utils.event_messaging.producers.pubsub import KalSensePubSubProducer
            self.__producer_cls = KalSensePubSubProducer
        else:
            self.__producer_cls = None
            raise ValueError("[ERROR] ValueError: Must Contain a valid string representing an event ")
    
    @property
    def mode(self):
        return self.__mode
    
    def get_producer(self, topic:str, producer_group:str) -> object:
        """return a child instance of KalSenseBaseProducer with the connection details.

        Args:
            topic (str): topic to consume from.
            producer_group (str): producer group for tracing.

        Returns:
            KalSenseBaseProducer: a child instance of KalSenseBaseProducer with connection details already
        """
        
                
        return self.__producer_cls(topic=topic, producer_group=producer_group)


# ------------------------------------------- UNIT TEST -------------------------------------------

class TestProducerRetriever(unittest.TestCase):
    @patch('os.getenv')
    def test_init_kafka(self, mock_getenv):
        mock_getenv.return_value = json.dumps("kafka")
        with patch('producers.kafka.KalSenseKafkaProducer') as mock_kafka:
            retriever = ProducerRetriever()
            self.assertEqual(retriever.mode, "kafka")
            self.assertEqual(retriever._ProducerRetriever__producer, mock_kafka)

    @patch('os.getenv')
    def test_init_rabbitmq(self, mock_getenv):
        mock_getenv.return_value = json.dumps("rabbitmq")
        with patch('producers.rabbitmq.KalSenseRabbitMQProducer') as mock_rabbitmq:
            retriever = ProducerRetriever()
            self.assertEqual(retriever.mode, "rabbitmq")
            self.assertEqual(retriever._ProducerRetriever__producer, mock_rabbitmq)

    @patch('os.getenv')
    def test_init_pubsub(self, mock_getenv):
        mock_getenv.return_value = json.dumps("pubsub")
        with patch('producers.pubsub.KalSensePubSubProducer') as mock_pubsub:
            retriever = ProducerRetriever()
            self.assertEqual(retriever.mode, "pubsub")
            self.assertEqual(retriever._ProducerRetriever__producer, mock_pubsub)

    @patch('os.getenv')
    def test_init_invalid(self, mock_getenv):
        mock_getenv.return_value = json.dumps("invalid")
        with self.assertRaises(ValueError):
            ProducerRetriever()

    def test_get_producer(self):
        with patch('os.getenv', return_value=json.dumps("kafka")):
            with patch('producers.kafka.KalSenseKafkaProducer') as mock_kafka:
                retriever = ProducerRetriever()
                producer = retriever.get_producer("test_topic", "test_group")
                mock_kafka.assert_called_once_with(topic="test_topic", producer_group="test_group")
                self.assertEqual(producer, mock_kafka.return_value)

if __name__ == '__main__':
    unittest.main()