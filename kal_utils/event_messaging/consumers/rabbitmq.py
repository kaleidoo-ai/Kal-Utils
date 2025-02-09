import os
import json
import pika
import ssl

from kal_utils.event_messaging.consumers.base import KalSenseBaseConsumer
from kal_utils.event_messaging.core.logging import logger
from kal_utils.event_messaging.core.settings import settings
# from loguru import logger


class KalSenseRabbitMQConsumer(KalSenseBaseConsumer):
    """
    RabbitMQ implementation of KalSenseBaseConsumer.
    
    This class provides functionality to consume messages from a RabbitMQ queue.
    """
    __consumer_conn = settings.rabbitmq.url
    
    def __init__(self, topic: str) -> None:
        consumer_group = settings.SERVICES[settings.SERVICE_NAME]
        super().__init__(topic=topic, consumer_group=consumer_group)
        self.__connection = None
        self.__channel = None
        self.__queue = None
        
        self.__connect()

    def __connect(self,
                  user:str=os.getenv("RABBITMQ_USER"),
                  password:str=os.getenv("RABBITMQ_PASS"),
                  host:str=os.getenv("RABBITMQ_HOST"),
                  port:str=os.getenv("RABBITMQ_PORT"),
                  protocol:str=os.getenv("RABBITMQ_PROTO")):
        logger.info(f"Connecting to RabbitMQ: {host}:{port}")
        self.__credentials = pika.PlainCredentials(username=user, password=password)
        # Default connection parameters
        connection_params = pika.ConnectionParameters(
            host=host,
            port=int(port),
            credentials=self.__credentials
        )

        # If SSL is enabled, configure SSL context and update connection parameters
        if protocol=="amqps":
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Optionally, you can load certificates if needed
            client_cert_path = os.getenv("RABBITMQ_CLIENT_CERT_PATH")
            client_key_path = os.getenv("RABBITMQ_CLIENT_KEY_PATH")
            ca_cert_path = os.getenv("RABBITMQ_CA_CERT_PATH")

            if client_cert_path and client_key_path and ca_cert_path:
                context.load_cert_chain(certfile=client_cert_path, keyfile=client_key_path)
                context.load_verify_locations(cafile=ca_cert_path)
                context.check_hostname = True  # Verify server hostname matches certificate
                context.verify_mode = ssl.CERT_REQUIRED  # Enforce certificate validation
            
            # Add SSL options to connection parameters
            ssl_options = pika.SSLOptions(context)
            connection_params.ssl_options = ssl_options

        # Establish the connection
        self.__connection = pika.BlockingConnection(connection_params)
        self.__channel = self.__connection.channel()

        # Set QoS to control the number of messages sent over the channel before an ack is required
        self.__channel.basic_qos(prefetch_count=10)

        # Declare the queue (replace with your queue/topic name)
        self.__queue = self.__channel.queue_declare(queue=self.topic, durable=True, auto_delete=False, exclusive=False)

    def consume(self):
        for method_frame, properties, body in self.__channel.consume(self.topic):
            try:
                decoded_message = json.loads(body.decode('utf-8'))
                yield decoded_message
                self.__channel.basic_ack(method_frame.delivery_tag)
            except Exception as e:
                logger.error(f"Error while consuming asynchronously from RabbitMQ {e}")
                self.__channel.basic_nack(method_frame.delivery_tag)
                continue

    def __del__(self):
        try:
            if self.__connection and self.__connection.is_open:
                self.__connection.close()
            delattr(self, "__topic")
            delattr(self, "__consumer_group")
            return True
        except Exception as e:
            logger.warning(f"An Error Occurred while deleting KalSenseRabbitMQConsumer instance:\n{e}")
            return False