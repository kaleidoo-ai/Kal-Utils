import os
import json
import pika
from dotenv import load_dotenv

from .base import KalSenseBaseProducer
from core.settings import settings
from core.logging import logger
# from loguru import logger

load_dotenv()

class KalSenseRabbitMQProducer(KalSenseBaseProducer):
    """
    RabbitMQ implementation of KalSenseBaseProducer.
    
    This class provides functionality to produce messages to a RabbitMQ queue.
    """
    __producer_conn = os.getenv("RABBITMQ_CONN_STR")
    
    def __init__(self, topic: str) -> None:
        """
        Initialize the RabbitMQ producer.
        
        Args:
            topic (str): The topic/queue to produce messages to.
            producer_group (str): The producer group name.
        """
        producer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic=topic, producer_group=producer_group)
        self.__connection = None
        self.__channel = None
        
        self.__connect()

    def __connect(self) -> None:
        """
        Establish a connection to RabbitMQ and create a channel.
        """
        host = settings.RABBITMQ_SERVICE_HOST
        port = settings.RABBITMQ_SERVICE_PORT
        user = settings.DEFAULT_USER_NAME
        password = settings.DEFAULT_PASSWORD
        logger.info(f"Connecting to RabbitMQ: {host}:{port}")
        self.__credentials = pika.PlainCredentials(username=user, password=password)
        self.__connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=int(port), credentials=self.__credentials))
        self.__channel = self.__connection.channel()
        self.__queue = self.__channel.queue_declare(queue=self.topic, durable=True, auto_delete=False, exclusive=False)


    def produce(self, message):
        """
        Produce a message to the RabbitMQ queue.
        
        Args:
            message: The message to be produced.
        """
        try:
            self.__channel.basic_publish(
                exchange='',
                routing_key=self.topic,
                body=json.dumps(message).encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Error producing message: {e}")

    def __del__(self):
        """
        Cleanup method to close the RabbitMQ connection when the object is deleted.
        """
        try:
            if self.__connection and self.__connection.is_open:
                self.__connection.close()
            delattr(self, "__topic")
            delattr(self, "__producer_group")
            return True
        except Exception as e:
            logger.warning(f"An Error Occurred: {e}")
            return False