import sys
# from kal_utils.event_messaging.core.logging import logger
import traceback
import asyncio
import psutil
from datetime import datetime
import os
import json
import asyncio
import uuid

from pydantic import ValidationError
# from kal_utils.event_messaging.core.logging import logger
import logging
# When deployed into a larger API comment the line below
#from loguru import logger
from kal_utils.event_messaging.core.schema import Message
from kal_utils.event_messaging.retrievers.consumer.async_retriever import AsyncConsumerRetriever
from kal_utils.event_messaging.retrievers.producer.async_retriever import AsyncProducerRetriever
from kal_utils.event_messaging.core.schema import Message, Metadata

original_stop_method = asyncio.AbstractEventLoop.stop

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def handle_system_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Uncaught exception:\n{error_msg}")

    # Log additional system information
    import psutil
    logger.info(f"CPU usage: {psutil.cpu_percent()}%")
    logger.info(f"Memory usage: {psutil.virtual_memory().percent}%")
    logger.info(f"Disk usage: {psutil.disk_usage('/').percent}%")

def handle_task_exception(task: asyncio.Task) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass  # Task cancellation is not an error
    except Exception:
        logger.exception(f"Unhandled exception in background task {task.get_name()}")

async def monitor_tasks_handler():
    while True:
        for task in asyncio.all_tasks():
            if task.done() and not task.cancelled():
                handle_task_exception(task)
        await asyncio.sleep(60)  # Check every minute


async def monitor_resources_handler():
    while True:
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
            logger.warning(f"High resource usage detected: CPU {cpu_percent}%, Memory {memory_percent}%, Disk {disk_percent}%")
        
        await asyncio.sleep(60)  # Check every minute
    
async def heartbeat():
    while True:
        logger.info("Application heartbeat")
        await asyncio.sleep(300)  # Log every 5 minutes

# handle loop errors
def patched_stop(self):
    logger.warning("Event loop is stopping", stack_info=True)
    original_stop_method(self)

async def generic_consumer(
    handler_function: callable,
    request_type: type,
    topic: str = None,
    exchange_name: str = None,
):
    """
    Generic consumer function to retrieve messages from a direct or fanout exchange.

    Usage:
      - If you want direct exchange: 
          generic_consumer(handler_function, MyModel, topic="my_topic")
      - If you want fanout exchange:
          generic_consumer(handler_function, MyModel, exchange_name="my_fanout_exchange")
    """
    try:
        consumer = AsyncConsumerRetriever()
        consumer = consumer.get_consumer(topic=topic, exchange_name=exchange_name)
        async with consumer:
            async for msg in consumer.consume():
                try:
                    # request_type is the pydantic model the developer wants to parse into
                    request = request_type(**msg.data)
                    # Call the appropriate handler function
                    if handler_function.__code__.co_argcount == 1:  # handler expects only the request
                        await handler_function(request)
                    else:  # handler expects both request and source
                        await handler_function(request, msg.source)
                except ValidationError as ve:
                    logger.error(f"Validation error for message: {msg.data}. Error: {ve}")
                except Exception as e:
                    logger.error(f"Error processing message: {msg.data}. Error: {e}")
    except Exception as e:
        logger.error(f"Error setting up consumer for topic/exchange '{topic or exchange_name}': {e}")

async def generic_producer(
    body: dict,
    topic: str = None,
    exchange_name: str = None
):
    """
    Generic producer function to send messages to a direct or fanout exchange.

    Usage:
      - If you want direct exchange:
          generic_producer(body={"foo": "bar"}, topic="my_topic")
      - If you want fanout exchange:
          generic_producer(body={"foo": "bar"}, exchange_name="my_fanout_exchange")
    """
    try:
        producer = AsyncProducerRetriever()
        producer = producer.get_producer(topic=topic, exchange_name=exchange_name)
        
        # Build pydantic "Message"
        metadata = Metadata(
            service=os.getenv("SERVICE_NAME", "default_service"),
            system="On-Prem",
            timestamp=datetime.now().timestamp()
        )
        msg = Message(
            id=uuid.uuid4(),
            target=topic or exchange_name,
            source=os.getenv("SERVICE_NAME", "default_service"),
            data=body,
            metadata=metadata
        )

        async with producer:
            await producer.produce(msg)
            logger.info(f"Message successfully produced to '{topic or exchange_name}': {msg}")
    except Exception as e:
        logger.error(f"Error producing message to '{topic or exchange_name}': {e}")