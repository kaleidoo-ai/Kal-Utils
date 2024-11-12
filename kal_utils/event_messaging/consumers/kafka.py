from dotenv import load_dotenv
import os
import json
from typing import Generator

# For Unittests
import unittest
from unittest.mock import patch, MagicMock

# import relevant consumer from third party library
from kafka import KafkaConsumer

# import logger
# Comment in standalone testing
from core.logging import logger
# Uncomment in standalone testing
# from loguru import logger

# NOTE: REQUIRES the kafka environment variables (consumer, consumer connection string)
# load environment variables
load_dotenv()

# Import
from .base import KalSenseBaseConsumer
from core.settings import settings




class KalSenseKafkaConsumer(KalSenseBaseConsumer):
            __consumer_cls = KafkaConsumer
            __consumer_conn = settings.KAFKA_BOOTSTRAP_SERVERS
            
            def __init__(self, topic:str) -> None:
                consumer_group = settings.SERVICES[settings.SERVICE_NAME]
                super().__init__(topic=topic, consumer_group=consumer_group)
                self.__consumer = KalSenseKafkaConsumer.__consumer_cls(self.topic,
                                                                       bootstrap_servers=[KalSenseKafkaConsumer.__consumer_conn],
                                                                       group_id=self.consumer_group,
                                                                       auto_offset_reset='earliest',
                                                                       value_deserializer= lambda x: json.loads(x.decode('utf-8')))
            
            def consume(self) -> Generator:
                try:
                    for message in self.__consumer:
                        try:
                            yield message
                        except Exception as e:
                            logger.warning(f"Error in delivering message: {e}")
                            continue
                except Exception as e:
                    logger.error(f"Error trying to consume message: {e}")
            
            def __del__(self):
                try:
                    delattr(self, "__topic")
                    delattr(self, "__consumer_group")
                    del self
                    logger.info("Consumer deleted")
                    return True
                except Exception as e:
                    logger.error(f"An Error Occurred While Deleting {__name__}.KalSenseKafkaConsumer.__del__: {e}")
                    return False
                

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