import os
import json

from google.cloud import pubsub_v1
from google.auth import jwt

from base import KalSenseBaseConsumer
from core.logging import logger
# from loguru import logger
from core.settings import settings


class KalSensePubSubConsumer(KalSenseBaseConsumer):
    __consumer_cls = pubsub_v1.SubscriberClient
    __consumer_conn = settings.PUBSUB_CREDENTIALS_JSON
    
    def __init__(self, topic: str) -> None:
        consumer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic=topic, consumer_group=consumer_group)
        
        # Derive subscription path from topic and consumer group
        project_id = self.__consumer_conn.get('project_id')
        self.__subscription_path = f'projects/{project_id}/subscriptions/{topic}-{consumer_group}'
        
        # Create credentials
        credentials = jwt.Credentials.from_service_account_info(info=KalSensePubSubConsumer.__consumer_conn)
        self.__consumer = KalSensePubSubConsumer.__consumer_cls(credentials=credentials)
    
    def consume(self):
        try:
            streaming_pull_future = self.__consumer.subscribe(
                self.__subscription_path, callback=self.__message_callback, flow_control=pubsub_v1.FlowControl(max_messages=1))
            logger.info(f"Listening for messages on {self.__subscription_path}")
            streaming_pull_future.result()
        except Exception as e:
            streaming_pull_future.cancel()
            logger.error(f"Listening for messages on {self.__subscription_path} threw an exception: {e}")
    
    def __message_callback(self, message):
        try:
            logger.info(f"Received message: {message}")
            data = json.loads(message.data.decode("utf-8"))
            yield data
            message.ack()
        except Exception as e:
            logger.error(f"Error processing message: {e}\nin __message_callback for pubsub subscription")
            message.nack()
    
    def __del__(self):
        try:
            # TODO:Delete all instance attributes
            delattr(self, "__topic")
            delattr(self, "__consumer_group")
            # TODO: Close the connection to the PubSub client
            self.__consumer.close()
            del self
            return True
        except Exception as e:
            logger.error(f"An Error Occurred While Deleting KalSensePubSubConsumer instance:\n{e}")
            return False
        

import unittest
from unittest.mock import patch, MagicMock
        
# ------------------------------------------- UNIT TEST -------------------------------------------
class TestKalSensePubSubConsumer(unittest.TestCase):

    @patch.dict(os.environ, {"PUBSUB_CONSUMER_CONNECTION": '{"project_id": "test-project"}'})
    @patch('google.auth.jwt.Credentials.from_service_account_info')
    @patch('google.cloud.pubsub_v1.SubscriberClient')
    def setUp(self, mock_subscriber, mock_credentials):
        self.mock_subscriber = mock_subscriber
        self.mock_credentials = mock_credentials
        self.consumer = KalSensePubSubConsumer("test-topic", "test-group")

    def test_init(self):
        self.assertEqual(self.consumer.topic, "test-topic")
        self.assertEqual(self.consumer.consumer_group, "test-group")
        self.mock_credentials.assert_called_once()
        self.mock_subscriber.assert_called_once()

    def test_consumer_property(self):
        with self.assertRaises(AttributeError):
            _ = self.consumer.consumer

    @patch('builtins.print')
    @patch('google.cloud.pubsub_v1.subscriber.futures.StreamingPullFuture')
    async def test_consume(self, mock_future, mock_print):
        mock_future_instance = MagicMock()
        self.mock_subscriber.return_value.subscribe.return_value = mock_future_instance

        await self.consumer.consume()

        self.mock_subscriber.return_value.subscribe.assert_called_once()
        mock_future_instance.result.assert_awaited_once()
        mock_print.assert_called_with("Listening for messages on projects/test-project/subscriptions/test-topic-test-group")

    @patch('builtins.print')
    def test_message_callback(self, mock_print):
        mock_message = MagicMock()
        mock_message.data.decode.return_value = '{"key": "value"}'

        callback = self.consumer._KalSensePubSubConsumer__message_callback
        result = next(callback(mock_message))

        self.assertEqual(result, {"key": "value"})
        mock_message.ack.assert_called_once()
        mock_print.assert_called()

    @patch('builtins.print')
    def test_message_callback_error(self, mock_print):
        mock_message = MagicMock()
        mock_message.data.decode.side_effect = Exception("Test error")

        callback = self.consumer._KalSensePubSubConsumer__message_callback
        list(callback(mock_message))  # Consume the generator

        mock_message.nack.assert_called_once()
        mock_print.assert_called_with("Error processing message: Test error")

    def test_del(self):
        result = self.consumer.__del__()
        self.assertTrue(result)
        self.mock_subscriber.return_value.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()