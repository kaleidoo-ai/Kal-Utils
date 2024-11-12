# from dotenv import load_dotenv
import os
import json

# For Unittests
import unittest
from unittest.mock import patch, MagicMock

# import relevant Producer from third party library
import kafka
from kafka import KafkaProducer
from kafka.future import Future
from kafka.errors import KafkaError
import kafka.future

# NOTE: REQUIRES the kafka environment variables (Producer, Producer connection string)
# load environment variables
# load_dotenv()

# Import
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.logging import logger
from kal_utils.event_messaging.producers.base import KalSenseBaseProducer

# Uncomment next line to test env vars
# print (os.getenv('KAFKA_BOOTSTRAP_SERVERS_CONNECTION'))


class KalSenseKafkaProducer(KalSenseBaseProducer):
            __producer_cls = KafkaProducer
            __producer_conn = settings.KAFKA_BOOTSTRAP_SERVERS
            
            def __init__(self, topic:str) -> None:
                producer_group = settings.SERVICES[settings.SERVICE_NAME]
                super().__init__(topic, producer_group)
                self.__producer = KalSenseKafkaProducer.__producer_cls(bootstrap_servers=[KalSenseKafkaProducer.__producer_conn],
                                                                       value_serializer = lambda m: json.dumps(m).encode('utf-8'))
            
            
            def produce(self, json_msg:dict) -> kafka.future.Future:
                """Produces a kafka message to topic=self.__topic and returns a future (will receive produce results in the future.).

                Args:
                    json_msg (dict): message dictionary that contains message Constructed from Schema.

                Returns:
                    kafka.future.Future: a Future object that will hold 
                """
                future = self.__producer.send(self.topic, json_msg)
                future.add_callback(lambda result: logger.info(f"Message sent to {self.topic}: {result.value()}"))
                try:
                    record_metadata = future.get(timeout=10)
                except KafkaError as e:
                    logger.error(f"Error sending message through KalSenseKafkaProducer:\n{e}")
                    future.set_exception(e)
                return future
                    
            
            def __del__(self):
                try:
                    delattr(self, "__topic")
                    delattr(self, "__producer_group")
                    del self
                    return True
                except Exception as e:
                    logger.warning(f"An Error Occurred while deleting KalSenseKafkaProducer instance: {e}")
                    return False
                

# ------------------------------------------- UNIT TEST -------------------------------------------

# Unittest
class TestKalSenseKafkaProducer(unittest.TestCase):
    @patch.dict(os.environ, {"KAFKA_PRODUCER_CONNECTION": '{"host": "localhost", "port": 9092}'})
    @patch('kafka.KafkaProducer')
    def setUp(self, mock_kafka_producer):
        self.mock_kafka_producer = mock_kafka_producer
        self.producer = KalSenseKafkaProducer("test-topic", "test-group")

    def test_init(self):
        self.assertEqual(self.producer.topic, "test-topic")
        self.assertEqual(self.producer.producer_group, "test-group")

    def test_Producer_property(self):
        with self.assertRaises(AttributeError):
            _ = self.Producer.Producer

    @patch('kafka.KafkaProducer')
    async def test_Produce(self, mock_kafka_Producer):
        mock_kafka_Producer.return_value.__aiter__.return_value = [
            MagicMock(value=json.dumps({"key": "value"}).encode('utf-8'))
        ]
        messages = [message async for message in self.Producer.Produce()]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].value, {"key": "value"})

    def test_del(self):
        result = self.Producer.__del__()
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()