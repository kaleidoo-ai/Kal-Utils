import os
import json
from google.cloud import pubsub_v1
from google.auth import jwt
from kal_utils.event_messaging.producers.base import KalSenseBaseProducer
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.logging import logger


class KalSensePubSubProducer(KalSenseBaseProducer):
    __producer_cls = pubsub_v1.PublisherClient
    # __producer_conn = json.loads(os.getenv("PUBSUB_PRODUCER_CONNECTION"))
    
    def __init__(self, topic: str) -> None:
        producer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic=topic, producer_group=producer_group)
        
        # Create credentials
        with open("../ai-orchestrator-57b48-aa5d73fe17.json", "r") as f:
            info = json.loads(f.read())
        credentials = jwt.Credentials.from_service_account_info(info=info)
        
        # Create a new KalSenseProducer instance
        self.__producer = KalSensePubSubProducer.__producer_cls(credentials=credentials)
        
        # Derive topic path from topic
        project_id = os.getenv("PUBSUB_PRODUCER_PROJECT")
        self.__topic_path = self.__producer.topic_path(project=project_id, topic=self.topic)
    
    def produce(self, message: dict):
        try:
            data = json.dumps(message).encode("utf-8")
            future = self.__producer.publish(self.__topic_path, data)
            message_id = future.result()
            # TODO: logging and verboseness
            logger.info(f"Published message to {self.__topic_path} with ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"An error occurred while publishing the message: {e}")
            return None
    
    def __verify_or_create_topic(self):
        try:
            self.__producer.get_topic(self.__topic_path)
            return True
        except Exception as get_exception:
        # If the topic doesn't exist, create it
            if "404" in str(get_exception):
                try:
                    topic = self.__producer.create_topic(name=self.__topic_path)
                    logger.info(f"Topic '{topic.name}' created.")
                except Exception as creation_exception:
                    # TODO: Logging
                    logger.critical(f"An error occurred while creating the topic: {creation_exception}")
            else:
                # TODO: Logging
                logger.warning(f"An error occurred while getting the topic: {get_exception}")
            
        
    
    def __del__(self):
        try:
            # Delete all instance attributes
            delattr(self, "__topic")
            # Close the connection to the PubSub client
            self.__producer.close()
            del self
            return True
        except Exception as e:
            logger.error(f"An Error Occurred: {e}")
            return False

# ------------------------------------------- UNIT TEST -------------------------------------------
import unittest
from unittest.mock import patch, MagicMock

class TestKalSensePubSubProducer(unittest.TestCase):

    @patch.dict(os.environ, {"PUBSUB_PRODUCER_CONNECTION": '{"project_id": "test-project"}'})
    @patch('google.auth.jwt.Credentials.from_service_account_info')
    @patch('google.cloud.pubsub_v1.PublisherClient')
    def setUp(self, mock_publisher, mock_credentials):
        self.mock_publisher = mock_publisher
        self.mock_credentials = mock_credentials
        self.producer = KalSensePubSubProducer("test-topic")

    def test_init(self):
        self.assertEqual(self.producer.topic, "test-topic")
        self.mock_credentials.assert_called_once()
        self.mock_publisher.assert_called_once()

    def test_producer_property(self):
        with self.assertRaises(AttributeError):
            _ = self.producer.producer

    @patch('builtins.print')
    def test_produce(self, mock_print):
        mock_future = MagicMock()
        mock_future.result.return_value = "test-message-id"
        self.mock_publisher.return_value.publish.return_value = mock_future

        message = {"key": "value"}
        result = self.producer.produce(message)

        self.assertEqual(result, "test-message-id")
        self.mock_publisher.return_value.publish.assert_called_once_with(
            'projects/test-project/topics/test-topic',
            b'{"key": "value"}'
        )
        mock_print.assert_called_with("Published message to projects/test-project/topics/test-topic with ID: test-message-id")

    @patch('builtins.print')
    def test_produce_error(self, mock_print):
        self.mock_publisher.return_value.publish.side_effect = Exception("Test error")

        result = self.producer.produce({"key": "value"})

        self.assertIsNone(result)
        mock_print.assert_called_with("An error occurred while publishing the message: Test error")

    def test_del(self):
        result = self.producer.__del__()
        self.assertTrue(result)
        self.mock_publisher.return_value.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
    
    
    
# class KalSensePubSubProducer(KalSenseBaseProducer):
#     __consumer_cls = pubsub_v1.PublisherClient
#     __consumer_conn = json.loads(os.getenv("PUBSUB_CONSUMER_CONNECTION"))
    
#     def __init__(self, topic: str, producer_group: str) -> None:
#         self.__topic = topic
#         self.__producer_group = producer_group
    
#     @property
#     def topic(self) -> str:
#         return self.__topic
    
#     @property
#     def producer_group(self) -> str:
#         return self.__producer_group
    
#     @property
#     def producer(self):
#         raise AttributeError("Cannot access self.producer attribute, to produce to topic call obj.produce() instead")
    
#     def produce(self):
#         pass
    
#     def __del__(self):
#         pass
    