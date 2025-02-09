import os
import json
import pika
import ssl
from dotenv import load_dotenv

from kal_utils.event_messaging.producers.base import KalSenseBaseProducer
from kal_utils.event_messaging.core.settings import settings
from kal_utils.event_messaging.core.logging import logger
# from loguru import logger

# load_dotenv()

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
        host = settings.RABBITMQ_HOST
        port = settings.RABBITMQ_PORT
        user = settings.RABBITMQ_USER
        password = settings.RABBITMQ_PASS
        use_ssl = settings.RABBITMQ_PROTO.lower() == 'amqps'  # Check if SSL should be enabled

        logger.info(f"Connecting to RabbitMQ: {host}:{port} using {'SSL' if use_ssl else 'non-SSL'}")

        # Set up credentials for RabbitMQ connection
        self.__credentials = pika.PlainCredentials(username=user, password=password)
        
        # Default connection parameters
        connection_params = pika.ConnectionParameters(
            host=host,
            port=int(port),
            credentials=self.__credentials
        )

        # If SSL is enabled, configure SSL context and update connection parameters
        if use_ssl:
            # Create SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            # Load certificates if needed
            client_cert_path = settings.RABBITMQ_CLIENT_CERT_PATH
            client_key_path = settings.RABBITMQ_CLIENT_KEY_PATH
            ca_cert_path = settings.RABBITMQ_CA_CERT_PATH

            if client_cert_path and client_key_path and ca_cert_path:
                logger.info("Loading SSL certificates")
                context.load_cert_chain(certfile=client_cert_path, keyfile=client_key_path)
                context.load_verify_locations(cafile=ca_cert_path)
                context.check_hostname = True  # Ensure server hostname matches certificate
                context.verify_mode = ssl.CERT_REQUIRED  # Enforce certificate verification

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
                body=json.dumps(message).encode("utf-8"),
                properties=pika.BasicProperties(pika.DeliveryMode.Persistent)
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