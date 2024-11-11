import sys
sys.path.insert(0,'../event_messaging')

from datetime import datetime
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from google.cloud import pubsub_v1
from consumers.pubsub_async import KalSenseAioPubSubConsumer
from core.settings import settings
from core.schema import Message, Metadata
from core.logging import logger

@pytest.fixture
def mock_pubsub_client():
    with patch('google.cloud.pubsub_v1.SubscriberClient') as mock_client:
        yield mock_client

@pytest.fixture
def mock_service_account():
    with patch('google.oauth2.service_account.Credentials.from_service_account_info') as mock_creds:
        yield mock_creds

@pytest.fixture
def consumer(mock_pubsub_client, mock_service_account):
    return KalSenseAioPubSubConsumer("test-topic")

@pytest.mark.asyncio
async def test_init(consumer):
    # print(await anext(consumer))
    # consumer = await consumer
    assert consumer.topic == "test-topic"
    assert consumer._KalSenseAioPubSubConsumer__subscription_name == settings.SERVICES[settings.SERVICE_NAME]
    logger.info("PYTEST: consumer topic and subscription name validated")

@pytest.mark.asyncio
async def test_verify_topic(consumer, mock_pubsub_client):
    publisher_mock = MagicMock()
    mock_pubsub_client.return_value.topic_path.return_value = "test-topic-path"
    mock_pubsub_client.return_value.subscription_path.return_value = "test-subscription-path"

    with patch('google.cloud.pubsub_v1.PublisherClient', return_value=publisher_mock):
        await consumer.verify_topic()

    publisher_mock.get_topic.assert_called_once()
    mock_pubsub_client.return_value.get_subscription.assert_called_once()
    logger.info("PYTEST: consumer topic and get_subscription verified")

# @pytest.mark.asyncio
# async def test_message_callback(consumer):
#     mock_message = MagicMock()
#     mock_message.data = json.dumps({"target": settings.SERVICE_NAME, "test": "data"}).encode('utf-8')

#     with patch.object(consumer, '_KalSenseAioPubSubConsumer__message_queue') as mock_queue:
#         consumer.message_callback(mock_message)

#     mock_queue.put.assert_called_once()
#     mock_message.ack.assert_called_once()
#     logger.info("PYTEST: message_callback verified")

@pytest.mark.asyncio
async def test_start_consumer(consumer):
    with patch.object(consumer, '_KalSenseAioPubSubConsumer__consumer') as mock_consumer:
        consumer.start_consumer()

    mock_consumer.subscribe.assert_called_once()

@pytest.mark.asyncio
async def test_consume(consumer):
    metadata = Metadata(system = settings.SYS_EVENT_MODE,
                        service = settings.SERVICE_NAME,
                        timestamp = datetime.now().isoformat())
    data = {"content": f"Test message 1 for {consumer.topic}"}
    mock_message = Message(
        id = '1',
        target = settings.SERVICE_NAME,
        source = settings.SERVICE_NAME,
        metadata = metadata,
        data = data
    )
    consumer._KalSenseAioPubSubConsumer__message_queue = AsyncMock()
    consumer._KalSenseAioPubSubConsumer__message_queue.get.return_value = (mock_message.model_dump(), None)
    consumer.subscription = MagicMock()
    consumer.subscription.cancelled.return_value = False

    messages = []
    async for message in consumer.consume():
        messages.append(message)
        break  # Break after first message to avoid infinite loop

    assert len(messages) == 1
    assert messages[0] == mock_message

@pytest.mark.asyncio
async def test_aenter_aexit(mock_pubsub_client, mock_service_account):
    consumer = KalSenseAioPubSubConsumer("test-topic")

    with patch.object(consumer, 'verify_topic'):
        async with consumer:
            assert consumer._KalSenseAioPubSubConsumer__consumer is not None

    assert consumer._KalSenseAioPubSubConsumer__consumer is None
    assert consumer.subscription is None

if __name__ == "__main__":
    pytest.main()