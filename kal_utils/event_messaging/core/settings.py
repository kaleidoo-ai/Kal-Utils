import os
import json
from typing import Dict, List, Union
from pydantic import AnyHttpUrl, Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings

class RabbitMQSettings(BaseSettings):
    """RabbitMQ-specific configuration"""
    host: str = Field(..., alias="RABBITMQ_SERVICE_HOST")
    port: int = Field(5672, alias="RABBITMQ_SERVICE_PORT")
    url: str = Field(..., alias="RABBITMQ_URL")
    connection_timeout: int = Field(30, alias="RABBITMQ_CONNECTION_TIMEOUT")
    pool_size: int = Field(5, alias="RABBITMQ_POOL_SIZE")

    @field_validator('url')
    def validate_url(cls, v):
        if not v.startswith("amqp://"):
            raise ValueError("Invalid RabbitMQ URL format")
        return v

class CoreSettings(BaseSettings):
    """Application core configuration"""
    project_name: str = Field(..., alias="PROJECT_NAME")
    service_name: str = Field(..., alias="SERVICE_NAME")
    version: str = Field("1.0.0", alias="VERSION")
    allowed_origins: List[AnyHttpUrl] = Field(default=[], alias="ALLOWED_ORIGINS")
    
    @field_validator('allowed_origins', mode='before')
    def parse_origins(cls, value):
        if isinstance(value, str):
            return value.split(',')
        return value

class TopicSettings(BaseSettings):
    """Message topic configuration"""
    mappings: Dict[str, Dict[str, str]] = Field(..., alias="TOPICS")
    
    @field_validator('mappings', mode='before')
    def parse_topics(cls, value):
        if isinstance(value, str):
            return json.loads(value)
        return value

class Settings(BaseSettings):
    """Main application settings"""
    core: CoreSettings = CoreSettings()
    rabbitmq: RabbitMQSettings = RabbitMQSettings()
    topics: TopicSettings = TopicSettings()
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = 'ignore'

# Simplified initialization
settings = Settings()


# OLD SETTINGS

# from typing import List, Union, Dict
# import os
# import json
# import dotenv

# from pydantic import AnyHttpUrl, Field, field_validator
# from pydantic_settings import BaseSettings
# # from core.utils.setup import setup_settings

# # WARNING: The following line should only be un-commented if you are in local testing...
# #          It is up to the DevOps team in your company to make sure that these are CONSISTENT
# #          Across Services (IP, Or DNS name) and that every env var is addressed.
# #          It needs to be stressed that this is still an EXPERIMENTAL feature.
# #          !!!! Refinement of necessary or un-necessary env vars can occur !!!!
# # dotenv.load_dotenv()

# # print (os.environ)

# class Settings(BaseSettings):
#     # General Settings
#     PROJECT_NAME: str = Field(default=os.environ["PROJECT_NAME"])
#     SYS_EVENT_MODE: str = Field(default=os.environ["SYS_EVENT_MODE"])
#     TOPICS: Dict = Field(default=json.loads(os.environ["TOPICS"]))
#     ALLOWED_ORIGINS: Union[str, List[AnyHttpUrl]] = Field([], env="ALLOWED_ORIGINS")
#     SERVICES: Dict = Field(default=json.loads(os.environ["SERVICES"]))
#     SERVICE_NAME: str = Field(default=os.environ["SERVICE_NAME"])
#     VERSION : str = Field(default=os.environ["VERSION"])
#     DEFAULT_USER_NAME: str = Field(default=os.environ["DEFAULT_USER_NAME"])
#     DEFAULT_PASSWORD: str = Field(default=os.environ["DEFAULT_PASSWORD"])
#     CREATE_TASK_TRIGGER_SOURCE: str = Field(default="kal_sense")
        
#     # Kafka Settings
#     KAFKA_TOPIC: str = Field(default=json.loads(os.environ["TOPICS"])[os.environ["SERVICE_NAME"]]["incoming"])
#     KAFKA_BOOTSTRAP_SERVERS: str = Field(default=os.environ["KAFKA_BOOTSTRAP_SERVERS"])
#     KAFKA_TOPICS: List[str] = Field(default=json.loads(os.environ["KAFKA_TOPICS"]))
    
#     # RabbitMQ Settings
#     RABBITMQ_SERVICE_HOST: str = Field(default=os.environ["RABBITMQ_SERVICE_HOST"])
#     RABBITMQ_SERVICE_PORT: str = Field(default=os.environ["RABBITMQ_SERVICE_PORT"])
#     RABBITMQ_URL: str = Field(default=os.environ["RABBITMQ_URL"])
#     REDIS_URL: str = Field(default=os.environ["REDIS_URL"])
    
#     # PubSub Settings
#     # PUBSUB_PROJECT_ID: str = Field(default=os.environ["PUBSUB_PROJECT_ID"])
#     PUBSUB_CREDENTIALS_PATH: str = Field(default=os.environ["PUBSUB_CREDENTIALS_PATH"])
#     PUBSUB_CREDENTIALS_JSON: Dict = Field(default={})
    
    
#     class Config:
#         # env_file = ".env"
#         case_sensitive = True
#         env_file_encoding = "utf-8"
#         extra = 'allow'


# def setup_settings(settings: Settings) -> Settings:
#     """
#     Deduces Further settings such as Incoming Topic name, outgoing topic name, and consumer/producer names
#     """
#     if not settings.PUBSUB_CREDENTIALS_JSON:
#         try:
#             with open(settings.PUBSUB_CREDENTIALS_PATH) as f:
#                 settings.PUBSUB_CREDENTIALS_JSON = json.load(f)
#         except:
#             settings.PUBSUB_CREDENTIALS_JSON = '{}'
    
#     for service in settings.SERVICES.keys():
#         attribute_name = service.upper() + "_INCOMING_TOPIC"
#         setattr(settings, attribute_name, settings.TOPICS[service]["incoming"])
    
#     return settings

# settings = setup_settings(Settings())