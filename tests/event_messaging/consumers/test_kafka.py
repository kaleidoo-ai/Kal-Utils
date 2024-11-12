from dotenv import load_dotenv
import os
import json

# For Unittests
import unittest
from unittest.mock import patch, MagicMock

# import relevant consumer from third party library
from kafka import KafkaConsumer

# import logger
# from core.logging import logger
from loguru import logger

# NOTE: REQUIRES the kafka environment variables (consumer, consumer connection string)
# load environment variables
load_dotenv()

# Import
from monitoring.event_messaging.consumers.kafka import KalSenseKafkaConsumer

# ------------------------------------------- UNIT TEST -------------------------------------------

# Unittest
class TestKalSenseKafkaConsumer(unittest.TestCase):
    @patch.dict(os.environ, {"KAFKA_CONSUMER_CONNECTION": '{"host": "localhost", "port": 9092}'})
    @patch('kafka.KafkaConsumer')
    def setUp(self, mock_kafka_consumer):
        self.mock_kafka_consumer = mock_kafka_consumer
        self.consumer = KalSenseKafkaConsumer("test-topic", "test-group")

    def test_init(self):
        self.assertEqual(self.consumer.topic, "test-topic")
        self.assertEqual(self.consumer.consumer_group, "test-group")

    def test_consumer_property(self):
        with self.assertRaises(AttributeError):
            _ = self.consumer.consumer

    @patch('kafka.KafkaConsumer')
    async def test_consume(self, mock_kafka_consumer):
        mock_kafka_consumer.return_value.__aiter__.return_value = [
            MagicMock(value=json.dumps({"key": "value"}).encode('utf-8'))
        ]
        messages = [message async for message in self.consumer.consume()]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].value, {"key": "value"})

    def test_del(self):
        result = self.consumer.__del__()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()