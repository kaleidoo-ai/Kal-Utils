import os
import json
from google.cloud import pubsub_v1
from google.auth import jwt
from monitoring.event_messaging.consumers.pubsub import KalSensePubSubConsumer
# from core.logging import logger
from loguru import logger

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